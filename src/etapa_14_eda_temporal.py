"""EDA temporal: variacoes por blocos e contexto setorial historico."""
import argparse
import html
import json
import math
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
import pyarrow as pa
import pyarrow.parquet as pq
from etapa_10_base_eda import PROJETO,carregar,sha,gravar,canon
from etapa_11_eda_estrutura import selecionar

PLANOS=[('populacao','6579','9324',[(2019,2021),(2024,2026)],'PESSOAS_ESTIMADAS'),('pib_nominal','5938','37',[(2018,2023)],'MONETARIO_NOMINAL'),('unidades_locais','9509','706',[(2022,2024)],'CONTAGEM'),('pessoal_ocupado','9509','707',[(2022,2024)],'CONTAGEM_LOCAL_TRABALHO'),('salario_medio_brl','9509','10143',[(2022,2024)],'MONETARIO_NOMINAL'),('remuneracoes_brl','9509','662',[(2022,2024)],'MONETARIO_NOMINAL')]

def taxas(inicio,fim,anos):
    if anos<=0:raise ValueError('Intervalo temporal invalido')
    absoluta=fim-inicio
    percentual=100*(fim/inicio-1) if inicio!=0 else None
    anualizada=100*((fim/inicio)**(1/anos)-1) if inicio>0 and fim>=0 else None
    return absoluta,percentual,anualizada

# Incidente documentado: divergencia entre divulgacao historica e APIs.
# Preserva valores e contas; bloqueia uso interpretativo da serie afetada.
INCIDENTE = 'PIB_SALES_OLIVEIRA_2019'
INCIDENTES = {'3544905':INCIDENTE, '3517406':'PIB_GUAIRA_2019', '3533601':'PIB_NUPORANGA_2019'}

def sinalizar_conferencia(rows, tipo):
    for r in rows:
        afetado = r['codigo_ibge'] in INCIDENTES and (tipo == 'setores' or r.get('alias') == 'pib_nominal')
        r['status_conferencia'] = 'CONFERENCIA_PENDENTE' if afetado else 'SEM_DIVERGENCIA_REGISTRADA'
        r['pendencia_id'] = INCIDENTES[r['codigo_ibge']] if afetado else ''
        r['uso_interpretativo'] = 'BLOQUEADO' if afetado else 'EXPLORATORIO_COM_LIMITACOES'


