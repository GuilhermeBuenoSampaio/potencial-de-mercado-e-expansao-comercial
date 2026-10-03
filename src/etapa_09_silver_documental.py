"""Silver documental de precos, estudos PDF e evidencias JPEG; sem previsoes."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import html
import json
import logging
from pathlib import Path
from uuid import uuid4
from etapa_06_coleta_municipal import PROJETO


def ler(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def hash_arquivo(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalizar(v):
    if isinstance(v,Decimal):return str(v)
    if isinstance(v,list):return [normalizar(x) for x in v]
    if isinstance(v,dict):return {k:normalizar(x) for k,x in v.items()}
    return v

def gravar(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(normalizar(d),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

IDENTIDADE=['source_sha256','pagina','tabela','dimensao','estrato','regiao','grupo_alimento','grupo','curso','frequencia','variavel','indicador']
def identidade(r):
    base={k:r.get(k) for k in IDENTIDADE}
    return hashlib.sha256(json.dumps(base,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def executar(raiz,run_id,bronze_run_id=None):
    import pyarrow as pa
    import pyarrow.parquet as pq
    raiz=Path(raiz).resolve();q=raiz/'quality'/'09_silver_documental'/run_id
    q.mkdir(parents=True,exist_ok=False)
    logger=logging.getLogger('documental_'+run_id);logger.setLevel(logging.INFO)
    h=logging.FileHandler(q/'execucao.log',encoding='utf-8');logger.addHandler(h)
    resumo={'projeto':PROJETO,'run_id':run_id,'inicio_utc':datetime.now(timezone.utc).isoformat(),'status':'EM_EXECUCAO'}
    try:
        if bronze_run_id is None:
            candidatos=[]
            for p in sorted((raiz/'datalake'/'01_bronze').glob('*')):
                if all((p/n).is_dir() for n in ['precos_produtos','estudos','imagens']) and all((raiz/'quality'/e/p.name/f).exists() for e,f in [('02_precos','conclusao_02_precos.json'),('03_estudos','conclusao_03_estudos.json'),('04_imagens','conclusao_04_imagens.json')]):candidatos.append(p)
            if not candidatos:raise FileNotFoundError('Nenhuma execucao com etapas 02, 03 e 04 completas na mesma Bronze; executar pipeline local')
            bronze_run_id=candidatos[-1].name
        b=raiz/'datalake'/'01_bronze'/bronze_run_id
        c2=ler(raiz/'quality'/'02_precos'/bronze_run_id/'conclusao_02_precos.json')
        c3=ler(raiz/'quality'/'03_estudos'/bronze_run_id/'conclusao_03_estudos.json')
        c4=ler(raiz/'quality'/'04_imagens'/bronze_run_id/'conclusao_04_imagens.json')
        if c2.get('pendencias_extracao') or any('FALHA' in str(c.get('status','')) for c in [c2,c3,c4]):raise ValueError('Extracao documental com falha; revisar etapas 02–04')
        entradas=[];fontes={};tabelas={};pendencias=[]
        def fonte(r,imagem=False):
            campo='arquivo_imagem' if imagem else 'arquivo_origem';campo_sha='imagem_sha256' if imagem else 'source_sha256'
            arquivo=r[campo];digest=r[campo_sha]
            if digest not in fontes:
                p=raiz/arquivo
                if not p.is_file() or hash_arquivo(p)!=digest:raise ValueError('Fonte ausente ou hash divergente: '+arquivo)
                fontes[digest]={'source_sha256':digest,'arquivo_origem':arquivo,'tipo':'JPEG' if imagem else 'PDF','hash_fisico_verificado':True}
            return digest
        def carregar(p):
            dados=ler(p);entradas.append({'arquivo':str(p.relative_to(raiz)),'sha256':hash_arquivo(p),'registros':len(dados) if isinstance(dados,list) else 1});return dados
        precos=carregar(b/'precos_produtos'/'precos_produtos.json')
        if len(precos)!=c2['registros_produto_estado']:raise ValueError('Contagem dos precos difere da etapa 02')
        for i,r in enumerate(precos):
            fonte(r)
            if r['source_sha256']!=c2['source_sha256']:raise ValueError('Preco associado a fonte diferente da etapa 02')
            r['registro_id']=r['source_sha256']+':preco:'+str(r['pagina'])+':'+str(r['linha'])+':'+r['estado']
            r['preco_pacote_original']=r['preco_pacote_brl'];r['preco_unidade_original']=r.get('preco_unidade_brl')
            if r['preco_pacote_brl'] is None:raise ValueError('Preco do pacote ausente')
            for campo in ['preco_pacote_brl','preco_unidade_brl']:
                if r.get(campo) is not None:
                    d=Decimal(str(r[campo]))
                    if not d.is_finite() or d<=0 or d.as_tuple().exponent < -4:raise ValueError('Preco invalido ou precisao nao suportada')
                    r[campo]=d.quantize(Decimal('0.0001'))
            r.update(unidade_monetaria='BRL',vigencia_confirmada=False,uso_proposto='REFERENCIA_COMERCIAL_PENDENTE_CONFERENCIA',liberado_orcamento_atual=False)
        tabelas['precos_produtos']=precos
        pendencias.append({'tipo':'VIGENCIA_PRECOS','fonte':c2['source_sha256'],'detalhe':'Vigencia e conferencia comercial pendentes; nao usar automaticamente como orcamento atual'})
        tipos={'indicadores_consumo':'consumo_historico','indicadores_universitarios':'universitarios_historico','coeficientes_modelo':'coeficientes_publicados','ajuste_modelo':'ajustes_publicados','testes_publicados':'testes_publicados'}
        alertas_univ=[]
        for meta in c3['fontes']:
            pasta=b/'estudos'/meta['source_sha256'][:16]
            if (pasta/'alertas_fonte.json').exists():alertas_univ.extend(carregar(pasta/'alertas_fonte.json'))
            for nome,n in meta['tabelas_estruturadas'].items():
                if nome=='alertas_fonte':
                    if len(ler(pasta/'alertas_fonte.json'))!=n:raise ValueError('Contagem dos alertas difere da etapa 03')
                    continue
                if nome not in tipos:raise ValueError('Tabela de estudo nao prevista: '+nome)
                rows=carregar(pasta/(nome+'.json'))
                if len(rows)!=n:raise ValueError('Contagem do estudo difere da etapa 03')
                destino=tipos[nome]
                for i,r in enumerate(rows):
                    fonte(r)
                    if r['source_sha256']!=meta['source_sha256']:raise ValueError('Registro associado ao estudo errado')
                    r['registro_id']=r['source_sha256']+':'+nome+':'+str(i+1)
                    r['uso_proposto']='CONTEXTO_HISTORICO_PUBLICADO';r['uso_previsao_vendas_atual']=False
                    if r.get('percentual') is not None and not 0<=r['percentual']<=100:raise ValueError('Percentual fora de 0–100')
                    if nome=='coeficientes_modelo':r['limitacao_modelo']='Modelo publicado; nao tratar coeficiente de renda como elasticidade-preco ou parametro causal municipal'
                    if nome=='ajuste_modelo' and not 0<=r['r_quadrado']<=1:raise ValueError('R quadrado fora de 0–1')
                tabelas.setdefault(destino,[]).extend(rows)
        consumo=tabelas['consumo_historico'];mapa={identidade(r):r for r in consumo}
        if len(mapa)!=len(consumo):raise ValueError('Identidade semantica duplicada no consumo PDF')
        imagens=[];vinculos=[]
        for meta in c4['fontes']:
            p=b/'imagens'/meta['imagem_sha256'][:16]
            rows=carregar(p/'indicadores_imagem.json');vinculo=carregar(p/'vinculo_fonte.json');vinculos.append(vinculo)
            if len(rows)!=meta['percentuais_comparados']:raise ValueError('Contagem da imagem difere da etapa 04')
            for i,r in enumerate(rows):
                fonte(r,True);fonte(r)
                pdf=mapa.get(identidade(r))
                if pdf is None:raise ValueError('Imagem sem observacao PDF equivalente')
                if r['percentual_pdf']!=pdf['percentual']:raise ValueError('Valor PDF na imagem difere da observacao canonica')
                divergencia=r['percentual_imagem']!=r['percentual_pdf']
                if divergencia!=r['divergencia_pdf_imagem']:raise ValueError('Flag de divergencia inconsistente')
                if not r['duplicidade_semantica'] or r['incluir_como_nova_observacao']:raise ValueError('Imagem repetida indevidamente habilitada como nova observacao')
                r['registro_id']=r['imagem_sha256']+':imagem:'+str(i+1);r['registro_pdf_id']=pdf['registro_id']
                r['uso_proposto']='EVIDENCIA_COMPLEMENTAR';r['incluir_como_nova_observacao']=False
                imagens.append(r)
                if divergencia:
                    pdf['divergencia_pdf_imagem_pendente']=True;pdf['uso_proposto']='REFERENCIA_COM_DIVERGENCIA_PENDENTE'
                    pendencias.append({'tipo':'DIVERGENCIA_PDF_JPEG','registro_id':pdf['registro_id'],'evidencia_id':r['registro_id'],
                      'detalhe':json.dumps({k:r.get(k) for k in ['grupo_alimento','estrato','percentual_pdf','percentual_imagem']},ensure_ascii=False)})
            if sum(r['divergencia_pdf_imagem'] for r in rows)!=meta['divergencias_pdf_imagem']:raise ValueError('Divergencias da imagem diferem da etapa 04')
        for r in consumo:r.setdefault('divergencia_pdf_imagem_pendente',False)
        universidade=tabelas['universitarios_historico']
        for r in universidade:
            matches=[a for a in alertas_univ if all(str(r.get(k))==str(a.get(k)) for k in ['pagina','tabela','curso','grupo','frequencia'])]
            r['inconsistencia_publicada_pendente']=bool(matches)
            if matches:r['uso_proposto']='REFERENCIA_COM_INCONSISTENCIA_PENDENTE'
            for a in matches:pendencias.append({'tipo':'INCONSISTENCIA_N_PERCENTUAL','registro_id':r['registro_id'],'detalhe':json.dumps(a,ensure_ascii=False)})
        if sum(r['inconsistencia_publicada_pendente'] for r in universidade)!=len(alertas_univ):raise ValueError('Alertas universitarios nao vinculados de forma univoca')
        tabelas['evidencias_imagens']=imagens;tabelas['fontes_documentais']=list(fontes.values());tabelas['pendencias_documentais']=pendencias
        dicionario=[];manifesto=[]
        out=raiz/'datalake'/'02_silver'/run_id/'documental';out.mkdir(parents=True,exist_ok=False)
        for nome,rows in tabelas.items():
            if not rows:raise ValueError('Tabela documental vazia: '+nome)
            campos=sorted(set().union(*(r.keys() for r in rows)))
            if rows[0].get('registro_id') is not None and len({r['registro_id'] for r in rows})!=len(rows):raise ValueError('Registro duplicado: '+nome)
            schema_campos=[]
            for campo in campos:
                valores=[r[campo] for r in rows if r.get(campo) is not None]
                if valores and all(isinstance(x,Decimal) for x in valores):tipo=pa.decimal128(18,4)
                elif valores and all(isinstance(x,bool) for x in valores):tipo=pa.bool_()
                elif valores and all(isinstance(x,int) and not isinstance(x,bool) for x in valores):tipo=pa.int64()
                elif valores and all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in valores):tipo=pa.float64()
                else:tipo=pa.string()
                schema_campos.append((campo,tipo));dicionario.append({'tabela':nome,'campo':campo,'tipo_parquet':str(tipo),'aceita_nulo':any(r.get(campo) is None for r in rows),
                  'definicao':'Campo publicado preservado' if campo not in ['registro_id','uso_proposto'] else 'Identificador rastreavel ou restricao de uso documental',
                  'unidade':'BRL' if campo.startswith('preco_') else '%' if campo.startswith(('percentual','ic95')) else None})
            schema=pa.schema(schema_campos)
            flat=[{c:r.get(c) for c in campos} for r in rows]
            jp=out/(nome+'.json');pp=out/(nome+'.parquet')
            gravar(jp,flat);pq.write_table(pa.Table.from_pylist(flat,schema=schema),pp,compression='snappy')
            if normalizar(pq.read_table(pp).to_pylist())!=ler(jp):raise ValueError('Reconciliacao JSON x Parquet falhou: '+nome)
            manifesto.append({'tabela':nome,'linhas':len(rows),'sha256_json':hash_arquivo(jp),'sha256_parquet':hash_arquivo(pp),'reconciliacao':'APROVADA'})
            logger.info('Exportada e reconciliada: %s, %s linhas',nome,len(rows))
        gravar(out/'dicionario_documental.json',dicionario)
        pq.write_table(pa.Table.from_pylist(dicionario),out/'dicionario_documental.parquet',compression='snappy')
        if normalizar(pq.read_table(out/'dicionario_documental.parquet').to_pylist())!=ler(out/'dicionario_documental.json'):raise ValueError('Dicionario nao reconciliado')
        resumo.update({'status':'SILVER_DOCUMENTAL_GERADA_COM_PENDENCIAS','bronze_run_id':bronze_run_id,'saida':str(out),'exportacoes':manifesto,
          'dicionario_campos':len(dicionario),'fontes_fisicas_verificadas':len(fontes),'entradas':entradas,'pendencias':dict(Counter(r['tipo'] for r in pendencias)),
          'observacoes_imagens_adicionais':0,'limites':['Extracao tabular nao e aprovacao comercial ou estatistica','Vigencia dos precos pendente; preco unitario publicado nao e custo fabril',
          'PDF e JPEG divergentes preservados sem resolucao automatica','Estudos publicados descrevem suas populacoes e periodos; nao estimam automaticamente demanda municipal atual',
          'P-valores e notas preservados; valor arredondado 0,000 nao tratado como probabilidade exatamente zero','Silver municipal permanece separada; comparacao original somente no encerramento']})
        gravar(out/'manifesto_documental.json',resumo)
        linhas=''.join('<tr><td>'+html.escape(x['tabela'])+'</td><td>'+str(x['linhas'])+'</td><td>'+x['reconciliacao']+'</td></tr>' for x in manifesto)
        notas=''.join('<li>'+html.escape(x['tipo']+': '+x['detalhe'])+'</li>' for x in pendencias)
        (out/'conferencia_documental.html').write_text('<!doctype html><meta charset="utf-8"><title>Silver documental</title><style>body{font:15px Arial;margin:24px}td,th{padding:8px;border:1px solid #ddd}table{border-collapse:collapse}</style><h1>'+PROJETO+'</h1><p>'+resumo['status']+'</p><table><tr><th>Tabela</th><th>Linhas</th><th>Reconciliacao</th></tr>'+linhas+'</table><h2>Pendencias preservadas</h2><ul>'+notas+'</ul>',encoding='utf-8')
        return resumo
    except Exception as e:resumo.update(status='FALHA',erro=str(e));logger.exception('Silver documental interrompida');raise
    finally:
        resumo['fim_utc']=datetime.now(timezone.utc).isoformat();gravar(q/'conclusao_09_silver_documental.json',resumo);h.close();logger.removeHandler(h)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--bronze-run-id',help='Execucao conjunta das etapas 02–04; padrao: ultima completa')
    a=p.parse_args();rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8]
    r=executar(a.raiz,rid,a.bronze_run_id);print(json.dumps({k:r[k] for k in ['run_id','status','saida','fontes_fisicas_verificadas','pendencias']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
