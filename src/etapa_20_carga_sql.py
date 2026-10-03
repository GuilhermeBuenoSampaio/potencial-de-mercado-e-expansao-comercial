"""Carga SQL transacional e reconciliacao integral da Gold dimensional."""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pyarrow.parquet as pq
from contrato_dimensional import CONTRATO
from etapa_19_gold_dimensional import PROJETO, STATUS, TABELAS, DIMENSOES, CHAVES, hash_obj, normalizar, validar_rows, canon, sha, gravar, texto

def selecionar_gold(raiz):
    for p in sorted((raiz/'datalake/03_gold').glob('*/dimensional/manifesto_dimensional.json'),reverse=True):
        m=json.loads(p.read_text(encoding='utf-8'));q=raiz/'quality/19_gold_dimensional'/m['run_id']/'conclusao_19_gold_dimensional.json'
        if m.get('status')==STATUS and q.exists() and json.loads(q.read_text(encoding='utf-8')).get('status')==STATUS:return p.parent
    raise ValueError('Gold dimensional aprovada nao encontrada')

def ler_gold(raiz,p):
    m=json.loads((p/'manifesto_dimensional.json').read_text(encoding='utf-8'))
    q=json.loads((raiz/'quality/19_gold_dimensional'/m['run_id']/'conclusao_19_gold_dimensional.json').read_text(encoding='utf-8'))
    if m!=q or m['projeto']!=PROJETO or m['status']!=STATUS or m['contrato_sha256']!=hash_obj(CONTRATO):raise ValueError('Gold ou contrato nao corresponde a conclusao')
    if [e['tabela'] for e in m['exportacoes']]!=TABELAS:raise ValueError('Conjunto ou ordem de tabelas invalido')
    out={}
    for e in m['exportacoes']:
        t=e['tabela'];nome=t.replace('.','__')
        if nome!=e['arquivo']:raise ValueError('Arquivo fora do contrato')
        j=p/(nome+'.json');a=p/(nome+'.parquet')
        if sha(j)!=e['sha256_json'] or sha(a)!=e['sha256_parquet']:raise ValueError('Gold alterada: '+t)
        rows=pq.read_table(a).to_pylist()
        if len(rows)!=e['linhas'] or canon(rows)!=json.loads(j.read_text(encoding='utf-8')):raise ValueError('Parquet/JSON divergentes '+t)
        out[t]=validar_rows(t,rows)
    return m,out

def nome_sql(t):
    if t not in CONTRATO:raise ValueError('Tabela fora do contrato')
    return '.'.join('['+s+']' for s in t.split('.'))

def conferir_schema(cur):
    cur.execute("SELECT s.name,t.name,c.name,ty.name,c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id WHERE s.name IN ('gold','audit','quality')")
    actual={(r[0]+'.'+r[1],r[2]):tuple(r[3:]) for r in cur.fetchall()}
    for t,cols in CONTRATO.items():
        if len([k for k in actual if k[0]==t])!=len(cols):raise ValueError('Colunas SQL divergentes '+t)
        for c in cols:
            ty=c['tipo'];args=c['args'];length={'bigint':8,'int':4,'smallint':2,'bit':1,'datetime2':8}.get(ty);prec,scale={'bigint':(19,0),'int':(10,0),'smallint':(5,0),'bit':(1,0),'datetime2':(26,6)}.get(ty,(0,0))
            if ty in ['nvarchar','varchar','char']:length=-1 if args=='max' else int(args)*(2 if ty=='nvarchar' else 1)
            if ty=='decimal':prec,scale=map(int,args.split(','));length=5 if prec<=9 else 9 if prec<=19 else 13 if prec<=28 else 17
            wanted=(ty,length,prec,scale,c['nullable'],c['identity'])
            if actual.get((t,c['nome']))!=wanted:raise ValueError('Tipo SQL divergente '+t+'.'+c['nome'])
    cur.execute("SELECT ps.name,pt.name,pc.name,rs.name,rt.name,rc.name,f.is_disabled,f.is_not_trusted FROM sys.foreign_keys f JOIN sys.foreign_key_columns fc ON fc.constraint_object_id=f.object_id JOIN sys.tables pt ON pt.object_id=f.parent_object_id JOIN sys.schemas ps ON ps.schema_id=pt.schema_id JOIN sys.columns pc ON pc.object_id=pt.object_id AND pc.column_id=fc.parent_column_id JOIN sys.tables rt ON rt.object_id=f.referenced_object_id JOIN sys.schemas rs ON rs.schema_id=rt.schema_id JOIN sys.columns rc ON rc.object_id=rt.object_id AND rc.column_id=fc.referenced_column_id WHERE ps.name IN ('gold','audit','quality')")
    fks={(r[0]+'.'+r[1],r[2],r[3]+'.'+r[4],r[5]):(r[6],r[7]) for r in cur.fetchall()}
    for t,cols in CONTRATO.items():
        for c in cols:
            if c['fk'] and fks.get((t,c['nome'],*c['fk']))!=(False,False):raise ValueError('FK ausente/desabilitada/nao confiavel '+t)

