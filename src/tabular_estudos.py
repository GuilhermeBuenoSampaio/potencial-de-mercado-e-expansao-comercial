"""Conversores por layout conhecido; valores publicados sempre preservados."""
import re
from decimal import Decimal

NUM = r'\d+(?:,\d+)?'
REGIOES = ['Brasil', 'Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
GRUPOS = ['Bebidas alcoólicas','Refrigerantes','Biscoitos','Frutas','Doces','Leite e derivados','Refeições','Fast foods','Salgados fritos e assados']
CURSOS = ['Enfermagem','Nutrição','Fisioterapia','Total']


def decimal(s):
    return float(Decimal(s.replace(',', '.')))


def base(sha, arquivo, t, texto):
    return {'source_sha256': sha, 'arquivo_origem': arquivo, 'pagina': t['pagina'], 'tabela': t['tabela'].split('_')[0], 'texto_original': texto, 'validacao': 'ESTRUTURADO_PENDENTE_CONFERENCIA'}


def nacional(tabelas, sha, arquivo):
    dados, testes = [], []
    campos = {'2':REGIOES, '3':['Até ½ salário','½–2 salários','2–5 salários','5 salários ou mais'], '4':['Homem','Mulher','Urbano','Rural'], '5':['10–19','20–29','30–39','40–49','50–59','60 ou mais']}
    for t in tabelas:
        linhas = [r[0] for r in t['linhas']]
        if t['tabela'] != '1':
            grupos_extraidos = 0
            for i, linha in enumerate(linhas):
                v = re.fullmatch(r'\s*(' + NUM + r'(?:\s+' + NUM + r')+)\s*',linha)
                if not v or i+2 >= len(linhas): continue
                valores = linha.split()
                ic = re.findall(r'\((' + NUM + r');(' + NUM + r')\)',linhas[i+2])
                if not ic: continue
                colunas = campos[t['tabela']]
                if len(valores)!=len(colunas) or len(ic)!=len(colunas): raise ValueError('Numero de colunas incompatível com o cabeçalho')
                grupo = linhas[i+1].strip()
                if grupo != GRUPOS[grupos_extraidos]: raise ValueError('Nome de alimento inesperado: '+grupo)
                for col, valor, limites in zip(colunas,valores,ic):
                    r = base(sha,arquivo,t,' | '.join(linhas[i:i+3]))
                    r.update(grupo_alimento=grupo, dimensao=({'2':'regiao','3':'renda_per_capita_salarios_minimos','4':('sexo' if col in ['Homem','Mulher'] else 'situacao_domicilio'),'5':'idade_anos'}[t['tabela']]), estrato=col, percentual=decimal(valor), percentual_original=valor, ic95_inferior=decimal(limites[0]), ic95_superior=decimal(limites[1]), periodo_referencia='2002–2003', abrangencia='Brasil', indicador='Prevalencia de consumo fora do domicilio referido em uma semana')
                    dados.append(r)
                grupos_extraidos += 1
            if grupos_extraidos!=9: raise ValueError(f"Tabela {t['tabela']}: esperado 9 grupos; obtido {grupos_extraidos}")
        else:
            dimensao = None
            grupos = {'Faixa etária (anos)','Sexo','Nível de escolaridade','Renda mensal familiar per capita (em salários mínimos)','Moradores por domicílios','Situação do domicílio','Município de localização do domicílio'}
            for i, linha in enumerate(linhas):
                if linha in grupos: dimensao=linha; continue
                if linha.startswith('p '):
                    vs=re.findall(r'<?\d+,\d+',linha)
                    if len(vs)==6:
                        for col,v in zip(REGIOES,vs):
                            r=base(sha,arquivo,t,linha);r.update(dimensao=dimensao,regiao=col,p_valor_original=v);testes.append(r)
                    continue
                m=re.fullmatch(r'(.*?)\s*((?:\d+,\d+\s+){5}\d+,\d+)',linha)
                if not m or not dimensao:continue
                label=m[1].strip()
                if not label and i>0 and 'Superior incompleto' in linhas[i-1]:label='Superior incompleto, completo e pós-graduação'
                if not label:raise ValueError('Estrato sem rotulo')
                for col,v in zip(REGIOES,m[2].split()):
                    r=base(sha,arquivo,t,linha);r.update(dimensao=dimensao,estrato=label,regiao=col,percentual=decimal(v),percentual_original=v,periodo_referencia='2002–2003',indicador='Prevalencia de consumo fora do domicilio referido em uma semana');dados.append(r)
    if len(dados)!=312:raise ValueError(f'Estudo nacional: esperado 312 observacoes; obtido {len(dados)}')
    return {'indicadores_consumo':dados,'testes_publicados':testes}


def universitarios(tabelas,sha,arquivo):
    dados, testes, alertas = [], [], []
    cabecalhos = {'Sexo','Faixa etária','Residente em Goiânia','Estado Civil','Moradores por domicílios','Trabalha fora','Renda mensal familiar (em salários mínimos)'}
    freq2=['4–7 vezes/semana','1–3 vezes/semana','1–3 vezes/mes','Menos de 3 vezes/mes','Nunca']
    freq3=['1 vez ou mais/dia','4–6 vezes/semana','1–3 vezes/semana','1–4 vezes/mes','Menos de 4 vezes/mes','Nunca']
    for t in tabelas:
        idt=t['tabela'].split('_')[0];contador=0;dimensao=None
        for linha0 in t['linhas']:
            linha=linha0[0]
            if idt=='1' and linha in cabecalhos:dimensao=linha;continue
            if idt=='1' and re.fullmatch(r'\d+,\d+[ab]',linha):
                r=base(sha,arquivo,t,linha);r.update(dimensao=dimensao,p_valor_original=linha);testes.append(r);continue
            if idt=='1':
                # Oito numeros: n e percentual para cada curso e total.
                m=re.fullmatch(r'(.*?)\s+((?:'+NUM+r'\s+){7}'+NUM+r')(?:\s+(\d+,\d+[ab]))?',linha)
                if not m or not dimensao:continue
                label=m[1];vals=m[2].split()
                for j,curso in enumerate(CURSOS):
                    n=int(vals[2*j]);pct=decimal(vals[2*j+1]);r=base(sha,arquivo,t,linha)
                    r.update(dimensao=dimensao,estrato=label,curso=curso,n=n,percentual=pct,percentual_original=vals[2*j+1],p_valor_linha_original=m[3],periodo_referencia='2011',abrangencia='Instituicao privada de Goiania')
                    dados.append(r)
                contador+=1
            else:
                quantidade=10 if idt=='2' else 12
                m=re.fullmatch(r'(.*?)\s+((?:'+NUM+r'\s+){'+str(quantidade-1)+'}'+NUM+r')',linha)
                if not m:continue
                label=m[1];vals=m[2].split()
                if idt=='2':curso='Enfermagem' if t['pagina']==5 else ['Nutrição','Fisioterapia'][contador//6];freq=freq2;den={'Enfermagem':40,'Nutrição':35,'Fisioterapia':26}[curso]
                else:curso=CURSOS[contador//8];freq=freq3;den={'Enfermagem':37,'Nutrição':34,'Fisioterapia':24}[curso]
                soma_n=0
                for j,frequencia in enumerate(freq):
                    n=int(vals[2*j]);pct=decimal(vals[2*j+1]);soma_n+=n
                    r=base(sha,arquivo,t,linha);r.update(grupo=label,curso=curso,frequencia=frequencia,n=n,denominador_publicado=den,percentual=pct,percentual_original=vals[2*j+1],periodo_referencia='2011',abrangencia='Instituicao privada de Goiania')
                    dados.append(r)
                    if abs(n/den*100-pct)>0.11:
                        alertas.append({'pagina':t['pagina'],'tabela':idt,'curso':curso,'grupo':label,'frequencia':frequencia,'n':n,'percentual_publicado':pct,'percentual_conferencia':round(n/den*100,4),'acao':'PRESERVAR_FONTE; INVESTIGAR'})
                if soma_n!=den:alertas.append({'pagina':t['pagina'],'tabela':idt,'curso':curso,'grupo':label,'soma_n':soma_n,'denominador':den,'acao':'PRESERVAR_FONTE; INVESTIGAR'})
                contador+=1
        esperado={'1':10,'1_continuacao':9,'2':6,'2_continuacao':12,'3':24}[t['tabela']]
        if contador!=esperado:raise ValueError(f"Universitarios {t['tabela']}: esperado {esperado} linhas; obtido {contador}")
    return {'indicadores_universitarios':dados,'testes_publicados':testes,'alertas_fonte':alertas}


def regionais(tabelas,sha,arquivo):
    dados,ajustes=[],[]
    for t in tabelas:
        regiao=None;coef=None
        for linha0 in t['linhas']:
            linha=linha0[0]
            if 'N° de observações:' in linha:
                regiao=linha.split('N°')[0].strip();n=int(linha.split(':')[-1].strip().replace('.',''));continue
            if linha.startswith('Coeficiente'):
                coef=re.findall(r'-?\d+,\d+\*{0,2}',linha)[:4];continue
            if linha.startswith('P-valor'):
                ps=re.findall(r'\d+,\d+\*{0,2}',linha)
                if not regiao or not coef or len(coef)!=4 or len(ps)!=7:raise ValueError('Modelo regional incompleto')
                for variavel,c,p in zip(['Constante','LogRendaTot','D_urbana','D_urbana_x_LogRendaTot'],coef,ps[:4]):
                    r=base(sha,arquivo,t,linha);r.update(regiao=regiao,n_observacoes=n,variavel=variavel,coeficiente=decimal(c.rstrip('*')),coeficiente_original=c,p_valor_original=p,base_referencia='IBGE 2019, conforme fonte do artigo',ano_publicacao=2024);dados.append(r)
                ajustes.append(dict(base(sha,arquivo,t,linha),regiao=regiao,n_observacoes=n,r_quadrado=decimal(ps[4]),estatistica_f=decimal(ps[5]),prob_f_original=ps[6]))
    if len(dados)!=20:raise ValueError(f'Esperado 20 coeficientes; obtido {len(dados)}')
    return {'coeficientes_modelo':dados,'ajuste_modelo':ajustes}


def tabular(tabelas,sha,arquivo):
    if sha.startswith('8da8'):return nacional(tabelas,sha,arquivo)
    if sha.startswith('32f1'):return universitarios(tabelas,sha,arquivo)
    if sha.startswith('be05'):return regionais(tabelas,sha,arquivo)
    raise ValueError('Fonte desconhecida')
