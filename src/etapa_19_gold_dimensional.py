"""Gold dimensional versionada, sem conexao SQL nem projecao de vendas."""
import argparse
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from contrato_dimensional import CONTRATO
from etapa_10_base_eda import PROJETO, carregar, sha, gravar
from etapa_11_eda_estrutura import selecionar, STATUS_BASE

STATUS='GOLD_DIMENSIONAL_VERIFICADA_COM_LIMITACOES'
DIMENSOES=[t for t in CONTRATO if '.dim_' in t]
TABELAS=[t for t in CONTRATO if t.startswith('gold.') or t in ['quality.evidencia_imagem','quality.pendencia','quality.registro_documental_auxiliar']]
CHAVES={'gold.dim_municipio':'codigo_ibge','gold.dim_periodo':'periodo_chave','gold.dim_indicador':'indicador_chave','gold.dim_fonte':'fonte_chave','gold.dim_ponto_distribuicao':'ponto_chave','gold.dim_produto':'produto_chave','gold.dim_estrato_estudo':'estrato_chave'}

def canon(v):
    if isinstance(v,Decimal):return str(v)
    if isinstance(v,datetime):return v.isoformat()
    if isinstance(v,dict):return {k:canon(x) for k,x in v.items()}
    if isinstance(v,list):return [canon(x) for x in v]
    return v

