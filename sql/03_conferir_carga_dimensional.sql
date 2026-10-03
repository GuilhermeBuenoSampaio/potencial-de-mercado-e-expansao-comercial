USE [potencial-de-mercado-e-expansao-comercial];
GO
SELECT execucao_id,run_id,inicio_utc,fim_utc,status,silver_municipal_run_id,silver_documental_run_id
FROM audit.execucao_carga ORDER BY execucao_id DESC;
DECLARE @execucao_id bigint=(SELECT TOP(1) execucao_id FROM audit.execucao_carga WHERE status='APROVADA' ORDER BY execucao_id DESC);
SELECT tabela_destino,regra,registros_esperados,registros_observados,aprovado
FROM quality.reconciliacao_carga WHERE execucao_id=@execucao_id ORDER BY tabela_destino;
SELECT 'fato_indicador_municipal' AS tabela,COUNT_BIG(*) AS linhas FROM gold.fato_indicador_municipal WHERE execucao_id=@execucao_id
UNION ALL SELECT 'fato_distancia_municipio_origem',COUNT_BIG(*) FROM gold.fato_distancia_municipio_origem WHERE execucao_id=@execucao_id
UNION ALL SELECT 'fato_preco_referencia',COUNT_BIG(*) FROM gold.fato_preco_referencia WHERE execucao_id=@execucao_id
UNION ALL SELECT 'fato_estudo_publicado',COUNT_BIG(*) FROM gold.fato_estudo_publicado WHERE execucao_id=@execucao_id;
