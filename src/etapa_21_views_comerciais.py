"""Instala e valida as nove views comerciais da versão atual.
Executa SQL 04/05 numa transação; reverte as views se a validação falhar.
Não carrega ou altera fatos, dimensões nem auditoria SQL.
"""
import argparse
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

PROJETO='potencial-de-mercado-e-expansao-comercial'
CONTAGENS={'serie':1524,'ultimo_disponivel':646,'painel_comercial':60,
           'perfil_comercial':12,'distancias':60,'precos':67,'estudos':622}

def normalizar(valor):
    if isinstance(valor,Decimal):return str(valor)
    if isinstance(valor,datetime):return valor.isoformat()
    raise TypeError(type(valor).__name__)

def lotes(texto):
    return [x.strip() for x in re.split(r'^\s*GO\s*(?:--[^\n]*)?$',texto,flags=re.MULTILINE|re.IGNORECASE) if x.strip()]

def validar(resultados):
    if len(resultados)!=9:raise ValueError('SQL 05 deve produzir exatamente nove resultados')
    regras=[]
    def regra(nome,ok):
        regras.append({'regra':nome,'aprovado':bool(ok)})
    regra('UMA_CARGA_APROVADA',len(resultados[0])==1)
    regra('CONTAGENS_VERSAO_ATUAL',{x['objeto']:int(x['linhas']) for x in resultados[1]}==CONTAGENS)
    for i,nome in [(2,'SEM_DUPLICATAS'),(3,'CATALOGO_UNICO'),(4,'SEM_AUSENCIAS_NO_PAINEL'),
                   (5,'IMAGENS_NAO_DUPLICAM_OBSERVACOES'),(8,'EXCECAO_HISTORICA_LIMITADA')]:
        regra(nome,len(resultados[i])==0)
    historico=resultados[6]
    regra('DOZE_DENOMINADORES_HISTORICOS',len(historico)==12 and len({x['municipio'] for x in historico})==12 and all(
        x['ano_referencia']==2024 and x['valor_publicado'] is not None and x['valor_comercial']==x['valor_publicado']
        and Decimal(str(x['valor_comercial']))>0 and x['liberado_analise_comercial']==0
        and x['elegivel_uso_painel']==1 and x['criterio_uso_painel']=='DENOMINADOR_HISTORICO_2024'
        and x['motivo_restricao']=='FORA_CANDIDATO_EDA' for x in historico))
    perfis=resultados[7]
    regra('DOZE_PERFIS_COMPLETOS',len(perfis)==12 and len({x['municipio'] for x in perfis})==12 and all(
        x['indicadores_disponiveis']==5 and x['ano_populacao_mais_recente']==2026
        and all(x[k] is not None and Decimal(str(x[k]))>0 for k in
        ('populacao_2024','populacao_mais_recente','alimentacao_por_10mil_2024','varejo_alimentar_por_10mil_2024')) for x in perfis))
    return regras

def executar(raiz,run_id,servidor,driver='ODBC Driver 17 for SQL Server',confiar_certificado=False):
    raiz=Path(raiz);destino=raiz/'quality'/'21_views_comerciais'/run_id
    destino.mkdir(parents=True,exist_ok=False)
    log=logging.getLogger('views21.'+run_id);log.setLevel(logging.INFO)
    handler=logging.FileHandler(destino/'execucao.log',encoding='utf-8');log.addHandler(handler)
    conclusao={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),
               'status':'EM_EXECUCAO','versao_validacao':'21.1_BASE_ATUAL_20261003'}
    conn=None;resultados=[]
    try:
        import pyodbc
        for valor in (servidor,driver):
            if not valor or any(c in valor for c in ';{}\r\n'):raise ValueError('Servidor/driver inválido')
        if driver not in pyodbc.drivers():raise ValueError('Driver ODBC não instalado: '+driver)
        arquivos=[raiz/'sql'/'04_criar_views_comerciais.sql',raiz/'sql'/'05_validar_views_comerciais.sql']
        textos=[p.read_text(encoding='utf-8-sig') for p in arquivos]
        conclusao['scripts']=[{'arquivo':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in arquivos]
        conclusao['executor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        criacao=lotes(textos[0]);validacao=lotes(textos[1])
        if sum(bool(re.match(r'CREATE OR ALTER VIEW\s+gold\.vw_',x,re.I)) for x in criacao)!=9:
            raise ValueError('SQL 04 divergente: esperadas nove definições de view')
        conn=pyodbc.connect(f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate={"yes" if confiar_certificado else "no"};',autocommit=False,timeout=15)
        cur=conn.cursor()
        cur.execute('SELECT DB_NAME()');banco=cur.fetchone()[0]
        if banco!=PROJETO:raise ValueError('Banco divergente')
        cur.execute('SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE; SET LOCK_TIMEOUT 15000;')
        for lote in criacao:
            cur.execute(lote)
            while cur.nextset():pass
        for lote in validacao:
            cur.execute(lote)
            while True:
                if cur.description:
                    nomes=[x[0] for x in cur.description]
                    resultados.append([dict(zip(nomes,row)) for row in cur.fetchall()])
                if not cur.nextset():break
        regras=validar(resultados);conclusao['regras']=regras
        conclusao['regras_aprovadas']=sum(x['aprovado'] for x in regras)
        conclusao['regras_reprovadas']=sum(not x['aprovado'] for x in regras)
        if conclusao['regras_reprovadas']:raise ValueError('Validação reprovada; alterações nas views serão revertidas')
        conn.commit();conclusao.update(status='VIEWS_COMERCIAIS_VALIDADAS',execucao_id_sql=resultados[0][0]['execucao_id'],
            carga_gold_run_id=resultados[0][0]['run_id'],contagens=CONTAGENS,saida=str(destino))
        log.info('Nove views instaladas e nove regras aprovadas; transação confirmada.')
        return conclusao
    except Exception as exc:
        if conn:
            conn.rollback()
        conclusao.update(status='FALHA',erro=str(exc));log.exception('Etapa 21 interrompida');raise
    finally:
        if conn:conn.close()
        conclusao['fim_utc']=datetime.now(timezone.utc).isoformat()
        (destino/'resultados_validacao.json').write_text(json.dumps(resultados,ensure_ascii=False,indent=2,default=normalizar),encoding='utf-8')
        (destino/'conclusao_21.json').write_text(json.dumps(conclusao,ensure_ascii=False,indent=2,default=normalizar),encoding='utf-8')
        log.removeHandler(handler);handler.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--servidor',required=True)
    p.add_argument('--driver',default='ODBC Driver 17 for SQL Server')
    p.add_argument('--confiar-certificado',action='store_true')
    a=p.parse_args()
    r=executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.driver,a.confiar_certificado)
    print(json.dumps(r,ensure_ascii=False,indent=2,default=normalizar))

if __name__=='__main__':main()
