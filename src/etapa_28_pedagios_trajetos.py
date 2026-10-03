"""Geometria OSRM e candidatos OSM: estimativa, nunca tarifa integral homologada."""
import argparse,json,hashlib,math,re,html
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from uuid import uuid4
from etapa_27_equilibrio_viagens import PROJETO,ler,sha,fonte,arquivo,calcular
OSRM='https://router.project-osrm.org'
OVERPASS='https://overpass-api.de/api/interpreter'
ECO='https://www.ecoviasnoroestepaulista.com.br'
URL_NOTICIA=ECO+'/noticias/novas-tarifas-de-pedagio-entram-em-vigor-em-1o-de-maio-nas-rodovias-da-ecovias-noroeste-paulista/'
URL_PDF=ECO+'/wp-content/uploads/sites/15/2026/04/2026-Tarifas-Site.pdf'

def baixar(url,p,registro,cache=None):
    if cache is not None:
        b=(Path(cache)/p.name).read_bytes();modo='REPLAY_LOCAL_PARA_TESTE'
    else:
        with urlopen(Request(url,headers={'User-Agent':'PesquisaLogistica/1.0'}),timeout=40) as resp:
            b=resp.read(25*1024*1024+1)
        modo='ONLINE'
    if len(b)>25*1024*1024:raise ValueError('Resposta excede limite')
    p.write_bytes(b);registro.append({'url':url,'arquivo':p.name,'sha256':sha(p),'coleta_utc':datetime.now(timezone.utc).isoformat(),'modo':modo});return b

