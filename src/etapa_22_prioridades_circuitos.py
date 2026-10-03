"""Diagnóstico comercial e circuitos por centroides. SQL somente leitura.
Não prevê vendas nem calcula custo rodoviário sem parâmetros externos.
"""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

PROJETO = 'potencial-de-mercado-e-expansao-comercial'
CODIGOS = {'3516200','3505500','3127107','3534302','3517406','3531902',
           '3533601','3544905','3521309','3151602','3513207','3512100'}


def haversine(a, b):
    lat1, lat2 = map(math.radians, [float(a['latitude_centroide']), float(b['latitude_centroide'])])
    dl = math.radians(float(b['longitude_centroide']) - float(a['longitude_centroide']))
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dl/2)**2
    return 2*6371.0088*math.asin(math.sqrt(min(1, max(0, h))))


def otimizar(cidades, origem, dist):
    """Held-Karp: menor ciclo fechado para este subconjunto/matriz simétrica."""
    if not cidades:
        return [origem, origem], 0.0
    cidades = tuple(sorted(cidades))
    @lru_cache(None)
    def resolver(mask, atual):
        if not mask:
            return dist[atual, origem], ()
        candidatos = []
        for j, cidade in enumerate(cidades):
            if mask & (1 << j):
                custo, resto = resolver(mask ^ (1 << j), cidade)
                candidatos.append((dist[atual, cidade]+custo, (cidade,)+resto))
        return min(candidatos)
    custo, caminho = resolver((1 << len(cidades))-1, origem)
    return [origem, *caminho, origem], custo


