USE [potencial-de-mercado-e-expansao-comercial];
GO

SELECT *
FROM gold.vw_painel_comercial
WHERE liberado_analise_comercial = 0
  AND valor_comercial IS NOT NULL
  AND (
      alias <> 'populacao_2024'
      OR ano_referencia <> 2024
      OR motivo_restricao IS NULL
      OR motivo_restricao <> 'FORA_CANDIDATO_EDA'
  );