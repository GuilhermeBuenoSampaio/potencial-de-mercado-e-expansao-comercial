"""EDA univariada municipal: descricao do conjunto de cidades, sem inferencia."""
import argparse
import html
import json
import math
import statistics as st
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO, sha, gravar, canon
from etapa_11_eda_estrutura import selecionar

def quantil(valores,p):
    x=sorted(valores); h=(len(x)-1)*p; i=math.floor(h)
    return x[i] if i==len(x)-1 else x[i]+(h-i)*(x[i+1]-x[i])

def descrever(x):
    if not x:return dict.fromkeys(['minimo','maximo','amplitude','media','mediana','q1','q3','iqr','variancia_descritiva','desvio_padrao_descritivo','assimetria_momento','curtose_excesso_momento','limite_inferior_iqr','limite_superior_iqr'])
    media=st.fmean(x);q1=quantil(x,.25);q3=quantil(x,.75);iqr=q3-q1
    m2=st.fmean((v-media)**2 for v in x)
    return {'minimo':min(x),'maximo':max(x),'amplitude':max(x)-min(x),'media':media,'mediana':st.median(x),'q1':q1,'q3':q3,'iqr':iqr,'variancia_descritiva':m2,'desvio_padrao_descritivo':math.sqrt(m2),'assimetria_momento':st.fmean((v-media)**3 for v in x)/m2**1.5 if m2>0 and len(x)>=3 else None,'curtose_excesso_momento':st.fmean((v-media)**4 for v in x)/m2**2-3 if m2>0 and len(x)>=4 else None,'limite_inferior_iqr':q1-1.5*iqr,'limite_superior_iqr':q3+1.5*iqr}