def analisar(perfis, pontos):
    perfis = [dict(p) for p in perfis]
    if {p['codigo_ibge'] for p in perfis} != CODIGOS or len(perfis) != 12:
        raise ValueError('Escopo municipal diferente das 12 cidades aprovadas')
    if len({p['execucao_id'] for p in perfis}) != 1:
        raise ValueError('Mais de uma carga no perfil')
    origem = '3543402'
    pontos = {p['codigo_ibge']: p for p in pontos}
    if not (CODIGOS | {origem}) <= pontos.keys():
        raise ValueError('Coordenadas incompletas')
    for p in pontos.values():
        if p['latitude_centroide'] is None or p['longitude_centroide'] is None:
            raise ValueError('Centroide ausente')
        if not (-90 <= float(p['latitude_centroide']) <= 90 and -180 <= float(p['longitude_centroide']) <= 180):
            raise ValueError('Coordenada inválida')
    dist = {(a,b): haversine(pontos[a],pontos[b]) for a in pontos for b in pontos}
    for p in perfis:
        for chave in ('populacao_2024','varejo_alimentar_2024','renda_mediana_2022'):
            if p[chave] is None or float(p[chave]) <= 0:
                raise ValueError('Indicador incompleto: '+chave)
        p['distancia_cd_geodesica_km'] = dist[origem,p['codigo_ibge']]
        p['varejo_por_10mil_2024_recalculado'] = float(p['varejo_alimentar_2024'])*10000/float(p['populacao_2024'])
    total = sum(float(p['varejo_alimentar_2024']) for p in perfis)
    acumulado = 0
    for p in sorted(perfis, key=lambda x: (-float(x['varejo_alimentar_2024']),x['codigo_ibge'])):
        acumulado += float(p['varejo_alimentar_2024'])
        p['participacao_varejo_percentual'] = float(p['varejo_alimentar_2024'])/total*100
        p['participacao_acumulada_percentual'] = acumulado/total*100
        # Renda é contextual: não é assumida como demanda/preço aceito.
        dominantes = [q['municipio'] for q in perfis if
            float(q['varejo_alimentar_2024']) >= float(p['varejo_alimentar_2024']) and
            q['distancia_cd_geodesica_km'] <= p['distancia_cd_geodesica_km'] and
            (float(q['varejo_alimentar_2024']) > float(p['varejo_alimentar_2024']) or
             q['distancia_cd_geodesica_km'] < p['distancia_cd_geodesica_km'])]
        p['fronteira_escala_proximidade'] = not dominantes
        p['cidades_dominantes_nesses_dois_criterios'] = '; '.join(sorted(dominantes))
    perfis.sort(key=lambda p: (-float(p['varejo_alimentar_2024']), p['codigo_ibge']))
    nomes = {k:v['municipio'] for k,v in pontos.items()}
    index = {p['codigo_ibge']:p for p in perfis}
    rotas, trechos = [], []
    def registrar(rid, caminho, metodo, grupo):
        cidades = caminho[1:-1]
        if len(cidades) != len(set(cidades)):
            raise ValueError('Cidade repetida no circuito')
        km = sum(dist[a,b] for a,b in zip(caminho,caminho[1:]))
        r = {'circuito_id':rid,'metodo':metodo,'grupo':grupo,'origem':'Ribeirão Preto',
             'retorno_origem':True,'numero_cidades':len(cidades),
             'unidades_varejo_2024':sum(float(index[c]['varejo_alimentar_2024']) for c in cidades),
             'distancia_geodesica_total_km':km,'sequencia':' -> '.join(nomes[c] for c in caminho),
             'tipo_distancia':'GEODESICA_CENTROIDES','viabilidade_diaria_confirmada':False}
        rotas.append(r)
        for ordem,(a,b) in enumerate(zip(caminho,caminho[1:]),1):
            trechos.append({'circuito_id':rid,'ordem':ordem,'origem_codigo':a,'destino_codigo':b,
                           'origem':nomes[a],'destino':nomes[b],'distancia_geodesica_km':dist[a,b]})
    lista = sorted(CODIGOS, key=lambda c:(dist[origem,c],c))
    registrar('TODAS_PROXIMAS_PRIMEIRO',[origem,*lista,origem],'ORDEM_DISTANCIA_CD','TODAS')
    registrar('TODAS_DISTANTES_PRIMEIRO',[origem,*reversed(lista),origem],'ORDEM_INVERSA','TODAS')
    caminho,_ = otimizar(CODIGOS,origem,dist)
    registrar('TODAS_MENOR_CICLO',caminho,'HELD_KARP_EXATO_GEODESICO','TODAS')
    # Duas âncoras de maior escala observada; alocação por proximidade é exploratória.
    ancoras = ['3516200','3505500']
    grupos = {a:[] for a in ancoras}
    for c in sorted(CODIGOS):
        a = min(ancoras,key=lambda x:(dist[c,x],x))
        grupos[a].append(c)
    assert set(grupos[ancoras[0]]) | set(grupos[ancoras[1]]) == CODIGOS
    assert not set(grupos[ancoras[0]]) & set(grupos[ancoras[1]])
    desvios = []
    for a, cidades in grupos.items():
        caminho,_ = otimizar(cidades,origem,dist)
        registrar('ANCORA_'+a,caminho,'HELD_KARP_SUBCONJUNTO','PROXIMIDADE_'+nomes[a])
        for c in cidades:
            adicional = max(0,dist[origem,c]+dist[c,a]-dist[origem,a])
            desvios.append({'ancora':nomes[a],'municipio':nomes[c],
                'codigo_ibge':c,'unidades_varejo_2024':float(index[c]['varejo_alimentar_2024']),
                'desvio_geodesico_percurso_cd_ancora_km':adicional,
                'criterio':'Inserção isolada no trajeto CD-âncora; desvios não são somáveis'})
    return perfis,rotas,trechos,desvios


