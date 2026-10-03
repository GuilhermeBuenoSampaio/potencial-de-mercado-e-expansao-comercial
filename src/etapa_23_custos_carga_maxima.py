"""Cenarios incrementais com carga maxima; nenhuma distancia geodesica vira rodoviaria."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from etapa_22_prioridades_circuitos import custos

PROJETO = 'potencial-de-mercado-e-expansao-comercial'


def positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor) or valor <= 0:
        raise ValueError(f'{campo}: esperado numero positivo finito')
    return valor


def analisar(rotas, config):
    if config.get('projeto') != PROJETO:
        raise ValueError('Nome do projeto divergente')
    veiculo = config['veiculo']
    if veiculo.get('combustivel') != 'GASOLINA' or veiculo.get('refrigeracao') is not False or veiculo.get('operacao') != 'SAIDA_COM_CARGA_MAXIMA':
        raise ValueError('Contrato: gasolina, sem refrigeracao, saida com carga maxima')
    capacidade = veiculo.get('capacidade_produtos_kg')
    if capacidade is not None:
        positivo(capacidade, 'capacidade_produtos_kg')
        if not veiculo.get('fonte_capacidade'):
            raise ValueError('Registrar fonte da capacidade liquida de produtos')
    cenarios = config.get('consumos', [])
    if not cenarios or len({c['cenario'] for c in cenarios}) != len(cenarios):
        raise ValueError('Informar cenarios de consumo com nomes unicos')
    ids = [r['circuito_id'] for r in rotas]
    if len(ids) != len(set(ids)) or set(config.get('circuitos', {})) != set(ids):
        raise ValueError('Circuitos da configuracao divergem da etapa 22')
    linhas = []
    for c in cenarios:
        positivo(c['km_l'], 'km_l')
        if c.get('natureza') not in ('HIPOTESE_NAO_CALIBRADA', 'MEDICAO_COM_CARGA'):
            raise ValueError('Identificar hipotese ou medicao com carga')
        if c['natureza'] == 'MEDICAO_COM_CARGA' and not c.get('fonte'):
            raise ValueError('Medicao exige fonte')
        entradas = {}
        for rid, v in config['circuitos'].items():
            for campo in ('distancia_rodoviaria_total_km', 'preco_combustivel_brl_l', 'desgaste_brl_km', 'pedagios_total_brl'):
                x = v.get(campo)
                if x is not None and (isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or x < 0):
                    raise ValueError(f'{rid}: {campo} invalido')
            if v.get('desgaste_brl_km') is not None and not v.get('origem_estimativa_desgaste'):
                raise ValueError('Desgaste exige origem da estimativa, inclusive quando zero')
            if v.get('preco_combustivel_brl_l') is not None and not v.get('periodo_combustivel'):
                raise ValueError('Combustivel exige periodo de referencia')
            if v.get('combustivel') != 'GASOLINA':
                raise ValueError('Combustivel por circuito divergente')
            for m in v.get('margens_disponiveis', []):
                positivo(m, 'margem');
                if m > 1:
                    raise ValueError('Margem deve ser fracao entre 0 e 1')
            entradas[rid] = dict(v, consumo_km_l=c['km_l'])
        for linha in custos(rotas, {'circuitos': entradas}):
            v = entradas[linha['circuito_id']]
            receita = v.get('receita_media_brl_kg')
            if receita is not None:
                positivo(receita, 'receita_media_brl_kg')
                if not v.get('fonte_receita_por_kg') or v.get('natureza_receita_por_kg') not in ('HIPOTESE', 'MIX_CONFIRMADO'):
                    raise ValueError('Receita/kg exige fonte e natureza; nao usar media global do catalogo')
            eq = linha['faturamento_equilibrio_brl']
            linhas.append(dict(linha, cenario_consumo=c['cenario'], natureza_consumo=c['natureza'], consumo_km_l=c['km_l'],
                premissa_carga='CONSUMO_CARREGADO_EM_TODO_PERCURSO', capacidade_produtos_kg=capacidade,
                receita_media_brl_kg=receita, natureza_receita_por_kg=v.get('natureza_receita_por_kg'),
                kg_equilibrio=None if eq is None or receita is None else eq / receita,
                faturamento_capacidade_brl=None if capacidade is None or receita is None else capacidade * receita,
                equilibrio_cabe_no_peso=None if eq is None or receita is None or capacidade is None else eq <= capacidade * receita))
    return linhas


def executar(raiz, run_id, parametros=None, circuitos=None):
    raiz = Path(raiz)
    parametros = Path(parametros) if parametros else raiz/'docs/23_custos_carga_maxima/PARAMETROS_CARGA_MAXIMA.json'
    if circuitos is None:
        candidatos = sorted((raiz/'datalake/03_gold').glob('*/prioridades_circuitos/circuitos.json'))
        if not candidatos:
            raise ValueError('Nao encontrado circuitos.json da etapa 22')
        circuitos = candidatos[-1]
    circuitos = Path(circuitos)
    manifesto = circuitos.parent/'manifesto.json'
    if manifesto.exists():
        meta = json.loads(manifesto.read_text(encoding='utf-8-sig'))
        hashes = {x['arquivo']: x['sha256'] for x in meta['exportacoes']}
        if meta.get('projeto') != PROJETO or hashes.get('circuitos.json') != hashlib.sha256(circuitos.read_bytes()).hexdigest():
            raise ValueError('Manifesto da etapa 22 divergente')
    else:
        raise ValueError('Manifesto da etapa 22 ausente; usar a pasta original da execucao')
    config = json.loads(parametros.read_text(encoding='utf-8-sig'))
    rotas = json.loads(circuitos.read_text(encoding='utf-8-sig'))
    linhas = analisar(rotas, config)
    destino = raiz/'datalake/03_gold'/run_id/'custos_carga_maxima'
    quality = raiz/'quality/23_custos_carga_maxima'/run_id
    quality.mkdir(parents=True, exist_ok=False)
    conclusao = {'projeto': PROJETO, 'run_id': run_id, 'inicio_utc': datetime.now(timezone.utc).isoformat(),
                 'entrada_circuitos': str(circuitos), 'entrada_circuitos_sha256': hashlib.sha256(circuitos.read_bytes()).hexdigest(),
                 'entrada_parametros_sha256': hashlib.sha256(parametros.read_bytes()).hexdigest(),
                 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        destino.mkdir(parents=True, exist_ok=False)
        (destino/'cenarios.json').write_text(json.dumps(linhas, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        pq.write_table(pa.Table.from_pylist(linhas), destino/'cenarios.parquet')
        (destino/'parametros_utilizados.json').write_text(json.dumps(config, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        if pq.read_table(destino/'cenarios.parquet').to_pylist() != linhas:
            raise ValueError('Reconciliacao Parquet divergente')
        conclusao.update(status='CENARIOS_COM_PENDENCIAS' if any(x['status'] == 'PENDENTE_PARAMETROS' or x['faturamento_equilibrio_brl'] is None or x['equilibrio_cabe_no_peso'] is None for x in linhas) else 'CENARIOS_ESTIMADOS', linhas=len(linhas), saida=str(destino),
            exportacoes=[{'arquivo':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(destino.iterdir())])
        texto = '# Custos com carga maxima\n\nHipoteses de consumo nao sao medicoes da frota. Custos dependem de distancia rodoviaria, gasolina, desgaste e pedagios. Equilibrio depende tambem da margem. Peso depende do mix e capacidade liquida.\n\n'
        texto += '| Circuito | Consumo km/l | Custo R$ | Equilibrio R$ | Pendencias |\n|---|---:|---:|---:|---|\n'
        for x in linhas:
            texto += f"| {x['circuito_id']} | {x['consumo_km_l']} | {x['custo_adicional_brl']} | {x['faturamento_equilibrio_brl']} | {x['pendencias'] or 'Conferir margem, mix e capacidade'} |\n"
        (destino/'RELATORIO.md').write_text(texto,encoding='utf-8')
        conclusao['exportacoes'] = [{'arquivo':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(destino.iterdir())]
    except Exception as e:
        if pq.read_table(destino/'cenarios.parquet').to_pylist() != linhas:
            raise ValueError('Reconciliacao Parquet divergente')
        conclusao.update(status='FALHA',erro=str(e))
        raise
    finally:
        conclusao['fim_utc'] = datetime.now(timezone.utc).isoformat()
        (quality/'conclusao_23.json').write_text(json.dumps(conclusao, ensure_ascii=False, indent=2),encoding='utf-8')
    return conclusao


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--raiz',type=Path,default=Path(__file__).resolve().parent.parent)
    p.add_argument('--parametros',type=Path)
    p.add_argument('--circuitos',type=Path)
    a = p.parse_args()
    resultado = executar(a.raiz,datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex[:8],a.parametros,a.circuitos)
    print(json.dumps(resultado,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
