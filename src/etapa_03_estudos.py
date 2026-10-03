"""Extracao Bronze dos estudos; tabelas detectadas exigem validacao semantica."""
import hashlib
import html
import json
import pdfplumber
from tabular_estudos import tabular


# Recortes normalizados (x0, y0, x1, y1), conferidos no layout das fontes.
PERFIS = {
 '8da8c016ceece3a20ba576d72e5ec1074b7c1bc0a51246ba314bd59fa7c20590': [(5, '1', (.07,.13,.95,.86)), (6,'2',(.07,.13,.95,.485)), (6,'3',(.07,.62,.95,.995)), (7,'4',(.07,.13,.95,.48)), (7,'5',(.07,.62,.95,.995))],
 '32f193e0096844b87c383ffb4bdbcfeadb9b1f968efcf92e40b636d8452c3d6b': [(4,'1',(.08,.49,.92,.98)), (5,'1_continuacao',(.08,.08,.92,.485)), (5,'2',(.08,.69,.92,.98)), (6,'2_continuacao',(.08,.08,.92,.485)), (7,'3',(.08,.22,.92,.98))],
 'be0580b26c38c07ad7e326d9fd0cea9182be9a21b2198f549d5b38a174754a76': [(14,'1',(.10,.21,.93,.55))]
}

def executar(raiz, run_id):
    landing = raiz / 'datalake/00_landing'
    fontes = sorted(p for p in landing.glob('*.pdf') if p.name != 'TABELA DE PREÇOS DOS PRODUTOS.pdf')
    if not fontes:
        raise ValueError('Nenhum PDF de estudo encontrado')
    saida = raiz / 'datalake/01_bronze' / run_id / 'estudos'
    quality = raiz / 'quality/03_estudos' / run_id
    saida.mkdir(parents=True, exist_ok=False)
    quality.mkdir(parents=True, exist_ok=False)
    resumo = []
    erros = []
    for fonte in fontes:
        sha = hashlib.sha256(fonte.read_bytes()).hexdigest()
        pasta = saida / sha[:16]
        pasta.mkdir(exist_ok=False)
        paginas, celulas, tabelas = [], [], []
        try:
            with pdfplumber.open(fonte) as pdf:
                for numero, pagina in enumerate(pdf.pages, 1):
                    texto = pagina.extract_text() or ''
                    paginas.append({'arquivo_origem': fonte.relative_to(raiz).as_posix(), 'source_sha256': sha, 'pagina': numero, 'texto_original': texto, 'status': 'EXTRAIDO' if texto.strip() else 'OCR_NECESSARIO'})
                    if sha not in PERFIS:
                        raise ValueError('PDF sem perfil de layout validado; nao aplicar recorte de outra fonte')
                    for numero_alvo, tabela_id, bbox in PERFIS[sha]:
                        if numero_alvo != numero:
                            continue
                        recorte = pagina.crop((bbox[0]*pagina.width,bbox[1]*pagina.height,bbox[2]*pagina.width,bbox[3]*pagina.height))
                        recorte = recorte.filter(lambda obj: obj.get('object_type') != 'char' or obj.get('upright', True))
                        texto_tabela = recorte.extract_text(layout=False) or ''
                        linhas = texto_tabela.splitlines()
                        marcadores_fim = ('DISCUSSÃO', 'da capital e com menos', 'Do total dos entrevistados,')
                        for j, l in enumerate(linhas):
                            if l.startswith(marcadores_fim):
                                linhas = linhas[:j]
                                break
                        tabelas.append({'pagina': numero, 'tabela': tabela_id, 'bbox_normalizado': bbox, 'linhas': [[l] for l in linhas], 'metodo': 'recorte_layout_texto', 'interpretacao_colunas': 'PENDENTE'})
                        for linha, valor in enumerate(linhas,1):
                            celulas.append({'arquivo_origem': fonte.relative_to(raiz).as_posix(), 'source_sha256': sha, 'pagina': numero, 'tabela': tabela_id, 'linha': linha, 'coluna': 1, 'valor_original': valor, 'validacao': 'PENDENTE_CONFERENCIA'})
            for nome, dados in [('texto_paginas.json', paginas), ('celulas_tabelas.json', celulas), ('tabelas_detectadas.json', tabelas)]:
                (pasta / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
            estruturadas = tabular(tabelas, sha, fonte.relative_to(raiz).as_posix())
            for nome, dados in estruturadas.items():
                (pasta / (nome + '.json')).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
            doc = '<!doctype html><meta charset="utf-8"><title>Conferencia de estudos</title><style>table{border-collapse:collapse}td{border:1px solid #aaa;padding:5px}pre{white-space:pre-wrap}</style><h1>'+html.escape(fonte.name)+'</h1><p>Tabelas candidatas. Ausencia de tabelas detectadas nao significa ausencia de dados no PDF.</p>'
            for t in tabelas:
                doc += f"<h2>Pagina {t['pagina']} — tabela {t['tabela']}</h2><table>"
                doc += ''.join('<tr>'+''.join('<td>'+html.escape(v or '')+'</td>' for v in linha)+'</tr>' for linha in t['linhas'])+'</table>'
            for nome, dados in estruturadas.items():
                doc += '<h2>'+html.escape(nome)+'</h2>'
                if dados:
                    cols=list(dict.fromkeys(k for r in dados for k in r))
                    doc += '<table><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in cols)+'</tr>'
                    doc += ''.join('<tr>'+''.join('<td>'+html.escape(str(r.get(c,'')))+'</td>' for c in cols)+'</tr>' for r in dados)+'</table>'
            for p in paginas:
                doc += f"<details><summary>Texto da pagina {p['pagina']}</summary><pre>"+html.escape(p['texto_original'])+'</pre></details>'
            (pasta / 'conferencia_estudo.html').write_text(doc, encoding='utf-8')
            resumo.append({'arquivo': fonte.name, 'source_sha256': sha, 'paginas': len(paginas), 'segmentos_tabelas_recortados': len(tabelas), 'tabelas_logicas': len({t['tabela'].split('_')[0] for t in tabelas}), 'linhas_extraidas': len(celulas), 'tabelas_estruturadas': {k: len(v) for k,v in estruturadas.items()}, 'paginas_sem_texto': [p['pagina'] for p in paginas if p['status'] == 'OCR_NECESSARIO'], 'saida': pasta.relative_to(raiz).as_posix()})
        except Exception as e:
            erros.append({'arquivo': fonte.name, 'erro': str(e)})
    resultado = {'etapa': '03_estudos', 'status': 'FALHA' if erros else 'EXTRAIDO_PENDENTE_CONFERENCIA', 'fontes': resumo, 'erros': erros, 'observacao': 'Recortes por layout substituem a deteccao automatica anterior. Colunas estruturadas e contagens esperadas verificadas. Conferencia visual final e aplicabilidade comercial pendentes. Valores publicados preservados; alertas da fonte separados.'}
    (quality / 'conclusao_03_estudos.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    if erros:
        raise RuntimeError('Falha na extracao dos estudos; consultar conclusao')
    return resultado
