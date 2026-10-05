"""Instala e verifica views BI sobre a carga comercial reconciliada."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
from uuid import uuid4
from etapa_27_equilibrio_viagens import PROJETO,sha,fonte

CONTAGENS={'vw_bi_execucao_comercial':1,'vw_bi_circuito':5,'vw_bi_municipio_comercial':12,'vw_bi_cenario_comercial':27,'vw_bi_custo_viagem_simulado':135}
REGRAS={
 'circuito_chave_unica':'SELECT COUNT(*) FROM (SELECT circuito_chave FROM gold.vw_bi_circuito GROUP BY circuito_chave HAVING COUNT(*)<>1) x',
 'municipio_chave_unica':'SELECT COUNT(*) FROM (SELECT municipio_chave FROM gold.vw_bi_municipio_comercial GROUP BY municipio_chave HAVING COUNT(*)<>1) x',
 'cenario_chave_unica':'SELECT COUNT(*) FROM (SELECT cenario_chave FROM gold.vw_bi_cenario_comercial GROUP BY cenario_chave HAVING COUNT(*)<>1) x',
 'fato_grao_unico':'SELECT COUNT(*) FROM (SELECT circuito_chave,cenario_chave FROM gold.vw_bi_custo_viagem_simulado GROUP BY circuito_chave,cenario_chave HAVING COUNT(*)<>1) x',
 'fatos_sem_dimensao':'SELECT COUNT(*) FROM gold.vw_bi_custo_viagem_simulado f LEFT JOIN gold.vw_bi_circuito c ON c.circuito_chave=f.circuito_chave LEFT JOIN gold.vw_bi_cenario_comercial s ON s.cenario_chave=f.cenario_chave WHERE c.circuito_chave IS NULL OR s.cenario_chave IS NULL',
 'municipios_sem_circuito':'SELECT COUNT(*) FROM gold.vw_bi_municipio_comercial m LEFT JOIN gold.vw_bi_circuito c ON c.circuito_chave=m.circuito_chave WHERE c.circuito_chave IS NULL',
 'agregacao_varejo_divergente':'SELECT COUNT(*) FROM gold.vw_bi_circuito c LEFT JOIN (SELECT circuito_chave,SUM(varejo_alimentar_2024) total FROM gold.vw_bi_municipio_comercial GROUP BY circuito_chave) m ON m.circuito_chave=c.circuito_chave WHERE m.total IS NULL OR m.total<>c.varejo_especializado_2024',
 'referencia_receita_divergente':'SELECT COUNT(*) FROM gold.vw_bi_custo_viagem_simulado f JOIN gold.vw_bi_cenario_comercial s ON s.cenario_chave=f.cenario_chave JOIN gold.vw_bi_circuito c ON c.circuito_chave=f.circuito_chave WHERE s.cenario_referencia=1 AND (ABS(f.receita_equilibrio_estimada_brl-c.receita_referencia_brl)>0.000001 OR (f.receita_equilibrio_estimada_brl IS NULL AND c.receita_referencia_brl IS NOT NULL) OR (f.receita_equilibrio_estimada_brl IS NOT NULL AND c.receita_referencia_brl IS NULL))',
 'equilibrio_divergente':'SELECT COUNT(*) FROM gold.vw_bi_custo_viagem_simulado f JOIN gold.vw_bi_cenario_comercial s ON s.cenario_chave=f.cenario_chave WHERE ABS(f.receita_equilibrio_estimada_brl-f.custo_estimado_brl/s.margem_contribuicao)>0.000001 OR (f.receita_equilibrio_estimada_brl IS NULL AND f.custo_estimado_brl IS NOT NULL) OR (f.receita_equilibrio_estimada_brl IS NOT NULL AND f.custo_estimado_brl IS NULL)'}

def executar(raiz,run_id,servidor,driver='ODBC Driver 17 for SQL Server',confiar_certificado=False):
    import pyodbc
    raiz=Path(raiz);p30,m30=fonte(raiz,'30_carga_circuitos_sql','conclusao_30.json','CARGA_CIRCUITOS_SQL_VERIFICADA')
    ddl=raiz/'sql/32_views_power_bi.sql'
    if driver not in pyodbc.drivers():raise ValueError('Driver nao instalado: '+driver)
    for v in (driver,servidor):
        if any(c in v for c in ';{}'):raise ValueError('Conexao invalida')
    q=raiz/'quality/31_views_power_bi'/run_id;q.mkdir(parents=True,exist_ok=False)
    meta={'projeto':PROJETO,'run_id':run_id,'entrada_30_run_id':m30['run_id'],'entrada_29_run_id':m30['entrada_29_run_id'],'script_sha256':sha(__file__),'entradas_sha256':{str(p):sha(p) for p in (p30,ddl)},'contagens':{},'regras':[]};con=None
    try:
        con=pyodbc.connect(f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate={"yes" if confiar_certificado else "no"};',autocommit=False,timeout=30)
        cur=con.cursor();cur.execute('SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;')
        cur.execute("DECLARE @r int; EXEC @r=sp_getapplock @Resource='carga_circuitos_comerciais',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=30000; IF @r<0 THROW 51000,'Bloqueio indisponivel',1;")
        for bloco in ddl.read_text(encoding='utf-8-sig').split('\nGO'):
            if bloco.strip():cur.execute(bloco.strip())
        cur.execute('SELECT run_29 FROM gold.vw_bi_execucao_comercial');row=cur.fetchone()
        if not row or row[0]!=m30['entrada_29_run_id']:raise ValueError('Execucao SQL selecionada diverge da ultima carga 30')
        for nome,esperado in CONTAGENS.items():
            cur.execute('SELECT COUNT(*) FROM gold.'+nome);n=cur.fetchone()[0];meta['contagens'][nome]=n
            if n!=esperado:raise ValueError('Contagem divergente: '+nome)
        cur.execute('SELECT COUNT(*) FROM gold.vw_bi_cenario_comercial WHERE cenario_referencia=1')
        if cur.fetchone()[0]!=1:raise ValueError('Cenario de referencia deve ser unico')
        for nome,sql in REGRAS.items():
            cur.execute(sql);n=cur.fetchone()[0];meta['regras'].append({'regra':nome,'divergencias':n})
            if n:raise ValueError('Regra reprovada: '+nome)
        for p in (p30,ddl):
            if sha(p)!=meta['entradas_sha256'][str(p)]:raise ValueError('Entrada modificada durante execucao')
        con.commit();meta['status']='VIEWS_POWER_BI_VERIFICADAS'
    except Exception as e:
        if con:con.rollback()
        meta.update(status='FALHA',erro=str(e));raise
    finally:
        if con:con.close()
        meta['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_31.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--servidor',required=True);p.add_argument('--driver',default='ODBC Driver 17 for SQL Server');p.add_argument('--confiar-certificado',action='store_true');a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.driver,a.confiar_certificado),ensure_ascii=False,indent=2))
