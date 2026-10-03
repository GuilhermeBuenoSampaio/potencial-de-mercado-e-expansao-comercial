USE [potencial-de-mercado-e-expansao-comercial];
GO
-- A. Dimensao comercial: unidades locais CNAE; ainda sem qualificacao de compradores.
-- Participacao calculada entre as 12 cidades do escopo. Se houver ausencias, nao calcular.
SELECT codigo_ibge,municipio,uf,populacao_2024,alimentacao_2024,varejo_alimentar_2024,
 CASE WHEN COUNT(alimentacao_2024) OVER()=COUNT(*) OVER()
 THEN CAST(100.0*alimentacao_2024/NULLIF(SUM(alimentacao_2024) OVER(),0) AS decimal(18,4)) END AS participacao_alimentacao_percentual,
 DENSE_RANK() OVER(ORDER BY alimentacao_2024 DESC) AS posicao_volume_alimentacao,
 indicadores_disponiveis
FROM gold.vw_perfil_comercial ORDER BY alimentacao_2024 DESC,codigo_ibge;
-- B. Perfis: comparar escala, concentracao e renda; periodos explicitos.
SELECT codigo_ibge,municipio,renda_mediana_2022,urbanizacao_percentual_2022,
 alimentacao_por_10mil_2024,varejo_alimentar_por_10mil_2024
FROM gold.vw_perfil_comercial ORDER BY renda_mediana_2022 DESC,codigo_ibge;
-- C. Proximidade: menor distancia entre centroides dos CDs, preservando empates.
WITH cd AS (
 SELECT *,DENSE_RANK() OVER(PARTITION BY execucao_id,codigo_ibge ORDER BY distancia_km) AS posicao_cd
 FROM gold.vw_distancias_origens WHERE tipo_origem='CD' AND tipo_distancia='GEODESICA_CENTROIDES'
)
SELECT codigo_ibge,municipio,origem,distancia_km,metodo FROM cd WHERE posicao_cd=1 ORDER BY distancia_km,codigo_ibge;
-- D. Comparacao direta CD Ribeirao Preto versus fabrica Sao Carlos.
SELECT codigo_ibge,municipio,
 MAX(CASE WHEN origem=N'Ribeirão Preto' AND tipo_origem='CD' THEN distancia_km END) AS distancia_cd_ribeirao_km,
 MAX(CASE WHEN origem=N'São Carlos' AND tipo_origem='FABRICA' THEN distancia_km END) AS distancia_fabrica_km,
 MAX(CASE WHEN origem=N'São Carlos' AND tipo_origem='FABRICA' THEN distancia_km END)
 -MAX(CASE WHEN origem=N'Ribeirão Preto' AND tipo_origem='CD' THEN distancia_km END) AS diferenca_geodesica_km
FROM gold.vw_distancias_origens WHERE tipo_distancia='GEODESICA_CENTROIDES'
GROUP BY codigo_ibge,municipio ORDER BY codigo_ibge;
-- E. Catalogo: sem media global e sem assumir produtos equivalentes.
SELECT categoria,estado,peso_pacote_kg,COUNT(*) AS apresentacoes,
 MIN(preco_pacote_brl) AS minimo_pacote_brl,MAX(preco_pacote_brl) AS maximo_pacote_brl,
 SUM(CASE WHEN vigencia_confirmada=0 THEN 1 ELSE 0 END) AS referencias_sem_vigencia
FROM gold.vw_preco_referencia GROUP BY categoria,estado,peso_pacote_kg ORDER BY categoria,estado,peso_pacote_kg;
-- F. Estudos: cobertura e pendencias, sem somar percentuais ou extrapolar para cidades.
SELECT tabela_silver,periodo_referencia,COUNT(*) AS observacoes,
 SUM(CASE WHEN pendencia_publicada=1 THEN 1 ELSE 0 END) AS observacoes_com_pendencia
FROM gold.vw_estudo_publicado GROUP BY tabela_silver,periodo_referencia;
