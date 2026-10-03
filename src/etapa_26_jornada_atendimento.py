"""Particionamento por jornada total e hipoteses explicitas de atendimento."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

PROJETO='potencial-de-mercado-e-expansao-comercial'


def resolver(pontos, matriz, limites):
    if not limites or len({x['cenario'] for x in limites})!=len(limites):raise ValueError('Cenarios unicos obrigatorios')
    origem=next(i for i,p in enumerate(pontos) if p['municipio']=='Ribeirão Preto')
    cidades=sorted((i for i in range(len(pontos)) if i!=origem),key=lambda i:pontos[i]['codigo_ibge'])
    n=len(cidades);total=(1<<n)-1
    if n!=12:raise ValueError('Exige as 12 cidades de expansao e Ribeirao Preto')
    tempo=matriz['durations'];dist=matriz['distances']
    for a in (tempo,dist):
        if len(a)!=n+1 or any(len(l)!=n+1 for l in a):raise ValueError('Dimensoes da matriz divergentes')
        if any(v is None or not math.isfinite(v) or v<0 or (i!=j and v<=0) for i,l in enumerate(a) for j,v in enumerate(l)):raise ValueError('Matriz invalida')
    @lru_cache(None)
    def caminho(mask,j):
        atual=cidades[j];anterior=mask^(1<<j)
        if not anterior:return tempo[origem][atual],dist[origem][atual],(j,)
        candidatos=[]
        for k in range(n):
            if anterior&(1<<k):
                t,d,seq=caminho(anterior,k)
                candidatos.append((t+tempo[cidades[k]][atual],d+dist[cidades[k]][atual],seq+(j,)))
        return min(candidatos)
    ciclos={}
    for mask in range(1,total+1):
        candidatos=[]
        for j in range(n):
            if mask&(1<<j):
                t,d,seq=caminho(mask,j)
                candidatos.append((t+tempo[cidades[j]][origem],d+dist[cidades[j]][origem],seq))
        ciclos[mask]=min(candidatos)
    resumos=[];rotas=[];paradas=[];isoladas_tabela=[]
    for cfg in limites:
        jornada,pausa,reserva,visitas,minutos=(cfg[k] for k in ('jornada_h','pausas_h','reserva_h','atendimentos_por_cidade','minutos_por_atendimento'))
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in (jornada,pausa,reserva,visitas,minutos)) or jornada<=0 or visitas<=0 or int(visitas)!=visitas or minutos<=0 or pausa+reserva>=jornada:
            raise ValueError('Parametros de jornada/atendimento invalidos')
        limite=jornada-pausa-reserva;servico=visitas*minutos*60
        permitidos={m for m,(t,d,s) in ciclos.items() if t+m.bit_count()*servico<=limite*3600+1e-7}
        @lru_cache(None)
        def cobrir(mask):
            if not mask:return (0,0.,0.,())
            primeiro=mask&-mask;sub=mask;melhor=None
            while sub:
                if sub&primeiro and sub in permitidos:
                    resto=cobrir(mask^sub)
                    if resto is not None:
                        t,d,_=ciclos[sub];cand=(resto[0]+1,resto[1]+t,resto[2]+d,(sub,)+resto[3])
                        if melhor is None or cand<melhor:melhor=cand
                sub=(sub-1)&mask
            return melhor
        plano=cobrir(total);sid=cfg['cenario']
        isoladas=[pontos[cidades[j]]['municipio'] for j in range(n) if ciclos[1<<j][0]+servico>limite*3600+1e-7]
        resumos.append({'cenario':sid,'orcamento_deslocamento_e_atendimento_h':limite,'natureza_limite':'HIPOTESES_DE_JORNADA_E_ATENDIMENTO', 'jornada_h':jornada,'pausas_h':pausa,'reserva_h':reserva,'atendimentos_por_cidade':visitas,'minutos_por_atendimento':minutos,'status':'COBERTURA_COMPLETA_PRELIMINAR' if plano is not None else 'INVIAVEL_NESTE_LIMITE','cidades_cobertas':n if plano is not None else 0,'numero_circuitos':plano[0] if plano else None,'tempo_total_deslocamento_h':plano[1]/3600 if plano else None,'distancia_total_km':plano[2]/1000 if plano else None,'cidades_com_viagem_isolada_acima_jornada':'; '.join(isoladas),'viabilidade_diaria_confirmada':False})
        for j,i in enumerate(cidades):
            t,d,_=ciclos[1<<j];livre=limite*3600-t
            isoladas_tabela.append({'cenario':sid,'codigo_ibge':pontos[i]['codigo_ibge'],'municipio':pontos[i]['municipio'],'ida_volta_deslocamento_h':t/3600,'tempo_atendimento_planejado_h':servico/3600,'tempo_total_com_reservas_h':t/3600+servico/3600+pausa+reserva,'cabe_na_jornada_hipotetica':t+servico<=limite*3600+1e-7,'maximo_atendimentos_na_viagem_isolada':max(0,math.floor(livre/(minutos*60))),'natureza':'SIMULACAO_NAO_PEDIDOS_CONFIRMADOS'})
        if plano is None:continue
        for ordem,mask in enumerate(plano[3],1):
            t,d,seq=ciclos[mask];indices=[origem]+[cidades[j] for j in seq]+[origem]
            rid=sid+f'_C{ordem:02d}'
            rotas.append({'cenario':sid,'circuito_id':rid,'numero_cidades':len(seq),'tempo_deslocamento_h':t/3600,'tempo_atendimento_h':len(seq)*servico/3600,'tempo_total_com_reservas_h':t/3600+len(seq)*servico/3600+pausa+reserva,'jornada_h':jornada,'atendimentos_planejados':len(seq)*visitas,'maximo_atendimentos_modelados':max(0,math.floor((limite*3600-t)/(minutos*60))),'distancia_preliminar_km':d/1000,'sequencia':' -> '.join(pontos[i]['municipio'] for i in indices),'passa_franca':any(pontos[i]['codigo_ibge']=='3516200' for i in indices),'passa_barretos':any(pontos[i]['codigo_ibge']=='3505500' for i in indices),'custo_total_rota_brl':None,'faturamento_equilibrio_brl':None,'viabilidade_diaria_confirmada':False})
            for k,i in enumerate(indices[1:-1],1):paradas.append({'cenario':sid,'circuito_id':rid,'ordem':k,'codigo_ibge':pontos[i]['codigo_ibge'],'municipio':pontos[i]['municipio']})
        cobertura=[p['codigo_ibge'] for p in paradas if p['cenario']==sid]
        if len(cobertura)!=12 or len(set(cobertura))!=12:raise ValueError('Cobertura municipal divergente')
    return resumos,rotas,paradas,isoladas_tabela


def executar(raiz,run_id,etapa24=None,parametros=None):
    config_path=Path(parametros) if parametros else Path(raiz)/'docs/26_jornada_atendimento/PARAMETROS_JORNADA.json'
    config=json.loads(config_path.read_text(encoding='utf-8-sig'))
    if config.get('projeto')!=PROJETO:raise ValueError('Projeto divergente')
    limites=config['cenarios']
    raiz=Path(raiz)
    if etapa24 is None:
        pastas=sorted((raiz/'quality/24_coleta_logistica').glob('*/conclusao_24.json'))
        if not pastas:raise ValueError('Conclusao da etapa 24 nao encontrada')
        etapa24=pastas[-1]
    etapa24=Path(etapa24);meta=json.loads(etapa24.read_text(encoding='utf-8-sig'))
    if meta.get('projeto')!=PROJETO or meta.get('erros'):raise ValueError('Exige etapa 24 com coleta completa sem erros')
    pasta=Path(meta['saida']);raw=Path(meta['bronze'])
    arquivos=('ajustes_coordenadas.json','circuitos_rodoviarios_preliminares.json')
    hashes={x['arquivo']:x['sha256'] for x in meta['exportacoes']}
    for nome in arquivos:
        if hashlib.sha256((pasta/nome).read_bytes()).hexdigest()!=hashes[nome]:raise ValueError('Arquivo da etapa 24 divergente: '+nome)
    registro=json.loads((raw/'registro_coleta.json').read_text(encoding='utf-8-sig'))
    matriz_arquivo=raw/'osrm_matriz.json'
    fonte=next(x for x in registro['fontes'] if x['arquivo']=='osrm_matriz.json')
    if hashlib.sha256(matriz_arquivo.read_bytes()).hexdigest()!=fonte['sha256']:raise ValueError('Matriz original OSRM divergente')
    pontos=json.loads((pasta/'ajustes_coordenadas.json').read_text(encoding='utf-8-sig'));matriz=json.loads(matriz_arquivo.read_text(encoding='utf-8-sig'))
    if matriz.get('code')!='Ok' or matriz.get('fallback_speed_cells'):raise ValueError('Matriz OSRM sem rotas validas')
    for i,p in enumerate(pontos):
        if not all(math.isclose(a,b,abs_tol=1e-7) for a,b in zip(matriz['sources'][i]['location'],(p['longitude_roteada'],p['latitude_roteada']))):raise ValueError('Ordem dos pontos diverge da matriz')
    q=raiz/'quality/26_jornada_atendimento'/run_id;out=raiz/'datalake/03_gold'/run_id/'jornada_atendimento';q.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
    conclusao={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'entrada_24_run_id':meta['run_id'],'entrada_24_sha256':hashlib.sha256(etapa24.read_bytes()).hexdigest(),'matriz_sha256':fonte['sha256'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'hipoteses_utilizadas':config,'parametros_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest()}
    try:
        resumo,rotas,paradas,isoladas=resolver(pontos,matriz,limites)
        import pyarrow as pa
        import pyarrow.parquet as pq
        for nome,linhas in {'resumo_cenarios':resumo,'circuitos_divididos':rotas,'cobertura_municipal':paradas,'viagens_isoladas':isoladas,'pontos_revisao':[p for p in pontos if p['revisar_ponto']]}.items():
            (out/(nome+'.json')).write_text(json.dumps(linhas,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
            if linhas:
                pq.write_table(pa.Table.from_pylist(linhas),out/(nome+'.parquet'))
                if pq.read_table(out/(nome+'.parquet')).to_pylist()!=linhas:raise ValueError('Exportacao divergente')
        texto='# Jornada total e atendimento — simulacao\n\nObjetivo lexicografico: menor numero de circuitos; menor soma de tempo de deslocamento; menor soma de km para desempate. Cada subconjunto usa seu ciclo de menor tempo na matriz OSRM dirigida. Hipoteses de jornada e atendimentos, nao agenda real.\n\n'
        texto+='| Cenario | Status | Circuitos | Horas totais | km totais |\n|---|---|---:|---:|---:|\n'
        for x in resumo:texto+=f"| {x['cenario']} | {x['status']} | {x['numero_circuitos']} | {x['tempo_total_deslocamento_h']} | {x['distancia_total_km']} |\n"
        for x in rotas:texto+=f"\n- {x['circuito_id']}: {x['sequencia']}; {x['tempo_deslocamento_h']:.2f} h dirigindo, {x['tempo_total_com_reservas_h']:.2f} h incluindo atendimento/pausas/reserva; {x['distancia_preliminar_km']:.2f} km.\n"
        texto+='\nCentroides e pontos de revisao mantidos, sem substituir por enderecos inventados. Atendimentos, pausas e reserva sao hipoteses. Tempo dentro das cidades e carga por cliente nao sao conhecidos. Pedagios nao integram a otimizacao. Nenhum municipio pode ser omitido para declarar cobertura completa.\n'
        (out/'RELATORIO.md').write_text(texto,encoding='utf-8')
        conclusao.update(status='SIMULACAO_JORNADA_COM_PENDENCIAS',saida=str(out),resumo=resumo,exportacoes=[{'arquivo':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())])
    except Exception as e:conclusao.update(status='FALHA',erro=str(e));raise
    finally:
        conclusao['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_26.json').write_text(json.dumps(conclusao,ensure_ascii=False,indent=2),encoding='utf-8')
    return conclusao


def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);p.add_argument('--conclusao24',type=Path);p.add_argument('--parametros',type=Path);a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.conclusao24,a.parametros),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