def texto(v):
    return json.dumps(canon(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def hash_obj(v):
    return hashlib.sha256(texto(v).encode('utf-8')).hexdigest()

def normalizar(v,c):
    if v is None:
        if not c['nullable']:raise ValueError('Nulo obrigatorio: '+c['nome'])
        return None
    t=c['tipo']
    if t=='decimal':
        p,s=map(int,c['args'].split(','));d=Decimal(str(v));q=d.quantize(Decimal(1).scaleb(-s))
        if not d.is_finite() or d!=q or abs(d)>=Decimal(10)**(p-s):raise ValueError('Perda decimal: '+c['nome'])
        return q
    if t=='bit':
        if v not in [True,False,0,1]:raise ValueError('Booleano invalido')
        return bool(v)
    if t in ['int','bigint','smallint']:
        i=int(v);bits={'smallint':16,'int':32,'bigint':64}[t]
        if Decimal(str(v))!=i or not -(2**(bits-1))<=i<2**(bits-1):raise ValueError('Inteiro invalido')
        return i
    if t=='datetime2':
        d=v if isinstance(v,datetime) else datetime.fromisoformat(v)
        return d.astimezone(timezone.utc).replace(tzinfo=None) if d.tzinfo else d
    v=str(v)
    if c['args']!='max':
        n=len(v.encode('utf-16-le'))//2 if t=='nvarchar' else len(v.encode('ascii'))
        if n>int(c['args']):raise ValueError('Texto excede '+c['nome'])
    return v

def schema(t):
    fields=[]
    for c in CONTRATO[t]:
        ty=c['tipo'];a=c['args']
        tipo=pa.decimal128(*map(int,a.split(','))) if ty=='decimal' else pa.bool_() if ty=='bit' else pa.int64() if ty in ['int','bigint','smallint'] else pa.timestamp('us') if ty=='datetime2' else pa.string()
        fields.append(pa.field(c['nome'],tipo,nullable=c['nullable']))
    return pa.schema(fields)

def validar_rows(t,rows):
    cols=CONTRATO[t];out=[]
    for r in rows:
        if set(r)!=set(c['nome'] for c in cols):raise ValueError('Colunas divergentes: '+t)
        out.append({c['nome']:normalizar(r[c['nome']],c) for c in cols})
    pk=cols[0]['nome']
    if len({r[pk] for r in out})!=len(out):raise ValueError('PK duplicada '+t)
    return out

def entradas(raiz,base):
    p=Path(base).resolve() if base else selecionar(raiz)
    bm=json.loads((p/'manifesto_base_eda.json').read_text(encoding='utf-8'))
    cq=json.loads((raiz/'quality/10_base_eda'/bm['run_id']/'conclusao_10_base_eda.json').read_text(encoding='utf-8'))
    if bm['projeto']!=PROJETO or bm['status']!=STATUS_BASE or cq['status']!=STATUS_BASE or cq['run_id']!=bm['run_id'] or cq['entradas']!=bm['entradas']:raise ValueError('Base sem conclusao correspondente')
    # Verify physical base exports too; no untrusted lineage change.
    for e in bm['exportacoes']:
        if Path(e['tabela']).name!=e['tabela']:raise ValueError('Tabela invalida')
        if sha(p/(e['tabela']+'.json'))!=e['sha256_json'] or sha(p/(e['tabela']+'.parquet'))!=e['sha256_parquet']:raise ValueError('Base alterada')
    data={};refs={}
    for tipo in ['municipal','documental']:
        rs=[r for r in bm['entradas'] if r['tipo']==tipo]
        if len(rs)!=1 or Path(rs[0]['run_id']).name!=rs[0]['run_id']:raise ValueError('Linhagem invalida')
        ref=rs[0];folder=raiz/'datalake/02_silver'/ref['run_id']/tipo
        nome='manifesto_silver.json' if tipo=='municipal' else 'manifesto_documental.json'
        if sha(folder/nome)!=ref['manifesto_sha256']:raise ValueError('Manifesto Silver alterado')
        m,ts=carregar(folder,tipo)
        etapa='08_silver_municipal' if tipo=='municipal' else '09_silver_documental'
        qc=json.loads((raiz/'quality'/etapa/ref['run_id']/('conclusao_'+etapa+'.json')).read_text(encoding='utf-8'))
        if m['run_id']!=ref['run_id'] or m['exportacoes']!=ref['tabelas'] or qc['status']!=m['status'] or qc['run_id']!=m['run_id'] or qc['exportacoes']!=m['exportacoes']:raise ValueError('Silver sem qualidade correspondente')
        data[tipo]={k:v[0] for k,v in ts.items()};refs[tipo]=ref
    return data,refs,{'run_id':bm['run_id'],'manifesto_sha256':sha(p/'manifesto_base_eda.json')}

def construir(data):
    mt,dt=data['municipal'],data['documental'];out={t:[] for t in TABELAS};indexes={t:{} for t in DIMENSOES}
    def dim(t,r):
        pk=CONTRATO[t][0]['nome'];key=r[CHAVES[t]]
        if key in indexes[t]:
            old=indexes[t][key]
            if {k:v for k,v in old.items() if k!=pk}!=r:raise ValueError('Colisao ou atributos divergentes '+t)
            return old[pk]
        row={pk:len(out[t])+1,**r};out[t].append(row);indexes[t][key]=row;return row[pk]
    def fato(t,r):
        pk=CONTRATO[t][0]['nome'];i=len(out[t])+1;out[t].append({pk:i,'execucao_id':1,**r});return i
    def periodo(rotulo):
        if rotulo is None or rotulo=='NAO_INFORMADA':typ='NAO_INFORMADO';a=b=None;original='NAO_INFORMADO'
        else:
            original=str(rotulo);ns=re.findall(r'\d{4}',original)
            if len(ns) not in [1,2]:raise ValueError('Periodo nao reconhecido: '+original)
            a=int(ns[0]);b=int(ns[-1]);typ='ANUAL' if a==b else 'INTERVALO_ANOS'
        return dim('gold.dim_periodo',{'periodo_chave':f'{typ}:{a}:{b}','rotulo_original':original,'tipo_periodo':typ,'ano_inicial':a,'ano_final':b})
    fonte_doc={}
    for r in dt['fontes_documentais']:
        payload={'sha256':r['source_sha256'],'arquivo':r['arquivo_origem'],'edicao':None}
        fonte_doc[r['source_sha256']]=dim('gold.dim_fonte',{'fonte_chave':hash_obj(payload),'fonte_sha256':r['source_sha256'],'tipo':r['tipo'],'fonte_url':None,'arquivo_origem':r['arquivo_origem'],'edicao':None,'edicao_informada':False,'coleta_utc':None,'hash_fisico_verificado':r['hash_fisico_verificado'],'observacao':'Edicao nao informada; periodo do estudo preservado na fato'})
    mun={}
    for r in mt['municipios']:
        mun[r['codigo_ibge']]=dim('gold.dim_municipio',{k:r.get(k) for k in [c['nome'] for c in CONTRATO['gold.dim_municipio'][1:]]})
    indicadores={};dic={r['indicador_id']:r for r in mt['dicionario_indicadores']}
    for r in dic.values():
        indicadores[r['indicador_id']]=dim('gold.dim_indicador',{'indicador_chave':r['indicador_id'],'nome_oficial':r['nome_oficial'],'grupo':r['grupo'],'tabela_origem':r['tabela'],'variavel_origem':r['variavel_id'],'classificacoes_json':r['classificacoes_json'],'unidade':r['unidade_silver'],'escala_percentual':r['escala_percentual'],'definicao':r['definicao'],'limitacoes_uso_json':r['limitacoes_uso_json'],'url_metadados':r['url_metadados']})
    pontos={}
    for r in mt['municipios']:
        if not r['cidade_expansao']:
            codigo=r['codigo_ibge'];typ='FABRICA' if codigo=='3548906' else 'CD'
            pontos[codigo]=dim('gold.dim_ponto_distribuicao',{'ponto_chave':typ+':'+codigo,'nome':r['municipio'],'tipo':typ,'municipio_id':mun[codigo],'endereco_confirmado':None,'latitude_endereco':None,'longitude_endereco':None})
    if len(pontos)!=5 or set(pontos)!={'3548906','3543402','3509502','3552205','3550308'}:raise ValueError('Origens diferentes das aprovadas')
    for r in mt['indicadores_serie']:
        fid=dim('gold.dim_fonte',{'fonte_chave':hash_obj({'sha256':r['fonte_sha256'],'url':r['fonte_url'],'coleta':r['coleta_utc'],'edicao':None}),'fonte_sha256':r['fonte_sha256'],'tipo':'API_IBGE','fonte_url':r['fonte_url'],'arquivo_origem':None,'edicao':None,'edicao_informada':False,'coleta_utc':r['coleta_utc'],'hash_fisico_verificado':False,'observacao':'Hash da resposta registrado na Silver; arquivo HTTP bruto nao relido nesta etapa; nao identifica edicao formal'})
        pib=dic[r['indicador_id']]['grupo']=='pib';afetado=pib and r['codigo_ibge'] in ['3544905','3517406','3533601']
        motivos=[]
        if r['valor'] is None:motivos.append('SEM_VALOR_NUMERICO')
        if not r['candidato_eda']:motivos.append('FORA_CANDIDATO_EDA')
        if r['conferencia_distribuicao_renda_pendente']:motivos.append('CONFERENCIA_RENDA_PENDENTE')
        if pib:motivos.append('PIB_FORA_APROFUNDAMENTO_COMERCIAL_INICIAL')
        if afetado:motivos.append('REVISAO_PIB_ENTRE_EDICOES_PENDENTE')
        fato('gold.fato_indicador_municipal',{'municipio_id':mun[r['codigo_ibge']],'indicador_id':indicadores[r['indicador_id']],'periodo_id':periodo(r['ano_referencia']),'fonte_id':fid,'valor':r['valor'],'valor_original':r['valor_original'],'unidade_original':r['unidade_original'],'multiplicador':r['multiplicador'],'status_valor':r['status_valor'],'status_atualidade':r['status_atualidade'],'defasagem_anos':r['defasagem_anos'],'ultimo_valor_numerico':r['ultimo_valor_numerico'],'candidato_eda':r['candidato_eda'],'conferencia_renda_pendente':r['conferencia_distribuicao_renda_pendente'],'revisao_pib_pendente':afetado,'liberado_analise_comercial':not motivos,'motivo_restricao':';'.join(motivos) or None,'limitacoes_uso_json':r['limitacoes_uso_json'],'registro_origem_json':texto(r)})
    for r in mt['distancias_geodesicas']:
        fato('gold.fato_distancia_municipio_origem',{'municipio_id':mun[r['destino_codigo']],'ponto_id':pontos[r['origem_codigo']],'metodo':r['metodo'],'tipo_distancia':'GEODESICA_CENTROIDES','distancia_km':r['distancia_geodesica_centroides_km'],'tempo_minutos':None,'fontes_sha256_json':r['fontes_sha256_json'],'uso_proposto':r['uso'],'registro_origem_json':texto(r)})
    for r in dt['precos_produtos']:
        campos=['categoria','descricao_original','estado','peso_pacote_kg','quantidade_pacote','quantidade_aproximada'];attrs={k:r.get(k) for k in campos}
        # Null and approximate quantities retained; no invented SKU.
        if attrs['quantidade_aproximada'] is not None:attrs['quantidade_aproximada']=str(attrs['quantidade_aproximada'])
        pid=dim('gold.dim_produto',{'produto_chave':hash_obj(attrs),**attrs,'sku_confirmado':None})
        fato('gold.fato_preco_referencia',{'produto_id':pid,'fonte_id':fonte_doc[r['source_sha256']],'periodo_id':periodo(None),'registro_id':r['registro_id'],'pagina':r['pagina'],'linha':r['linha'],'preco_pacote_brl':r['preco_pacote_brl'],'preco_unidade_brl':r['preco_unidade_brl'],'preco_pacote_original':r['preco_pacote_original'],'preco_unidade_original':r['preco_unidade_original'],'vigencia_original':r['vigencia'],'vigencia_confirmada':r['vigencia_confirmada'],'liberado_orcamento_atual':r['liberado_orcamento_atual'],'validacao':r['validacao'],'registro_origem_json':texto(r)})
    estudos={}
    for tabela in ['consumo_historico','universitarios_historico']:
        for r in dt[tabela]:
            attrs={k:r.get(k) for k in ['abrangencia','regiao','dimensao','estrato','grupo_alimento','curso','grupo','frequencia']}
            attrs.update(estudo=tabela,tabela_original=r['tabela'],indicador_publicado=r.get('indicador'))
            # Include study source in hash to keep different publications distinct.
            eid=dim('gold.dim_estrato_estudo',{'estrato_chave':hash_obj({'fonte':r['source_sha256'],**attrs}),**attrs})
            estudos[r['registro_id']]=fato('gold.fato_estudo_publicado',{'estrato_id':eid,'fonte_id':fonte_doc[r['source_sha256']],'periodo_id':periodo(r['periodo_referencia']),'registro_id':r['registro_id'],'tabela_silver':tabela,'pagina':r['pagina'],'percentual':r['percentual'],'percentual_original':r['percentual_original'],'n_publicado':r.get('n'),'denominador_publicado':r.get('denominador_publicado'),'ic95_inferior':r.get('ic95_inferior'),'ic95_superior':r.get('ic95_superior'),'p_valor_original':r.get('p_valor_linha_original'),'pendencia_publicada':r.get('divergencia_pdf_imagem_pendente',False) or r.get('inconsistencia_publicada_pendente',False),'uso_previsao_vendas_atual':r['uso_previsao_vendas_atual'],'registro_origem_json':texto(r)})
    for r in dt['evidencias_imagens']:
        if r['incluir_como_nova_observacao']:raise ValueError('Imagem adicionando observacao')
        fato('quality.evidencia_imagem',{'observacao_estudo_id':estudos[r['registro_pdf_id']],'fonte_imagem_id':fonte_doc[r['imagem_sha256']],'registro_id':r['registro_id'],'registro_pdf_id':r['registro_pdf_id'],'incluir_como_nova_observacao':False,'registro_origem_json':texto(r)})
    for r in dt['pendencias_documentais']:
        fato('quality.pendencia',{'pendencia_chave':hash_obj(r),'tipo':r['tipo'],'registro_id':r.get('registro_id'),'detalhe':texto(r),'resolvida':False,'evidencia_resolucao':None})
    for tabela in ['coeficientes_publicados','ajustes_publicados','testes_publicados']:
        for r in dt[tabela]:fato('quality.registro_documental_auxiliar',{'fonte_id':fonte_doc[r['source_sha256']],'tabela_silver':tabela,'registro_id':r['registro_id'],'registro_origem_json':texto(r)})
    out={t:validar_rows(t,rs) for t,rs in out.items()}
    for r in out['gold.fato_estudo_publicado']:
        if r['uso_previsao_vendas_atual'] or (r['percentual'] is not None and not 0<=r['percentual']<=100):raise ValueError('Regra de estudo violada')
    for r in out['gold.fato_preco_referencia']:
        if r['preco_pacote_brl']<0 or (r['liberado_orcamento_atual'] and not r['vigencia_confirmada']):raise ValueError('Regra de preco violada')
    for t,rs in out.items():
        for c in CONTRATO[t]:
            if c['fk'] and c['fk'][0]!='audit.execucao_carga':
                ref,pk=c['fk'];ids={r[pk] for r in out[ref]}
                if any(r[c['nome']] not in ids for r in rs):raise ValueError('FK invalida '+t)
    for t in ['gold.fato_preco_referencia','gold.fato_estudo_publicado','quality.evidencia_imagem','quality.registro_documental_auxiliar']:
        if len({r['registro_id'] for r in out[t]})!=len(out[t]):raise ValueError('Registro duplicado '+t)
    for t,cs in [('gold.fato_indicador_municipal',['municipio_id','indicador_id','periodo_id','fonte_id']),('gold.fato_distancia_municipio_origem',['municipio_id','ponto_id','tipo_distancia'])]:
        if len({tuple(r[c] for c in cs) for r in out[t]})!=len(out[t]):raise ValueError('Grao duplicado '+t)
    return out

def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve();q=raiz/'quality/19_gold_dimensional'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO'}
    handler=logging.FileHandler(q/'execucao.log',encoding='utf-8');logger=logging.getLogger('gold19.'+run_id);logger.setLevel(logging.INFO);logger.addHandler(handler)
    try:
        data,refs,b=entradas(raiz,base);logger.info('Entradas reconciliadas')
        out=construir(data);destino=raiz/'datalake/03_gold'/run_id/'dimensional';destino.mkdir(parents=True,exist_ok=False);export=[]
        for t,rs in out.items():
            nome=t.replace('.','__');jp=destino/(nome+'.json');pp=destino/(nome+'.parquet');arrow=pa.Table.from_pylist(rs,schema=schema(t));gravar(jp,canon(rs));pq.write_table(arrow,pp,compression='snappy')
            if pq.read_table(pp).to_pylist()!=rs or json.loads(jp.read_text(encoding='utf-8'))!=canon(rs):raise ValueError('Exportacao divergente '+t)
            export.append({'tabela':t,'arquivo':nome,'linhas':len(rs),'sha256_json':sha(jp),'sha256_parquet':sha(pp)});logger.info('%s: %s linhas reconciliadas',t,len(rs))
        rel.update(status=STATUS,base_eda=b,entradas=refs,saida=str(destino),exportacoes=export,versao_modelo='1.0',contrato_sha256=hash_obj(CONTRATO),politica='PIB excluido do aprofundamento comercial inicial; precos historicos e estudos nao projetam vendas',fim_utc=datetime.now(timezone.utc).isoformat())
        gravar(destino/'manifesto_dimensional.json',rel)
    except Exception as exc:
        rel.update(status='FALHA',erro=str(exc),fim_utc=datetime.now(timezone.utc).isoformat());logger.exception('Falha')
        raise
    finally:
        gravar(q/'conclusao_19_gold_dimensional.json',rel);handler.close();logger.removeHandler(handler)
    return rel

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--base',type=Path);a=p.parse_args()
    r=executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.base)
    print(texto({'status':r['status'],'run_id':r['run_id'],'saida':r['saida'],'tabelas':len(r['exportacoes'])}))
if __name__=='__main__':main()
