SELECT
    municipio,
    populacao_2024,
    populacao_mais_recente,
    ano_populacao_mais_recente,
    indicadores_disponiveis,
    alimentacao_por_10mil_2024,
    varejo_alimentar_por_10mil_2024
FROM gold.vw_perfil_comercial
ORDER BY municipio;