"""Carga transacional de referencias comerciais, sem alterar fatos anteriores."""
import argparse,json,math
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
from uuid import uuid4
from etapa_27_equilibrio_viagens import PROJETO,ler,sha,fonte,arquivo
from etapa_29_priorizacao_comercial import analisar

DDL='''
IF OBJECT_ID('gold.sim_execucao_comercial','U') IS NULL
CREATE TABLE gold.sim_execucao_comercial (
 run_29 varchar(80) NOT NULL PRIMARY KEY, run_28 varchar(80) NOT NULL,
 sql_execucao_id bigint NOT NULL, hash_conclusao_29 char(64) NOT NULL,
 carregado_utc datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
 status varchar(60) NOT NULL CHECK(status='REFERENCIAS_COMERCIAIS_COM_LIMITACOES'));
IF OBJECT_ID('gold.dim_circuito_sugerido','U') IS NULL
CREATE TABLE gold.dim_circuito_sugerido (
 run_29 varchar(80) NOT NULL, circuito_id varchar(100) NOT NULL,
 sequencia_sugerida nvarchar(1000) NOT NULL, km_sugeridos decimal(20,8) NOT NULL,
 varejo_especializado_2024 decimal(20,8) NOT NULL,
 participacao_varejo_percentual decimal(20,8) NOT NULL,
 receita_referencia_brl decimal(20,8) NULL,
 PRIMARY KEY(run_29,circuito_id),
 FOREIGN KEY(run_29) REFERENCES gold.sim_execucao_comercial(run_29));
IF OBJECT_ID('gold.ponte_circuito_municipio','U') IS NULL
CREATE TABLE gold.ponte_circuito_municipio (
 run_29 varchar(80) NOT NULL,circuito_id varchar(100) NOT NULL,
 codigo_ibge varchar(7) NOT NULL,municipio nvarchar(150) NOT NULL,
 populacao_2024 decimal(20,8) NOT NULL,renda_mediana_2022 decimal(20,8) NOT NULL,
 varejo_alimentar_2024 decimal(20,8) NOT NULL,
 PRIMARY KEY(run_29,codigo_ibge),
 FOREIGN KEY(run_29,circuito_id) REFERENCES gold.dim_circuito_sugerido(run_29,circuito_id));
IF OBJECT_ID('gold.dim_cenario_comercial','U') IS NULL
CREATE TABLE gold.dim_cenario_comercial (
 run_29 varchar(80) NOT NULL,cenario_id int NOT NULL,
 consumo_km_l decimal(20,8) NOT NULL,desgaste_brl_km decimal(20,8) NOT NULL,
 margem_contribuicao decimal(20,8) NOT NULL,
 PRIMARY KEY(run_29,cenario_id), UNIQUE(run_29,consumo_km_l,desgaste_brl_km,margem_contribuicao),
 FOREIGN KEY(run_29) REFERENCES gold.sim_execucao_comercial(run_29),
 CHECK(consumo_km_l>0 AND desgaste_brl_km>=0 AND margem_contribuicao>0 AND margem_contribuicao<=1));
IF OBJECT_ID('gold.fato_custo_viagem_simulado','U') IS NULL
CREATE TABLE gold.fato_custo_viagem_simulado (
 run_29 varchar(80) NOT NULL,circuito_id varchar(100) NOT NULL,cenario_id int NOT NULL,
 gasolina_brl decimal(20,8) NOT NULL,desgaste_brl decimal(20,8) NOT NULL,
 pedagio_estimado_osm_brl decimal(20,8) NULL,custo_estimado_brl decimal(20,8) NULL,
 receita_equilibrio_estimada_brl decimal(20,8) NULL,
 natureza varchar(80) NOT NULL CHECK(natureza='REFERENCIA_COMERCIAL_SIMULADA'),
 PRIMARY KEY(run_29,circuito_id,cenario_id),
 FOREIGN KEY(run_29,circuito_id) REFERENCES gold.dim_circuito_sugerido(run_29,circuito_id),
 FOREIGN KEY(run_29,cenario_id) REFERENCES gold.dim_cenario_comercial(run_29,cenario_id));
'''

