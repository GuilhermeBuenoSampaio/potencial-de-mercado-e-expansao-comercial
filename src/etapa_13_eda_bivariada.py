"""Relacoes exploratorias municipais com controle de periodo e sensibilidade."""
import argparse
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO, carregar, sha, gravar, canon
from etapa_11_eda_estrutura import selecionar

# Cada selecao identifica exatamente a variavel e a categoria; nao soma categorias.
ESPECIFICACOES=[('populacao_2022','4714','93',None,2022),('populacao_2024','6579','9324',None,2024),('renda_media_2022','10295','13431',None,2022),('renda_mediana_2022','10295','13534',None,2022),('urbanizacao_2022','9923','1000093','1',2022),('salario_2024','9509','10143',None,2024),('empregos_2024','9509','707',None,2024),('alimentacao_2024','9528','706','117549',2024),('varejo_alimentar_2024','9528','706','117443',2024),('pib_per_capita_2023','pesquisa_38','47001',None,2023)]
PARES=[('populacao_2024','alimentacao_2024','Dimensao populacional e estrutura de alimentacao'),('populacao_2024','varejo_alimentar_2024','Dimensao populacional e varejo alimentar'),('populacao_2024','empregos_2024','Populacao e ocupacao no local de trabalho'),('populacao_2022','renda_mediana_2022','Dimensao populacional e renda dos moradores'),('urbanizacao_2022','renda_mediana_2022','Urbanizacao e renda dos moradores'),('renda_media_2022','renda_mediana_2022','Coerencia e diferencas entre medidas de renda'),('salario_2024','alimentacao_por_10mil_2024','Salario no trabalho e concentracao de estabelecimentos'),('pib_per_capita_2023','renda_media_2022','Contraste de conceitos economicos em anos diferentes')]

def ranks(x):
    order=sorted(range(len(x)),key=lambda i:x[i]);r=[0.0]*len(x);i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        for k in range(i,j):r[order[k]]=(i+1+j)/2
        i=j
    return r

def pearson(x,y):
    if len(x)<3:return None
    mx=math.fsum(x)/len(x);my=math.fsum(y)/len(y);a=[v-mx for v in x];b=[v-my for v in y]
    den=math.sqrt(math.fsum(v*v for v in a)*math.fsum(v*v for v in b))
    return max(-1.,min(1.,math.fsum(i*j for i,j in zip(a,b))/den)) if den else None

def coef(rows):
    x=[r['x'] for r in rows];y=[r['y'] for r in rows]
    return pearson(x,y),pearson(ranks(x),ranks(y))

