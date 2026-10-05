"""Coleta complementar IBGE e publicacao aditiva de comparacoes comerciais."""
import argparse
import gzip
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

PROJETO = 'potencial-de-mercado-e-expansao-comercial'
ANO = 2024
CATEGORIAS = ('117440', '117441', '117443')
MUNICIPIOS = {'3516200','3513207','3127107','3531902','3544905','3534302',
              '3533601','3521309','3517406','3505500','3151602','3512100'}
META_URL = 'https://servicodados.ibge.gov.br/api/v3/agregados/9528/metadados'
URL = ('https://servicodados.ibge.gov.br/api/v3/agregados/9528/periodos/2024/variaveis/706'
       '?localidades=N6['+','.join(sorted(MUNICIPIOS))+']&classificacao=12762['+','.join(CATEGORIAS)+']')

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def agora(): return datetime.now(timezone.utc).isoformat()
def gravar(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def obter(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Portfolio-Comparacao-Varejo/1.0'})
    with urllib.request.urlopen(req,timeout=45) as r: b=r.read()
    return gzip.decompress(b) if b[:2]==b'\x1f\x8b' else b

def validar_metadados(meta):
    cl=[c for c in meta['classificacoes'] if str(c['id'])=='12762']
    if len(cl)!=1: raise ValueError('Classificacao CNAE ausente ou duplicada')
    nomes={str(c['id']):c['nome'] for c in cl[0]['categorias']}
    for codigo,inicio in [('117440','47.11-3'),('117441','47.12-1'),('117443','47.2')]:
        if not nomes.get(codigo,'').startswith(inicio):
            raise ValueError('Definicao CNAE inesperada: '+codigo)
    return {c:nomes[c] for c in CATEGORIAS}

def normalizar(payload):
    if len(payload)!=1 or str(payload[0]['id'])!='706' or payload[0]['unidade']!='Unidades':
        raise ValueError('Variavel ou unidade inesperada')
    valores={};nomes={}
    for resultado in payload[0]['resultados']:
        classes=resultado['classificacoes']
        if len(classes)!=1 or str(classes[0]['id'])!='12762' or len(classes[0]['categoria'])!=1:
            raise ValueError('Grão CNAE inesperado')
        categoria=next(iter(classes[0]['categoria']))
        if categoria not in CATEGORIAS: raise ValueError('Categoria inesperada')
        for s in resultado['series']:
            local=s['localidade'];ibge=str(local['id']);v=s['serie'].get(str(ANO))
            if local['nivel']['id']!='N6' or ibge not in MUNICIPIOS:
                raise ValueError('Municipio ou nivel inesperado')
            if not isinstance(v,str) or not re.fullmatch(r'\d+',v):
                raise ValueError(f'Valor ausente/suprimido/invalido: {ibge}/{categoria}: {v!r}')
            chave=(ibge,categoria)
            if chave in valores: raise ValueError('Observacao duplicada')
            valores[chave]=int(v);nomes[ibge]=local['nome']
    if set(valores)!={(m,c) for m in MUNICIPIOS for c in CATEGORIAS}:
        raise ValueError('Cobertura deve conter 12 municipios x 3 categorias')
    return [{'codigo_ibge':m,'municipio_fonte':nomes[m],'ano_referencia':ANO,
             **{'categoria_'+c:valores[m,c] for c in CATEGORIAS}}
            for m in sorted(MUNICIPIOS)]

def linhas(cur,sql):
    cur.execute(sql);cols=[c[0] for c in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

def executar(raiz,servidor,driver,confiar):
    import pyodbc
    raiz=Path(raiz);run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    q=raiz/'quality/32_comparacao_varejo'/run
    q.mkdir(parents=True,exist_ok=False)
    bronze=raiz/'datalake/01_bronze_raw'/run/'comparacao_varejo'
    silver=raiz/'datalake/02_silver'/run/'comparacao_varejo'
    gold=raiz/'datalake/03_gold'/run/'comparacao_varejo'
    meta={'projeto':PROJETO,'run_id':run,'inicio_utc':agora(),'ano_referencia':ANO,
          'fonte_url':URL,'metadados_url':META_URL,'script_sha256':sha_bytes(Path(__file__).read_bytes()),
          'status':'EM_EXECUCAO'};con=None
    try:
        for v in (servidor,driver):
            if any(c in v for c in ';{}'): raise ValueError('Parametro de conexao invalido')
        if driver not in pyodbc.drivers(): raise ValueError('Driver ODBC nao instalado')
        ddl=raiz/'sql/37_views_comparacao_varejo.sql';sql_bytes=ddl.read_bytes()
        meta['sql_sha256']=sha_bytes(sql_bytes)
        bronze.mkdir(parents=True,exist_ok=False)
        for nome,url in [('metadados.json',META_URL),('dados_ibge.json',URL)]:
            b=obter(url);(bronze/nome).write_bytes(b)
        nomes=validar_metadados(json.loads((bronze/'metadados.json').read_bytes()))
        fonte=(bronze/'dados_ibge.json').read_bytes();dados=normalizar(json.loads(fonte))
        meta['fonte_sha256']=sha_bytes(fonte);meta['metadados_sha256']=sha_bytes((bronze/'metadados.json').read_bytes())
        meta['categorias']=nomes
        gravar(silver/'indicadores_complementares.json',dados)
        meta['silver_sha256']=sha_bytes((silver/'indicadores_complementares.json').read_bytes())
        cs=f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate={"yes" if confiar else "no"};'
        con=pyodbc.connect(cs,autocommit=False,timeout=30);cur=con.cursor()
        cur.execute('SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;')
        cur.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource='carga_circuitos_comerciais',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=30000; IF @r<0 THROW 51000,'Bloqueio indisponivel',1;")
        execs=linhas(cur,'SELECT run_29 FROM gold.vw_bi_execucao_comercial')
        if len(execs)!=1: raise ValueError('Execucao comercial aprovada nao e unica')
        run29=execs[0]['run_29'];meta['entrada_29_run_id']=run29
        original=linhas(cur,'SELECT codigo_ibge,varejo_alimentar_2024 FROM gold.vw_bi_municipio_comercial')
        por_codigo={str(r['codigo_ibge']):r['varejo_alimentar_2024'] for r in original}
        if len(original)!=12 or set(por_codigo)!=MUNICIPIOS: raise ValueError('Cobertura municipal SQL divergente')
        for r in dados:
            if por_codigo[r['codigo_ibge']] is None or Decimal(str(por_codigo[r['codigo_ibge']]))!=r['categoria_117443']:
                raise ValueError('Varejo especializado SQL diverge da fonte: '+r['codigo_ibge'])
        cur.execute('SELECT COUNT(*) FROM gold.vw_bi_circuito')
        if cur.fetchone()[0]!=5: raise ValueError('Esperados cinco circuitos')
        cur.execute('SELECT * FROM gold.vw_bi_custo_viagem_simulado ORDER BY circuito_chave,cenario_chave FOR JSON PATH')
        custo_antes=''.join(r[0] for r in cur.fetchall());meta['custos_sql_sha256']=sha_bytes(custo_antes.encode())
        for bloco in re.split(r'^GO\s*$',sql_bytes.decode('utf-8-sig'),flags=re.M):
            if bloco.strip(): cur.execute(bloco)
        cur.execute('INSERT INTO gold.execucao_comparacao_varejo (run_32,run_29,ano,fonte_url,fonte_sha256,carregado_utc,status) VALUES (?,?,?,?,?,?,?)',
                    run,run29,ANO,URL,meta['fonte_sha256'],datetime.now(timezone.utc).replace(tzinfo=None),'COMPARACAO_VAREJO_VERIFICADA')
        for r in dados:
            cur.execute('INSERT INTO gold.complemento_varejo_municipal VALUES (?,?,?,?,?,?)',
                        run,r['codigo_ibge'],ANO,r['categoria_117440'],r['categoria_117441'],r['categoria_117443'])
        municipios=linhas(cur,'SELECT * FROM gold.vw_bi_municipio_varejo_comparado ORDER BY codigo_ibge')
        circuitos=linhas(cur,'SELECT * FROM gold.vw_bi_circuito_varejo_comparado ORDER BY circuito_chave')
        if len(municipios)!=12 or len(circuitos)!=5 or any(r['run_32']!=run for r in municipios+circuitos):
            raise ValueError('Contagem ou execucao das views divergente')
        por_fonte={r['codigo_ibge']:r for r in dados}
        for r in municipios:
            f=por_fonte[str(r['codigo_ibge'])]
            if r['varejo_alimentar_ampliado_2024']!=sum(f['categoria_'+c] for c in CATEGORIAS):
                raise ValueError('Total municipal divergente')
        for c in circuitos:
            grupo=[r for r in municipios if r['circuito_chave']==c['circuito_chave']]
            if len(grupo)!=c['municipios_comparados'] or sum(r['varejo_alimentar_ampliado_2024'] for r in grupo)!=c['varejo_alimentar_ampliado_2024']:
                raise ValueError('Agregacao de circuito divergente')
        cur.execute('SELECT * FROM gold.vw_bi_custo_viagem_simulado ORDER BY circuito_chave,cenario_chave FOR JSON PATH')
        if ''.join(r[0] for r in cur.fetchall())!=custo_antes: raise ValueError('Simulacoes de custo alteradas')
        gravar(gold/'comparacao_municipios.json',municipios);gravar(gold/'comparacao_circuitos.json',circuitos)
        meta.update(contagens={'municipios':12,'circuitos':5,'observacoes_ibge':36},
                    total_especializado=str(sum(r['varejo_especializado_2024'] for r in municipios)),
                    total_ampliado=str(sum(r['varejo_alimentar_ampliado_2024'] for r in municipios)),
                    verificacoes=['cobertura_ibge','categorias_oficiais','reconciliacao_especializado_sql',
                                  'totais_municipais','agregacao_circuitos','linhagem_run29','custos_preservados'])
        if ddl.read_bytes()!=sql_bytes: raise ValueError('SQL mudou durante execucao')
        con.commit();meta['status']='COMPARACAO_VAREJO_VERIFICADA'
    except Exception as e:
        if con: con.rollback()
        meta.update(status='FALHA',erro=str(e));raise
    finally:
        if con: con.close()
        meta['fim_utc']=agora();gravar(q/'conclusao_32.json',meta)
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--servidor',required=True);p.add_argument('--driver',default='ODBC Driver 17 for SQL Server')
    p.add_argument('--confiar-certificado',action='store_true');a=p.parse_args()
    print(json.dumps(executar(a.raiz,a.servidor,a.driver,a.confiar_certificado),ensure_ascii=False,indent=2))
