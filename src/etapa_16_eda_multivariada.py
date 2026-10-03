"""Perfis municipais integrados e associacoes com uma variavel de controle."""
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
from etapa_10_base_eda import PROJETO, sha, gravar, canon
from etapa_11_eda_estrutura import selecionar
from etapa_12_eda_univariada import quantil
from etapa_13_eda_bivariada import pearson, ranks

DIMENSOES=['populacao_2024','renda_mediana_2022','urbanizacao_2022','alimentacao_2024','alimentacao_por_10mil_2024','varejo_alimentar_por_10mil_2024','distancia_cd_centroides_km']
TRIPLAS=[('populacao_2024','alimentacao_2024','empregos_2024'),('populacao_2024','varejo_alimentar_2024','empregos_2024'),('urbanizacao_2022','renda_mediana_2022','populacao_2022')]


def residual(y,z):
    """Retira somente a componente linear associada a um controle, com intercepto."""
    if len(y)<4 or len(y)!=len(z):return None
    mz=statistics.fmean(z);my=statistics.fmean(y)
    den=math.fsum((v-mz)**2 for v in z)
    if den==0:return None
    beta=math.fsum((a-my)*(b-mz) for a,b in zip(y,z))/den
    r=[a-my-beta*(b-mz) for a,b in zip(y,z)]
    # Residuo quase nulo significa ajuste praticamente perfeito: coeficiente indefinido.
    total=math.fsum((a-my)**2 for a in y)
    if total==0 or math.fsum(a*a for a in r)<=total*1e-12:return None
    return r


def parcial(rows,x,y,z):
    rs=[r for r in rows if all(r.get(k) is not None for k in [x,y,z])]
    a=[r[x] for r in rs];b=[r[y] for r in rs];c=[r[z] for r in rs]
    ra=residual(a,c);rb=residual(b,c)
    return len(rs),pearson(a,b),None if ra is None or rb is None else pearson(ra,rb)


def carregar_eda(raiz, etapa, arquivo, status, hash_base):
    for f in sorted((raiz/'quality'/etapa).glob('*/'+arquivo),reverse=True):
        r=json.loads(f.read_text(encoding='utf-8'))
        if r.get('status')==status and r.get('entrada',{}).get('manifesto_base_sha256')==hash_base:
            sub='eda_geografica' if etapa.startswith('15') else 'eda_bivariada'
            return f,r,raiz/'datalake/03_gold'/r['run_id']/sub
    raise ValueError('Nenhuma conclusao correspondente: '+etapa)


def tabela(rows,cols):
    return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in cols)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in cols)+'</tr>' for r in rows)+'</table>'


