"""Orquestrador incremental de potencial-de-mercado-e-expansao-comercial."""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from etapa_01_inventario import executar
from etapa_02_precos import executar as extrair_precos
from etapa_03_estudos import executar as extrair_estudos
from etapa_04_imagens import executar as vincular_imagens
from etapa_05_revisao_xlsx import executar as revisar_xlsx
from etapa_06_coleta_municipal import executar as coletar_municipal
from etapa_07_validacao_municipal import executar as validar_municipal
from etapa_08_silver_municipal import executar as gerar_silver_municipal
from etapa_09_silver_documental import executar as gerar_silver_documental
from etapa_10_base_eda import executar as preparar_eda
from etapa_11_eda_estrutura import executar as explorar_estrutura
from etapa_12_eda_univariada import executar as explorar_univariada
from etapa_13_eda_bivariada import executar as explorar_bivariada
from etapa_14_eda_temporal import executar as explorar_temporal
from etapa_15_eda_geografica import executar as explorar_geografica
from etapa_16_eda_multivariada import executar as explorar_multivariada
from etapa_17_eda_documental import executar as explorar_documental


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raiz', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--coletar-externos', action='store_true', help='Executa tambem a coleta oficial municipal pela internet')
    parser.add_argument('--validar-municipais', action='store_true', help='Valida a ultima coleta local sem nova consulta externa')
    parser.add_argument('--gerar-silver-municipal', action='store_true', help='Valida a coleta local e materializa Silver municipal')
    parser.add_argument('--gerar-silver-documental', action='store_true', help='Materializa precos, estudos PDF e evidencias JPEG da execucao local')
    parser.add_argument('--preparar-eda', action='store_true', help='Valida as duas Silver e prepara bases para a EDA sem nova coleta')
    parser.add_argument('--eda-estrutura', action='store_true', help='Executa o bloco de estrutura e cobertura da EDA sobre a base existente')
    parser.add_argument('--eda-univariada', action='store_true', help='Executa a descricao municipal apos o bloco de estrutura da mesma base')
    parser.add_argument('--eda-bivariada', action='store_true', help='Explora relacoes municipais e sensibilidade apos a univariada')
    parser.add_argument('--eda-temporal', action='store_true', help='Explora evolucao dos indicadores em blocos comparaveis')
    parser.add_argument('--eda-geografica', action='store_true', help='Explora localizacao e distancias entre centroides apos a temporal')
    parser.add_argument('--eda-multivariada', action='store_true', help='Combina perfis municipais e associacoes com controle apos a geografica')
    parser.add_argument('--eda-documental', action='store_true', help='Explora precos, estudos historicos e evidencia JPEG da Silver vinculada a base')
    args = parser.parse_args()
    raiz = args.raiz.resolve()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:8]
    destino = raiz / 'quality' / '01_inventario' / run_id
    destino.mkdir(parents=True, exist_ok=False)
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(destino / 'execucao.log', encoding='utf-8'), logging.StreamHandler()])
    registro = {'projeto': 'potencial-de-mercado-e-expansao-comercial', 'run_id': run_id, 'inicio_utc': datetime.now(timezone.utc).isoformat(), 'etapas_disponiveis': ['01_inventario', '02_precos', '03_estudos', '04_imagens', '05_revisao_xlsx'], 'status': 'EM_EXECUCAO'}
    try:
        logging.info('Iniciando inventario: %s', raiz)
        resultado = executar(raiz, destino)
        registro['extracao_precos'] = extrair_precos(raiz, run_id)
        registro['extracao_estudos'] = extrair_estudos(raiz, run_id)
        registro['imagens'] = vincular_imagens(raiz, run_id)
        registro['revisao_xlsx'] = revisar_xlsx(raiz, run_id)
        if args.coletar_externos:
            registro['coleta_municipal'] = coletar_municipal(raiz, run_id)
            registro['etapas_disponiveis'].append('06_coleta_municipal')
        if args.coletar_externos or args.validar_municipais or args.gerar_silver_municipal:
            pasta_coleta = registro.get('coleta_municipal', {}).get('saida')
            registro['validacao_municipal'] = validar_municipal(raiz, run_id, pasta_coleta)
            registro['etapas_disponiveis'].append('07_validacao_municipal')
            if registro['validacao_municipal']['regras_reprovadas']:
                raise RuntimeError('Validacao municipal reprovada; consulte quality/07_validacao_municipal')
        if args.gerar_silver_municipal:
            registro['silver_municipal'] = gerar_silver_municipal(raiz, run_id, raiz / 'quality' / '07_validacao_municipal' / run_id, pasta_coleta)
            registro['etapas_disponiveis'].append('08_silver_municipal')
        if args.gerar_silver_documental:
            registro['silver_documental'] = gerar_silver_documental(raiz, run_id, run_id)
            registro['etapas_disponiveis'].append('09_silver_documental')
        if args.preparar_eda:
            registro['base_eda'] = preparar_eda(raiz, run_id)
            registro['etapas_disponiveis'].append('10_base_eda')
        if args.eda_estrutura:
            registro['eda_estrutura'] = explorar_estrutura(raiz, run_id)
            registro['etapas_disponiveis'].append('11_eda_estrutura')
        if args.eda_univariada:
            registro['eda_univariada'] = explorar_univariada(raiz, run_id)
            registro['etapas_disponiveis'].append('12_eda_univariada')
        if args.eda_bivariada:
            registro['eda_bivariada'] = explorar_bivariada(raiz, run_id)
            registro['etapas_disponiveis'].append('13_eda_bivariada')
        if args.eda_temporal:
            registro['eda_temporal'] = explorar_temporal(raiz, run_id)
            registro['etapas_disponiveis'].append('14_eda_temporal')
        if args.eda_geografica:
            registro['eda_geografica'] = explorar_geografica(raiz, run_id)
            registro['etapas_disponiveis'].append('15_eda_geografica')
        if args.eda_multivariada:
            registro['eda_multivariada'] = explorar_multivariada(raiz, run_id)
            registro['etapas_disponiveis'].append('16_eda_multivariada')
        if args.eda_documental:
            registro['eda_documental'] = explorar_documental(raiz, run_id)
            registro['etapas_disponiveis'].append('17_eda_documental')
        registro['status'] = 'CONCLUIDO_COM_CONFERENCIA_PENDENTE'
        if registro.get('coleta_municipal', {}).get('status') == 'COLETA_PARCIAL_COM_PENDENCIAS':
            registro['status'] = 'CONCLUIDO_COM_COLETA_PARCIAL'
        registro['total_arquivos'] = resultado['total_arquivos']
        logging.info('Inventario, precos, estudos, imagens e revisao do XLSX processados. Conferencia e qualidade pendentes.')
    except Exception as e:
        registro['status'] = 'FALHA'
        registro['erro'] = str(e)
        logging.exception('Pipeline interrompida')
        raise
    finally:
        registro['fim_utc'] = datetime.now(timezone.utc).isoformat()
        (destino / 'execucao.json').write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