def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve(); q=raiz/'quality/12_eda_univariada'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome,cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond:raise ValueError(nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz)
        m=json.loads((p/'manifesto_base_eda.json').read_text(encoding='utf-8'))
        regra('Projeto e status da base',m['projeto']==PROJETO and m['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        # Exige o primeiro bloco concluido sobre a mesma base, evitando misturar versoes.
        anteriores=[]
        for f in sorted((raiz/'quality/11_eda_estrutura').glob('*/conclusao_11_eda_estrutura.json'),reverse=True):
            r=json.loads(f.read_text(encoding='utf-8'))
            if r.get('status')=='EDA_ESTRUTURA_CONCLUIDA_COM_LIMITACOES' and r.get('entrada',{}).get('manifesto_sha256')==sha(p/'manifesto_base_eda.json'):
                anteriores.append(f);break
        regra('Bloco estrutura aprovado para a mesma base',bool(anteriores))
        tabelas={}
        for e in m['exportacoes']:
            nome=e['tabela'];regra('Nome seguro '+nome,Path(nome).name==nome and nome not in tabelas)
            j=p/(nome+'.json');a=p/(nome+'.parquet')
            regra('Hashes '+nome,sha(j)==e['sha256_json'] and sha(a)==e['sha256_parquet'])
            rows=json.loads(j.read_text(encoding='utf-8'));t=pq.read_table(a)
            regra('Reconciliacao '+nome,len(rows)==e['linhas'] and rows==canon(t.to_pylist()))
            tabelas[nome]=rows
        painel=tabelas['painel_periodo_comum'];controles=tabelas['controle_periodos']
        regra('Chave cidade indicador unica',len({(r['codigo_ibge'],r['indicador_id']) for r in painel})==len(painel))
        resumos=[];observacoes=[];extremos=[];graficos=[]
        for c in controles:
            ident=c['indicador_id'];rows=[r for r in painel if r['indicador_id']==ident]
            regra('Cobertura e periodo '+ident,len(rows)==12 and all(r['ano_referencia']==c['ano_referencia_comum'] for r in rows) and sum(r['valor'] is not None for r in rows)==c['cidades_com_valor'])
            validos=[r for r in rows if r['valor'] is not None]
            regra('Valores finitos '+ident,all(math.isfinite(r['valor']) for r in validos))
            vals=[float(r['valor']) for r in validos];s=descrever(vals)
            pendente=sum(r['renda_pendente'] for r in rows)
            resumo={'indicador_id':ident,'nome_oficial':c['nome_oficial'],'classificacoes_json':c['classificacoes_json'],'ano_referencia':c['ano_referencia_comum'],'unidade':rows[0]['unidade'],'cidades_validas':len(vals),'cidades_ausentes':12-len(vals),'renda_pendente_linhas':pendente,'analise_condicionada_conferencia_renda':bool(pendente),**s}
            conta=0
            for r in rows:
                v=r['valor'];flag=v is not None and (v<s['limite_inferior_iqr'] or v>s['limite_superior_iqr'])
                o={**r,'extremo_iqr':bool(flag),'criterio_extremo':'Q1 - 1,5 IQR; Q3 + 1,5 IQR; desigualdade estrita','acao':'INVESTIGAR_SEM_EXCLUIR' if flag else 'PRESERVAR'}
                observacoes.append(o)
                if flag:extremos.append(o);conta+=1
            resumo['cidades_extremas_iqr']=conta;resumos.append(resumo)
            # Pontos ordenados, eixo linear com zero incluido e escala por indicador.
            ordenar=sorted(validos,key=lambda r:r['valor']);altura=80+30*len(ordenar);lo=min([0]+vals);hi=max([0]+vals);span=hi-lo or 1
            svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 {altura}" role="img" aria-label="Valores por cidade"><line x1="230" x2="720" y1="35" y2="35" stroke="#8d9aaa"/>'
            svg+=f'<text x="230" y="25">{lo:.3g}</text><text x="680" y="25">{hi:.3g}</text>'
            for i,r in enumerate(ordenar):
                y=65+i*30;v=r['valor'];x=230+490*(v-lo)/span;flag=v<s['limite_inferior_iqr'] or v>s['limite_superior_iqr'];cor='#b64c28' if flag else '#176b9a'
                svg+=f'<text x="5" y="{y+5}">{html.escape(r["municipio"])}</text><circle cx="{x:.2f}" cy="{y}" r="5" fill="{cor}"/><text x="740" y="{y+5}">{v:,.4g}</text>'
            svg+='</svg>'
            graficos.append('<section><h2>'+html.escape(c['nome_oficial'])+'</h2><p>'+html.escape(c['classificacoes_json'])+'</p><p>Ano: '+str(c['ano_referencia_comum'])+' | Unidade: '+html.escape(rows[0]['unidade'])+' | Valores: '+str(len(vals))+'/12 | Extremos IQR: '+str(conta)+' | Linhas com renda pendente: '+str(pendente)+'</p>'+svg+'<p>Média: '+str(s['media'])+' | Mediana: '+str(s['mediana'])+' | Q1: '+str(s['q1'])+' | Q3: '+str(s['q3'])+'</p><p>Ausências: '+html.escape(', '.join(r['municipio'] for r in rows if r['valor'] is None) or 'Nenhuma')+'</p></section>')
        saida=raiz/'datalake/03_gold'/run_id/'eda_univariada';saida.mkdir(parents=True,exist_ok=False)
        exports=[]
        # Schema de resumos fixa metricas como double mesmo quando todas sao nulas.
        schema_resumo=pa.schema([(k,pa.float64() if k in descrever([]) else pa.bool_() if isinstance(v,bool) else pa.int64() if isinstance(v,int) else pa.string()) for k,v in resumos[0].items()])
        schema_obs=pq.read_schema(p/'painel_periodo_comum.parquet').append(pa.field('extremo_iqr',pa.bool_())).append(pa.field('criterio_extremo',pa.string())).append(pa.field('acao',pa.string()))
        for nome,rows,schema in [('estatisticas_indicadores',resumos,schema_resumo),('valores_cidades',observacoes,schema_obs),('extremos_investigar',extremos,schema_obs)]:
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rows);pq.write_table(pa.Table.from_pylist(rows,schema=schema),a,compression='snappy')
            regra('Exportacao '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()))
            exports.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        limites=['Estatisticas descritivas das cidades selecionadas, sem generalizacao ou testes de hipotese.','Cada indicador usa seu periodo comum; indicadores diferentes podem ter anos diferentes.','Ausencias nao foram imputadas; resumo calculado somente com cidades numericamente disponiveis.','Faixas de renda com pendencias sao descritas com ressalva; nao liberadas para recomendacao definitiva.','Extremo pelo IQR e sinalizacao, nao erro confirmado nem exclusao.','Categorias de indicadores nao sao dimensoes independentes e nao devem ser somadas indiscriminadamente.','Preco, consumo documental, analise temporal e relacoes entre variaveis permanecem para os proximos blocos.','Comparacao com analise original permanece para encerramento.']
        rel.update(status='EDA_UNIVARIADA_CONCLUIDA_COM_LIMITACOES',entrada={'run_id':m['run_id'],'pasta':str(p),'manifesto_sha256':sha(p/'manifesto_base_eda.json'),'conclusao_estrutura':str(anteriores[0]),'conclusao_estrutura_sha256':sha(anteriores[0])},saida=str(saida),exportacoes=exports,resumo={'indicadores_classificacoes':len(resumos),'linhas_descritivas':len(observacoes),'valores_numericos':sum(r['valor'] is not None for r in observacoes),'extremos_iqr':len(extremos),'indicadores_com_extremos':sum(r['cidades_extremas_iqr']>0 for r in resumos),'indicadores_com_conferencia_renda_pendente':sum(r['analise_condicionada_conferencia_renda'] for r in resumos)},metodos={'quartis':'Interpolacao linear h=(n-1)p, equivalente ao quantil tipo 7','variancia':'Divisor n; descricao do conjunto selecionado, sem estimar variancia de uma populacao maior','assimetria':'Momento central 3 / momento central 2 elevado a 1,5; sem correcao de vies; n>=3 e variancia>0','curtose':'Momento central 4 / momento central 2 ao quadrado menos 3; sem correcao de vies; n>=4 e variancia>0'},limites=limites)
        doc='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA univariada</title><style>body{font:15px Arial;color:#1c3042;margin:32px}section{border-top:1px solid #ccd5dd;padding:18px 0}svg{width:100%;max-width:1000px}svg text{font:13px Arial}h1,h2{color:#18496b}</style><h1>EDA univariada municipal</h1><p>'+PROJETO+' | Execução: '+run_id+' | Base: '+m['run_id']+'</p><p>Azul: valor preservado. Laranja: extremo IQR para investigar. Escalas independentes por indicador; números dos gráficos usam ponto decimal.</p><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in limites)+'</ul>'+''.join(graficos)+'</html>'
        (saida/'relatorio_univariado.html').write_text(doc,encoding='utf-8');rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(saida/'manifesto_eda_univariada.json',rel)
        return rel
    except Exception as e:rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_12_eda_univariada.json',rel)
        (q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path)
    a=ap.parse_args();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8];print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
