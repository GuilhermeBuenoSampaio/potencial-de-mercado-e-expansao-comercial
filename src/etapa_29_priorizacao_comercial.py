"""Prioridades comerciais por criterios separados; leitura SQL sem alterar o banco."""
import argparse
import json
from decimal import Decimal
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from etapa_27_equilibrio_viagens import PROJETO, ler, sha, fonte, arquivo, numero

def analisar(perfis, trajetos, cenarios):
    exigidas=['municipio','codigo_ibge','populacao_2024','renda_mediana_2022','varejo_alimentar_2024']
    if len(perfis)!=12 or len(trajetos)!=5: raise ValueError('Esperados 12 municipios e cinco circuitos')
    municipios={p['municipio']:p for p in perfis}
    if len(municipios)!=12: raise ValueError('Municipio repetido')
    for p in perfis:
        for k in exigidas:
            if k not in p or p[k] is None: raise ValueError('Campo necessario ausente: '+k)
        for k in exigidas[2:]: numero(p[k],True)
    ids=[r['circuito_id'] for r in trajetos]
    if len(set(ids))!=5: raise ValueError('Circuito repetido')
    cobertura=[]; cidades=[]; circuitos=[]
    total=sum(p['varejo_alimentar_2024'] for p in perfis)
    for r in trajetos:
        seq=r['sequencia'].split(' -> ')
        if seq[0]!='Ribeirão Preto' or seq[-1]!='Ribeirão Preto': raise ValueError('Origem inesperada')
        nomes=seq[1:-1]; cobertura.extend(nomes)
        if not nomes or any(n not in municipios for n in nomes): raise ValueError('Municipio desconhecido')
        cs=[s for s in cenarios if s['circuito_id']==r['circuito_id']]
        if len(cs)!=27 or len({(s['consumo_hipotetico_km_l'],s['desgaste_hipotetico_brl_km'],s['margem_hipotetica']) for s in cs})!=27: raise ValueError('Sensibilidade incompleta ou duplicada')
        base=next(s for s in cs if (s['consumo_hipotetico_km_l'],s['desgaste_hipotetico_brl_km'],s['margem_hipotetica'])==(10,0.2,0.25))
        for s in cs:
            if abs(s['distancia_preliminar_km']-r['km_trajeto_etapa28'])>1e-6: raise ValueError('Distancia divergente')
            v=s['receita_estimada_com_pontos_osm_brl']
            if v is not None and abs(v-s['custo_estimado_com_pontos_osm_brl']/s['margem_hipotetica'])>1e-6: raise ValueError('Equilibrio divergente')
        ps=[municipios[n] for n in nomes]; varejo=sum(p['varejo_alimentar_2024'] for p in ps)
        receitas=[s['receita_estimada_com_pontos_osm_brl'] for s in cs if s['receita_estimada_com_pontos_osm_brl'] is not None]
        circuitos.append({'circuito_id':r['circuito_id'],'sequencia_sugerida':r['sequencia'],'municipios':len(nomes),'varejo_especializado_2024':varejo,'participacao_varejo_percentual':varejo/total*100,'populacao_2024':sum(p['populacao_2024'] for p in ps),'renda_mediana_municipal_min_2022':min(p['renda_mediana_2022'] for p in ps),'renda_mediana_municipal_max_2022':max(p['renda_mediana_2022'] for p in ps),'km_sugeridos':r['km_trajeto_etapa28'],'receita_referencia_brl':base['receita_estimada_com_pontos_osm_brl'],'receita_sensibilidade_min_brl':min(receitas) if receitas else None,'receita_sensibilidade_max_brl':max(receitas) if receitas else None,'natureza':'REFERENCIA_COMERCIAL_SIMULADA'})
        for p in ps:
            cidades.append({k:p[k] for k in exigidas}|{'circuito_id':r['circuito_id'],'varejo_por_10mil_2024':p['varejo_alimentar_2024']/p['populacao_2024']*10000,'participacao_varejo_percentual':p['varejo_alimentar_2024']/total*100})
    if len(cobertura)!=12 or set(cobertura)!=set(municipios): raise ValueError('Cobertura municipal incompleta ou repetida')
    for c in cidades:
        c['posicao_escala_varejo']=1+sum(x['varejo_alimentar_2024']>c['varejo_alimentar_2024'] for x in cidades)
        c['posicao_renda']=1+sum(x['renda_mediana_2022']>c['renda_mediana_2022'] for x in cidades)
    for c in circuitos:
        c['posicao_escala_varejo']=1+sum(x['varejo_especializado_2024']>c['varejo_especializado_2024'] for x in circuitos)
        c['posicao_menor_referencia_receita']=None if c['receita_referencia_brl'] is None else 1+sum(x['receita_referencia_brl'] is not None and x['receita_referencia_brl']<c['receita_referencia_brl'] for x in circuitos)
        c['dominado_escala_custo']=None if c['receita_referencia_brl'] is None else any(x['circuito_id']!=c['circuito_id'] and x['receita_referencia_brl'] is not None and x['varejo_especializado_2024']>=c['varejo_especializado_2024'] and x['receita_referencia_brl']<=c['receita_referencia_brl'] and (x['varejo_especializado_2024']>c['varejo_especializado_2024'] or x['receita_referencia_brl']<c['receita_referencia_brl']) for x in circuitos)
    return sorted(cidades,key=lambda x:x['posicao_escala_varejo']),sorted(circuitos,key=lambda x:x['posicao_escala_varejo'])

