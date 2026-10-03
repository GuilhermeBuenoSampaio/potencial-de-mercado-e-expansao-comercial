USE [potencial-de-mercado-e-expansao-comercial];
GO
-- Presenca comercial observada, não clientes confirmados. Sem escore arbitrário.
WITH base AS (
 SELECT p.*,d.distancia_km AS distancia_cd_geodesica_km
 FROM gold.vw_perfil_comercial p
 JOIN gold.vw_distancias_origens d ON d.execucao_id=p.execucao_id AND d.codigo_ibge=p.codigo_ibge
 WHERE d.tipo_origem='CD' AND d.origem=N'Ribeirão Preto' AND d.tipo_distancia='GEODESICA_CENTROIDES'
)
SELECT codigo_ibge,municipio,uf,varejo_alimentar_2024 AS unidades_varejo_especializado_2024,
 renda_mediana_2022,populacao_2024,populacao_mais_recente,ano_populacao_mais_recente,
 CAST(CAST(varejo_alimentar_2024 AS decimal(18,6))*10000.0
 /NULLIF(CAST(populacao_2024 AS decimal(18,6)),0) AS decimal(18,6)) AS varejo_por_10mil_2024,
 distancia_cd_geodesica_km,
 CASE WHEN COUNT(varejo_alimentar_2024) OVER()=COUNT(*) OVER()
 THEN CAST(CAST(varejo_alimentar_2024 AS decimal(18,6))*100.0
 /NULLIF(SUM(varejo_alimentar_2024) OVER(),0) AS decimal(18,4)) END AS participacao_varejo_percentual,
 CASE WHEN COUNT(varejo_alimentar_2024) OVER()=COUNT(*) OVER()
 THEN CAST(CAST(SUM(varejo_alimentar_2024) OVER(ORDER BY varejo_alimentar_2024 DESC,codigo_ibge ROWS UNBOUNDED PRECEDING) AS decimal(18,6))*100.0
 /NULLIF(SUM(varejo_alimentar_2024) OVER(),0) AS decimal(18,4)) END AS participacao_acumulada_percentual,
 CASE WHEN varejo_alimentar_2024 IS NULL OR distancia_cd_geodesica_km IS NULL THEN NULL
 WHEN EXISTS (
  SELECT 1 FROM base b WHERE b.varejo_alimentar_2024>=a.varejo_alimentar_2024
  AND b.distancia_cd_geodesica_km<=a.distancia_cd_geodesica_km
  AND (b.varejo_alimentar_2024>a.varejo_alimentar_2024 OR b.distancia_cd_geodesica_km<a.distancia_cd_geodesica_km)
 ) THEN 0 ELSE 1 END AS fronteira_escala_proximidade
FROM base a ORDER BY varejo_alimentar_2024 DESC,codigo_ibge;
