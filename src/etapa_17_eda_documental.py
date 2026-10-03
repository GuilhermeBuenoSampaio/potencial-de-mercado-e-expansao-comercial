"""EDA documental com precos por apresentacao e estudos historicos rastreaveis."""
import argparse
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO, sha, gravar, canon, carregar
from etapa_11_eda_estrutura import selecionar

STATUS = 'EDA_DOCUMENTAL_CONCLUIDA_COM_LIMITACOES'
LIMITES = [
 'Precos publicados por pacote; vigencia nao confirmada impede orcamento atual.',
 'Mediana de precos descreve o catalogo; nao representa custo, ticket ou preco global.',
 'Resumo de percentuais descreve celulas publicadas, sem ponderacao ou estimativa combinada.',
 'POF 2002–2003 e universitarios de instituicao privada de Goiania em 2011: contexto historico, sem extrapolacao municipal.',
 'Coeficientes, testes e ajustes sao publicados; nao foram reestimados com microdados.',
 'Coeficiente de renda nao e elasticidade-preco. Interacao exige interpretacao conjunta do modelo original.',
 'JPEG e PDF equivalentes nao formam amostras independentes.',
 'Pendencias documentais permanecem abertas; nenhum dado foi imputado ou corrigido automaticamente.',
 'Comparacao com analise original somente no encerramento; sem estimativa atual de demanda ou ranking.'
]