def executar(raiz,run_id,servidor,driver='ODBC Driver 17 for SQL Server',confiar_certificado=False):
    import pyodbc
    import pyarrow as pa
    import pyarrow.parquet as pq
    raiz=Path(raiz)
    p28,m28=fonte(raiz,'28_pedagios_trajetos','conclusao_28.json','ESTIMATIVA_PROVISORIA_PEDAGIOS_NAO_HOMOLOGADOS')
    rp=arquivo(m28,'trajetos.json');sp=arquivo(m28,'sensibilidade_provisoria.json')
    if driver not in pyodbc.drivers(): raise ValueError('Driver nao instalado: '+driver)
    for v in (servidor,driver):
        if any(t in v for t in (';','{','}')): raise ValueError('Parametro de conexao invalido')
    consulta='SELECT * FROM gold.vw_perfil_comercial ORDER BY municipio;'
    with pyodbc.connect(f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate={"yes" if confiar_certificado else "no"};',timeout=30) as con:
        con.autocommit=False
        cur=con.cursor();cur.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;')
        cur.execute('SELECT execucao_id, run_id FROM gold.vw_carga_aprovada;')
        cargas=cur.fetchall()
        if len(cargas)!=1: raise ValueError('Carga SQL aprovada deve ser unica')
        cur.execute(consulta);cols=[c[0] for c in cur.description]
        perfis=[dict(zip(cols,[float(v) if isinstance(v,Decimal) else v for v in row])) for row in cur.fetchall()]
        con.rollback()
    cidades,circuitos=analisar(perfis,ler(rp),ler(sp))
    out=raiz/'datalake/03_gold'/run_id/'priorizacao_comercial';q=raiz/'quality/29_priorizacao_comercial'/run_id
    out.mkdir(parents=True,exist_ok=False);q.mkdir(parents=True,exist_ok=False)
    meta={'projeto':PROJETO,'run_id':run_id,'entrada_28_run_id':m28['run_id'],'sql_execucao_id':cargas[0][0],'sql_run_id':cargas[0][1],'consulta_sql':consulta,'entradas_sha256':{str(p):sha(p) for p in (p28,rp,sp)},'script_sha256':sha(__file__),'saida':str(out)}
    try:
        for nome,rows in [('municipios_prioridades',cidades),('circuitos_comerciais',circuitos)]:
            (out/(nome+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            pq.write_table(pa.Table.from_pylist(rows),out/(nome+'.parquet'))
            if pq.read_table(out/(nome+'.parquet')).to_pylist()!=rows: raise ValueError('Exportacao divergente')
        texto='# Prioridades de prospeccao\n\nCinco agrupamentos sugeridos, sem definir rotas fixas do CD. Varejo especializado CNAE 47.2 exclui supermercados CNAE 47.1. Contagens sao universo observado de estabelecimentos, nao clientes ou compras.\n\n| Circuito | Sequencia | Varejo 2024 | Participacao % | Referencia de receita R$ |\n|---|---|---:|---:|---:|\n'
        for c in circuitos:
            receita='PENDENTE' if c['receita_referencia_brl'] is None else f"{c['receita_referencia_brl']:.2f}"
            texto+=f"| {c['circuito_id']} | {c['sequencia_sugerida']} | {c['varejo_especializado_2024']:.0f} | {c['participacao_varejo_percentual']:.2f} | {receita} |\n"
        texto+='\nCenario de referencia: 10 km/l, desgaste hipotetico R$ 0,20/km e margem de contribuicao hipotetica 25%, antes desta viagem e apos outros custos variaveis. Pedagios OSM nao homologados. Intervalos sao cenarios de sensibilidade, nao intervalos de confianca.\n\nPrioridade por escala: maior contagem de varejo. Prioridade por menor necessidade de receita: menor limiar simulado. Fronteira escala/custo: circuito nao dominado quando nenhum outro tem simultaneamente mais estabelecimentos e menor limiar, com ao menos uma melhora estrita. Essa comparacao nao inclui renda, concorrencia, carteira ou conversao e nao significa inviabilidade das demais cidades. Renda aparece separada, em valores nominais de 2022; nao somar medianas nem interpretar como capacidade de compra comprovada.\n\nComecar pela prospeccao dos circuitos com maior escala; avaliar o circuito com menor referencia financeira como alternativa de entrada gradual. Preservar os cinco grupos e todas as cidades. Pedidos maiores podem sustentar atendimento compartilhado a cidades menores. Viagem dedicada e condicional ao pedido e tempo de descarga, sob decisao do gerente do CD. Nao distribuir metas municipais proporcionalmente a populacao ou CNAE.\n'
        (out/'RELATORIO.md').write_text(texto,encoding='utf-8')
        meta.update(status='REFERENCIAS_COMERCIAIS_COM_LIMITACOES',municipios=len(cidades),circuitos=len(circuitos),exportacoes=[{'arquivo':p.name,'sha256':sha(p)} for p in sorted(out.iterdir())])
    except Exception as e: meta.update(status='FALHA',erro=str(e));raise
    finally:
        meta['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_29.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--servidor',required=True);p.add_argument('--driver',default='ODBC Driver 17 for SQL Server');p.add_argument('--confiar-certificado',action='store_true');a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.driver,a.confiar_certificado),ensure_ascii=False,indent=2))