def gap(p,a,b):
    # Projecao local em metros, adequada para identificar candidatos a poucos metros.
    c=math.cos(math.radians(p[1]));ax=(a[0]-p[0])*111320*c;ay=(a[1]-p[1])*111320;bx=(b[0]-p[0])*111320*c;by=(b[1]-p[1])*111320
    dx=bx-ax;dy=by-ay;t=max(0,min(1,-(ax*dx+ay*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
    return math.hypot(ax+t*dx,ay+t*dy)

def candidatos(legs,nodes,sequencia,circuito):
    rows=[]
    for ordem,leg in enumerate(legs,1):
        if not math.isclose(sum(s['distance'] for s in leg['steps']),leg['distance'],abs_tol=2):raise ValueError('Distancia dos passos diverge do trecho')
        segments=[(a,b) for s in leg['steps'] for a,b in zip(s['geometry']['coordinates'],s['geometry']['coordinates'][1:])]
        for n in nodes:
            dist=min((gap((n['lon'],n['lat']),a,b) for a,b in segments),default=math.inf)
            if dist>3:continue
            tags=n.get('tags',{});v=re.search(r'(\d+(?:\.\d+)?)BRL/motorcar(?:;|$)',tags.get('charge',''))
            rows.append({'circuito_id':circuito,'ordem_trecho':ordem,'origem':sequencia[ordem-1],'destino':sequencia[ordem],'osm_node_id':n['id'],'latitude':n['lat'],'longitude':n['lon'],'identificacao':tags.get('name') or tags.get('note') or str(n['id']),'operador':tags.get('operator'),'distancia_geometria_m':dist,'tarifa_osm_brl':float(v.group(1)) if v else None,'data_verificacao_osm':tags.get('check_date'),'fonte_posicao':'https://www.openstreetmap.org/node/'+str(n['id']),'status':'CANDIDATO_GEOMETRICO_NAO_PASSAGEM_OPERACIONAL_CONFIRMADA'})
    return rows

def executar(raiz,run_id,cache=None):
    raiz=Path(raiz)
    p27,m27=fonte(raiz,'27_equilibrio_viagens','conclusao_27.json','SENSIBILIDADE_COM_PEDAGIOS_E_DEMANDA_PENDENTES')
    p26,m26=fonte(raiz,'26_jornada_atendimento','conclusao_26.json','SIMULACAO_JORNADA_COM_PENDENCIAS')
    p24,m24=fonte(raiz,'24_coleta_logistica','conclusao_24.json','COLETA_CONCLUIDA_COM_ROTAS_PRELIMINARES')
    if m27['entrada_26_run_id']!=m26['run_id'] or m26['entrada_24_run_id']!=m24['run_id']:raise ValueError('Vinculo das entradas divergente')
    rp=arquivo(m26,'circuitos_divididos.json');cp=arquivo(m24,'ajustes_coordenadas.json');fp=arquivo(m24,'combustivel_oficial.json')
    rotas=ler(rp);coords=ler(cp);por_nome={x['municipio']:x for x in coords};fuel=ler(fp)[0]
    if len(coords)!=13 or len(por_nome)!=13:raise ValueError('Pontos duplicados ou faltantes')
    q=raiz/'quality/28_pedagios_trajetos'/run_id;out=raiz/'datalake/03_gold'/run_id/'pedagios_trajetos';raw=raiz/'datalake/01_bronze'/run_id/'pedagios_trajetos'
    for p in (q,out,raw):p.mkdir(parents=True,exist_ok=False)
    registro=[];meta={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'entrada_27_run_id':m27['run_id'],'entrada_26_run_id':m26['run_id'],'entrada_24_run_id':m24['run_id'],'entrada_sha256':{str(p):sha(p) for p in (p27,p26,p24,rp,cp,fp)},'script_sha256':sha(__file__),'saida':str(out),'bronze':str(raw),'modo':'REPLAY_TESTE' if cache else 'ONLINE','tolerancia_candidato_m':3,'erros_fontes':[]}
    try:
        detalhadas=[];trechos=[];allcandidates=[];novas=[]
        # Primeiro obter trajetos: o bounding box da busca inclui todas as geometrias.
        routes=[];allpoints=[]
        for i,r in enumerate(rotas):
            seq=r['sequencia'].split(' -> ')
            pts=[por_nome[n] for n in seq]
            u=OSRM+'/route/v1/driving/'+';'.join(f"{p['longitude_roteada']},{p['latitude_roteada']}" for p in pts)+'?steps=true&overview=full&geometries=geojson'
            data=json.loads(baixar(u,raw/f'rota{i}.json',registro,cache))
            if data.get('code')!='Ok' or len(data.get('routes',[]))!=1:raise ValueError('OSRM sem rota unica')
            route=data['routes'][0]
            if len(route['legs'])!=len(seq)-1 or route['geometry'].get('type')!='LineString':raise ValueError('Geometria ou numero de trechos invalido')
            if any(not math.isfinite(route[k]) or route[k]<=0 for k in ('distance','duration')):raise ValueError('Distancia/tempo invalidos')
            if not math.isclose(sum(l['distance'] for l in route['legs']),route['distance'],abs_tol=2):raise ValueError('Trechos nao reconciliam')
            allpoints.extend(route['geometry']['coordinates']);routes.append((r,seq,route))
        # Inclui cabines e porticos. Ausencia de um ponto OSM nao comprova ausencia de pedagio.
        bbox=(min(p[1] for p in allpoints)-.01,min(p[0] for p in allpoints)-.01,max(p[1] for p in allpoints)+.01,max(p[0] for p in allpoints)+.01)
        box=','.join(f'{v:.6f}' for v in bbox)
        query=f'[out:json][timeout:25];(node["barrier"="toll_booth"]({box});node["highway"="toll_gantry"]({box});way["highway"="toll_gantry"]({box}););out center;'
        osm=json.loads(baixar(OVERPASS+'?'+urlencode({'data':query}),raw/'osm_local.json',registro,cache))
        if 'remark' in osm or not isinstance(osm.get('elements'),list):raise ValueError('Resposta OSM incompleta')
        nodes=[n for n in osm['elements'] if n['type']=='node' and 'lat' in n and 'lon' in n]
        meta['bbox_osm']=list(bbox);meta['porticos_way_sem_matching']=sum(n['type']=='way' for n in osm['elements'])
        oficiais=[]
        try:
            b=baixar(URL_NOTICIA,raw/'noticia_ecovias.html',registro,cache)
            texto=html.unescape(re.sub('<[^>]*>',' ',b.decode('utf8','replace')))
            texto=texto.split('TAG com desconto')[0]
            if 'maio de 2026' not in texto:raise ValueError('Vigencia da publicacao exige revisao')
            for nome,rod,valor in re.findall(r'([A-ZÁÀÃÂÉÊÍÓÔÕÚÇ][A-ZÁÀÃÂÉÊÍÓÔÕÚÇ\s]+)\s*\([^)]*(SP-\d+)[^)]*\)\s*:\s*R\$\s*([\d,]+)',texto):
                oficiais.append({'praca':nome.strip(),'rodovia':rod,'tarifa_cat1_sem_desconto_brl':float(valor.replace(',','.')),'vigencia_inicio':'2026-05-01','fonte_url':URL_NOTICIA,'fonte_sha256':sha(raw/'noticia_ecovias.html'),'natureza':'TARIFA_PRIMARIA_PUBLICADA_PASSAGEM_NAO_CONFIRMADA'})
            if len(oficiais)!=10:raise ValueError('Tabela oficial exige revisao de estrutura')
            pdf=baixar(URL_PDF,raw/'tarifa_ecovias.pdf',registro,cache)
            if not pdf.startswith(b'%PDF'):raise ValueError('Fonte oficial nao retornou PDF')
        except Exception as e:meta['erros_fontes'].append({'fonte':'ECOVIAS','erro':str(e)});oficiais=[]
        for r,seq,route in routes:
            cs=candidatos(route['legs'],nodes,seq,r['circuito_id']);allcandidates.extend(cs)
            # Nao usar zero se nada identificado. Nenhum total homologado e gerado.
            est=sum(c['tarifa_osm_brl'] for c in cs) if cs and all(c['tarifa_osm_brl'] is not None for c in cs) else None
            km=route['distance']/1000;h=route['duration']/3600;totalh=r['tempo_total_com_reservas_h']-r['tempo_deslocamento_h']+h
            detalhadas.append({'circuito_id':r['circuito_id'],'sequencia':r['sequencia'],'km_etapa26':r['distancia_preliminar_km'],'km_trajeto_etapa28':km,'diferenca_km':km-r['distancia_preliminar_km'],'diferenca_percentual':100*(km/r['distancia_preliminar_km']-1),'tempo_deslocamento_h':h,'tempo_total_com_reservas_h':totalh,'jornada_h':r['jornada_h'],'cabe_jornada_hipotetica_atualizada':totalh<=r['jornada_h'],'candidatos_identificados':len(cs),'pedagio_estimado_pontos_osm_brl':est,'pedagio_total_homologado_brl':None,'cobertura_pedagios_completa_confirmada':False,'rodovias':' | '.join(sorted({s['ref'] for l in route['legs'] for s in l['steps'] if s.get('ref')}))})
            for i,l in enumerate(route['legs']):trechos.append({'circuito_id':r['circuito_id'],'ordem':i+1,'origem':seq[i],'destino':seq[i+1],'km':l['distance']/1000,'tempo_h':l['duration']/3600,'rodovias':' | '.join(sorted({s['ref'] for s in l['steps'] if s.get('ref')}))})
            novo=dict(r,distancia_preliminar_km=km,tempo_total_com_reservas_h=totalh);novas.append(novo)
        cfg=json.loads(json.dumps(m27['parametros']));cfg['pedagios_por_circuito']={}
        sens=calcular(novas,fuel['preco_medio_brl_l'],cfg);totais={x['circuito_id']:x for x in detalhadas}
        for x in sens:
            t=totais[x['circuito_id']]['pedagio_estimado_pontos_osm_brl'];cost=x['custo_parcial_sem_pedagio_brl']+t if t is not None else None
            x.update(pedagio_estimado_pontos_osm_brl=t,custo_estimado_com_pontos_osm_brl=cost,receita_estimada_com_pontos_osm_brl=cost/x['margem_hipotetica'] if cost is not None else None,natureza='SIMULACAO_PEDAGIOS_OSM_NAO_HOMOLOGADOS_KM_ETAPA28')
        import pyarrow as pa
        import pyarrow.parquet as pq
        for nome,rows in {'trajetos':detalhadas,'trechos':trechos,'passagens_candidatas':allcandidates,'tarifas_oficiais_ecovias':oficiais,'sensibilidade_provisoria':sens}.items():
            (out/(nome+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
            if rows:
                pq.write_table(pa.Table.from_pylist(rows),out/(nome+'.parquet'))
                if pq.read_table(out/(nome+'.parquet')).to_pylist()!=rows:raise ValueError('Exportacao divergente')
        (raw/'registro_coleta.json').write_text(json.dumps(registro,ensure_ascii=False,indent=2),encoding='utf8')
        texto='# Pedagios e trajetos — estimativa provisoria\n\nKM reconsultados com geometria OSRM. Valores OSM nao sao tarifas oficiais homologadas. A ausencia de ponto OSM nao prova ausencia de cobranca. Nao transfere valores para a configuracao aprovada da etapa 27.\n\n| Circuito | km novos | Candidatos | Estimativa OSM R$ |\n|---|---:|---:|---:|\n'
        for r in detalhadas:texto+=f"| {r['circuito_id']} | {r['km_trajeto_etapa28']:.2f} | {r['candidatos_identificados']} | {r['pedagio_estimado_pontos_osm_brl']} |\n"
        texto+='\nTodos os valores de pedagio total homologado e cobertura confirmada ficam pendentes. Nao inclui descontos TAG/DUF. Fiorino sem reboque, dois eixos, rodagem simples: estimativa motorcar; categoria operacional deve ser conferida. Fontes oficiais Entrevias/ViaPaulista ainda requerem confirmacao; porticos novos podem nao constar no OSM. Consumo/desgaste/margem seguem hipoteses da etapa 27.\n'
        (out/'RELATORIO.md').write_text(texto,encoding='utf8')
        meta.update(status='ESTIMATIVA_PROVISORIA_PEDAGIOS_NAO_HOMOLOGADOS',contagens={'trajetos':len(detalhadas),'trechos':len(trechos),'passagens_candidatas':len(allcandidates),'tarifas_oficiais':len(oficiais),'sensibilidade':len(sens)},exportacoes=[{'arquivo':p.name,'sha256':sha(p)} for p in sorted(out.iterdir())],registro_coleta_sha256=sha(raw/'registro_coleta.json'))
    except Exception as e:meta.update(status='FALHA',erro=str(e));raise
    finally:
        meta['fim_utc']=datetime.now(timezone.utc).isoformat();(q/'conclusao_28.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);a=p.parse_args()
    print(json.dumps(executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