def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve();q=raiz/'quality/16_eda_multivariada'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome,cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond:raise ValueError(nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz);man=p/'manifesto_base_eda.json';m=json.loads(man.read_text(encoding='utf-8'));mh=sha(man)
        regra('Projeto e status base',m['projeto']==PROJETO and m['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        fg,g,pg=carregar_eda(raiz,'15_eda_geografica','conclusao_15_eda_geografica.json','EDA_GEOGRAFICA_CONCLUIDA_COM_LIMITACOES',mh)
        fb,b,pb=carregar_eda(raiz,'13_eda_bivariada','conclusao_13_eda_bivariada.json','EDA_BIVARIADA_CONCLUIDA_COM_LIMITACOES',mh)
        regra('Mesma Silver nas entradas',g['entrada']['silver_run_id']==b['entrada']['silver_run_id'])
        entradas={}
        for prefix,prev,pasta,arquivo in [('geo',g,pg,'manifesto_eda_geografica.json'),('biv',b,pb,'manifesto_eda_bivariada.json')]:
            mm=json.loads((pasta/arquivo).read_text(encoding='utf-8'))
            regra('Manifesto '+prefix,mm['run_id']==prev['run_id'] and mm['status']==prev['status'] and mm['entrada']==prev['entrada'] and mm['exportacoes']==prev['exportacoes'])
            for e in prev['exportacoes']:
                n=e['tabela'];regra('Nome de tabela '+prefix+' '+n,Path(n).name==n)
                j=pasta/(n+'.json');a=pasta/(n+'.parquet');regra('Hashes '+prefix+' '+n,sha(j)==e['sha256_json'] and sha(a)==e['sha256_parquet'])
                rows=json.loads(j.read_text(encoding='utf-8'));rr=canon(pq.read_table(a).to_pylist())
                regra('Linhas e conteudo '+prefix+' '+n,len(rows)==e['linhas'] and rows==rr);entradas[prefix+'_'+n]=rows
        dados=entradas['biv_indicadores_alinhados'];cat=entradas['biv_catalogo_variaveis'];geo=entradas['geo_proximidade_por_cidade']
        ids={r['codigo_ibge'] for r in geo};regra('12 cidades geograficas unicas',len(geo)==len(ids)==12)
        regra('Chaves bivariadas unicas',len({(r['codigo_ibge'],r['alias']) for r in dados})==len(dados))
        regra('Mesmas cidades nas entradas',ids=={r['codigo_ibge'] for r in dados})
        refs={(r['codigo_ibge'],r['alias']):r for r in dados};aux=['populacao_2022','empregos_2024','varejo_alimentar_2024'];aliases=DIMENSOES[:-1]+aux
        catalogo=[]
        for alias in DIMENSOES[:-1]:
            rs=[r for r in cat if r['alias']==alias];regra('Catalogo unico '+alias,len(rs)==1)
            catalogo.append({**rs[0],'transformacao_visual':'log1p' if alias in ['populacao_2024','alimentacao_2024'] else 'identidade','interpreta_z_positivo':'Acima da mediana transformada; nao significa melhor'})
        catalogo.append({'alias':'distancia_cd_centroides_km','indicador_id':None,'nome_oficial':'Distancia entre centroide municipal e centroide do CD mais proximo','classificacoes_json':'[]','ano_referencia':None,'unidade':'km','formula':'Haversine; raio medio 6371.0088 km','transformacao_visual':'identidade','interpreta_z_positivo':'Mais distante que a mediana; nao classifica desempenho comercial'})
        painel=[];linhagem=[]
        for c in sorted(geo,key=lambda r:r['codigo_ibge']):
            row={'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'uf':c['uf'],'cd_mais_proximo':c['cd_mais_proximo'],'distancia_cd_centroides_km':c['distancia_cd_centroides_km']}
            for alias in aliases:
                regra('Registro existente '+alias+' '+c['codigo_ibge'],(c['codigo_ibge'],alias) in refs)
                rr=refs[c['codigo_ibge'],alias];row[alias]=rr['valor']
                regra('Periodo '+alias+' '+c['codigo_ibge'],rr['ano_referencia']==int(alias[-4:]))
                linhagem.append({k:rr[k] for k in ['codigo_ibge','municipio','alias','ano_referencia','unidade','fonte_url','fontes_sha256_json','formula']})
            painel.append(row)
        regra('Nenhum PIB no painel',not any('pib' in k.lower() for k in painel[0]))
        parametros=[];perfis=[]
        for alias in DIMENSOES:
            transform=math.log1p if alias in ['populacao_2024','alimentacao_2024'] else lambda v:v
            vals=[transform(r[alias]) for r in painel if r[alias] is not None];med=statistics.median(vals) if vals else None;q1=quantil(vals,.25) if vals else None;q3=quantil(vals,.75) if vals else None;iqr=None if not vals else q3-q1
            parametros.append({'alias':alias,'n':len(vals),'transformacao':'log1p' if alias in ['populacao_2024','alimentacao_2024'] else 'identidade','mediana_transformada':med,'q1_transformado':q1,'q3_transformado':q3,'iqr_transformado':iqr})
            for r in painel:
                v=r[alias];t=None if v is None else transform(v);z=None if t is None or not iqr else (t-med)/iqr
                perfis.append({'codigo_ibge':r['codigo_ibge'],'municipio':r['municipio'],'alias':alias,'valor_original':v,'valor_transformado':t,'posicao_robusta':z,'status':'VALOR_AUSENTE' if v is None else 'IQR_ZERO' if not iqr else 'CALCULADO','uso':'Perfil por variavel; nao somar para criar escore'})
                if z is not None:regra('Reversao perfil '+alias+' '+r['codigo_ibge'],math.isclose(z*iqr+med,t,rel_tol=1e-12,abs_tol=1e-10))
        correls=[]
        for x,y in combinations(DIMENSOES,2):
            rs=[r for r in painel if r[x] is not None and r[y] is not None];a=[r[x] for r in rs];bb=[r[y] for r in rs]
            anos=[x[-4:] if x[-4:].isdigit() else 'SEM_ANO_DADO_ESTATICO',y[-4:] if y[-4:].isdigit() else 'SEM_ANO_DADO_ESTATICO']
            correls.append({'x':x,'y':y,'n':len(rs),'pearson_valores_originais':pearson(a,bb),'spearman_valores_originais':pearson(ranks(a),ranks(bb)),'periodos_json':json.dumps(anos),'dependencia_formula':'Populacao aparece no denominador das taxas; contagem e taxa compartilham numerador' if any('por_10mil' in k for k in [x,y]) else 'NAO_DERIVADA_POR_FORMULA_COMUM_REGISTRADA','uso':'Associacao exploratoria; periodos distintos quando indicados; nao causal'})
        parciais=[];sensibilidade=[]
        for x,y,z in TRIPLAS:
            n,bruta,ajustada=parcial(painel,x,y,z);regra('Periodos iguais na tripla '+x+' '+y+' '+z,x[-4:]==y[-4:]==z[-4:])
            completas=[r for r in painel if all(r[k] is not None for k in [x,y,z])]
            rxz=pearson([r[x] for r in completas],[r[z] for r in completas]);ryz=pearson([r[y] for r in completas],[r[z] for r in completas])
            parciais.append({'x':x,'y':y,'controle':z,'ano':int(x[-4:]),'n':n,'pearson_bruto':bruta,'pearson_parcial':ajustada,'pearson_x_controle':rxz,'pearson_y_controle':ryz,'fracao_variancia_x_residual':None if rxz is None else max(0.,1-rxz**2),'fracao_variancia_y_residual':None if ryz is None else max(0.,1-ryz**2),'status':'CALCULADO' if ajustada is not None else 'INDEFINIDO','uso':'Associacao linear entre residuos; nao representa efeito causal'})
            for r in painel:
                nn,rb,rp=parcial([a for a in painel if a['codigo_ibge']!=r['codigo_ibge']],x,y,z)
                sensibilidade.append({'x':x,'y':y,'controle':z,'codigo_excluido':r['codigo_ibge'],'cidade_excluida':r['municipio'],'n':nn,'pearson_bruto':rb,'pearson_parcial':rp,'delta_parcial':None if rp is None or ajustada is None else rp-ajustada})
        regra('Dimensoes e perfis',len(catalogo)==7 and len(perfis)==84)
        regra('21 pares e 3 triplas',len(correls)==21 and len(parciais)==3 and len(sensibilidade)==36)
        saida=raiz/'datalake/03_gold'/run_id/'eda_multivariada';saida.mkdir(parents=True,exist_ok=False);exports=[]
        numericos=set(DIMENSOES+aux+['mediana_transformada','q1_transformado','q3_transformado','iqr_transformado','valor_original','valor_transformado','posicao_robusta','pearson_valores_originais','spearman_valores_originais','pearson_bruto','pearson_parcial','delta_parcial','pearson_x_controle','pearson_y_controle','fracao_variancia_x_residual','fracao_variancia_y_residual'])
        for nome,rows in [('catalogo_perfis',catalogo),('painel_integrado',painel),('linhagem_indicadores',linhagem),('parametros_perfis',parametros),('perfis_padronizados',perfis),('associacoes_dimensoes',correls),('associacoes_parciais',parciais),('sensibilidade_parcial',sensibilidade)]:
            campos=[]
            for k,v in rows[0].items():
                tipo=pa.float64() if k in numericos else pa.int64() if k in ['ano_referencia','ano','n'] or isinstance(v,int) else pa.string();campos.append(pa.field(k,tipo))
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rows);pq.write_table(pa.Table.from_pylist(rows,schema=pa.schema(campos)),a,compression='snappy')
            regra('JSON Parquet '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()));exports.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        limites=['12 cidades selecionadas; resultados exploratorios sem generalizacao, p-valores ou causalidade.','Renda e urbanizacao: 2022. Populacao, unidades comerciais e ocupacao: 2024. Distancias entre centroides sem ano estatistico definido.','Log1p aplicado apenas a populacao e unidades de alimentacao para visualizar perfis; correlacoes usam valores originais.','Posicao robusta = (valor transformado - mediana) / IQR; sinais nao significam bom ou ruim.','Nenhum escore, pesos comerciais, ranking, PCA ou cluster foi criado.','Taxas por 10 mil compartilham denominador populacional; correlacoes podem refletir acoplamento matematico.','Correlacao parcial ajusta um controle linear; nao remove confundimento nao observado nem garante comparabilidade entre cidades.','Pessoal ocupado total nao e taxa de emprego dos residentes; pode incluir empregados do proprio setor de alimentacao.','Distancia geografica nao representa frete, tempo ou atendimento operacional.','PIB e composicao setorial pendentes excluidos do bloco para todas as cidades; renda domiciliar permanece com conceito proprio.','Unidades CNAE nao comprovam demanda, concorrencia ou clientes potenciais interessados.','Comparacao com analise original somente no encerramento.']
        # Heatmap por dimensao: cores simetricas em torno da mediana, sem somar sinais.
        by={(r['codigo_ibge'],r['alias']):r for r in perfis};body='<h1>EDA multivariada: perfis municipais</h1><p>'+PROJETO+' | '+run_id+'</p><ul>'+''.join('<li>'+html.escape(v)+'</li>' for v in limites)+'</ul><h2>Perfis robustos por dimensão</h2><p>Azul: acima da mediana transformada. Laranja: abaixo. Cor limitada visualmente a ±2 IQR; valores integrais preservados. Acima não significa melhor.</p><table><tr><th>Cidade</th>'+''.join('<th>'+html.escape(v)+'</th>' for v in DIMENSOES)+'</tr>'
        for r in painel:
            body+='<tr><th>'+html.escape(r['municipio'])+'</th>'
            for alias in DIMENSOES:
                z=by[r['codigo_ibge'],alias]['posicao_robusta'];t=0 if z is None else min(1,abs(z)/2);rgb=(int(255-180*t),int(255-130*t),255) if z is not None and z>=0 else (255,int(255-125*t),int(255-180*t))
                body+='<td style="background:rgb'+str(rgb)+'">'+('AUSENTE/INDEFINIDO' if z is None else f'{z:.3f}')+'</td>'
            body+='</tr>'
        body+='</table><h2>Valores originais e períodos</h2>'+tabela(painel,['municipio']+DIMENSOES)
        body+='<h2>Associações com um controle</h2>'+tabela(parciais,['x','y','controle','ano','n','pearson_bruto','pearson_parcial','fracao_variancia_x_residual','fracao_variancia_y_residual','status'])
        body+='<h2>Sensibilidade: retirada de uma cidade</h2>'+tabela(sensibilidade,['x','y','controle','cidade_excluida','pearson_parcial','delta_parcial'])
        body+='<h2>Associações entre dimensões — triagem de redundância</h2>'+tabela(correls,['x','y','n','pearson_valores_originais','spearman_valores_originais','dependencia_formula'])
        doc='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA multivariada</title><style>body{font:15px Arial;margin:30px;color:#183248}table{border-collapse:collapse;display:block;overflow:auto}td,th{border:1px solid #ccd5dd;padding:7px}th{font-size:12px}h2{margin-top:30px}</style>'+body+'</html>'
        (saida/'relatorio_multivariado.html').write_text(doc,encoding='utf-8')
        rel.update(status='EDA_MULTIVARIADA_CONCLUIDA_COM_LIMITACOES',entrada={'base_run_id':m['run_id'],'manifesto_base_sha256':mh,'silver_run_id':g['entrada']['silver_run_id'],'conclusao_geografica_sha256':sha(fg),'conclusao_bivariada_sha256':sha(fb)},saida=str(saida),exportacoes=exports,resumo={'cidades':12,'dimensoes':7,'perfis':84,'associacoes_pares':21,'triplas_controle':3,'sensibilidade_exclusoes':36,'valores_ausentes_perfis':sum(r['valor_original'] is None for r in perfis)},metodos={'perfil':'(transformacao(valor)-mediana)/IQR; quantis lineares tipo 7; null se IQR zero','parcial':'Pearson dos residuos de dois ajustes lineares separados no mesmo controle com intercepto','sensibilidade':'Uma cidade retirada por vez; sem criterio automatico de estabilidade'},limites=limites)
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(saida/'manifesto_eda_multivariada.json',rel);return rel
    except Exception as e:rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_16_eda_multivariada.json',rel);(q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path);a=ap.parse_args();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8];print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