def custos(rotas, parametros):
    resultados = []
    for r in rotas:
        entrada = parametros.get('circuitos',{}).get(r['circuito_id'],{})
        campos = ('distancia_rodoviaria_total_km','consumo_km_l','preco_combustivel_brl_l',
                  'desgaste_brl_km','pedagios_total_brl')
        pendentes = [c for c in campos if entrada.get(c) is None]
        if pendentes:
            resultados.append({'circuito_id':r['circuito_id'],'status':'PENDENTE_PARAMETROS',
                               'pendencias':'; '.join(pendentes),'custo_adicional_brl':None,
                               'margem_disponivel':None,'faturamento_equilibrio_brl':None})
            continue
        v = {c:float(entrada[c]) for c in campos}
        if not all(math.isfinite(x) for x in v.values()) or any(v[c]<0 for c in campos):
            raise ValueError('Parâmetros de custo inválidos')
        if min(v[c] for c in campos[:3]) <= 0:
            raise ValueError('Distância, consumo e preço devem ser positivos')
        if not entrada.get('fonte_distancia') or not entrada.get('fonte_combustivel') or not entrada.get('fonte_pedagios'):
            raise ValueError('Registrar fontes dos parâmetros preenchidos')
        custo = v[campos[0]]*(v[campos[2]]/v[campos[1]]+v[campos[3]])+v[campos[4]]
        margens = entrada.get('margens_disponiveis',[])
        for margem in margens or [None]:
            if margem is not None and (not math.isfinite(float(margem)) or not 0<float(margem)<=1):
                raise ValueError('Margem disponível deve estar em (0,1]')
            resultados.append({'circuito_id':r['circuito_id'], 'status':'CENARIO_ESTIMADO',
                'pendencias':None,'custo_adicional_brl':custo,'margem_disponivel':margem,
                'faturamento_equilibrio_brl':None if margem is None else custo/float(margem)})
    return resultados


