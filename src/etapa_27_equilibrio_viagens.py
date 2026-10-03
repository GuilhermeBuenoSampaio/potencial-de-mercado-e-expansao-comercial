"""Custo incremental e sensibilidade; nao estima pedidos nem aprova rotas."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from itertools import product
PROJETO='potencial-de-mercado-e-expansao-comercial'
def ler(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def numero(v, positivo=False):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 or (positivo and v==0): raise ValueError('Parametro numerico invalido')
    return v

def fonte(raiz, etapa, nome, status):
    caminhos=sorted((raiz/f'quality/{etapa}').glob(f'*/{nome}'))
    if not caminhos: raise ValueError('Conclusao ausente: '+nome)
    p=caminhos[-1];m=ler(p)
    if m.get('projeto')!=PROJETO or m.get('status')!=status: raise ValueError('Ultima execucao nao aprovada: '+nome)
    return p,m

def arquivo(meta,nome):
    p=Path(meta['saida'])/nome
    h=next((x['sha256'] for x in meta['exportacoes'] if x['arquivo']==nome),None)
    if not h or sha(p)!=h: raise ValueError('Hash divergente: '+nome)
    return p

def calcular(rotas, preco, cfg):
    numero(preco,True)
    for k in ('consumos_km_l','desgastes_brl_km','margens_contribuicao'):
        if not cfg[k] or len(set(cfg[k]))!=len(cfg[k]): raise ValueError('Cenarios vazios ou repetidos: '+k)
        for v in cfg[k]: numero(v,k!='desgastes_brl_km')
    if any(v>1 for v in cfg['margens_contribuicao']): raise ValueError('Margem deve ser fracao entre 0 e 1')
    ids=[r['circuito_id'] for r in rotas]
    if len(set(ids))!=len(ids): raise ValueError('Circuitos repetidos')
    if set(cfg.get('pedagios_por_circuito',{}))-set(ids): raise ValueError('Pedagio referencia circuito inexistente')
    linhas=[]
    for r in rotas:
        km=numero(r['distancia_preliminar_km'],True)
        p=cfg.get('pedagios_por_circuito',{}).get(r['circuito_id'])
        if p is not None:
            numero(p['total_brl'])
            if not p.get('fonte') or not p.get('vigencia') or p.get('passagens_verificadas') is not True: raise ValueError('Pedagio exige fonte, vigencia e passagens verificadas')
        for consumo,desgaste,margem in product(cfg['consumos_km_l'],cfg['desgastes_brl_km'],cfg['margens_contribuicao']):
            gasolina=km/consumo*preco;manutencao=km*desgaste;parcial=gasolina+manutencao
            total=parcial+p['total_brl'] if p else None
            linhas.append({'cenario_jornada':r['cenario'],'circuito_id':r['circuito_id'],'sequencia':r['sequencia'],'distancia_preliminar_km':km,'tempo_total_com_reservas_h':r['tempo_total_com_reservas_h'],'consumo_hipotetico_km_l':consumo,'desgaste_hipotetico_brl_km':desgaste,'margem_hipotetica':margem,'gasolina_brl':gasolina,'desgaste_brl':manutencao,'custo_parcial_sem_pedagio_brl':parcial,'pedagio_brl':p['total_brl'] if p else None,'custo_modelado_com_pedagio_brl':total,'receita_limite_parcial_sem_pedagio_brl':parcial/margem,'receita_equilibrio_modelada_brl':total/margem if total is not None else None,'pedagio_por_10_brl_receita_adicional':10/margem,'viabilidade_confirmada':False,'natureza':'SENSIBILIDADE_NAO_ORCAMENTO_OPERACIONAL'})
    return linhas

def executar(raiz,run_id,parametros=None):
    raiz=Path(raiz);cp=Path(parametros) if parametros else raiz/'docs/27_equilibrio_viagens/PARAMETROS_EQUILIBRIO.json';cfg=ler(cp)
    if cfg.get('projeto')!=PROJETO: raise ValueError('Projeto divergente')
    p26,m26=fonte(raiz,'26_jornada_atendimento','conclusao_26.json','SIMULACAO_JORNADA_COM_PENDENCIAS')
    p24,m24=fonte(raiz,'24_coleta_logistica','conclusao_24.json','COLETA_CONCLUIDA_COM_ROTAS_PRELIMINARES')
    if m26['entrada_24_run_id']!=m24['run_id']: raise ValueError('Etapas 24 e 26 usam coletas diferentes')
    rp=arquivo(m26,'circuitos_divididos.json');ip=arquivo(m26,'viagens_isoladas.json');fp=arquivo(m24,'combustivel_oficial.json')
    fuels=ler(fp)
    if len(fuels)!=1 or fuels[0]['produto']!='GASOLINA COMUM' or fuels[0]['municipio']!='Ribeirão Preto' or fuels[0]['status']!='FONTE_PRIMARIA_SEMANAL': raise ValueError('Referencia de combustivel inesperada')
    linhas=calcular(ler(rp),fuels[0]['preco_medio_brl_l'],cfg)
    out=raiz/'datalake/03_gold'/run_id/'equilibrio_viagens';q=raiz/'quality/27_equilibrio_viagens'/run_id
    out.mkdir(parents=True,exist_ok=False);q.mkdir(parents=True,exist_ok=False)
    meta={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'entrada_26_run_id':m26['run_id'],'entrada_24_run_id':m24['run_id'],'entradas_sha256':{str(p):sha(p) for p in (p26,p24,rp,ip,fp,cp)},'script_sha256':sha(__file__),'saida':str(out),'combustivel':fuels[0],'parametros':cfg}
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        for nome,rows in {'sensibilidade_equilibrio':linhas,'referencia_tempo_viagens_dedicadas':ler(ip)}.items():
            (out/(nome+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            if rows:
                pq.write_table(pa.Table.from_pylist(rows),out/(nome+'.parquet'))
                if pq.read_table(out/(nome+'.parquet')).to_pylist()!=rows: raise ValueError('Exportacao divergente')
        texto='# Equilibrio por viagem\n\nSimulacao de sensibilidade. Consumo carregado, desgaste e margem nao medidos. Distancias por centroides; custo real nao confirmado. Preco ANP da semana '+fuels[0]['inicio']+' a '+fuels[0]['fim']+'; nao e cotacao vigente automatica.\n\n'
        texto+='Custo = km × (gasolina/consumo + desgaste/km) + pedagios. Receita de equilibrio = custo/margem de contribuicao ANTES desta viagem e APOS demais custos variaveis. Nao descontar a logistica novamente na margem. Limite parcial sem pedagio NAO autoriza viagem.\n\n'
        texto+='| Circuito | km | Gasolina (10 km/l) | Custo parcial (desgaste 0,20/km) | Receita parcial (margem 25%) |\n|---|---:|---:|---:|---:|\n'
        for x in linhas:
            if (x['consumo_hipotetico_km_l'],x['desgaste_hipotetico_brl_km'],x['margem_hipotetica'])==(10,0.2,0.25): texto+=f"| {x['circuito_id']} | {x['distancia_preliminar_km']:.2f} | {x['gasolina_brl']:.2f} | {x['custo_parcial_sem_pedagio_brl']:.2f} | {x['receita_limite_parcial_sem_pedagio_brl']:.2f} |\n"
        texto+='\nSugestoes condicionais: compartilhar cidades quando pedidos somados cobrem a viagem; consolidar pedidos com menor frequencia quando compativel com atendimento; dedicar viagem a pedido maior com descarga longa quando esse pedido cobre o custo. Nao ha demanda, frete, peso ou receita por cliente observados. Os tempos de viagens isoladas sao referencia de jornada, nao custo de rota dedicada.\n\nNao alocar receita por populacao ou CNAE. Nao excluir municipios de menor escala. Maior numero de viagens pode aumentar km e custos. Supermercados CNAE 47.1 nao estao abrangidos na contagem de varejo especializado 47.2.\n'
        (out/'RELATORIO.md').write_text(texto,encoding='utf-8')
        meta.update(status='SENSIBILIDADE_COM_PEDAGIOS_E_DEMANDA_PENDENTES',linhas=len(linhas),exportacoes=[{'arquivo':p.name,'sha256':sha(p)} for p in sorted(out.iterdir())])
    except Exception as e: meta.update(status='FALHA',erro=str(e));raise
    finally:
        meta['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_27.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--parametros',type=Path);a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.parametros),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