def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve();q=raiz/'quality/13_eda_bivariada'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome,cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond:raise ValueError(nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz);m=json.loads((p/'manifesto_base_eda.json').read_text(encoding='utf-8'));mh=sha(p/'manifesto_base_eda.json')
        regra('Projeto e status base',m['projeto']==PROJETO and m['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        anteriores=[]
        for f in sorted((raiz/'quality/12_eda_univariada').glob('*/conclusao_12_eda_univariada.json'),reverse=True):
            a=json.loads(f.read_text(encoding='utf-8'))
            if a.get('status')=='EDA_UNIVARIADA_CONCLUIDA_COM_LIMITACOES' and a.get('entrada',{}).get('manifesto_sha256')==mh:anteriores.append(f);break
        regra('Univariada concluida sobre mesma base',bool(anteriores))
        entrada=next(x for x in m['entradas'] if x['tipo']=='municipal');pm=raiz/'datalake/02_silver'/entrada['run_id']/'municipal'
        regra('Manifesto Silver da linhagem',sha(pm/'manifesto_silver.json')==entrada['manifesto_sha256'])
        sm,mt=carregar(pm,'municipal')
        dic=mt['dicionario_indicadores'][0];serie=mt['indicadores_serie'][0];cidades=[r for r in mt['municipios'][0] if r['cidade_expansao']]
        regra('12 cidades de expansao',len(cidades)==12 and len({r['codigo_ibge'] for r in cidades})==12)
        dados=[];mapa={};specs=[]
        for alias,tabela,var,cat,ano in ESPECIFICACOES:
            possiveis=[]
            for d in dic:
                categorias=json.loads(d['classificacoes_json']);cats=[str(k) for c in categorias for k in c['categoria']]
                if d['tabela']==tabela and d['variavel_id']==var and (cat is None or cat in cats):possiveis.append(d)
            regra('Selecao unica '+alias,len(possiveis)==1);d=possiveis[0];ident=d['indicador_id']
            linhas=[r for r in serie if r['indicador_id']==ident and r['ano_referencia']==ano]
            regra('Sem duplicacao '+alias,len({r['codigo_ibge'] for r in linhas})==len(linhas));refs={r['codigo_ibge']:r for r in linhas}
            specs.append({'alias':alias,'indicador_id':ident,'nome_oficial':d['nome_oficial'],'classificacoes_json':d['classificacoes_json'],'ano_referencia':ano,'unidade':d['unidade_silver'],'formula':None})
            for c in cidades:
                r=refs.get(c['codigo_ibge']);v=None if r is None else r['valor']
                regra('Valor finito '+alias+' '+c['codigo_ibge'],v is None or math.isfinite(v))
                row={'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'uf':c['uf'],'alias':alias,'ano_referencia':ano,'valor':v,'unidade':d['unidade_silver'],'status_valor':'SEM_REGISTRO_NO_ANO' if r is None else r['status_valor'],'fonte_url':None if r is None else r['fonte_url'],'fontes_sha256_json':json.dumps([] if r is None else [r['fonte_sha256']]),'formula':None}
                dados.append(row);mapa[(c['codigo_ibge'],alias)]=row
        for origem,alias in [('alimentacao_2024','alimentacao_por_10mil_2024'),('varejo_alimentar_2024','varejo_alimentar_por_10mil_2024')]:
            specs.append({'alias':alias,'indicador_id':None,'nome_oficial':origem+' por 10 mil habitantes','classificacoes_json':'[]','ano_referencia':2024,'unidade':'Unidades por 10 mil habitantes','formula':'unidades_2024 / populacao_estimada_2024 * 10000'})
            for c in cidades:
                num=mapa[(c['codigo_ibge'],origem)];den=mapa[(c['codigo_ibge'],'populacao_2024')]
                valor=num['valor']/den['valor']*10000 if num['valor'] is not None and den['valor'] is not None and den['valor']>0 else None
                row={**num,'alias':alias,'valor':valor,'unidade':'Unidades por 10 mil habitantes','status_valor':'CALCULADO' if valor is not None else 'COMPONENTE_AUSENTE_OU_DENOMINADOR_INVALIDO','fonte_url':json.dumps([num['fonte_url'],den['fonte_url']],ensure_ascii=False),'fontes_sha256_json':json.dumps(sorted(set(json.loads(num['fontes_sha256_json'])+json.loads(den['fontes_sha256_json'])))),'formula':'unidades_2024 / populacao_estimada_2024 * 10000'}
                dados.append(row);mapa[(c['codigo_ibge'],alias)]=row
        resultados=[];pontos=[];sensibilidade=[];secoes=[]
        for x,y,pergunta in PARES:
            pair=x+'__'+y;rows=[];ausentes=[]
            for c in cidades:
                a=mapa[(c['codigo_ibge'],x)];b=mapa[(c['codigo_ibge'],y)]
                if a['valor'] is None or b['valor'] is None:ausentes.append(c['municipio']);continue
                rows.append({'par_id':pair,'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'x':a['valor'],'y':b['valor'],'ano_x':a['ano_referencia'],'ano_y':b['ano_referencia'],'fontes_x_json':a['fontes_sha256_json'],'fontes_y_json':b['fontes_sha256_json']})
            pr,sr=coef(rows);pontos.extend(rows);mesmo=next(s['ano_referencia'] for s in specs if s['alias']==x)==next(s['ano_referencia'] for s in specs if s['alias']==y)
            base_r={'par_id':pair,'x_alias':x,'y_alias':y,'pergunta':pergunta,'pares_validos':len(rows),'cidades_ausentes_json':json.dumps(ausentes,ensure_ascii=False),'mesmo_ano':mesmo,'uso':'ASSOCIACAO_DESCRITIVA' if mesmo else 'CONTEXTO_NAO_CONTEMPORANEO','pearson':pr,'spearman':sr}
            alternativas=[]
            cenarios=[('SEM_UMA_CIDADE',[r['municipio']]) for r in rows]+[('SEM_FRANCA_BARRETOS',['Franca','Barretos'])]
            for tipo,excluir in cenarios:
                sub=[r for r in rows if r['municipio'] not in excluir];pc,sc=coef(sub)
                novo={'par_id':pair,'cenario':tipo,'excluidas_json':json.dumps(excluir,ensure_ascii=False),'pares_validos':len(sub),'pearson':pc,'spearman':sc,'delta_pearson':None if pc is None or pr is None else pc-pr,'delta_spearman':None if sc is None or sr is None else sc-sr};alternativas.append(novo);sensibilidade.append(novo)
            loo=[r for r in alternativas if r['cenario']=='SEM_UMA_CIDADE'];base_r['maior_variacao_absoluta_pearson_loo']=max([abs(r['delta_pearson']) for r in loo if r['delta_pearson'] is not None],default=None);base_r['maior_variacao_absoluta_spearman_loo']=max([abs(r['delta_spearman']) for r in loo if r['delta_spearman'] is not None],default=None);resultados.append(base_r)
            regra('Coeficientes no intervalo '+pair,all(v is None or -1<=v<=1 for r in [base_r]+alternativas for v in [r['pearson'],r['spearman']]))
            ax=next(s for s in specs if s['alias']==x);ay=next(s for s in specs if s['alias']==y)
            svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 460" role="img" aria-label="Dispersao municipal">'
            if rows:
                lx=min(0,min(r['x'] for r in rows));hx=max(r['x'] for r in rows);ly=min(0,min(r['y'] for r in rows));hy=max(r['y'] for r in rows)
                svg+='<path d="M80 25V390H780" fill="none" stroke="#798ca0"/>'
                for r in rows:
                    px=80+650*(r['x']-lx)/(hx-lx or 1);py=390-340*(r['y']-ly)/(hy-ly or 1)
                    svg+=f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="#176b9a"><title>{html.escape(r["municipio"])}: {r["x"]}, {r["y"]}</title></circle><text x="{px+7:.2f}" y="{py-7:.2f}">{html.escape(r["municipio"])}</text>'
                svg+=f'<text x="80" y="415">X: {lx:.4g} a {hx:.4g} | {html.escape(x)}</text><text x="80" y="440">Y: {ly:.4g} a {hy:.4g} | {html.escape(y)}</text>'
            svg+='</svg>'
            tabela='<table><tr><th>Cidade</th><th>X</th><th>Y</th></tr>'+''.join('<tr><td>'+html.escape(r['municipio'])+'</td><td>'+str(r['x'])+'</td><td>'+str(r['y'])+'</td></tr>' for r in rows)+'</table>'
            secoes.append('<section><h2>'+html.escape(pergunta)+'</h2><p>X: '+html.escape(ax['nome_oficial'])+' — '+str(ax['ano_referencia'])+' — '+html.escape(ax['unidade'])+'</p><p>Y: '+html.escape(ay['nome_oficial'])+' — '+str(ay['ano_referencia'])+' — '+html.escape(ay['unidade'])+'</p><p>'+base_r['uso']+' | Pares: '+str(len(rows))+' | Pearson: '+str(pr)+' | Spearman: '+str(sr)+'</p>'+svg+tabela+'<p>Ausências: '+html.escape(', '.join(ausentes) or 'Nenhuma')+'</p><p>Maior variação absoluta ao retirar uma cidade — Pearson: '+str(base_r['maior_variacao_absoluta_pearson_loo'])+'; Spearman: '+str(base_r['maior_variacao_absoluta_spearman_loo'])+'</p></section>')
        saida=raiz/'datalake/03_gold'/run_id/'eda_bivariada';saida.mkdir(parents=True,exist_ok=False);exports=[]
        for nome,rows in [('catalogo_variaveis',specs),('indicadores_alinhados',dados),('correlacoes_exploratorias',resultados),('pontos_relacoes',pontos),('sensibilidade_correlacoes',sensibilidade)]:
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rows)
            # Tipos numericos de colunas potencialmente vazias continuam explicitos.
            floats={'valor','x','y','pearson','spearman','delta_pearson','delta_spearman','maior_variacao_absoluta_pearson_loo','maior_variacao_absoluta_spearman_loo'}
            schema=pa.schema([(k,pa.float64() if k in floats else pa.bool_() if isinstance(v,bool) else pa.int64() if isinstance(v,int) else pa.string()) for k,v in rows[0].items()])
            pq.write_table(pa.Table.from_pylist(rows,schema=schema),a,compression='snappy');regra('Exportacao '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()));exports.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        limites=['Associacao entre 12 municipios selecionados nao prova causalidade nem comportamento individual dos moradores.','Oito pares definidos por perguntas, sem matriz indiscriminada, testes ou p-valores.','Sete pares usam anos iguais; PIB per capita 2023 versus renda 2022 e apenas contraste nao contemporaneo.','Razoes por habitante sao concentracoes cadastrais, nao demanda, concorrencia efetiva ou saturacao.','Salario no local de trabalho nao equivale a renda domiciliar; correlacao entre renda media e mediana nao e evidência independente.','Faixas de renda com conferencia pendente nao entram nos pares; medidas media e mediana possuem definicoes distintas.','Sensibilidade retira observacoes apenas para diagnostico; nenhum municipio foi removido das bases oficiais.','Periodos da populacao 2024 e dos estabelecimentos 2024 estao alinhados; fonte e formula de cada razao ficam registradas.','Comparacao com analise original somente no encerramento.']
        doc='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA bivariada</title><style>body{font:15px Arial;margin:32px;color:#183248}section{border-top:1px solid #ccd5dd;padding:20px 0}svg{width:100%;max-width:1000px}svg text{font:12px Arial}table{border-collapse:collapse}td,th{border:1px solid #cad5df;padding:6px}</style><h1>EDA bivariada municipal</h1><p>'+PROJETO+' | Execução: '+run_id+'</p><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in limites)+'</ul>'+''.join(secoes)+'</html>'
        (saida/'relatorio_bivariado.html').write_text(doc,encoding='utf-8')
        rel.update(status='EDA_BIVARIADA_CONCLUIDA_COM_LIMITACOES',entrada={'base_run_id':m['run_id'],'manifesto_base_sha256':mh,'silver_run_id':sm['run_id'],'conclusao_univariada_sha256':sha(anteriores[0])},saida=str(saida),exportacoes=exports,resumo={'cidades':12,'variaveis':len(specs),'pares_explorados':len(resultados),'pares_mesmo_ano':sum(r['mesmo_ano'] for r in resultados),'pares_anos_diferentes':sum(not r['mesmo_ano'] for r in resultados),'pontos_validos':len(pontos),'cenarios_sensibilidade':len(sensibilidade)},metodos={'pearson':'Covariacao normalizada; null se n<3 ou variavel constante','spearman':'Pearson dos postos medios para empates; null se n<3 ou postos constantes','sensibilidade':'Retirada de uma cidade por vez e de Franca+Barretos; sem exclusao da base','populacao_denominador':'Estimativa 2024; sem substituicao por 2026'},limites=limites,fim_utc=datetime.now(timezone.utc).isoformat());gravar(saida/'manifesto_eda_bivariada.json',rel);return rel
    except Exception as e:rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_13_eda_bivariada.json',rel);(q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path);a=ap.parse_args();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8];print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
