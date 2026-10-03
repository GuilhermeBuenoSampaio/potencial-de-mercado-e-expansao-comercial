"""Valida a coleta municipal local sem consultar rede ou comparar a analise antiga."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
from uuid import uuid4
from etapa_06_coleta_municipal import POLITICA, distancia, gravar, PROJETO


def identidade(o, com_ano=True):
    k=(o['codigo_ibge'],o['tabela'],o['variavel_id'],json.dumps(o['classificacoes'],sort_keys=True,ensure_ascii=False))
    return k+(o['ano_referencia'],) if com_ano else k


def categoria(o,cid):
    for c in o['classificacoes']:
        if str(c['id'])==cid:return next(iter(c['categoria']))
    return None


def executar(raiz,run_id,coleta=None):
    raiz=Path(raiz).resolve()
    if coleta is None:
        candidatos=sorted((raiz/'datalake'/'01_bronze').glob('*/coleta_municipal'))
        if not candidatos:raise FileNotFoundError('Nenhuma coleta municipal em datalake/01_bronze')
        coleta=candidatos[-1]
    coleta=Path(coleta).resolve()
    dest=raiz/'quality'/'07_validacao_municipal'/run_id
    dest.mkdir(parents=True,exist_ok=False)
    nomes=['indicadores_municipais','indicadores_ultimo_disponivel','municipios_geografia','distancias_geodesicas','indices_recalculados']
    dados={};entradas=[];checks=[]
    for nome in nomes:
        f=coleta/(nome+'.json');raw=f.read_bytes();dados[nome]=json.loads(raw)
        entradas.append({'arquivo':str(f),'sha256':hashlib.sha256(raw).hexdigest()})
    def check(codigo,ok,detalhe):
        checks.append({'regra':codigo,'status':'APROVADO' if ok else 'REPROVADO','detalhe':detalhe})
    obs=dados['indicadores_municipais']; latest=dados['indicadores_ultimo_disponivel'];geo=dados['municipios_geografia']
    alvos={m['codigo_ibge'] for m in geo if m['alvo']};numericos=[o for o in obs if o['valor'] is not None]
    check('M01',len(alvos)==12 and all(o['codigo_ibge'] in alvos for o in obs),'12 municipios alvo e nenhum territorio inesperado')
    chaves=Counter(identidade(o) for o in obs)
    check('M02',all(n==1 for n in chaves.values()),'Chave: municipio, tabela, variavel, classificacoes e ano')
    check('M03',all(isinstance(o['valor'],(int,float)) and math.isfinite(o['valor']) and o['valor']>=0 for o in numericos),'Valores numericos finitos e nao negativos nesta selecao de indicadores')
    check('M04',all(o['valor']<=100 for o in numericos if o['unidade'] in ('%','Percentual')),'Percentuais na escala 0 a 100')
    check('M05',all(o['multiplicador']==1000 and o['unidade']=='R$' and math.isclose(o['valor'],float(o['valor_original'])*1000,rel_tol=1e-12) for o in numericos if o['unidade_original'].lower()=='mil reais'),'Conversao de mil reais para reais')
    check('M06',all(o['status_valor']=='MARCADOR_PRESERVADO' for o in obs if o['valor'] is None),'Marcadores nao convertidos em zero')
    esperados={}
    for o in numericos:
        k=identidade(o,False)
        if k not in esperados or o['ano_referencia']>esperados[k]['ano_referencia']:esperados[k]=o
    check('M07',len(latest)==len(esperados) and len(set(identidade(o,False) for o in latest))==len(latest) and all(o==esperados.get(identidade(o,False)) for o in latest),'Ultimo valor numerico por municipio, indicador e categoria')
    ano=datetime.now(timezone.utc).year
    check('M08',all(o['defasagem_anos']==ano-o['ano_referencia'] and o['status_atualidade']==('ESTRUTURAL' if o['grupo']=='censo' else 'DENTRO_DO_LIMITE' if ano-o['ano_referencia']<=POLITICA[o['grupo']] else 'DEFASADO') for o in obs),'Politica de atualidade recalculada na data desta validacao')
    fontes_validas=all(o['url'].startswith('https://servicodados.ibge.gov.br/api/') and len(o['sha256'])==64 and o['coleta_utc'] and o['url_metadados'] for o in obs)
    check('M09',fontes_validas,'Presenca de URL oficial, hash, metadados e data de coleta; nao equivale a verificar os arquivos brutos')
    renda=[]
    for codigo in sorted(alvos):
        partes=[o for o in latest if o['codigo_ibge']==codigo and o['tabela']=='10296' and o['variavel_id']=='1013604' and categoria(o,'386')!='9680']
        soma=sum(o['valor'] for o in partes)
        renda.append({'codigo_ibge':codigo,'categorias_numericas':len(partes),'soma_percentual':soma,'tolerancia_pp':0.06})
        if len(partes)!=11:
            checks.append({'regra':'R01_'+codigo,'status':'INCONCLUSIVO','detalhe':'Faixas com marcadores sem valor numerico. Preservar e verificar significado na fonte; nao imputar zero.'})
        else:
            check('R01_'+codigo,abs(soma-100)<=0.06,'Soma das 11 faixas exclusivas, incluindo sem rendimento; tolerancia de arredondamento 0,06 p.p.')
    for indice in dados['indices_recalculados']:
        pib={o['ano_referencia']:o['valor'] for o in numericos if o['codigo_ibge']==indice['codigo_ibge'] and o['tabela']=='5938' and o['variavel_id']=='37'}
        inicio=indice['ano_inicial'];fim=indice['ano_final'];ok=False
        if fim-inicio==5 and pib.get(inicio,0)>0 and pib.get(fim,0)>0:
            razao=pib[fim]/pib[inicio]
            ok=math.isclose(indice['acumulado_percentual'],(razao-1)*100,abs_tol=1e-8) and math.isclose(indice['taxa_anualizada_percentual'],(razao**0.2-1)*100,abs_tol=1e-8)
        check('I01_'+indice['codigo_ibge'],ok,'Crescimento nominal acumulado e anualizado, par exato de cinco anos')
    check('I02',len(dados['indices_recalculados'])==12 and {o['codigo_ibge'] for o in dados['indices_recalculados']}==alvos,'Um indice de crescimento por municipio')
    por_id={m['codigo_ibge']:m for m in geo}
    rotas=dados['distancias_geodesicas'];pares={(r['destino_codigo'],r['origem_codigo']) for r in rotas}
    check('G01',len(geo)==17 and len(rotas)==60 and len(pares)==60,'12 destinos por 5 origens municipais')
    for m in geo:
        check('G02_'+m['codigo_ibge'],'latitude' in m and 'longitude' in m and -90<=m.get('latitude',999)<=90 and -180<=m.get('longitude',999)<=180,'Coordenadas validas de centroide municipal')
    ok=True
    for r in rotas:
        try:ok=ok and math.isclose(r['distancia_geodesica_centroides_km'],distancia(por_id[r['destino_codigo']],por_id[r['origem_codigo']]),abs_tol=0.001)
        except (KeyError,ValueError):ok=False
    check('G03',ok,'Distancias geodesicas reconciliadas; nao valida percursos rodoviarios')
    catalogo=[]
    for o in latest:
        uso='CONTEXTO_HISTORICO' if o['status_atualidade']=='DEFASADO' else 'PERFIL_ESTRUTURAL' if o['grupo']=='censo' else 'CANDIDATO_EDA'
        limites=[]
        if o['tabela']=='5938':limites.append('PIB/VAB nao mede vendas de salgados ou renda disponivel')
        if o['tabela']=='pesquisa_38':limites.append('PIB por habitante nao e renda domiciliar mensal')
        if o['tabela'] in ('9509','9528'):limites.append('CEMPRE: postos e organizacoes locais; nao taxa de residentes empregados')
        if o['tabela']=='9528':limites.append('CNAE nao confirma cliente, concorrente ou interesse de compra; respeitar supressao e anos distintos')
        if o['tabela']=='10296':limites.append('Faixas de renda per capita nao equivalem automaticamente a classes familiares A–E')
        if o['grupo']=='censo':limites.append('Referencia censitaria; nao representa nova medicao em 2026')
        catalogo.append({**o,'uso_proposto':uso,'limitacoes_uso':limites})
    reprovados=[c for c in checks if c['status']=='REPROVADO']
    resultado={'projeto':PROJETO,'run_id':run_id,'coleta_entrada':str(coleta),'validacao_utc':datetime.now(timezone.utc).isoformat(),
      'status':'REPROVADO' if reprovados else 'VALIDACAO_TECNICA_APROVADA_COM_LIMITACOES',
      'total_regras':len(checks),'regras_aprovadas':sum(c['status']=='APROVADO' for c in checks),'regras_inconclusivas':sum(c['status']=='INCONCLUSIVO' for c in checks),'regras_reprovadas':len(reprovados),
      'observacoes':len(obs),'ultimos_valores':len(latest),'atualidade':dict(Counter(o['status_atualidade'] for o in latest)),
      'entradas':entradas,'politica':POLITICA,'limites':['Confiabilidade tecnica nao aprova automaticamente uso comercial','Respostas brutas nao incluidas neste pacote: hashes declarados, sem reconciliacao fisica','Rotas rodoviarias e enderecos reais pendentes','Comparacao com projeto original reservada para encerramento','Sem promocao automatica para Silver']}
    gravar(dest/'conclusao_07_validacao_municipal.json',resultado);gravar(dest/'regras_validacao.json',checks)
    gravar(dest/'conferencia_faixas_renda.json',renda);gravar(dest/'catalogo_uso_indicadores.json',catalogo)
    linhas=''.join('<tr><td>'+html.escape(c['regra'])+'</td><td>'+c['status']+'</td><td>'+html.escape(c['detalhe'])+'</td></tr>' for c in checks)
    (dest/'conferencia_validacao.html').write_text('<!doctype html><meta charset="utf-8"><title>Validacao municipal</title><style>body{font:15px Arial;margin:24px}td,th{border:1px solid #ccc;padding:8px}table{border-collapse:collapse}</style><h1>'+PROJETO+'</h1><p>'+resultado['status']+'</p><p>Validacao tecnica dos dados coletados. Uso comercial, rotas rodoviarias e reconciliacao fisica das fontes permanecem sujeitos a conferencia.</p><table><tr><th>Regra</th><th>Status</th><th>Conferencia</th></tr>'+linhas+'</table>',encoding='utf-8')
    return resultado


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--coleta',type=Path,help='Pasta coleta_municipal especifica; padrao: ultima pasta por run_id')
    a=p.parse_args();rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    r=executar(a.raiz,rid,a.coleta);print(json.dumps(r,ensure_ascii=False,indent=2))
    if r['regras_reprovadas']:raise SystemExit(1)
if __name__=='__main__':main()
