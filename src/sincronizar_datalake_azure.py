"""Sincroniza camadas e registros de qualidade sem sobrescrever blobs existentes."""
import argparse
import hashlib
import json
import logging
import mimetypes
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PROJETO='potencial-de-mercado-e-expansao-comercial'
CONTA='stcustomeranalyticsgb01'
PREFIXOS=['datalake/01_bronze','datalake/01_bronze_raw','datalake/02_silver','datalake/03_gold','quality']
EXTENSOES={'.xlsx','.xls','.xlsm','.parquet','.json','.html','.log','.txt','.svg'}

def sha_arquivo(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for bloco in iter(lambda:f.read(1024*1024),b''):h.update(bloco)
    return h.hexdigest()

def inventariar(raiz):
    itens=[]
    for prefix in PREFIXOS:
        pasta=raiz/prefix
        if not pasta.is_dir():continue
        for p in sorted(pasta.rglob('*')):
            if not p.is_file() or p.suffix.lower() not in EXTENSOES or p.name.startswith('~$'):continue
            if p.is_symlink() or not p.resolve().is_relative_to(raiz):raise ValueError('Arquivo fora da raiz: '+str(p))
            itens.append({'caminho':p.relative_to(raiz).as_posix(),'bytes':p.stat().st_size,'sha256':sha_arquivo(p)})
    if not itens:raise ValueError('Nenhum arquivo elegivel encontrado nas camadas ou quality.')
    return itens

def conferir_remoto(blob,item):
    from azure.core import MatchConditions
    props=blob.get_blob_properties()
    if props.size!=item['bytes']:raise ValueError('Conflito de tamanho: '+item['caminho'])
    h=hashlib.sha256()
    for bloco in blob.download_blob(etag=props.etag,match_condition=MatchConditions.IfNotModified).chunks():h.update(bloco)
    if h.hexdigest()!=item['sha256']:raise ValueError('Conflito SHA-256: '+item['caminho'])
    return props.etag

def enviar_item(container,raiz,item):
    from azure.core.exceptions import ResourceExistsError
    p=raiz/item['caminho'];blob=container.get_blob_client(item['caminho'])
    # Revalida o arquivo antes da transferencia; leitura posterior detecta alteracao durante o envio.
    if sha_arquivo(p)!=item['sha256']:raise ValueError('Arquivo local mudou desde o inventario: '+item['caminho'])
    criado=False
    if not blob.exists():
        from azure.storage.blob import ContentSettings
        try:
            with p.open('rb') as f:
                blob.upload_blob(f,blob_type='BlockBlob',overwrite=False,metadata={'sha256':item['sha256']},content_settings=ContentSettings(content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'))
            criado=True
        except ResourceExistsError:
            pass # Outra execucao pode ter criado o blob: precisa ser identico para seguir.
    etag=conferir_remoto(blob,item)
    if sha_arquivo(p)!=item['sha256']:raise ValueError('Arquivo local mudou durante a transferencia: '+item['caminho'])
    return {**item,'resultado':'ENVIADO_VERIFICADO' if criado else 'EXISTENTE_IDENTICO','etag':etag}

def executar(raiz,aplicar=False):
    raiz=Path(raiz).resolve();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    itens=inventariar(raiz) # Inventario antes de criar os proprios registros para evitar autorreferencia.
    q=raiz/'quality/AZ01_sincronizacao'/run;q.mkdir(parents=True,exist_ok=False)
    logger=logging.getLogger('azure_'+run);logger.setLevel(logging.INFO)
    handler=logging.FileHandler(q/'execucao.log',encoding='utf-8');logger.addHandler(handler)
    rel={'projeto':PROJETO,'run_id':run,'inicio_utc':datetime.now(timezone.utc).isoformat(),'conta':CONTA,'container':PROJETO,'modo':'APLICAR' if aplicar else 'PLANO_LOCAL','status':'EM_EXECUCAO','arquivos':[],'prefixos':PREFIXOS,'extensoes':sorted(EXTENSOES)}
    try:
        if not aplicar:
            rel['arquivos']=[{**r,'resultado':'PLANEJADO'} for r in itens];rel['status']='PLANO_LOCAL_GERADO'
        else:
            from azure.identity import AzureCliCredential
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ResourceExistsError
            with AzureCliCredential() as credential:
                with BlobServiceClient('https://'+CONTA+'.blob.core.windows.net',credential=credential) as service:
                    container=service.get_container_client(PROJETO)
                    try:container.create_container()
                    except ResourceExistsError:pass
                    for i,item in enumerate(itens,1):
                        print(f'[{i}/{len(itens)}] {item["caminho"]}',flush=True)
                        try:resultado=enviar_item(container,raiz,item)
                        except Exception:
                            rel['arquivos'].append({**item,'resultado':'FALHA'});raise
                        rel['arquivos'].append(resultado);logger.info('%s %s',resultado['resultado'],item['caminho'])
            rel['status']='SINCRONIZACAO_VERIFICADA'
    except Exception as e:
        rel['status']='FALHA';rel['erro']=str(e);logger.exception('Sincronizacao interrompida')
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();rel['resumo']=dict(Counter(r['resultado'] for r in rel['arquivos']));rel['total_planejado']=len(itens)
        (q/'inventario_envio.json').write_text(json.dumps(itens,ensure_ascii=False,indent=2),encoding='utf-8')
        (q/'conclusao_AZ01.json').write_text(json.dumps(rel,ensure_ascii=False,indent=2),encoding='utf-8')
        logger.info('Status %s',rel['status']);handler.close();logger.removeHandler(handler)
    # Registros desta sincronizacao sao enviados apos fechamento: bytes estaveis, sem autorreferencia.
    if aplicar and rel['status']=='SINCRONIZACAO_VERIFICADA':
        try:
            with AzureCliCredential() as credential:
                with BlobServiceClient('https://'+CONTA+'.blob.core.windows.net',credential=credential) as service:
                    container=service.get_container_client(PROJETO)
                    for p in [q/'inventario_envio.json',q/'conclusao_AZ01.json',q/'execucao.log']:
                        enviar_item(container,raiz,{'caminho':p.relative_to(raiz).as_posix(),'bytes':p.stat().st_size,'sha256':sha_arquivo(p)})
        except Exception as e:
            print('Dados verificados, mas envio dos registros AZ01 falhou: '+str(e));return 2
    print(json.dumps({'status':rel['status'],'total_planejado':len(itens),'resumo':rel['resumo'],'conclusao':str(q/'conclusao_AZ01.json')},ensure_ascii=False,indent=2))
    return 1 if rel['status']=='FALHA' else 0

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--aplicar',action='store_true',help='Envia e verifica os arquivos no Azure. Sem esta flag gera somente plano local.')
    a=ap.parse_args();raise SystemExit(executar(a.raiz,a.aplicar))
