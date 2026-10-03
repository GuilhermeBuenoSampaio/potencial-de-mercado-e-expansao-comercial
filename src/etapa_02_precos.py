"""Extrai tabela historica de precos sem alterar ou atualizar valores."""
import hashlib
import html
import json
import re
from decimal import Decimal
import pdfplumber


def executar(raiz, run_id):
    fonte = raiz / 'datalake/00_landing/TABELA DE PREÇOS DOS PRODUTOS.pdf'
    sha = hashlib.sha256(fonte.read_bytes()).hexdigest()
    saida = raiz / 'datalake/01_bronze' / run_id / 'precos_produtos'
    quality = raiz / 'quality/02_precos' / run_id
    saida.mkdir(parents=True, exist_ok=False)
    quality.mkdir(parents=True, exist_ok=False)
    registros, pendencias, linhas_brutas = [], [], []
    categoria, quantidade, kg = None, None, None
    com_preco = 0
    with pdfplumber.open(fonte) as pdf:
        for pagina, folha in enumerate(pdf.pages, 1):
            for linha_num, linha in enumerate((folha.extract_text() or '').splitlines(), 1):
                linhas_brutas.append({'pagina': pagina, 'linha': linha_num, 'texto': linha})
                if 'R$' not in linha:
                    if 'PACOTE COM' in linha or linha.startswith('MINIS -'):
                        categoria = linha.split(' - ')[0] if ' - ' in linha else 'EMPADAS'
                        m = re.search(r'PACOTE COM (\d+) UNIDADES', linha)
                        quantidade = int(m[1]) if m else None
                        kg = 1 if '1KG' in linha else None
                    continue
                com_preco += 1
                descricao = linha.split('R$')[0].strip()
                precos = re.findall(r'R\$\s*([\d.]+,\d{2})', linha)
                if not categoria or len(precos) not in (1, 2, 4):
                    pendencias.append({'pagina': pagina, 'linha': linha_num, 'texto': linha})
                    continue
                qtd = quantidade
                override = re.search(r'PACOTE COM (\d+) UNIDADES', descricao)
                if override:
                    qtd = int(override[1])
                pares = [('CRU', precos[:2]), ('FRITO', precos[2:])] if len(precos) == 4 else [('CRU', precos[:1]), ('FRITO', precos[1:])] if categoria == 'MINIS' else [('NAO_INFORMADO', precos)]
                for estado, valores in pares:
                    pacote = Decimal(valores[0].replace('.', '').replace(',', '.'))
                    un = Decimal(valores[1].replace('.', '').replace(',', '.')) if len(valores) == 2 else None
                    registros.append({'source_sha256': sha, 'arquivo_origem': fonte.relative_to(raiz).as_posix(), 'pagina': pagina, 'linha': linha_num, 'categoria': categoria, 'descricao_original': descricao, 'estado': estado, 'quantidade_pacote': qtd, 'peso_pacote_kg': kg, 'quantidade_aproximada': 50 if categoria == 'MINIS' else None, 'preco_pacote_brl': str(pacote), 'preco_unidade_brl': str(un) if un is not None else None, 'texto_original': linha, 'validacao': 'PENDENTE_CONFERENCIA', 'vigencia': 'NAO_INFORMADA'})
    (saida / 'linhas_pdf.json').write_text(json.dumps(linhas_brutas, ensure_ascii=False, indent=2), encoding='utf-8')
    (saida / 'precos_produtos.json').write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')
    cols = list(registros[0]) if registros else []
    tabela = '<!doctype html><meta charset="utf-8"><title>Conferencia de precos</title><style>table{border-collapse:collapse}td,th{border:1px solid #bbb;padding:6px}th{background:#dce8f3}</style><h1>Precos extraidos — conferencia pendente</h1><p>Fonte historica; vigencia nao informada. Valores monetarios preservados como decimais.</p><table><tr>' + ''.join('<th>'+html.escape(c)+'</th>' for c in cols) + '</tr>'
    tabela += ''.join('<tr>'+''.join('<td>'+html.escape(str(r[c]) if r[c] is not None else '')+'</td>' for c in cols)+'</tr>' for r in registros)+'</table>'
    (saida / 'conferencia_precos.html').write_text(tabela, encoding='utf-8')
    resultado = {'status': 'EXTRAIDO_PENDENTE_CONFERENCIA' if registros and not pendencias else 'FALHA_EXTRACAO', 'linhas_com_precos': com_preco, 'registros_produto_estado': len(registros), 'pendencias_extracao': pendencias, 'source_sha256': sha, 'qualidade_comercial': 'NAO_AVALIADA', 'saida': saida.relative_to(raiz).as_posix()}
    (quality / 'conclusao_02_precos.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    if resultado['status'] == 'FALHA_EXTRACAO':
        raise RuntimeError('Extracao incompleta; consultar conclusao_02_precos.json')
    return resultado
