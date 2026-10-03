USE [potencial-de-mercado-e-expansao-comercial];
GO

SELECT
    municipio,
    ano_referencia,
    valor_publicado,
    valor_comercial,
    liberado_analise_comercial,
    elegivel_uso_painel,
    criterio_uso_painel,
    motivo_restricao
FROM gold.vw_painel_comercial
WHERE alias = 'populacao_2024'
ORDER BY municipio;