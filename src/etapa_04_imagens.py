"""Vincula imagens conhecidas ao PDF equivalente; não executa OCR genérico."""
import hashlib
import html
import json
import shutil
from pathlib import Path

PDF_SHA = '8da8c016ceece3a20ba576d72e5ec1074b7c1bc0a51246ba314bd59fa7c20590'
PERFIS = {
    '42c233741149a450faa34e16dc9ddcdaca8f50fa69447e4e60a6b79ed0008b13': '1',
    '7f73d7baad90354a82c50771714008b68558e64f1eeba44771e26850d9363df0': '2',
    '3ed44ab5d6168ddfc3d4d5d4f93cb95a3787ee4c944abddb1653de2c83786e35': '3',
    'd75aca5d0b1b3d810884a32bad7cd766f57eb2aa7466d0d6301329be7d8db8ed': '4',
    '8337111608d28a4e622229ad3399a74b60daffef0a19b298780db354aeb9964a': '5',
}
# Percentuais transcritos visualmente dos JPEGs, na ordem de linhas/colunas.
# Não substituem valores do PDF; servem para reconciliação independente.
PERCENTUAIS = {
'1': '''30.6 16.2 31.0 27.0 35.4 27.1
42.5 36.7 37.3 37.5 47.3 44.0
42.2 39.0 39.3 35.7 45.4 42.4
38.0 34.1 33.1 33.7 41.4 38.1
30.9 25.1 28.0 23.0 34.3 30.8
19.0 18.3 18.4 16.3 19.3 20.0
39.1 32.3 36.1 35.6 43.2 37.7
31.4 23.9 29.0 26.3 34.7 32.0
18.5 17.8 21.1 13.6 16.3 16.6
31.3 31.3 31.2 26.9 32.2 30.8
45.8 43.0 43.6 40.6 46.3 45.4
61.7 58.2 52.7 57.1 64.7 60.9
22.5 17.4 23.4 15.0 25.7 20.3
31.6 29.2 33.4 27.4 32.9 28.1
41.9 38.3 45.6 39.1 41.9 40.9
52.4 48.8 52.0 48.2 53.4 51.4
31.6 24.6 30.2 28.4 35.6 30.0
37.6 33.1 34.7 32.3 40.6 36.8
28.4 19.0 28.5 19.6 35.4 27.4
36.5 31.1 33.9 32.4 39.1 36.3
33.5 25.7 30.7 28.6 37.4 33.5
40.6 33.8 38.3 39.6 43.0 42.8''',
'2': '''6.4 5.7 6.6 5.1 6.8 5.7
12.0 11.0 9.2 11.2 14.1 12.0
2.8 2.7 3.4 2.3 2.9 2.1
0.7 0.9 0.9 0.3 0.6 0.4
9.5 7.2 10.3 6.1 10.2 8.4
2.3 2.1 2.3 1.6 2.6 1.6
11.5 7.0 8.6 10.7 13.3 14.0
7.2 4.1 5.1 5.2 9.2 7.8
9.2 8.7 8.4 9.0 10.6 6.8''',
'3': '''3.9 5.7 7.9 9.2
5.1 10.6 16.0 19.0
2.8 3.2 2.5 2.3
0.6 0.7 0.6 0.8
8.0 9.2 10.2 11.0
1.4 2.0 2.8 3.4
5.8 8.3 13.7 27.0
2.1 5.1 10.7 15.2
5.8 8.6 11.2 11.7''',
'4': '''11.2 1.7 6.4 6.1
14.3 9.9 12.7 8.4
2.5 3.2 2.9 2.8
0.6 0.7 0.6 0.9
7.7 11.1 9.7 8.2
2.5 2.0 2.3 1.9
13.2 9.8 11.9 9.3
8.0 6.4 8.0 3.2
9.4 8.9 9.6 6.4''',
'5': '''1.9 8.7 9.1 8.7 6.7 3.9
11.3 16.5 14.5 11.4 8.7 4.6
4.6 3.4 2.6 1.7 1.5 0.8
0.7 0.9 0.7 0.5 0.4 0.4
13.4 10.2 10.8 7.4 5.4 2.8
1.5 3.0 2.9 2.7 2.2 1.2
7.5 13.3 15.7 14.5 10.8 6.4
6.5 10.5 8.6 7.0 5.0 2.3
9.6 11.8 10.7 8.6 6.6 3.4'''
}


def gravar(p, dados):
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')


