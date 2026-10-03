"""Primeiro bloco da EDA: estrutura, cobertura, periodos e restricoes."""
import argparse
import html
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO, sha, gravar, canon

STATUS_BASE = 'BASE_EDA_PREPARADA_COM_LIMITACOES'

def selecionar(raiz):
    for p in sorted((raiz/'datalake/03_gold').glob('*/base_eda/manifesto_base_eda.json'), reverse=True):
        m=json.loads(p.read_text(encoding='utf-8'))
        q=raiz/'quality/10_base_eda'/m['run_id']/'conclusao_10_base_eda.json'
        if m.get('status')==STATUS_BASE and q.exists():
            r=json.loads(q.read_text(encoding='utf-8'))
            if r.get('run_id')==m['run_id'] and r.get('status')==STATUS_BASE: return p.parent
    raise ValueError('Nenhuma base EDA com manifesto e conclusao correspondentes')

def executar(raiz, run_id, base=None):
    raiz=Path(raiz).resolve(); q=raiz/'quality/11_eda_estrutura'/run_id
    q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome,cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond: raise ValueError('Regra reprovada: '+nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz)
        man=p/'manifesto_base_eda.json'; m=json.loads(man.read_text(encoding='utf-8'))
        regra('Projeto e status da base',m.get('projeto')==PROJETO and m.get('status')==STATUS_BASE)
        rel['entrada']={'pasta':str(p),'run_id':m['run_id'],'manifesto_sha256':sha(man)}
        tabelas={}; schemas=[]; perfil=[]
        for e in m['exportacoes']:
            nome=e['tabela']; regra('Nome de tabela '+nome,Path(nome).name==nome and nome not in tabelas)
            j=p/(nome+'.json'); a=p/(nome+'.parquet')
            regra('Hashes '+nome,sha(j)==e['sha256_json'] and sha(a)==e['sha256_parquet'])
            rows=json.loads(j.read_text(encoding='utf-8')); t=pq.read_table(a)
            regra('Reconciliacao '+nome,len(rows)==e['linhas'] and rows==canon(t.to_pylist()))
            tabelas[nome]=rows
            schemas.append({'tabela':nome,'linhas':t.num_rows,'colunas':t.num_columns,'linhas_duplicadas_integrais':len(rows)-len({json.dumps(r,sort_keys=True,ensure_ascii=False) for r in rows}),'schema':str(t.schema)})
            for f in t.schema:
                vals=[r[f.name] for r in rows]; nulos=sum(v is None for v in vals)
                perfil.append({'tabela':nome,'campo':f.name,'tipo_parquet':str(f.type),'linhas':len(rows),'nulos':nulos,'nulos_percentual':100*nulos/len(rows) if rows else None,'cardinalidade_nao_nula':len({json.dumps(v,sort_keys=True,ensure_ascii=False) for v in vals if v is not None})})
        painel=tabelas['painel_periodo_comum']; controle=tabelas['controle_periodos']; ult=tabelas['indicadores_ultimo_disponivel_eda']
        cidades=sorted({r['codigo_ibge'] for r in painel}); ids={r['indicador_id'] for r in controle}
        regra('12 cidades e controles unicos',len(cidades)==12 and len(ids)==len(controle))
        regra('Painel cidade indicador unico e completo',len(painel)==12*len(ids) and len({(r['codigo_ibge'],r['indicador_id']) for r in painel})==len(painel) and {r['indicador_id'] for r in painel}==ids)
        cobertura=[]
        for c in controle:
            rows=[r for r in painel if r['indicador_id']==c['indicador_id']]; valido=sum(r['valor'] is not None for r in rows)
            regra('Periodo e cobertura '+c['indicador_id'],len(rows)==12 and all(r['ano_referencia']==c['ano_referencia_comum'] for r in rows) and valido==c['cidades_com_valor'] and 12-valido==c['cidades_sem_valor'])
            cobertura.append({**c,'cobertura_percentual':100*valido/12,'renda_pendente_linhas':sum(r['renda_pendente'] for r in rows)})
        por_cidade=[]
        for codigo in cidades:
            rows=[r for r in painel if r['codigo_ibge']==codigo]; n=sum(r['valor'] is not None for r in rows)
            por_cidade.append({'codigo_ibge':codigo,'municipio':rows[0]['municipio'],'uf':rows[0]['uf'],'combinacoes_indicador_classificacao':len(rows),'com_valor':n,'sem_valor':len(rows)-n,'cobertura_percentual':100*n/len(rows),'renda_pendente_linhas':sum(r['renda_pendente'] for r in rows)})
        ausencias=[r for r in painel if r['valor'] is None]
        disponibilidade={r['indicador_id']:r['ano_referencia_comum'] for r in controle}
        uso=[]
        for (status,proposta),n in sorted(Counter((r['status_atualidade'],r['uso_proposto']) for r in ult).items()):
            uso.append({'status_atualidade':status,'uso_proposto':proposta,'linhas':n})
        rel['resumo']={'cidades':len(cidades),'indicadores_classificacoes':len(ids),'linhas_painel':len(painel),'com_valor_painel':len(painel)-len(ausencias),'sem_valor_painel':len(ausencias),'cobertura_numerica_percentual':100*(len(painel)-len(ausencias))/len(painel),'indicadores_cobertura_completa':sum(c['cidades_sem_valor']==0 for c in controle),'ultimos_disponiveis_em_ano_anterior_ao_painel':sum(r['ano_referencia']<disponibilidade[r['indicador_id']] for r in ult),'marcadores_ausencias':dict(Counter(r['status_valor'] for r in ausencias)),'pendencias_documentais':m['pendencias_documentais']}
        saida=raiz/'datalake/03_gold'/run_id/'eda_estrutura'; saida.mkdir(parents=True,exist_ok=False)
        exports=[]
        for nome,rows in [('estrutura_tabelas',schemas),('perfil_colunas',perfil),('cobertura_indicadores',cobertura),('cobertura_cidades',por_cidade),('ausencias_painel',ausencias),('uso_ultimos_disponiveis',uso)]:
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rows)
            schema=None
            if nome=='ausencias_painel': schema=pq.read_schema(p/'painel_periodo_comum.parquet')
            t=pa.Table.from_pylist(rows,schema=schema);pq.write_table(t,a,compression='snappy')
            regra('Exportacao '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()))
            exports.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        def tabela(rows):
            keys=list(rows[0]) if rows else []
            return '<table><thead><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in keys)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in keys)+'</tr>' for r in rows)+'</tbody></table>'
        limites=['Cobertura numerica nao representa elegibilidade automatica para comparacao comercial.','As 56 combinacoes incluem categorias do mesmo indicador; nao sao 56 dimensoes independentes.','Nao se inferiu mecanismo MCAR, MAR ou MNAR; marcadores seguem a fonte.','Candidatos a EDA ainda exigem conferencia de renda, periodos e metodologia.','Precos continuam com vigencia pendente; estudos historicos nao estimam demanda municipal.','Distancias entre centroides nao representam rotas rodoviarias.','Comparacao com analise original permanece reservada ao encerramento.']
        conteudo='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA: estrutura e cobertura</title><style>body{font:15px Arial;margin:32px;color:#172638}table{border-collapse:collapse;font-size:13px}td,th{border:1px solid #cbd3dc;padding:7px}th{background:#e8eef5;text-align:left}h1,h2{color:#18496b}</style><h1>EDA — estrutura, cobertura e periodos</h1><p>Projeto: '+PROJETO+' | Execucao: '+run_id+'</p><h2>Resumo</h2>'+tabela([rel['resumo']])+ '<h2>Cobertura por cidade</h2>'+tabela(por_cidade)+'<h2>Cobertura e periodo por indicador/classificacao</h2>'+tabela(cobertura)+'<h2>Uso dos ultimos valores disponiveis</h2>'+tabela(uso)+'<h2>Cuidados de interpretacao</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in limites)+'</ul></html>'
        (saida/'relatorio_estrutura.html').write_text(conteudo,encoding='utf-8')
        rel.update(status='EDA_ESTRUTURA_CONCLUIDA_COM_LIMITACOES',saida=str(saida),exportacoes=exports,limites=limites,fim_utc=datetime.now(timezone.utc).isoformat())
        gravar(saida/'manifesto_eda_estrutura.json',rel)
        return rel
    except Exception as e:
        rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_11_eda_estrutura.json',rel)
        (q/'execucao.log').write_text('\n'.join(x['resultado']+' '+x['regra'] for x in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path,help='Base escolhida manualmente; valida manifesto e tabelas diretamente')
    a=ap.parse_args();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
