"""Prepara bases analiticas sem estimar demanda ou combinar universos distintos."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq

PROJETO = 'potencial-de-mercado-e-expansao-comercial'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def gravar(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def canon(v):
    if isinstance(v, Decimal): return str(v)
    if isinstance(v, dict): return {k: canon(x) for k, x in v.items()}
    if isinstance(v, list): return [canon(x) for x in v]
    return v

def selecionar(raiz, tipo):
    nome, etapa, status = ('manifesto_silver.json', '08_silver_municipal', 'SILVER_GERADA_COM_LIMITACOES') if tipo == 'municipal' else ('manifesto_documental.json', '09_silver_documental', 'SILVER_DOCUMENTAL_GERADA_COM_PENDENCIAS')
    candidatos = sorted((raiz / 'datalake/02_silver').glob('*/' + tipo + '/' + nome), reverse=True)
    for p in candidatos:
        m = json.loads(p.read_text(encoding='utf-8'))
        q = raiz / 'quality' / etapa / m['run_id'] / ('conclusao_' + etapa + '.json')
        if m.get('status') == status and q.exists():
            conclusao = json.loads(q.read_text(encoding='utf-8'))
            if conclusao.get('status') == status and conclusao.get('run_id') == m['run_id']: return p.parent
    raise ValueError('Silver ' + tipo + ' sem manifesto e conclusao de qualidade correspondentes')

def carregar(p, tipo):
    nome = 'manifesto_silver.json' if tipo == 'municipal' else 'manifesto_documental.json'
    m = json.loads((p / nome).read_text(encoding='utf-8'))
    esperado = 'SILVER_GERADA_COM_LIMITACOES' if tipo == 'municipal' else 'SILVER_DOCUMENTAL_GERADA_COM_PENDENCIAS'
    if m.get('projeto') != PROJETO or m.get('status') != esperado: raise ValueError('Manifesto incompativel: ' + str(p))
    tabelas = {}
    for e in m['exportacoes']:
        t = e['tabela']
        if Path(t).name != t or t in tabelas: raise ValueError('Nome de tabela invalido ou repetido')
        j, a = p / (t + '.json'), p / (t + '.parquet')
        if sha(j) != e['sha256_json'] or sha(a) != e['sha256_parquet']: raise ValueError('Hash divergente: ' + t)
        dados = json.loads(j.read_text(encoding='utf-8'))
        arrow = pq.read_table(a)
        if len(dados) != e['linhas'] or arrow.num_rows != e['linhas'] or dados != canon(arrow.to_pylist()): raise ValueError('Reconciliacao divergente: ' + t)
        tabelas[t] = (dados, arrow)
    return m, tabelas

def executar(raiz, run_id, municipal=None, documental=None):
    raiz = Path(raiz).resolve()
    qualidade = raiz / 'quality/10_base_eda' / run_id
    qualidade.mkdir(parents=True, exist_ok=False)
    rel = {'projeto': PROJETO, 'run_id': run_id, 'inicio_utc': datetime.now(timezone.utc).isoformat(), 'status': 'EM_EXECUCAO', 'regras': []}
    def regra(nome, cond):
        rel['regras'].append({'regra': nome, 'resultado': 'APROVADA' if cond else 'REPROVADA'})
        if not cond: raise ValueError('Regra reprovada: ' + nome)
    def unico(rows, campos, nome):
        keys = [tuple(r[c] for c in campos) for r in rows]
        regra(nome, len(keys) == len(set(keys)) and all(all(x is not None for x in k) for k in keys))
    try:
        pm = Path(municipal).resolve() if municipal else selecionar(raiz, 'municipal')
        pd = Path(documental).resolve() if documental else selecionar(raiz, 'documental')
        mm, mt = carregar(pm, 'municipal'); md, dt = carregar(pd, 'documental')
        rel['entradas'] = [{'tipo': t, 'pasta': str(p), 'run_id': m['run_id'], 'manifesto_sha256': sha(p / n), 'tabelas': m['exportacoes']} for t,p,m,n in [('municipal',pm,mm,'manifesto_silver.json'),('documental',pd,md,'manifesto_documental.json')]]
        municipios = mt['municipios'][0]; dic = mt['dicionario_indicadores'][0]
        unico(municipios, ['codigo_ibge'], 'Municipios unicos'); unico(dic, ['indicador_id'], 'Indicadores unicos')
        cidades = {r['codigo_ibge']: r for r in municipios}; indicadores = {r['indicador_id']: r for r in dic}
        alvos = {k for k,v in cidades.items() if v['cidade_expansao']}; origens = set(cidades) - alvos
        regra('12 cidades de expansao e 5 origens', len(alvos) == 12 and len(origens) == 5)
        for nome, campos in [('indicadores_serie',['codigo_ibge','indicador_id','ano_referencia']),('indicadores_ultimo_disponivel',['codigo_ibge','indicador_id'])]:
            rows = mt[nome][0]; unico(rows, campos, 'Granularidade ' + nome)
            regra('Chaves municipais e indicadores ' + nome, all(r['codigo_ibge'] in alvos and r['indicador_id'] in indicadores for r in rows))
        serie = {(r['codigo_ibge'],r['indicador_id'],r['ano_referencia']):r for r in mt['indicadores_serie'][0]}
        regra('Ultimos valores pertencem a serie', all(serie.get((r['codigo_ibge'],r['indicador_id'],r['ano_referencia'])) == r for r in mt['indicadores_ultimo_disponivel'][0]))
        dist = mt['distancias_geodesicas'][0]
        unico(dist,['destino_codigo','origem_codigo'],'Pares geograficos unicos')
        regra('Cobertura geografica 12 por 5', {(r['destino_codigo'],r['origem_codigo']) for r in dist} == {(a,b) for a in alvos for b in origens})
        unico(mt['crescimento_pib'][0],['codigo_ibge'],'Crescimento por cidade')
        regra('Cobertura crescimento', {r['codigo_ibge'] for r in mt['crescimento_pib'][0]} == alvos)
        fontes = dt['fontes_documentais'][0]; unico(fontes,['source_sha256'],'Fontes documentais unicas')
        hashes = {r['source_sha256'] for r in fontes}
        for nome,(rows,_) in dt.items():
            if nome != 'pendencias_documentais' and rows and 'registro_id' in rows[0]: unico(rows,['registro_id'],'Registros documentais ' + nome)
            regra('Fontes existentes ' + nome, all(r.get('source_sha256') is None or r['source_sha256'] in hashes for r in rows))
        pdf_ids = {r['registro_id'] for r in dt['consumo_historico'][0]}
        imagens = dt['evidencias_imagens'][0]
        regra('JPEG vinculado ao PDF sem observacao adicional', all(r['registro_pdf_id'] in pdf_ids and r['imagem_sha256'] in hashes and r['duplicidade_semantica'] and not r['incluir_como_nova_observacao'] for r in imagens))
        unico(imagens,['registro_pdf_id'],'Uma evidencia por observacao PDF')
        regra('Precos com vigencia pendente preservada', all(not r['liberado_orcamento_atual'] and not r['vigencia_confirmada'] for r in dt['precos_produtos'][0]))
        enriquecidos = []
        for r in mt['indicadores_ultimo_disponivel'][0]:
            d = indicadores[r['indicador_id']]; c = cidades[r['codigo_ibge']]
            enriquecidos.append({**r, 'nome_oficial':d['nome_oficial'],'tabela_ibge':d['tabela'],'variavel_id':d['variavel_id'],'classificacoes_json':d['classificacoes_json'],'regiao_imediata':c['regiao_imediata'],'regiao_intermediaria':c['regiao_intermediaria']})
        regra('Juncao muitos para um preserva quantidade',len(enriquecidos) == len(mt['indicadores_ultimo_disponivel'][0]))
        painel=[]; periodos=[]
        for ident,d in indicadores.items():
            rows = [r for r in mt['indicadores_serie'][0] if r['indicador_id']==ident]
            ano = max(r['ano_referencia'] for r in rows)
            refs={r['codigo_ibge']:r for r in rows if r['ano_referencia']==ano}
            numericos=sum(refs.get(c,{}).get('valor') is not None for c in alvos)
            periodos.append({'indicador_id':ident,'nome_oficial':d['nome_oficial'],'classificacoes_json':d['classificacoes_json'],'ano_referencia_comum':ano,'cidades_com_valor':numericos,'cidades_sem_valor':len(alvos)-numericos,'criterio':'Maior ano presente na serie, inclusive marcadores sem valor; sem retroceder por cidade'})
            for codigo in sorted(alvos):
                r=refs.get(codigo); c=cidades[codigo]
                painel.append({'codigo_ibge':codigo,'municipio':c['municipio'],'uf':c['uf'],'indicador_id':ident,'nome_oficial':d['nome_oficial'],'classificacoes_json':d['classificacoes_json'],'ano_referencia':ano,'valor':None if r is None else r['valor'],'unidade':d['unidade_silver'],'status_valor':'SEM_REGISTRO_NO_PERIODO' if r is None else r['status_valor'],'candidato_eda':False if r is None else r['candidato_eda'],'renda_pendente':False if r is None else r['conferencia_distribuicao_renda_pendente'],'fonte_url':None if r is None else r['fonte_url'],'fonte_sha256':None if r is None else r['fonte_sha256']})
        regra('Painel completo sem preenchimento de ausencias',len(painel)==len(alvos)*len(indicadores))
        saida=raiz/'datalake/03_gold'/run_id/'base_eda'; saida.mkdir(parents=True,exist_ok=False)
        exportacoes=[]
        def exportar(nome, arrow):
            j=saida/(nome+'.json'); p=saida/(nome+'.parquet')
            gravar(j,canon(arrow.to_pylist())); pq.write_table(arrow,p,compression='snappy')
            regra('Reconciliacao exportacao '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(p).to_pylist()))
            exportacoes.append({'tabela':nome,'linhas':arrow.num_rows,'sha256_json':sha(j),'sha256_parquet':sha(p),'schema':str(arrow.schema)})
        exportar('indicadores_ultimo_disponivel_eda',pa.Table.from_pylist(enriquecidos))
        exportar('painel_periodo_comum',pa.Table.from_pylist(painel))
        exportar('controle_periodos',pa.Table.from_pylist(periodos))
        exportar('precos_referencia_eda',dt['precos_produtos'][1])
        limites=['Preparacao da EDA; sem ranking ou estimativa de demanda.', 'Painel usa o maior ano registrado por indicador; ausencias nao viram zero nem valores de anos anteriores.', 'Anos diferentes entre indicadores continuam explicitos. Periodo comum nao elimina diferencas metodologicas.', 'Candidato EDA nao dispensa conferencia de renda ou validade metodologica.', 'Estudos historicos permanecem na Silver documental como contexto; nao foram associados a cidades.', 'JPEG complementa PDF, sem duplicar amostra.', 'Precos historicos exigem confirmacao antes de orcamentos; cada pacote possui seu preco.', 'Distancias de centroides nao representam rotas, fretes ou enderecos.', 'Comparacao com analise original somente no encerramento.']
        rel.update(status='BASE_EDA_PREPARADA_COM_LIMITACOES',saida=str(saida),exportacoes=exportacoes,pendencias_documentais=len(dt['pendencias_documentais'][0]),limites=limites)
        gravar(saida/'manifesto_base_eda.json',rel)
        (saida/'LEIA_ANTES_DA_EDA.md').write_text('# Base da EDA\n\n'+'\n'.join('- '+x for x in limites)+'\n',encoding='utf-8')
        return rel
    except Exception as e:
        rel.update(status='FALHA',erro=str(e)); raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat()
        gravar(qualidade/'conclusao_10_base_eda.json',rel)
        (qualidade/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent); ap.add_argument('--municipal',type=Path); ap.add_argument('--documental',type=Path)
    a=ap.parse_args(); run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    print(json.dumps(executar(a.raiz,run,a.municipal,a.documental),ensure_ascii=False,indent=2))