def executar(raiz: Path, run_id: str):
    quality = raiz / 'quality' / '04_imagens' / run_id
    quality.mkdir(parents=True, exist_ok=False)
    destino = raiz / 'datalake' / '01_bronze' / run_id / 'imagens'
    destino.mkdir(parents=True, exist_ok=False)
    fontes, erros, alertas = [], [], []
    vistas = set()
    pdf = raiz / 'datalake' / '01_bronze' / run_id / 'estudos' / PDF_SHA[:16]
    try:
        dados = json.loads((pdf / 'indicadores_consumo.json').read_text(encoding='utf-8'))
        testes = json.loads((pdf / 'testes_publicados.json').read_text(encoding='utf-8'))
        if any(r['source_sha256'] != PDF_SHA for r in dados + testes):
            raise ValueError('Proveniência do PDF incompatível')
        arquivos = sorted(p for p in (raiz / 'datalake' / '00_landing').rglob('*') if p.is_file() and p.suffix.lower() in {'.jpeg', '.jpg'})
        for arquivo in arquivos:
            sha = hashlib.sha256(arquivo.read_bytes()).hexdigest()
            try:
                if sha not in PERFIS:
                    raise ValueError('Imagem sem perfil visual conferido; exige revisão ou novo OCR')
                if sha in vistas:
                    raise ValueError('Imagem repetida por conteúdo; conferir inventário')
                vistas.add(sha)
                tabela = PERFIS[sha]
                registros = [r for r in dados if r['tabela'] == tabela]
                publicados = [r for r in testes if r['tabela'] == tabela]
                valores = [float(v) for v in PERCENTUAIS[tabela].split()]
                if len(registros) != len(valores):
                    raise ValueError('Quantidade de observações diverge da imagem')
                locais = []
                for indice, (r, valor) in enumerate(zip(registros, valores)):
                    if r['percentual'] != valor:
                        a = {'imagem_sha256': sha, 'tabela': tabela, 'indice_observacao': indice, 'grupo_alimento': r.get('grupo_alimento'), 'estrato': r.get('estrato'), 'percentual_imagem': valor, 'percentual_pdf': r['percentual'], 'acao': 'PRESERVAR_AMBAS_AS_FONTES; NAO_RESOLVER_AUTOMATICAMENTE'}
                        locais.append(a)
                        alertas.append(a)
                pasta = destino / sha[:16]
                pasta.mkdir(exist_ok=False)
                shutil.copyfile(arquivo, pasta / 'fonte.jpeg')
                def vincular(r):
                    return {**r, 'imagem_sha256': sha, 'arquivo_imagem': arquivo.relative_to(raiz).as_posix(), 'metodo_imagem': 'VINCULO_PDF_EQUIVALENTE_COM_PERCENTUAIS_CONFERIDOS_VISUALMENTE', 'duplicidade_semantica': True, 'incluir_como_nova_observacao': False, 'validacao_imagem': 'PERCENTUAIS_CONFERIDOS; IC_E_TESTES_HERDADOS_DO_PDF'}
                tabulados = []
                for r, valor in zip(registros, valores):
                    item = vincular(r)
                    item['percentual_pdf'] = item.pop('percentual')
                    item['percentual_pdf_original'] = item.pop('percentual_original')
                    item['percentual_imagem'] = valor
                    item['divergencia_pdf_imagem'] = valor != item['percentual_pdf']
                    item['origem_percentual_imagem'] = 'TRANSCRICAO_VISUAL_PERFIL_SHA256'
                    for campo in ['ic95_inferior', 'ic95_superior']:
                        if campo in item: item[campo + '_pdf'] = item.pop(campo)
                    tabulados.append(item)
                gravar(pasta / 'alertas_imagem.json', locais)
                gravar(pasta / 'indicadores_imagem.json', tabulados)
                gravar(pasta / 'testes_imagem.json', [vincular(r) for r in publicados])
                meta = {'arquivo': arquivo.relative_to(raiz).as_posix(), 'imagem_sha256': sha, 'pdf_sha256': PDF_SHA, 'tabela_pdf': tabela, 'percentuais_comparados': len(registros), 'divergencias_pdf_imagem': len(locais), 'testes_vinculados': len(publicados), 'metodo': 'vinculo_pdf_equivalente', 'ocr_executado': False, 'observacoes_adicionais_para_analise': 0, 'saida': pasta.relative_to(raiz).as_posix()}
                gravar(pasta / 'vinculo_fonte.json', meta)
                cols = list(dict.fromkeys(k for r in tabulados for k in r))
                doc = '<!doctype html><meta charset="utf-8"><title>Conferência de imagem</title><style>table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:5px}img{max-width:100%}</style><h1>'+html.escape(arquivo.name)+'</h1><p>Imagem equivalente à tabela '+tabela+' do PDF nacional. Percentuais transcritos visualmente e comparados; divergências preservadas. Intervalos e testes vinculados ao PDF. Não somar estas observações novamente.</p><img src="fonte.jpeg" alt="Imagem original"><table><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in cols)+'</tr>'
                doc += ''.join('<tr>'+''.join('<td>'+html.escape(str(r.get(c,'')))+'</td>' for c in cols)+'</tr>' for r in tabulados)+'</table>'
                (pasta / 'conferencia_imagem.html').write_text(doc, encoding='utf-8')
                fontes.append(meta)
            except Exception as e:
                erros.append({'arquivo': arquivo.relative_to(raiz).as_posix(), 'sha256': sha, 'erro': str(e)})
        ausentes = set(PERFIS) - vistas
        if ausentes:
            erros.append({'erro': 'Imagens esperadas ausentes', 'sha256_ausentes': sorted(ausentes)})
    except Exception as e:
        erros.append({'erro': str(e)})
    resultado = {'etapa': '04_imagens', 'run_id': run_id, 'status': 'FALHA' if erros else 'VINCULADO_COM_DIVERGENCIAS_REGISTRADAS', 'fontes': fontes, 'erros': erros, 'total_percentuais_comparados': sum(f['percentuais_comparados'] for f in fontes), 'alertas': alertas, 'observacoes_adicionais_para_analise': 0, 'limitacoes': ['Perfis exclusivos dos cinco JPEGs conhecidos; não é OCR genérico.', 'IC95 e testes herdados do PDF; não conferidos integralmente e de modo independente nos JPEGs.', 'Aplicabilidade comercial atual continua pendente.']}
    gravar(quality / 'conclusao_04_imagens.json', resultado)
    if erros:
        raise RuntimeError('Falha na etapa de imagens; consultar conclusao_04_imagens.json')
    return resultado