def executar(raiz,run_id,servidor,driver='ODBC Driver 17 for SQL Server',confiar_certificado=False,parametros=None):
    import pyodbc
    import pyarrow as pa
    import pyarrow.parquet as pq
    for valor in (servidor,driver):
        if not valor or any(c in valor for c in ';{}\r\n'):
            raise ValueError('Servidor/driver inválido')
    if driver not in pyodbc.drivers():
        raise ValueError('Driver ODBC não instalado: '+driver)
    destino = Path(raiz)/'datalake'/'03_gold'/run_id/'prioridades_circuitos'
    quality = Path(raiz)/'quality'/'22_prioridades_circuitos'/run_id
    destino.mkdir(parents=True,exist_ok=False);quality.mkdir(parents=True,exist_ok=False)
    conclusao = {'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO'}
    try:
        conexao = (f'DRIVER={{{driver}}};SERVER={servidor};DATABASE={PROJETO};Trusted_Connection=yes;'
                   f'Encrypt=yes;TrustServerCertificate={"yes" if confiar_certificado else "no"};')
        def ler(cur,sql):
            cur.execute(sql)
            nomes = [c[0] for c in cur.description]
            return [dict(zip(nomes,linha)) for linha in cur.fetchall()]
        with pyodbc.connect(conexao,autocommit=True,timeout=15) as conn:
            cur = conn.cursor()
            carga = ler(cur,'SELECT * FROM gold.vw_carga_aprovada')
            if len(carga)!=1:raise ValueError('Exige uma carga aprovada')
            perfis = ler(cur,'SELECT * FROM gold.vw_perfil_comercial')
            pontos = ler(cur,"SELECT codigo_ibge,municipio,latitude_centroide,longitude_centroide,fonte_url,fonte_sha256 FROM gold.dim_municipio WHERE cidade_expansao=1 OR codigo_ibge='3543402'")
            carga_final = ler(cur,'SELECT * FROM gold.vw_carga_aprovada')
            if carga_final!=carga:raise ValueError('Carga ativa mudou durante a leitura; repetir')
            if {p['execucao_id'] for p in perfis}!={carga[0]['execucao_id']}:raise ValueError('Carga divergente no perfil')
        configs = json.loads(Path(parametros).read_text(encoding='utf-8-sig')) if parametros else {}
        if configs and configs.get('projeto') != PROJETO:
            raise ValueError('Projeto divergente nos parâmetros de custo')
        perfis,rotas,trechos,desvios = analisar(perfis,pontos)
        tabelas = {'perfis':perfis,'circuitos':rotas,'trechos':trechos,'desvios':desvios,
                   'cenarios_custo':custos(rotas,configs),'coordenadas_fontes':pontos}
        exportacoes = []
        for nome,rows in tabelas.items():
            js = destino/(nome+'.json');parq=destino/(nome+'.parquet')
            js.write_text(json.dumps(rows,ensure_ascii=False,indent=2,default=lambda v:float(v) if isinstance(v,Decimal) else v.isoformat()),encoding='utf-8')
            pq.write_table(pa.Table.from_pylist(rows),parq)
            if pq.read_table(parq).num_rows!=len(rows):raise ValueError('Contagem exportação divergente')
            for arquivo in (js,parq):
                exportacoes.append({'arquivo':arquivo.name,'linhas':len(rows),'sha256':hashlib.sha256(arquivo.read_bytes()).hexdigest()})
        meta = {'projeto':PROJETO,'carga_sql':carga,'parametros_utilizados':configs,'exportacoes':exportacoes,
                'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'parametros_arquivo_sha256':hashlib.sha256(Path(parametros).read_bytes()).hexdigest() if parametros else None,
                'tipo_distancia':'GEODESICA_CENTROIDES','hipotese_origem_retorno':'Ribeirão Preto',
                'fontes_parametros_pendentes':not bool(configs),'status':'DIAGNOSTICO_COM_CUSTOS_PENDENTES' if any(x['status']=='PENDENTE_PARAMETROS' for x in tabelas['cenarios_custo']) else 'DIAGNOSTICO_COM_CENARIOS_ESTIMADOS'}
        (destino/'manifesto.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        texto = ['# Prioridades e circuitos','', 'Escopo: varejo especializado CNAE 47.2, ano 2024. Renda de 2022 é contexto.',
                 'Distâncias por centroides. Ciclos fechados com retorno a Ribeirão Preto. Não são itinerários rodoviários nem agendas diárias validadas.',
                 '', '| Circuito | Cidades | Unidades varejo | km geodésicos |','|---|---:|---:|---:|']
        for r in rotas:texto.append(f"| {r['circuito_id']} | {r['numero_cidades']} | {r['unidades_varejo_2024']:.0f} | {r['distancia_geodesica_total_km']:.2f} |")
        texto += ['', 'O menor ciclo é exato somente para a matriz geodésica e as cidades selecionadas. Os dois grupos por âncora são uma alternativa exploratória, sem prova de partição ótima.',
                  'Custos exigem distância rodoviária, consumo, combustível, desgaste e pedágios explicitamente preenchidos. Ausências permanecem pendentes.',
                  'Faturamento de equilíbrio = custo adicional / margem disponível após os outros custos variáveis. Margem é cenário ou informação da empresa, nunca inferida do catálogo.',
                  'Não há previsão de vendas, clientes confirmados ou escore ponderado de potencial.']
        (destino/'RELATORIO.md').write_text('\n'.join(texto),encoding='utf-8')
        conclusao.update(status=meta['status'],saida=str(destino),execucao_id_sql=carga[0]['execucao_id'],total_cidades=12,total_circuitos=len(rotas),exportacoes=exportacoes)
        return conclusao
    except Exception as exc:
        conclusao.update(status='FALHA',erro=str(exc));raise
    finally:
        conclusao['fim_utc']=datetime.now(timezone.utc).isoformat()
        (quality/'conclusao_22.json').write_text(json.dumps(conclusao,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--servidor',required=True)
    p.add_argument('--driver',default='ODBC Driver 17 for SQL Server')
    p.add_argument('--confiar-certificado',action='store_true')
    p.add_argument('--parametros',type=Path)
    a=p.parse_args()
    r=executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.servidor,a.driver,a.confiar_certificado,a.parametros)
    print(json.dumps(r,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
