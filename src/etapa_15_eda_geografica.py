"""EDA geografica sobre centroides municipais; nao calcula rotas de entrega."""
import argparse
import html
import json
import math
import statistics
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO, carregar, sha, gravar, canon
from etapa_11_eda_estrutura import selecionar

ORIGENS = {'3548906': 'FABRICA', '3543402': 'CD', '3509502': 'CD', '3552205': 'CD', '3550308': 'CD'}
RAIO_KM = 6371.0088


def distancia(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (
        a['latitude_centroide'], a['longitude_centroide'],
        b['latitude_centroide'], b['longitude_centroide']))
    v = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return RAIO_KM * 2 * math.asin(math.sqrt(min(1, max(0, v))))


def tabela_html(rows, colunas):
    return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in colunas)+'</tr>'+''.join(
        '<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in colunas)+'</tr>' for r in rows)+'</table>'


def mapa_svg(pontos):
    # Coordenadas projetadas localmente: x = longitude*cos(latitude media).
    fator = math.cos(math.radians(statistics.mean(r['latitude_centroide'] for r in pontos)))
    xs = [r['longitude_centroide']*fator for r in pontos]
    ys = [r['latitude_centroide'] for r in pontos]
    escala = min(560/(max(xs)-min(xs)), 500/(max(ys)-min(ys)))
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 640" role="img" aria-label="Posicoes relativas de 17 centroides municipais"><rect width="760" height="640" fill="#f4f7fb"/><text x="24" y="28" font-size="18">Centroides municipais — posições relativas</text>'
    for r, x, y in zip(pontos, xs, ys):
        px=85+(x-min(xs))*escala; py=565-(y-min(ys))*escala
        cor={'EXPANSAO':'#176b9a','CD':'#d45d19','FABRICA':'#7850a3'}[r['papel']]
        svg+=f'<circle cx="{px:.2f}" cy="{py:.2f}" r="7" fill="{cor}"><title>{html.escape(r["municipio"])} ({r["uf"]}) — {r["papel"]}</title></circle><text x="{px+10:.2f}" y="{py+(-12 if r['numero_mapa']==6 else 4):.2f}" font-size="13">{r["numero_mapa"]}</text>'
    svg+='<text x="680" y="75">N ↑</text><text x="24" y="620" font-size="13">Azul: expansão | Laranja: CD | Roxo: fábrica. Sem limites, vias ou rotas.</text></svg>'
    return svg


def executar(raiz, run_id, base=None):
    raiz=Path(raiz).resolve(); q=raiz/'quality/15_eda_geografica'/run_id
    q.mkdir(parents=True, exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome, cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond: raise ValueError(nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz)
        m=json.loads((p/'manifesto_base_eda.json').read_text(encoding='utf-8')); mh=sha(p/'manifesto_base_eda.json')
        regra('Projeto e status base',m['projeto']==PROJETO and m['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        anterior=None
        for f in sorted((raiz/'quality/14_eda_temporal').glob('*/conclusao_14_eda_temporal.json'),reverse=True):
            r=json.loads(f.read_text(encoding='utf-8'))
            if r.get('status')=='EDA_TEMPORAL_CONCLUIDA_COM_LIMITACOES' and r.get('entrada',{}).get('manifesto_base_sha256')==mh:
                anterior=f; break
        regra('Temporal concluida para mesma base',anterior is not None)
        temporal=json.loads(anterior.read_text(encoding='utf-8'))
        ent=next(x for x in m['entradas'] if x['tipo']=='municipal')
        pm=raiz/'datalake/02_silver'/ent['run_id']/'municipal'
        regra('Hash manifesto Silver municipal',sha(pm/'manifesto_silver.json')==ent['manifesto_sha256'])
        sm, mt=carregar(pm,'municipal'); municipios=mt['municipios'][0]; dists=mt['distancias_geodesicas'][0]
        por_codigo={r['codigo_ibge']:r for r in municipios}
        cidades=[r for r in municipios if r['cidade_expansao']]
        origens=[por_codigo[c] for c in ORIGENS if c in por_codigo]
        regra('17 municipios distintos',len(municipios)==len(por_codigo)==17)
        regra('12 destinos e 5 origens',len(cidades)==12 and len(origens)==5 and {r['codigo_ibge'] for r in municipios if not r['cidade_expansao']}==set(ORIGENS))
        pontos=[]
        for i,r in enumerate(municipios,1):
            regra('Coordenadas validas '+r['codigo_ibge'],all(isinstance(r[k],(int,float)) and math.isfinite(r[k]) for k in ['latitude_centroide','longitude_centroide']) and -90<=r['latitude_centroide']<=90 and -180<=r['longitude_centroide']<=180 and r['tipo_coordenada']=='CENTROIDE_MUNICIPAL')
            pontos.append({**r,'numero_mapa':i,'papel':'EXPANSAO' if r['cidade_expansao'] else ORIGENS[r['codigo_ibge']],'uso':'PROXIMIDADE_GEOGRAFICA_PRELIMINAR'})
        esperado={(c['codigo_ibge'],o['codigo_ibge']) for c in cidades for o in origens}
        regra('Matriz completa 12 por 5',len(dists)==60 and {(r['destino_codigo'],r['origem_codigo']) for r in dists}==esperado)
        matriz=[]
        for r in dists:
            a=por_codigo[r['destino_codigo']]; b=por_codigo[r['origem_codigo']]
            regra('Reconciliacao Haversine '+r['destino_codigo']+' '+r['origem_codigo'],abs(r['distancia_geodesica_centroides_km']-distancia(a,b))<=0.000501 and r['destino']==a['municipio'] and r['origem']==b['municipio'])
            regra('Linhagem coordenadas '+r['destino_codigo']+' '+r['origem_codigo'],set(json.loads(r['fontes_sha256_json']))=={a['fonte_sha256'],b['fonte_sha256']})
            matriz.append({**r,'origem_tipo':ORIGENS[r['origem_codigo']],'status_rodoviario':'NAO_COLETADO','distancia_rodoviaria_km':None,'tempo_viagem_minutos':None})
        proximidade=[]
        for c in cidades:
            rows=sorted([r for r in matriz if r['destino_codigo']==c['codigo_ibge']],key=lambda r:(r['distancia_geodesica_centroides_km'],r['origem_codigo']))
            cds=[r for r in rows if r['origem_tipo']=='CD']; fabrica=next(r for r in rows if r['origem_tipo']=='FABRICA')
            menor=rows[0]['distancia_geodesica_centroides_km']; empate=[r['origem_codigo'] for r in rows if r['distancia_geodesica_centroides_km']==menor]
            proximidade.append({'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'uf':c['uf'],'origem_mais_proxima_codigo':rows[0]['origem_codigo'],'origem_mais_proxima':rows[0]['origem'],'origem_mais_proxima_tipo':rows[0]['origem_tipo'],'distancia_minima_centroides_km':menor,'empates_minimo_json':json.dumps(empate),'cd_mais_proximo_codigo':cds[0]['origem_codigo'],'cd_mais_proximo':cds[0]['origem'],'distancia_cd_centroides_km':cds[0]['distancia_geodesica_centroides_km'],'distancia_fabrica_centroides_km':fabrica['distancia_geodesica_centroides_km'],'diferenca_fabrica_menos_cd_km':round(fabrica['distancia_geodesica_centroides_km']-cds[0]['distancia_geodesica_centroides_km'],3),'vantagem_primeira_para_segunda_origem_km':round(rows[1]['distancia_geodesica_centroides_km']-menor,3),'interpretacao':'Menor distancia entre centroides; nao define origem de atendimento'})
        # Dimensao de mercado em periodos fixos; nao normaliza nem cria escore.
        dicionario=mt['dicionario_indicadores'][0]; serie=mt['indicadores_serie'][0]
        specs=[('populacao_2026','6579','9324',2026,None),('unidades_alimentacao_2024','9528','706',2024,'117549')]
        ids={}
        for alias,tab,var,ano,cat in specs:
            ds=[d for d in dicionario if d['tabela']==tab and d['variavel_id']==var and (d['classificacoes_json']=='[]' if cat is None else cat in d['classificacoes_json'])]
            regra('Indicador unico '+alias,len(ds)==1);ids[alias]=ds[0]['indicador_id']
        mercado=[]
        for r in proximidade:
            item={'codigo_ibge':r['codigo_ibge'],'municipio':r['municipio'],'distancia_cd_centroides_km':r['distancia_cd_centroides_km'],'cd_mais_proximo':r['cd_mais_proximo']}
            fontes=[]
            for alias,tab,var,ano,cat in specs:
                rs=[x for x in serie if x['codigo_ibge']==r['codigo_ibge'] and x['indicador_id']==ids[alias] and x['ano_referencia']==ano]
                regra('Ano e municipio unicos '+alias+' '+r['codigo_ibge'],len(rs)<=1)
                item[alias]=None if not rs else rs[0]['valor']
                if rs:fontes.append({'indicador_id':ids[alias],'ano':ano,'fonte_url':rs[0]['fonte_url'],'fonte_sha256':rs[0]['fonte_sha256']})
            item['fontes_indicadores_json']=json.dumps(fontes,ensure_ascii=False)
            item['uso']='Contexto com periodos diferentes; unidades CNAE nao equivalem a clientes, concorrentes ou demanda'
            mercado.append(item)
        pares=[]
        for a,b in combinations(sorted(cidades,key=lambda r:r['codigo_ibge']),2):
            pares.append({'cidade_a_codigo':a['codigo_ibge'],'cidade_a':a['municipio'],'cidade_b_codigo':b['codigo_ibge'],'cidade_b':b['municipio'],'distancia_centroides_km':round(distancia(a,b),3),'metodo':'Haversine; raio medio 6371.0088 km','fontes_sha256_json':json.dumps(sorted({a['fonte_sha256'],b['fonte_sha256']})),'uso':'Proximidade territorial; nao representa rota conjunta'})
        regra('66 pares de destinos unicos',len(pares)==66 and len({(r['cidade_a_codigo'],r['cidade_b_codigo']) for r in pares})==66)
        resumo=[]
        for o in origens:
            vals=[r['distancia_geodesica_centroides_km'] for r in matriz if r['origem_codigo']==o['codigo_ibge']]
            resumo.append({'origem_codigo':o['codigo_ibge'],'origem':o['municipio'],'origem_tipo':ORIGENS[o['codigo_ibge']],'destinos':len(vals),'minimo_km':min(vals),'mediana_km':statistics.median(vals),'media_km':statistics.mean(vals),'maximo_km':max(vals),'destinos_com_menor_distancia':sum(r['origem_mais_proxima_codigo']==o['codigo_ibge'] for r in proximidade),'cd_mais_proximo_em_destinos':sum(r['cd_mais_proximo_codigo']==o['codigo_ibge'] for r in proximidade) if ORIGENS[o['codigo_ibge']]=='CD' else 0,'uso':'Estatisticas descritivas sem ponderacao por demanda; nao escolher CD por media'})
        pendencias=[{'codigo_ibge':r['codigo_ibge'],'municipio':r['municipio'],'papel':r['papel'],'status':'ENDERECO_REAL_PENDENTE','necessidade':'Endereco da instalacao' if r['papel']!='EXPANSAO' else 'Definir pontos de atendimento ou referencia urbana documentada','efeito':'Rotas, tempo, frete e escolha operacional da origem nao calculados'} for r in pontos]
        saida=raiz/'datalake/03_gold'/run_id/'eda_geografica';saida.mkdir(parents=True,exist_ok=False)
        exportacoes=[]
        tabelas=[('pontos_geograficos',pontos),('matriz_origem_destino',matriz),('proximidade_por_cidade',proximidade),('pares_cidades_expansao',pares),('resumo_por_origem',resumo),('pendencias_logisticas',pendencias),('mercado_proximidade',mercado)]
        for nome,rows in tabelas:
            campos=[]
            for k,v in rows[0].items():
                tipo=pa.bool_() if isinstance(v,bool) else pa.int64() if isinstance(v,int) else pa.float64() if isinstance(v,float) or k in ['distancia_rodoviaria_km','tempo_viagem_minutos','populacao_2026','unidades_alimentacao_2024'] else pa.string()
                campos.append(pa.field(k,tipo))
            j=saida/(nome+'.json'); a=saida/(nome+'.parquet');gravar(j,rows)
            pq.write_table(pa.Table.from_pylist(rows,schema=pa.schema(campos)),a,compression='snappy')
            regra('JSON Parquet '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()))
            exportacoes.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        limites=['Coordenadas sao centroides municipais, nao sedes urbanas, instalacoes ou clientes.','Haversine usa esfera de raio medio: aproximacao geografica, nao geodesica elipsoidal precisa.','Quilometros nao representam percurso rodoviario, tempo, frete, pedágios ou cadeia fria.','Menor distancia geografica nao significa melhor CD; depende tambem de estoque, atendimento e operacao.','Mapa esquematico sem limites municipais, vias ou rotas; sem nova coleta ou basemap externo.','Pares entre cidades nao determinam roteiro de visitas ou entregas.','Pendencias do PIB permanecem no bloco temporal; nenhum PIB ou perfil setorial foi utilizado nesta etapa.','Comparacao com analise original somente no encerramento.']
        svg=mapa_svg(pontos);(saida/'mapa_centroides.svg').write_text(svg,encoding='utf-8')
        body='<h1>EDA geográfica municipal</h1><p>'+PROJETO+' | '+run_id+'</p><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in limites)+'</ul>'+svg
        body+='<h2>Legenda dos pontos</h2>'+tabela_html(pontos,['numero_mapa','municipio','uf','papel'])
        body+='<h2>Proximidade por cidade</h2>'+tabela_html(proximidade,['municipio','origem_mais_proxima','distancia_minima_centroides_km','distancia_fabrica_centroides_km','vantagem_primeira_para_segunda_origem_km'])
        body+='<h2>Dimensão de mercado e proximidade</h2><p>População: 2026. Unidades de alimentação CNAE 56: 2024. Comparação contextual; não estima demanda.</p>'+tabela_html(mercado,['municipio','populacao_2026','unidades_alimentacao_2024','distancia_cd_centroides_km'])
        body+='<h2>Matriz completa: 60 comparações</h2>'+tabela_html(matriz,['destino','origem','origem_tipo','distancia_geodesica_centroides_km','status_rodoviario'])
        body+='<h2>Pares de destinos: ordenação geográfica</h2>'+tabela_html(sorted(pares,key=lambda r:r['distancia_centroides_km']),['cidade_a','cidade_b','distancia_centroides_km'])
        doc='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA geográfica</title><style>body{font:15px Arial;margin:30px;color:#183248}svg{width:100%;max-width:760px}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid #ccd5dd;padding:7px}h2{margin-top:30px}</style>'+body+'</html>'
        (saida/'relatorio_geografico.html').write_text(doc,encoding='utf-8')
        rel.update(status='EDA_GEOGRAFICA_CONCLUIDA_COM_LIMITACOES',entrada={'base_run_id':m['run_id'],'manifesto_base_sha256':mh,'silver_run_id':sm['run_id'],'conclusao_temporal_sha256':sha(anterior)},saida=str(saida),exportacoes=exportacoes,resumo={'municipios':17,'destinos':12,'origens':5,'comparacoes_origem_destino':60,'pares_destinos':66,'pendencias_enderecos':17,'rotas_rodoviarias_coletadas':0,'destinos_com_ribeirao_mais_proximo':sum(r['origem_mais_proxima_codigo']=='3543402' for r in proximidade)},pendencias_temporais_registradas=temporal.get('resumo',{}).get('pendencias_fontes'),metodos={'distancia':'Haversine; raio 6371.0088 km; reconciliacao Silver com tolerancia 0.000501 km','mapa':'Coordenadas locais x=longitude*cos(latitude media), y=latitude; escala igual nos eixos','proximidade':'Minimo entre cinco origens; empates pela precisao publicada registrados','pares':'12 escolhe 2 = 66; sem duplicar direcao'},limites=limites)
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(saida/'manifesto_eda_geografica.json',rel)
        return rel
    except Exception as e:
        rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_15_eda_geografica.json',rel)
        (q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path);a=ap.parse_args()
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