def mediana_decimal(vals):
    a=sorted(vals);n=len(a)
    return None if not n else a[n//2] if n%2 else (a[n//2-1]+a[n//2])/Decimal(2)

def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve();q=raiz/'quality/17_eda_documental'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(n,c):
        rel['regras'].append({'regra':n,'resultado':'APROVADA' if c else 'REPROVADA'})
        if not c:raise ValueError(n)
    try:
        p=Path(base).resolve() if base else selecionar(raiz)
        bm=json.loads((p/'manifesto_base_eda.json').read_text(encoding='utf-8'));bh=sha(p/'manifesto_base_eda.json')
        regra('Base aprovada do projeto',bm['projeto']==PROJETO and bm['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        refs=[r for r in bm['entradas'] if r['tipo']=='documental'];regra('Uma Silver documental na linhagem',len(refs)==1)
        ref=refs[0];pd=raiz/'datalake/02_silver'/ref['run_id']/'documental'
        regra('Hash do manifesto documental da base',sha(pd/'manifesto_documental.json')==ref['manifesto_sha256'])
        md,dt=carregar(pd,'documental');regra('Todas as tabelas reconciliadas',len(dt)==9 and md['exportacoes']==ref['tabelas'])
        f=raiz/'quality/09_silver_documental'/md['run_id']/'conclusao_09_silver_documental.json'
        cq=json.loads(f.read_text(encoding='utf-8'));regra('Conclusao Silver correspondente',cq['status']==md['status'] and cq['run_id']==md['run_id'] and cq['exportacoes']==md['exportacoes'])
        rows={k:v[0] for k,v in dt.items()}
        for nome,rs in rows.items():
            if rs and 'registro_id' in rs[0]:regra('IDs unicos '+nome,len({r['registro_id'] for r in rs})==len(rs))
        precos=[];grupos=defaultdict(list)
        for r in rows['precos_produtos']:
            v=Decimal(r['preco_pacote_brl']) if r['preco_pacote_brl'] is not None else None
            regra('Preco nao negativo '+r['registro_id'],v is None or v>=0)
            peso=r['peso_pacote_kg'];kg=None if v is None or peso is None or Decimal(str(peso))<=0 else v/Decimal(str(peso))
            precos.append({**r,'preco_por_kg_referencia_brl':None if kg is None else str(kg),'formula_preco_kg':'preco_pacote_brl / peso_pacote_kg; produtos distintos nao equivalentes','uso_eda':'DESCRICAO_CATALOGO_HISTORICO'})
            grupos[r['categoria'],r['estado'],peso].append(v)
        resumo=[]
        for (cat,estado,peso),vals in sorted(grupos.items(),key=lambda x:str(x[0])):
            vv=[v for v in vals if v is not None]
            resumo.append({'categoria':cat,'estado':estado,'peso_pacote_kg':peso,'registros':len(vals),'precos_validos':len(vv),'minimo_pacote_brl':str(min(vv)) if vv else None,'mediana_pacote_brl':str(mediana_decimal(vv)) if vv else None,'maximo_pacote_brl':str(max(vv)) if vv else None,'uso':'Resumo de produtos do catalogo, sem ponderacao por vendas'})
        consumo=rows['consumo_historico'];gs=defaultdict(list)
        for r in consumo:
            v=r['percentual'];regra('Percentual publicado no intervalo '+r['registro_id'],v is None or 0<=v<=100)
            gs[tuple(r[k] for k in ['source_sha256','tabela','periodo_referencia','indicador','dimensao','regiao','grupo_alimento'])].append(r)
        rescons=[]
        keys=['source_sha256','tabela','periodo_referencia','indicador','dimensao','regiao','grupo_alimento']
        for key,rs in sorted(gs.items(),key=lambda x:str(x[0])):
            vv=[r['percentual'] for r in rs if r['percentual'] is not None]
            rescons.append({**dict(zip(keys,key)),'celulas_publicadas':len(rs),'minimo_percentual':min(vv) if vv else None,'maximo_percentual':max(vv) if vv else None,'estratos_json':json.dumps([{'estrato':r['estrato'],'percentual':r['percentual'],'registro_id':r['registro_id']} for r in rs],ensure_ascii=False),'uso':'Intervalo de celulas; nao somar nem estimar prevalencia conjunta'})
        by={r['registro_id']:r for r in consumo};evidencias=[]
        for r in rows['evidencias_imagens']:
            regra('Referencia PDF existente '+r['registro_id'],r['registro_pdf_id'] in by)
            original=by[r['registro_pdf_id']]
            regra('Percentual PDF preservado '+r['registro_id'],r['percentual_pdf']==original['percentual'])
            regra('JPEG nao cria observacao '+r['registro_id'],r['incluir_como_nova_observacao'] is False)
            evidencias.append({**r,'diferenca_imagem_pdf':None if r['percentual_imagem'] is None or r['percentual_pdf'] is None else r['percentual_imagem']-r['percentual_pdf']})
        cobertura=[]
        for nome,rs in rows.items():
            cobertura.append({'tabela':nome,'registros':len(rs),'fontes_distintas':len({r.get('source_sha256',r.get('fonte')) for r in rs if r.get('source_sha256',r.get('fonte'))}),'periodos_json':json.dumps(sorted({str(r['periodo_referencia']) for r in rs if r.get('periodo_referencia')}),ensure_ascii=False),'status':'EVIDENCIA_COMPLEMENTAR' if nome=='evidencias_imagens' else 'PENDENCIAS' if nome=='pendencias_documentais' else 'PUBLICADO_COM_LIMITACOES'})
        saida=raiz/'datalake/03_gold'/run_id/'eda_documental';saida.mkdir(parents=True,exist_ok=False);exports=[]
        novas={'cobertura_documental':cobertura,'precos_referencia':precos,'resumo_precos_apresentacao':resumo,'resumo_consumo_publicado':rescons,'conferencia_imagens':evidencias}
        # Copias de estudos conservam os tipos da Silver e os IDs: nenhuma nova amostra.
        for nome in ['consumo_historico','universitarios_historico','coeficientes_publicados','ajustes_publicados','testes_publicados','pendencias_documentais','fontes_documentais']:
            novas[nome]=rows[nome]
        for nome,rs in novas.items():
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rs)
            ar=dt[nome][1] if nome in dt else pa.Table.from_pylist(rs)
            pq.write_table(ar,a,compression='snappy')
            regra('Saida reconciliada '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()))
            exports.append({'tabela':nome,'linhas':len(rs),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        def tabela(rs):
            if not rs:return '<p>Sem registros.</p>'
            ks=list(rs[0]);return '<table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in ks)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ks)+'</tr>' for r in rs)+'</table>'
        body='<h1>EDA documental</h1><p>'+PROJETO+' | '+run_id+'</p><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in LIMITES)+'</ul>'
        for title,rs in [('Cobertura',cobertura),('Precos por apresentacao',resumo),('Consumo historico: celulas publicadas',rescons),('Coeficientes publicados',rows['coeficientes_publicados']),('Ajustes publicados',rows['ajustes_publicados']),('Pendencias',rows['pendencias_documentais'])]:body+='<h2>'+title+'</h2>'+tabela(rs)
        (saida/'relatorio_documental.html').write_text('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA documental</title><style>body{font:15px Arial;margin:30px}table{border-collapse:collapse;display:block;overflow:auto}td,th{padding:7px;border:1px solid #ccc}h2{margin-top:30px}</style>'+body+'</html>',encoding='utf-8')
        rel.update(status=STATUS,entrada={'base_run_id':bm['run_id'],'manifesto_base_sha256':bh,'silver_documental_run_id':md['run_id'],'manifesto_documental_sha256':ref['manifesto_sha256'],'conclusao_silver_sha256':sha(f)},saida=str(saida),exportacoes=exports,resumo={'precos':len(precos),'grupos_precos':len(resumo),'celulas_consumo':len(consumo),'recortes_consumo':len(rescons),'evidencias_jpeg':len(evidencias),'divergencias_percentuais_jpeg':sum(r['diferenca_imagem_pdf'] not in [None,0] for r in evidencias),'pendencias':len(rows['pendencias_documentais'])},limites=LIMITES)
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(saida/'manifesto_eda_documental.json',rel);return rel
    except Exception as e:rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_17_eda_documental.json',rel)
        (q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path);a=ap.parse_args()
    run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