def inserir(cur,t,r):
    pk=CONTRATO[t][0]['nome'];cols=[c['nome'] for c in CONTRATO[t] if not c['identity']]
    cur.execute('INSERT INTO '+nome_sql(t)+' ('+','.join('['+c+']' for c in cols)+') OUTPUT INSERTED.['+pk+'] VALUES ('+','.join('?' for c in cols)+')',*[r[c] for c in cols])
    return int(cur.fetchone()[0])

def remapear(t,r,maps,exec_id):
    out=dict(r)
    for c in CONTRATO[t]:
        if c['fk']:
            ref,pk=c['fk'];out[c['nome']]=exec_id if ref=='audit.execucao_carga' else maps[ref][r[c['nome']]]
    return out

def linhas_sql(cur,t,ids=None,exec_id=None):
    cols=[c['nome'] for c in CONTRATO[t]];query='SELECT '+','.join('['+c+']' for c in cols)+' FROM '+nome_sql(t);params=[]
    if ids is not None:
        if not ids:return []
        query+=' WHERE ['+cols[0]+'] IN ('+','.join('?' for _ in ids)+')';params=list(ids)
    elif exec_id is not None:query+=' WHERE execucao_id=?';params=[exec_id]
    cur.execute(query,*params)
    return [{c['nome']:normalizar(v,c) for c,v in zip(CONTRATO[t],row)} for row in cur.fetchall()]

def reconciliar(cur,t,expected,maps,exec_id):
    pk=CONTRATO[t][0]['nome'];obs=linhas_sql(cur,t,ids=list(maps[t].values()) if t in DIMENSOES else None,exec_id=exec_id)
    # Compare entire normalized row including remapped PK/FK and original JSON.
    exp=[]
    for r in expected:
        rr=remapear(t,r,maps,exec_id);rr[pk]=maps[t][r[pk]];exp.append(rr)
    if sorted(obs,key=lambda r:r[pk])!=sorted(exp,key=lambda r:r[pk]):raise ValueError('Reconciliacao integral divergente '+t)
    return {'tabela_destino':t,'regra':'CONTEUDO_INTEGRAL','registros_esperados':len(exp),'registros_observados':len(obs),'aprovado':True,'detalhe':'PK/FK remapeadas; tipos, valores, nulos, flags e JSON original comparados'}

