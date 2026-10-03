"""Materializa Silver municipal em JSON/Parquet com dicionario e rastreabilidade."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import logging
from pathlib import Path
from uuid import uuid4
from etapa_06_coleta_municipal import PROJETO, gravar


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ler(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def classificacao(o):return json.dumps(o['classificacoes'],ensure_ascii=False,sort_keys=True,separators=(',',':'))
def id_indicador(o):return o['tabela']+'_'+o['variavel_id']+'_'+hashlib.sha256(classificacao(o).encode()).hexdigest()[:16]
def campos_json(lista):return json.dumps(lista,ensure_ascii=False,sort_keys=True)


def executar(raiz,run_id,validacao=None,coleta=None):
    import pyarrow as pa
    import pyarrow.parquet as pq
    raiz=Path(raiz).resolve(); q=raiz/'quality'/'08_silver_municipal'/run_id
    q.mkdir(parents=True,exist_ok=False)
    log=logging.getLogger('silver_'+run_id);log.setLevel(logging.INFO)
    h=logging.FileHandler(q/'execucao.log',encoding='utf-8');log.addHandler(h)
    r={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO'}
    try:
        if validacao is None:
            pastas=sorted((raiz/'quality'/'07_validacao_municipal').glob('*/conclusao_07_validacao_municipal.json'))
            if not pastas:raise FileNotFoundError('Executar a etapa 07 antes da Silver')
            validacao=pastas[-1].parent
        validacao=Path(validacao).resolve()
        if validacao.is_file():validacao=validacao.parent
        conclusao=ler(validacao/'conclusao_07_validacao_municipal.json')
        regras=ler(validacao/'regras_validacao.json')
        if datetime.fromisoformat(conclusao['validacao_utc']).year!=datetime.now(timezone.utc).year:
            raise ValueError('Reexecutar etapa 07 para atualizar a politica de defasagem no ano corrente')
        if conclusao['projeto']!=PROJETO or conclusao['status']!='VALIDACAO_TECNICA_APROVADA_COM_LIMITACOES' or conclusao['regras_reprovadas'] or any(x['status']=='REPROVADO' for x in regras):
            raise ValueError('Validacao tecnica nao aprovada; promocao bloqueada')
        if len(regras)!=conclusao['total_regras'] or sum(x['status']=='APROVADO' for x in regras)!=conclusao['regras_aprovadas']:
            raise ValueError('Conclusao e regras inconsistentes')
        if coleta is None:coleta=Path(conclusao['coleta_entrada'])
        coleta=Path(coleta).resolve()
        for entrada in conclusao['entradas']:
            nome=str(entrada['arquivo']).replace('\\','/').rsplit('/',1)[-1]
            if sha(coleta/nome)!=entrada['sha256']:raise ValueError('Entrada alterada apos validacao: '+nome)
        log.info('Hashes das entradas reconciliados com etapa 07')
        obs=ler(coleta/'indicadores_municipais.json');catalogo=ler(validacao/'catalogo_uso_indicadores.json')
        geo=ler(coleta/'municipios_geografia.json');rotas=ler(coleta/'distancias_geodesicas.json');indices=ler(coleta/'indices_recalculados.json')
        catalogo_por={(o['codigo_ibge'],id_indicador(o)):o for o in catalogo}
        if len(catalogo)!=conclusao['ultimos_valores'] or len(catalogo_por)!=len(catalogo):raise ValueError('Catalogo incompleto ou duplicado')
        ultimos={}
        for o in obs:
            if o['valor'] is None:continue
            k=(o['codigo_ibge'],id_indicador(o))
            if k not in ultimos or o['ano_referencia']>ultimos[k]['ano_referencia']:ultimos[k]=o
        if set(catalogo_por)!=set(ultimos) or any(catalogo_por[k]['valor']!=o['valor'] or catalogo_por[k]['ano_referencia']!=o['ano_referencia'] for k,o in ultimos.items()):
            raise ValueError('Catalogo nao corresponde ao ultimo valor da serie')
        renda_inconclusiva={x['regra'].split('_',1)[1] for x in regras if x['regra'].startswith('R01_') and x['status']=='INCONCLUSIVO'}
        dicionario={};series=[]
        for o in obs:
            iid=id_indicador(o);k=(o['codigo_ibge'],iid);cat=catalogo_por.get(k)
            ultimo=o['valor'] is not None and k in ultimos and o['ano_referencia']==ultimos[k]['ano_referencia']
            unidade='%' if o['unidade'] in ('%','Percentual') else o['unidade']
            uso=('PERFIL_ESTRUTURAL' if o['grupo']=='censo' else 'CONTEXTO_HISTORICO' if o['status_atualidade']=='DEFASADO' else 'CANDIDATO_EDA') if o['valor'] is not None else 'SEM_VALOR_NUMERICO'
            limites=cat['limitacoes_uso'] if cat else ['Marcador preservado; consultar notas oficiais antes de interpretar']
            alerta=o['tabela']=='10296' and o['codigo_ibge'] in renda_inconclusiva
            linha={'codigo_ibge':o['codigo_ibge'],'municipio':o['municipio'],'uf':o['uf'],'indicador_id':iid,'ano_referencia':o['ano_referencia'],
              'valor':o['valor'],'unidade':unidade,'valor_original':str(o['valor_original']),'unidade_original':o['unidade_original'],
              'multiplicador':o['multiplicador'],'status_valor':o['status_valor'],'status_atualidade':o['status_atualidade'],'defasagem_anos':o['defasagem_anos'],
              'ultimo_valor_numerico':ultimo,'uso_proposto':uso,'candidato_eda':ultimo and uso in ('CANDIDATO_EDA','PERFIL_ESTRUTURAL'),
              'conferencia_distribuicao_renda_pendente':alerta,'fonte_url':o['url'],'fonte_sha256':o['sha256'],'coleta_utc':o['coleta_utc'],
              'url_metadados':o['url_metadados'],'limitacoes_uso_json':campos_json(limites)}
            series.append(linha)
            doc={'indicador_id':iid,'tabela':o['tabela'],'variavel_id':o['variavel_id'],'nome_oficial':o['indicador'],
              'classificacoes_json':classificacao(o),'unidade_silver':unidade,'unidade_original':o['unidade_original'],
              'escala_percentual':100 if unidade=='%' else None,'grupo':o['grupo'],'granularidade':'municipio + indicador/classificacao + ano',
              'url_metadados':o['url_metadados'],'definicao':'Nome e categorias oficiais preservados; detalhes metodologicos nos metadados',
              'limitacoes_uso_json':campos_json(limites)}
            if iid in dicionario:
                for campo in ['nome_oficial','unidade_silver','unidade_original','grupo']:
                    if dicionario[iid][campo]!=doc[campo]:raise ValueError('Dicionario com conflito: '+iid)
            else:dicionario[iid]=doc
        municipios=[]
        for m in geo:
            regional=m['regionalizacao']; imediata=regional.get('regiao-imediata') or {};intermediaria=imediata.get('regiao-intermediaria') or {}
            municipios.append({'codigo_ibge':m['codigo_ibge'],'municipio':m['municipio'],'uf':m['uf'],'cidade_expansao':m['alvo'],
              'latitude_centroide':m['latitude'],'longitude_centroide':m['longitude'],'tipo_coordenada':m['tipo_coordenada'],
              'regiao_imediata':imediata.get('nome'),'regiao_intermediaria':intermediaria.get('nome'),
              'fonte_url':m['url_geografia'],'fonte_sha256':m['sha256_geografia'],'versao_malha':m['versao_malha']})
        series.sort(key=lambda x:(x['codigo_ibge'],x['indicador_id'],x['ano_referencia']))
        atuais=[o for o in series if o['ultimo_valor_numerico']]
        distancias=[{'destino_codigo':o['destino_codigo'],'destino':o['destino'],'origem_codigo':o['origem_codigo'],'origem':o['origem'],
          'distancia_geodesica_centroides_km':o['distancia_geodesica_centroides_km'],'metodo':o['metodo'],'uso':o['uso'],
          'fontes_sha256_json':campos_json(o['fontes_sha256'])} for o in rotas]
        crescimento=[{k:v for k,v in o.items() if k!='fontes_sha256'}|{'fontes_sha256_json':campos_json(o['fontes_sha256'])} for o in indices]
        tabelas={'municipios':municipios,'dicionario_indicadores':list(dicionario.values()),'indicadores_serie':series,
                 'indicadores_ultimo_disponivel':atuais,'distancias_geodesicas':distancias,'crescimento_pib':crescimento}
        if len(series)!=conclusao['observacoes'] or len(atuais)!=conclusao['ultimos_valores']:raise ValueError('Contagem divergente da etapa 07')
        if len({(o['codigo_ibge'],o['indicador_id'],o['ano_referencia']) for o in series})!=len(series):raise ValueError('Chave Silver duplicada')
        saida=raiz/'datalake'/'02_silver'/run_id/'municipal'
        saida.mkdir(parents=True,exist_ok=False)
        inteiros={'ano_referencia','multiplicador','defasagem_anos','escala_percentual','ano_inicial','ano_final'}
        reais={'valor','latitude_centroide','longitude_centroide','distancia_geodesica_centroides_km','acumulado_percentual','taxa_anualizada_percentual'}
        bools={'ultimo_valor_numerico','candidato_eda','conferencia_distribuicao_renda_pendente','cidade_expansao'}
        exportacoes=[]
        for nome,linhas in tabelas.items():
            campos=list(linhas[0]);schema=pa.schema([(c,pa.int64() if c in inteiros else pa.float64() if c in reais else pa.bool_() if c in bools else pa.string()) for c in campos])
            table=pa.Table.from_pylist(linhas,schema=schema)
            json_path=saida/(nome+'.json');parquet_path=saida/(nome+'.parquet')
            gravar(json_path,linhas);pq.write_table(table,parquet_path,compression='snappy')
            if pq.read_table(parquet_path).to_pylist()!=ler(json_path):raise ValueError('Reconciliacao JSON x Parquet falhou: '+nome)
            exportacoes.append({'tabela':nome,'linhas':len(linhas),'sha256_json':sha(json_path),'sha256_parquet':sha(parquet_path),
                                'schema':str(schema),'reconciliacao':'APROVADA'})
            log.info('Exportada e reconciliada: %s, %s linhas',nome,len(linhas))
        textos={o['indicador_id']:o['nome_oficial'] for o in dicionario.values()}
        linhas=''.join('<tr>'+''.join('<td>'+html.escape(str(v if v is not None else ''))+'</td>' for v in [o['municipio'],textos[o['indicador_id']],o['valor'],o['unidade'],o['ano_referencia'],o['uso_proposto'],o['conferencia_distribuicao_renda_pendente'],o['indicador_id']])+'</tr>' for o in atuais)
        (saida/'conferencia_silver.html').write_text('<!doctype html><meta charset="utf-8"><title>Silver municipal</title><style>body{font:14px Arial;margin:24px}td,th{border:1px solid #ccc;padding:8px}table{border-collapse:collapse}th{background:#eef;position:sticky;top:0}</style><h1>'+PROJETO+'</h1><p>Ultimo valor numerico por categoria. Anos podem diferir entre municipios. Consulte o dicionario e as limitacoes. Distribuicoes de renda com pendencia nao devem ser consideradas completas.</p><table><tr><th>Municipio</th><th>Indicador</th><th>Valor</th><th>Unidade</th><th>Ano</th><th>Uso</th><th>Renda pendente</th><th>Indicador ID</th></tr>'+linhas+'</table>',encoding='utf-8')
        r.update({'status':'SILVER_GERADA_COM_LIMITACOES','validacao_run_id':conclusao['run_id'],'validacao_sha256':sha(validacao/'conclusao_07_validacao_municipal.json'),
           'coleta_entrada':str(coleta),'saida':str(saida),'exportacoes':exportacoes,'catalogo_uso_sha256':sha(validacao/'catalogo_uso_indicadores.json'),
           'observacoes_sem_valor':sum(o['valor'] is None for o in series),'uso_ultimos':dict(Counter(o['uso_proposto'] for o in atuais)),
           'municipios_renda_inconclusiva':sorted(renda_inconclusiva),'limites':['Hashes das tabelas Bronze verificados; respostas brutas HTTP ainda nao reconciliadas fisicamente',
           'Candidato a EDA nao e medida de demanda, lucro ou previsao','Centroides nao sao enderecos nem percursos rodoviarios','Comparacao com analise original reservada para encerramento']})
        gravar(saida/'manifesto_silver.json',r)
        return r
    except Exception as e:
        r.update(status='FALHA',erro=str(e));log.exception('Silver interrompida');raise
    finally:
        r['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_08_silver_municipal.json',r);h.close();log.removeHandler(h)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--validacao',type=Path,help='Pasta da etapa 07 escolhida');p.add_argument('--coleta',type=Path,help='Pasta Bronze escolhida; precisa corresponder aos hashes validados')
    a=p.parse_args();rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    r=executar(a.raiz,rid,a.validacao,a.coleta)
    print(json.dumps({k:r[k] for k in ['run_id','status','saida','uso_ultimos','observacoes_sem_valor']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