COLUNAS={
 'dim_circuito_sugerido':['run_29','circuito_id','sequencia_sugerida','km_sugeridos','varejo_especializado_2024','participacao_varejo_percentual','receita_referencia_brl'],
 'ponte_circuito_municipio':['run_29','circuito_id','codigo_ibge','municipio','populacao_2024','renda_mediana_2022','varejo_alimentar_2024'],
 'dim_cenario_comercial':['run_29','cenario_id','consumo_km_l','desgaste_brl_km','margem_contribuicao'],
 'fato_custo_viagem_simulado':['run_29','circuito_id','cenario_id','gasolina_brl','desgaste_brl','pedagio_estimado_osm_brl','custo_estimado_brl','receita_equilibrio_estimada_brl','natureza']}

def decimal(v):
    if v is None:return None
    d=Decimal(str(v))
    if not d.is_finite():raise ValueError('Numero nao finito')
    return d.quantize(Decimal('0.00000001'))

def preparar(run,cidades,circuitos,sens):
    chaves=sorted({(s['consumo_hipotetico_km_l'],s['desgaste_hipotetico_brl_km'],s['margem_hipotetica']) for s in sens})
    if len(chaves)!=27 or len(sens)!=135:raise ValueError('Esperados 27 cenarios e 135 fatos')
    mapa={k:i+1 for i,k in enumerate(chaves)}
    dados={
      'dim_circuito_sugerido':[(run,c['circuito_id'],c['sequencia_sugerida'],*[decimal(c[k]) for k in ('km_sugeridos','varejo_especializado_2024','participacao_varejo_percentual','receita_referencia_brl')]) for c in circuitos],
      'ponte_circuito_municipio':[(run,c['circuito_id'],str(c['codigo_ibge']),c['municipio'],*[decimal(c[k]) for k in ('populacao_2024','renda_mediana_2022','varejo_alimentar_2024')]) for c in cidades],
      'dim_cenario_comercial':[(run,mapa[k],*[decimal(v) for v in k]) for k in chaves],
      'fato_custo_viagem_simulado':[(run,s['circuito_id'],mapa[(s['consumo_hipotetico_km_l'],s['desgaste_hipotetico_brl_km'],s['margem_hipotetica'])],*[decimal(s[k]) for k in ('gasolina_brl','desgaste_brl','pedagio_estimado_pontos_osm_brl','custo_estimado_com_pontos_osm_brl','receita_estimada_com_pontos_osm_brl')],'REFERENCIA_COMERCIAL_SIMULADA') for s in sens]}
    for c in cidades:
        if len(str(c['codigo_ibge']))!=7 or not str(c['codigo_ibge']).isdigit():raise ValueError('Codigo IBGE invalido')
    for rows in dados.values():
        if len(set(rows))!=len(rows):raise ValueError('Registro duplicado')
    return dados