def carregar_sql(conn,m,data,logger):
    cur=conn.cursor();cur.execute('SET XACT_ABORT ON; SET NOCOUNT ON;')
    if cur.execute('SELECT DB_NAME()').fetchone()[0]!=PROJETO:raise ValueError('Banco SQL incorreto')
    conferir_schema(cur)
    # Serialize loaders of this project; lock retained until explicit commit/rollback.
    cur.execute('IF @@TRANCOUNT=0 BEGIN TRANSACTION;')
    cur.execute("DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=N'potencial-de-mercado-e-expansao-comercial:carga',@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=10000; SELECT @r;")
    if cur.fetchone()[0]<0:raise ValueError('Outra carga SQL esta em andamento')
    previous=cur.execute('SELECT execucao_id,status,detalhe FROM audit.execucao_carga WHERE run_id=?',m['run_id']).fetchone()
    maps={};regras=[];reuso=False
    if previous:
        if previous[1]!='APROVADA':raise ValueError('Run SQL anterior nao aprovado; gerar nova Gold apos corrigir falha')
        detail=json.loads(previous[2])
        if detail['gold_manifesto_sha256']!=m['_hash_manifesto']:raise ValueError('Run Gold alterado apos carga')
        exec_id=int(previous[0]);maps={t:{int(k):v for k,v in d.items()} for t,d in detail['mapas'].items()};reuso=True
    else:
        audit={'run_id':m['run_id'],'inicio_utc':datetime.now(timezone.utc).replace(tzinfo=None),'fim_utc':None,'status':'EM_EXECUCAO','silver_municipal_run_id':m['entradas']['municipal']['run_id'],'silver_documental_run_id':m['entradas']['documental']['run_id'],'manifesto_municipal_sha256':m['entradas']['municipal']['manifesto_sha256'],'manifesto_documental_sha256':m['entradas']['documental']['manifesto_sha256'],'versao_modelo':m['versao_modelo'],'detalhe':None}
        exec_id=inserir(cur,'audit.execucao_carga',audit)
        for t in TABELAS:
            maps[t]={};pk=CONTRATO[t][0]['nome']
            for r in data[t]:
                rr=remapear(t,r,maps,exec_id)
                if t in DIMENSOES:
                    key=CHAVES[t];cols=[c['nome'] for c in CONTRATO[t]]
                    row=cur.execute('SELECT '+','.join('['+c+']' for c in cols)+' FROM '+nome_sql(t)+' WHERE ['+key+']=?',rr[key]).fetchone()
                    if row:
                        old={c['nome']:normalizar(v,c) for c,v in zip(CONTRATO[t],row)}
                        if any(old[c]!=rr[c] for c in cols if c!=pk):raise ValueError('Atributo dimensional mudou; revisar antes de atualizar '+t)
                        sid=old[pk]
                    else:sid=inserir(cur,t,rr)
                else:sid=inserir(cur,t,rr)
                maps[t][r[pk]]=sid
            logger.info('%s: %s registros preparados',t,len(data[t]))
    for t in TABELAS:
        regra=reconciliar(cur,t,data[t],maps,exec_id);regras.append(regra);logger.info('%s: reconciliacao integral aprovada',t)
        if not reuso:inserir(cur,'quality.reconciliacao_carga',{'execucao_id':exec_id,**regra})
    if not reuso:
        cur.execute('UPDATE audit.execucao_carga SET status=?,fim_utc=?,detalhe=? WHERE execucao_id=?','APROVADA',datetime.now(timezone.utc).replace(tzinfo=None),texto({'gold_manifesto_sha256':m['_hash_manifesto'],'mapas':maps}),exec_id)
    conn.commit()
    return exec_id,regras,reuso

def executar(raiz,run_id,servidor,gold=None,driver='ODBC Driver 18 for SQL Server',confiar_certificado=False):
    raiz=Path(raiz).resolve();q=raiz/'quality/20_carga_sql'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO'}
    handler=logging.FileHandler(q/'execucao.log',encoding='utf-8');logger=logging.getLogger('carga20.'+run_id);logger.setLevel(logging.INFO);logger.addHandler(handler);conn=None
    try:
        p=Path(gold).resolve() if gold else selecionar_gold(raiz);m,data=ler_gold(raiz,p);m['_hash_manifesto']=sha(p/'manifesto_dimensional.json')
        rel['gold_run_id']=m['run_id'];rel['gold_manifesto_sha256']=m['_hash_manifesto']
        if any(c in servidor for c in ';{}\n\r') or any(c in driver for c in ';{}\n\r'):raise ValueError('Servidor/driver invalido')
        import pyodbc
        if driver not in pyodbc.drivers():raise ValueError('Driver ODBC nao instalado: '+driver)
        cs='DRIVER={'+driver+'};SERVER='+servidor+';DATABASE='+PROJETO+';Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate='+('yes' if confiar_certificado else 'no')+';'
        conn=pyodbc.connect(cs,autocommit=False,timeout=15)
        conn.timeout=60
        eid,regras,reuso=carregar_sql(conn,m,data,logger)
        rel.update(status='CARGA_SQL_RECONCILIADA',execucao_id_sql=eid,regras=regras,reuso_sem_nova_carga=reuso)
    except Exception as exc:
        if conn is not None:conn.rollback()
        # Error remains local; rolled-back audit/data are not claimed as persisted.
        rel.update(status='FALHA',erro=str(exc),rollback_solicitado=conn is not None);logger.exception('Carga bloqueada ou revertida')
        raise
    finally:
        if conn is not None:conn.close()
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_20_carga_sql.json',rel);handler.close();logger.removeHandler(handler)
    return rel

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--servidor',required=True);p.add_argument('--gold',type=Path);p.add_argument('--driver',default='ODBC Driver 18 for SQL Server');p.add_argument('--confiar-certificado',action='store_true');a=p.parse_args()
    r=executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.gold,a.driver,a.confiar_certificado)
    print(texto({'status':r['status'],'execucao_id_sql':r['execucao_id_sql'],'regras_aprovadas':len(r['regras']),'conclusao':str(a.raiz/'quality/20_carga_sql'/r['run_id']/'conclusao_20_carga_sql.json')}))
if __name__=='__main__':main()
