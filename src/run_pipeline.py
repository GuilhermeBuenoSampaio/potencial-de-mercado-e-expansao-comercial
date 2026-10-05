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
from etapa_19_gold_dimensional import executar as gerar_gold_dimensional
from etapa_20_carga_sql import executar as carregar_sql
from etapa_22_prioridades_circuitos import executar as analisar_prioridades
from etapa_21_views_comerciais import executar as instalar_views
from etapa_23_custos_carga_maxima import executar as analisar_custos_carga
from etapa_24_coleta_logistica import executar as coletar_logistica
from etapa_25_divisao_circuitos import executar as dividir_circuitos
from etapa_26_jornada_atendimento import executar as simular_jornada


from etapa_27_equilibrio_viagens import executar as analisar_equilibrio

from etapa_28_pedagios_trajetos import executar as coletar_pedagios

from etapa_29_priorizacao_comercial import executar as priorizar_comercial

from etapa_30_carga_circuitos_sql import executar as carregar_circuitos_sql

from etapa_31_views_power_bi import executar as preparar_views_bi

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
    parser.add_argument('--gerar-gold-dimensional', action='store_true', help='Materializa Gold dimensional das Silver vinculadas a base EDA')
    parser.add_argument('--carregar-sql', action='store_true', help='Carrega Gold dimensional com reconciliacao integral SQL')
    parser.add_argument('--views-comerciais', action='store_true', help='Instala e valida as views SQL da etapa 21')
    parser.add_argument('--prioridades-circuitos', action='store_true', help='Analisa a carga SQL aprovada e gera circuitos geodesicos')
    parser.add_argument('--jornada-atendimento', action='store_true', help='Modo isolado: simula jornada total e atendimento')
    parser.add_argument('--parametros-jornada', type=Path)
    parser.add_argument('--dividir-circuitos', action='store_true', help='Modo isolado: divide circuitos por limites hipoteticos de deslocamento')
    parser.add_argument('--limites-deslocamento-h', nargs='+', type=float, default=[4,6,8])
    parser.add_argument('--coletar-logistica', action='store_true', help='Modo isolado: coleta ANP e OSRM sobre a etapa 22 existente')
    parser.add_argument('--custos-carga-maxima', action='store_true', help='Executa somente a etapa 23 sobre circuitos existentes')
    parser.add_argument('--parametros-carga-maxima', type=Path)
    parser.add_argument('--parametros-custo', type=Path, help='JSON opcional com parametros rodoviarios e margens por circuito')
    parser.add_argument('--sql-servidor', help='Nome da instancia SQL usada no SSMS')
    parser.add_argument('--sql-driver', default='ODBC Driver 18 for SQL Server')
    parser.add_argument('--confiar-certificado', action='store_true', help='Aceita certificado local da instancia SQL')
    parser.add_argument('--equilibrio-viagens', action='store_true', help='Modo isolado: sensibilidade de custos e equilibrio')
    parser.add_argument('--parametros-equilibrio', type=Path)
    parser.add_argument('--pedagios-trajetos', action='store_true', help='Modo isolado: coleta geometrias e estima pedagios OSM')
    parser.add_argument("--priorizacao-comercial", action="store_true", help="Modo isolado: cruza SQL com os cinco circuitos da etapa 28")
    parser.add_argument("--carregar-circuitos-sql", action="store_true", help="Modo isolado: carrega referencias comerciais no SQL")
    parser.add_argument("--views-power-bi", action="store_true", help="Modo isolado: instala e valida views de consumo BI")
    args = parser.parse_args()
    if args.views_power_bi:
        modos = [k for k,v in vars(args).items() if isinstance(v,bool) and v and k not in ("views_power_bi","confiar_certificado")]
        if modos or not args.sql_servidor: parser.error("--views-power-bi exige --sql-servidor e execucao isolada")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
        print(json.dumps(preparar_views_bi(args.raiz.resolve(), run_id, args.sql_servidor, args.sql_driver, args.confiar_certificado), ensure_ascii=False, indent=2))
        return
    if args.carregar_circuitos_sql:
        modos = [k for k,v in vars(args).items() if isinstance(v,bool) and v and k not in ("carregar_circuitos_sql","confiar_certificado")]
        if modos or not args.sql_servidor: parser.error("--carregar-circuitos-sql exige --sql-servidor e execucao isolada")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
        print(json.dumps(carregar_circuitos_sql(args.raiz.resolve(), run_id, args.sql_servidor, args.sql_driver, args.confiar_certificado), ensure_ascii=False, indent=2))
        return
    if args.priorizacao_comercial:
        modos = [k for k,v in vars(args).items() if isinstance(v,bool) and v and k not in ("priorizacao_comercial","confiar_certificado")]
        if modos or not args.sql_servidor: parser.error("--priorizacao-comercial exige --sql-servidor e execucao isolada")
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
        print(json.dumps(priorizar_comercial(args.raiz.resolve(), run_id, args.sql_servidor, args.sql_driver, args.confiar_certificado), ensure_ascii=False, indent=2))
        return
    if args.pedagios_trajetos:
        modos = [k for k,v in vars(args).items() if isinstance(v,bool) and v and k not in ('pedagios_trajetos','confiar_certificado')]
        if modos: parser.error('--pedagios-trajetos deve ser executado isoladamente')
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:8]
        print(json.dumps(coletar_pedagios(args.raiz.resolve(), run_id), ensure_ascii=False, indent=2))
        return
    if args.equilibrio_viagens:
        modos = [k for k,v in vars(args).items() if isinstance(v,bool) and v and k not in ('equilibrio_viagens','confiar_certificado')]
        if modos: parser.error('--equilibrio-viagens deve ser executado isoladamente')
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:8]
        print(json.dumps(analisar_equilibrio(args.raiz.resolve(), run_id, args.parametros_equilibrio), ensure_ascii=False, indent=2))
        return
    if (args.carregar_sql or args.views_comerciais or args.prioridades_circuitos) and not args.sql_servidor:
        parser.error('--carregar-sql, --views-comerciais e --prioridades-circuitos exigem --sql-servidor')
    raiz = args.raiz.resolve()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid4().hex[:8]
    if args.jornada_atendimento:
        if any((args.dividir_circuitos, args.coletar_logistica, args.custos_carga_maxima, args.coletar_externos, args.validar_municipais, args.gerar_silver_municipal, args.gerar_silver_documental, args.preparar_eda, args.eda_estrutura, args.eda_univariada, args.eda_bivariada, args.eda_temporal, args.eda_geografica, args.eda_multivariada, args.eda_documental, args.gerar_gold_dimensional, args.carregar_sql, args.views_comerciais, args.prioridades_circuitos)):
            parser.error('--jornada-atendimento deve ser executado isoladamente')
        print(json.dumps(simular_jornada(raiz, run_id, parametros=args.parametros_jornada), ensure_ascii=False, indent=2))
        return
    if args.dividir_circuitos:
        if any((args.coletar_logistica, args.custos_carga_maxima, args.coletar_externos, args.validar_municipais, args.gerar_silver_municipal, args.gerar_silver_documental, args.preparar_eda, args.eda_estrutura, args.eda_univariada, args.eda_bivariada, args.eda_temporal, args.eda_geografica, args.eda_multivariada, args.eda_documental, args.gerar_gold_dimensional, args.carregar_sql, args.views_comerciais, args.prioridades_circuitos)):
            parser.error('--dividir-circuitos deve ser executado isoladamente')
        print(json.dumps(dividir_circuitos(raiz, run_id, limites=args.limites_deslocamento_h), ensure_ascii=False, indent=2))
        return
    if args.coletar_logistica:
        if any((args.custos_carga_maxima, args.coletar_externos, args.validar_municipais, args.gerar_silver_municipal, args.gerar_silver_documental, args.preparar_eda, args.eda_estrutura, args.eda_univariada, args.eda_bivariada, args.eda_temporal, args.eda_geografica, args.eda_multivariada, args.eda_documental, args.gerar_gold_dimensional, args.carregar_sql, args.views_comerciais, args.prioridades_circuitos)):
            parser.error('--coletar-logistica deve ser executado isoladamente')
        print(json.dumps(coletar_logistica(raiz, run_id, parametros=args.parametros_carga_maxima), ensure_ascii=False, indent=2))
        return
    if args.custos_carga_maxima:
        if any((args.coletar_externos, args.validar_municipais, args.gerar_silver_municipal, args.gerar_silver_documental, args.preparar_eda, args.eda_estrutura, args.eda_univariada, args.eda_bivariada, args.eda_temporal, args.eda_geografica, args.eda_multivariada, args.eda_documental, args.gerar_gold_dimensional, args.carregar_sql, args.views_comerciais, args.prioridades_circuitos)):
            parser.error('--custos-carga-maxima e um modo isolado; execute as etapas anteriores separadamente')
        print(json.dumps(analisar_custos_carga(raiz, run_id, args.parametros_carga_maxima), ensure_ascii=False, indent=2))
        return
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
        if args.gerar_gold_dimensional:
            registro['gold_dimensional'] = gerar_gold_dimensional(raiz, run_id)
            registro['etapas_disponiveis'].append('19_gold_dimensional')
        if args.carregar_sql:
            pasta_gold = registro.get('gold_dimensional', {}).get('saida')
            registro['carga_sql'] = carregar_sql(raiz, run_id, args.sql_servidor, pasta_gold, args.sql_driver, args.confiar_certificado)
            registro['etapas_disponiveis'].append('20_carga_sql')
        if args.views_comerciais or args.prioridades_circuitos:
            registro['views_comerciais'] = instalar_views(raiz, run_id, args.sql_servidor, args.sql_driver, args.confiar_certificado)
            registro['etapas_disponiveis'].append('21_views_comerciais')
        if args.prioridades_circuitos:
            registro['prioridades_circuitos'] = analisar_prioridades(raiz, run_id, args.sql_servidor, args.sql_driver, args.confiar_certificado, args.parametros_custo)
            registro['etapas_disponiveis'].append('22_prioridades_circuitos')
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