def executar(raiz,run_id,base=None):
    raiz=Path(raiz).resolve();q=raiz/'quality/14_eda_temporal'/run_id;q.mkdir(parents=True,exist_ok=False)
    rel={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO','regras':[]}
    def regra(nome,cond):
        rel['regras'].append({'regra':nome,'resultado':'APROVADA' if cond else 'REPROVADA'})
        if not cond:raise ValueError(nome)
    try:
        p=Path(base).resolve() if base else selecionar(raiz);manifesto=p/'manifesto_base_eda.json';m=json.loads(manifesto.read_text(encoding='utf-8'));mh=sha(manifesto)
        regra('Projeto e status base',m['projeto']==PROJETO and m['status']=='BASE_EDA_PREPARADA_COM_LIMITACOES')
        anteriores=[]
        for f in sorted((raiz/'quality/13_eda_bivariada').glob('*/conclusao_13_eda_bivariada.json'),reverse=True):
            r=json.loads(f.read_text(encoding='utf-8'))
            if r.get('status')=='EDA_BIVARIADA_CONCLUIDA_COM_LIMITACOES' and r.get('entrada',{}).get('manifesto_base_sha256')==mh:anteriores.append(f);break
        regra('Bivariada concluida para mesma base',bool(anteriores))
        ent=next(x for x in m['entradas'] if x['tipo']=='municipal');pm=raiz/'datalake/02_silver'/ent['run_id']/'municipal'
        regra('Linhagem municipal',sha(pm/'manifesto_silver.json')==ent['manifesto_sha256']);sm,mt=carregar(pm,'municipal')
        dic=mt['dicionario_indicadores'][0];serie=mt['indicadores_serie'][0];cidades=[r for r in mt['municipios'][0] if r['cidade_expansao']]
        regra('Cidades unicas',len(cidades)==12 and len({r['codigo_ibge'] for r in cidades})==12)
        pontos=[];variacoes=[];resumos=[];catalogo=[];secoes=[]
        for alias,tabela,var,blocos,natureza in PLANOS:
            ds=[d for d in dic if d['tabela']==tabela and d['variavel_id']==var and d['classificacoes_json']=='[]'];regra('Selecao unica '+alias,len(ds)==1);d=ds[0]
            catalogo.append({'alias':alias,'indicador_id':d['indicador_id'],'nome_oficial':d['nome_oficial'],'unidade':d['unidade_silver'],'natureza':natureza,'blocos_json':json.dumps(blocos),'criterio':'Blocos previamente definidos; sem conectar populacao 2021 a 2024 nem CEMPRE a anos anteriores a 2022'})
            chartrows=[]
            for c in cidades:
                rows=sorted([r for r in serie if r['indicador_id']==d['indicador_id'] and r['codigo_ibge']==c['codigo_ibge']],key=lambda r:r['ano_referencia'])
                regra('Ano unico '+alias+' '+c['codigo_ibge'],len({r['ano_referencia'] for r in rows})==len(rows));byyear={r['ano_referencia']:r for r in rows}
                for r in rows:
                    bloco=next((str(a)+'_'+str(b) for a,b in blocos if a<=r['ano_referencia']<=b),None)
                    pontos.append({**r,'alias':alias,'natureza':natureza,'bloco_analitico':bloco})
                for a,b in blocos:
                    selected=[r for r in rows if a<=r['ano_referencia']<=b]
                    # Sem pular anos ausentes para produzir uma variacao anual ficticia.
                    for ano in range(a+1,b+1):
                        ini=byyear.get(ano-1);fim=byyear.get(ano)
                        disponivel=ini is not None and fim is not None and ini['valor'] is not None and fim['valor'] is not None
                        va,vp,ta=taxas(ini['valor'],fim['valor'],1) if disponivel else (None,None,None)
                        variacoes.append({'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'alias':alias,'natureza':natureza,'unidade':d['unidade_silver'],'ano_inicial':ano-1,'ano_final':ano,'variacao_absoluta':va,'variacao_percentual':vp,'status':'CALCULADO' if disponivel else 'VALOR_AUSENTE','fontes_sha256_json':json.dumps(sorted({r['fonte_sha256'] for r in [ini,fim] if r}))})
                    ini=byyear.get(a);fim=byyear.get(b);disponivel=ini is not None and fim is not None and ini['valor'] is not None and fim['valor'] is not None
                    va,vp,ta=taxas(ini['valor'],fim['valor'],b-a) if disponivel else (None,None,None)
                    resumos.append({'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'alias':alias,'natureza':natureza,'unidade':d['unidade_silver'],'ano_inicial':a,'ano_final':b,'intervalo_anos':b-a,'valor_inicial':None if ini is None else ini['valor'],'valor_final':None if fim is None else fim['valor'],'variacao_absoluta':va,'crescimento_acumulado_percentual':vp,'taxa_anualizada_percentual':ta,'cobertura_anos_numericos':sum(r['valor'] is not None for r in selected),'anos_esperados':b-a+1,'status':'CALCULADO' if disponivel else 'VALOR_AUSENTE','fontes_sha256_json':json.dumps(sorted({r['fonte_sha256'] for r in selected}))})
                    chartrows.append((c['municipio'],a,b,selected))
            # Pequenos graficos por cidade: eixo temporal real e segmentos desconectados.
            partes=[]
            for c in cidades:
                selected=[r for r in pontos if r['alias']==alias and r['codigo_ibge']==c['codigo_ibge'] and r['valor'] is not None];years=[r['ano_referencia'] for r in selected];vals=[r['valor'] for r in selected]
                svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 250" role="img" aria-label="Serie por ano"><path d="M65 20V200H650" fill="none" stroke="#7d8fa0"/>'
                if vals:
                    lo=0;hi=max(vals) or 1;ay=min(years);by=max(years)
                    for ano in sorted(set(years)):svg+=f'<text x="{65+550*(ano-ay)/(by-ay or 1):.1f}" y="222">{ano}</text>'
                    svg+=f'<text x="5" y="25">{hi:.3g}</text><text x="25" y="202">0</text>'
                    for a,b in blocos:
                        segment=[r for r in selected if a<=r['ano_referencia']<=b];prev=None
                        for r in segment:
                            x=65+550*(r['ano_referencia']-ay)/(by-ay or 1);y=200-170*r['valor']/hi
                            if prev is not None and r['ano_referencia']==prev[2]+1:svg+=f'<line x1="{prev[0]:.2f}" y1="{prev[1]:.2f}" x2="{x:.2f}" y2="{y:.2f}" stroke="#176b9a"/>'
                            svg+=f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#176b9a"><title>{r["ano_referencia"]}: {r["valor"]}</title></circle>';prev=(x,y,r['ano_referencia'])
                svg+='</svg>'
                tabela_html='<table><tr><th>Ano</th><th>Valor</th></tr>'+''.join('<tr><td>'+str(r['ano_referencia'])+'</td><td>'+str(r['valor'])+'</td></tr>' for r in selected)+'</table>'
                partes.append('<details><summary>'+html.escape(c['municipio'])+(' — CONFERENCIA_PENDENTE: uso interpretativo bloqueado' if c['codigo_ibge'] in INCIDENTES and alias=='pib_nominal' else '')+'</summary>'+svg+tabela_html+'</details>')
            secoes.append('<section><h2>'+html.escape(d['nome_oficial'])+'</h2><p>'+html.escape(d['unidade_silver'])+' | '+natureza+' | Blocos: '+html.escape(json.dumps(blocos))+'</p>'+''.join(partes)+'</section>')
        setores=[]
        for d in dic:
            if d['tabela']=='5938' and d['variavel_id'] in ['516','520','6574','528']:
                for c in cidades:
                    rows=[r for r in serie if r['indicador_id']==d['indicador_id'] and r['codigo_ibge']==c['codigo_ibge']];nums=[r for r in rows if r['valor'] is not None]
                    ultimo=max(nums,key=lambda r:r['ano_referencia']) if nums else None;primeiro=min(nums,key=lambda r:r['ano_referencia']) if nums else None
                    setores.append({'codigo_ibge':c['codigo_ibge'],'municipio':c['municipio'],'indicador_id':d['indicador_id'],'nome_oficial':d['nome_oficial'],'ano_inicial_disponivel':None if primeiro is None else primeiro['ano_referencia'],'ano_final_disponivel':None if ultimo is None else ultimo['ano_referencia'],'participacao_inicial_percentual':None if primeiro is None else primeiro['valor'],'participacao_final_percentual':None if ultimo is None else ultimo['valor'],'variacao_pontos_percentuais':None if primeiro is None or ultimo is None else ultimo['valor']-primeiro['valor'],'anos_sem_valor_json':json.dumps(sorted(r['ano_referencia'] for r in rows if r['valor'] is None)),'uso':'CONTEXTO_SETORIAL_HISTORICO; NAO_PREENCHER_2023','fontes_sha256_json':json.dumps(sorted({r['fonte_sha256'] for r in nums}))})
        regra('48 perfis setoriais',len(setores)==48)
        # Reconcilia o calculo de PIB com a Silver, sem assumir percentual como anual.
        growth={r['codigo_ibge']:r for r in mt['crescimento_pib'][0]}
        for r in resumos:
            if r['alias']=='pib_nominal':
                g=growth[r['codigo_ibge']];regra('PIB reconciliado '+r['codigo_ibge'],r['ano_inicial']==g['ano_inicial'] and r['ano_final']==g['ano_final'] and math.isclose(r['crescimento_acumulado_percentual'],g['acumulado_percentual'],abs_tol=1e-9) and math.isclose(r['taxa_anualizada_percentual'],g['taxa_anualizada_percentual'],abs_tol=1e-9))
        for rows,tipo in [(pontos,'serie'),(variacoes,'variacoes'),(resumos,'blocos'),(setores,'setores')]:
            sinalizar_conferencia(rows,tipo)
        regra('Bloqueio de interpretacao Sales Oliveira', all(r['uso_interpretativo']=='BLOQUEADO' for rows in [pontos,variacoes,resumos,setores] for r in rows if r['pendencia_id'] in INCIDENTES.values()))
        pendencias=[{'pendencia_id':INCIDENTE,'codigo_ibge':'3544905','municipio':'Sales Oliveira','ano_referencia':2019,'indicador':'PIB per capita','unidade':'R$','valor_publicacao_historica':308567.36,'valor_api_coletada':30638.65,'status':'CONFERENCIA_PENDENTE','causa':'NAO_CONFIRMADA','efeito':'Bloqueio interpretativo da serie de PIB nominal e contexto setorial; valores preservados','fonte_historica_url':'https://ftp.ibge.gov.br/Pib_Municipios/2019/base/base_de_dados_2010_2019_txt.zip','fonte_api_url':'https://servicodados.ibge.gov.br/api/v1/pesquisas/38/indicadores/47001/resultados/3544905','evidencia_documentada':'docs/11_eda/CONFERENCIA_PIB_SALES_OLIVEIRA.md'}]
        for codigo,nome,antes,depois in [('3517406','Guaira',83612.04,51739.62),('3533601','Nuporanga',54664.34,72118.89)]:
            pendencias.append({**pendencias[0],'pendencia_id':INCIDENTES[codigo],'codigo_ibge':codigo,'municipio':nome,'valor_publicacao_historica':antes,'valor_api_coletada':depois,'fonte_historica_url':'https://ftp.ibge.gov.br/Pib_Municipios/2019/base/base_de_dados_2010_2019_txt.zip','fonte_api_url':'https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip'})
        # Limiar operacional de triagem, nao teste estatistico nem prova de erro.
        alertas=[{**r,'criterio_triagem':'abs(variacao anual nominal) >= 30%; nao prova erro'} for r in variacoes if r['alias']=='pib_nominal' and r['variacao_percentual'] is not None and abs(r['variacao_percentual'])>=30]
        saida=raiz/'datalake/03_gold'/run_id/'eda_temporal';saida.mkdir(parents=True,exist_ok=False);exports=[]
        floats={'valor_inicial','valor_final','variacao_absoluta','variacao_percentual','crescimento_acumulado_percentual','taxa_anualizada_percentual','participacao_inicial_percentual','participacao_final_percentual','variacao_pontos_percentuais','valor_publicacao_historica','valor_api_coletada'}
        for nome,rows in [('catalogo_temporal',catalogo),('series_temporais',pontos),('variacoes_anuais',variacoes),('crescimento_por_bloco',resumos),('perfil_setorial_historico',setores),('pendencias_fontes',pendencias),('alertas_variacoes_pib',alertas)]:
            j=saida/(nome+'.json');a=saida/(nome+'.parquet');gravar(j,rows)
            if nome=='series_temporais':schema=pq.read_schema(pm/'indicadores_serie.parquet').append(pa.field('status_conferencia',pa.string())).append(pa.field('pendencia_id',pa.string())).append(pa.field('uso_interpretativo',pa.string())).append(pa.field('alias',pa.string())).append(pa.field('natureza',pa.string())).append(pa.field('bloco_analitico',pa.string()))
            else:schema=pa.schema([(k,pa.float64() if k in floats else pa.int64() if isinstance(v,int) else pa.string()) for k,v in rows[0].items()])
            pq.write_table(pa.Table.from_pylist(rows,schema=schema),a,compression='snappy');regra('Exportacao '+nome,json.loads(j.read_text(encoding='utf-8'))==canon(pq.read_table(a).to_pylist()));exports.append({'tabela':nome,'linhas':len(rows),'sha256_json':sha(j),'sha256_parquet':sha(a)})
        limites=['Sales Oliveira, Guaira e Nuporanga: series de PIB e contexto setorial com CONFERENCIA_PENDENTE; proibido interpretar a queda como contracao economica comprovada. Ver pendencias_fontes.json e documentacao.','SEM_DIVERGENCIA_REGISTRADA nao certifica comparabilidade; significa apenas ausencia de incidente registrado.','Triagem de variacoes nominais anuais de PIB com magnitude >=30%: limiar operacional, nao criterio de erro.','Valores monetarios a precos correntes: crescimento nominal, sem descontar inflacao.','Populacao: blocos 2019–2021 e 2024–2026 separados; nao se calcula crescimento atravessando 2021–2024.','Segmentar anos evita misturas conhecidas, mas nao certifica ausencia de revisoes metodologicas dentro de cada bloco.','CEMPRE: apenas serie de 2022 em diante; nao concatenada com tabelas antigas.','CAGR resume as pontas, nao informa trajetoria regular nem substitui variacoes anuais.','Dados ausentes nao foram interpolados ou convertidos em zero.','Participacoes setoriais usam ultimo periodo numerico historico, com diferencas em pontos percentuais; nao substituem 2023.','Censo 2022 nao foi inserido como estimativa anual de populacao.','Nao se estima demanda, causalidade, retorno ou ranking de expansao.','Comparacao com analise original somente no encerramento.']
        doc='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>EDA temporal</title><style>body{font:15px Arial;margin:32px;color:#183248}section{border-top:1px solid #ccd5dd;padding:20px 0}details{margin:12px 0}svg{width:100%;max-width:700px}svg text{font:12px Arial}td,th{padding:6px;border:1px solid #ccd5dd}table{border-collapse:collapse}</style><h1>EDA temporal municipal</h1><p>'+PROJETO+' | Execução: '+run_id+'</p><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in limites)+'</ul><p>Abra cada cidade para ver gráfico e valores. Escalas independentes por cidade; use tabelas para comparar níveis. Linhas não atravessam anos ausentes ou blocos separados.</p>'+''.join(secoes)+'</html>'
        cabecalho=['municipio','nome_oficial','ano_inicial_disponivel','ano_final_disponivel','participacao_inicial_percentual','participacao_final_percentual','variacao_pontos_percentuais','anos_sem_valor_json','status_conferencia','uso_interpretativo']
        tabela_setor='<h2>Contexto setorial historico</h2><p>Participacoes em percentual; diferencas em pontos percentuais. Nao representa composicao de 2023.</p><table><tr>'+''.join('<th>'+html.escape(k)+'</th>' for k in cabecalho)+'</tr>'+''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in cabecalho)+'</tr>' for r in setores)+'</table>'
        doc=doc.replace('</html>',tabela_setor+'</html>')
        (saida/'relatorio_temporal.html').write_text(doc,encoding='utf-8')
        rel.update(status='EDA_TEMPORAL_CONCLUIDA_COM_LIMITACOES',entrada={'base_run_id':m['run_id'],'manifesto_base_sha256':mh,'silver_run_id':sm['run_id'],'conclusao_bivariada_sha256':sha(anteriores[0])},saida=str(saida),exportacoes=exports,resumo={'cidades':12,'indicadores_temporais':len(catalogo),'observacoes_series':len(pontos),'variacoes_anuais':len(variacoes),'resumos_cidade_bloco':len(resumos),'perfis_setoriais_historicos':len(setores),'variacoes_com_valor_ausente':sum(r['status']=='VALOR_AUSENTE' for r in variacoes),'pendencias_fontes':len(pendencias),'alertas_variacoes_pib':len(alertas),'variacoes_com_conferencia_pendente':sum(r['status_conferencia']=='CONFERENCIA_PENDENTE' for r in variacoes)},metodos={'acumulado':'(final / inicial - 1) * 100; null se inicial zero','anualizado':'((final / inicial) ** (1 / intervalo_anos) - 1) * 100; inicial>0 e final>=0','setores':'Participacao final menos inicial, em pontos percentuais; periodos efetivamente disponiveis'},limites=limites,fim_utc=datetime.now(timezone.utc).isoformat());gravar(saida/'manifesto_eda_temporal.json',rel);return rel
    except Exception as e:rel.update(status='FALHA',erro=str(e));raise
    finally:
        rel['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_14_eda_temporal.json',rel);(q/'execucao.log').write_text('\n'.join(r['resultado']+' '+r['regra'] for r in rel['regras'])+'\n'+rel['status']+'\n'+rel.get('erro',''),encoding='utf-8')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent);ap.add_argument('--base',type=Path);a=ap.parse_args();run=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8];print(json.dumps(executar(a.raiz,run,a.base),ensure_ascii=False,indent=2))