def executar(raiz,run_id,servidor,driver='ODBC Driver 17 for SQL Server',confiar_certificado=False):
    import pyodbc
    raiz=Path(raiz)
    p29,m29=fonte(raiz,'29_priorizacao_comercial','conclusao_29.json','REFERENCIAS_COMERCIAIS_COM_LIMITACOES')
    p28,m28=fonte(raiz,'28_pedagios_trajetos','conclusao_28.json','ESTIMATIVA_PROVISORIA_PEDAGIOS_NAO_HOMOLOGADOS')
    if m29['entrada_28_run_id']!=m28['run_id']:raise ValueError('Vinculo 28/29 divergente')
    cp=arquivo(m29,'municipios_prioridades.json');rp=arquivo(m29,'circuitos_comerciais.json');sp=arquivo(m28,'sensibilidade_provisoria.json');tp=arquivo(m28,'trajetos.json')
    cidades=ler(cp);circuitos=ler(rp);sens=ler(sp)
    a,b=analisar(cidades,ler(tp),sens)
    if a!=cidades or b!=circuitos:raise ValueError('Etapa 29 diverge do recalculo')
    dados=preparar(m29['run_id'],cidades,circuitos,sens)
    if driver not in pyodbc.drivers():raise ValueError('Driver ODBC nao instalado: '+driver)
    for v in (driver,servidor):
        if any(c in v for c in ';{}'):raise ValueError('Conexao invalida')
    q=raiz/'quality/30_carga_circuitos_sql'/run_id;q.mkdir(parents=True,exist_ok=False)
    meta={'projeto':PROJETO,'run_id':run_id,'entrada_29_run_id':m29['run_id'],'entrada_28_run_id':m28['run_id'],'entradas_sha256':{str(p):sha(p) for p in (p29,p28,cp,rp,sp,tp)},'script_sha256':sha(__file__),'reconciliacao':[]}
    con=None
    try:
        con=pyodbc.connect(f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate={"yes" if confiar_certificado else "no"};',autocommit=False,timeout=30)
        cur=con.cursor();cur.execute('SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;')
        cur.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource='carga_circuitos_comerciais',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=30000; IF @r<0 THROW 51000,'Nao foi possivel obter bloqueio da carga',1;")
        cur.execute(DDL)
        cur.execute('SELECT execucao_id,run_id FROM gold.vw_carga_aprovada;');aprovadas=cur.fetchall()
        if len(aprovadas)!=1 or tuple(aprovadas[0])!=(m29['sql_execucao_id'],m29['sql_run_id']):raise ValueError('Carga municipal ativa mudou; refazer etapa 29')
        cur.execute('SELECT run_28,sql_execucao_id,hash_conclusao_29,status FROM gold.sim_execucao_comercial WHERE run_29=?',m29['run_id']);ant=cur.fetchone()
        esperado=(m28['run_id'],m29['sql_execucao_id'],sha(p29),'REFERENCIAS_COMERCIAIS_COM_LIMITACOES')
        if ant is not None and tuple(ant)!=esperado:raise ValueError('Conflito de historico; nada sera sobrescrito')
        if ant is None:
            cur.execute('INSERT INTO gold.sim_execucao_comercial(run_29,run_28,sql_execucao_id,hash_conclusao_29,status) VALUES(?,?,?,?,?)',m29['run_id'],*esperado)
            for tabela,rows in dados.items():
                cols=COLUNAS[tabela];cur.executemany(f"INSERT INTO gold.{tabela} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",rows)
        for tabela,rows in dados.items():
            cur.execute(f"SELECT {','.join(COLUNAS[tabela])} FROM gold.{tabela} WHERE run_29=?",m29['run_id']);sql=[tuple(r) for r in cur.fetchall()]
            if len(sql)!=len(rows) or set(sql)!=set(rows):raise ValueError('Reconciliacao integral divergente: '+tabela)
            meta['reconciliacao'].append({'tabela':'gold.'+tabela,'linhas':len(rows),'valores_conferidos':True})
        for p in (p29,p28,cp,rp,sp,tp):
            if sha(p)!=meta['entradas_sha256'][str(p)]:raise ValueError('Entrada mudou durante carga')
        con.commit();meta.update(status='CARGA_CIRCUITOS_SQL_VERIFICADA',resultado='EXISTENTE_IDENTICO' if ant else 'INSERIDO_VERIFICADO')
    except Exception as e:
        if con:con.rollback()
        meta.update(status='FALHA',erro=str(e));raise
    finally:
        if con:con.close()
        meta['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_30.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--servidor',required=True);p.add_argument('--driver',default='ODBC Driver 17 for SQL Server');p.add_argument('--confiar-certificado',action='store_true');a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.driver,a.confiar_certificado),ensure_ascii=False,indent=2))
