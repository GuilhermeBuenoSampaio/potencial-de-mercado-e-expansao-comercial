USE [potencial-de-mercado-e-expansao-comercial];
SELECT * FROM gold.vw_bi_execucao_comercial;
SELECT 'circuitos' AS objeto,COUNT(*) AS linhas FROM gold.vw_bi_circuito
UNION ALL SELECT 'municipios',COUNT(*) FROM gold.vw_bi_municipio_comercial
UNION ALL SELECT 'cenarios',COUNT(*) FROM gold.vw_bi_cenario_comercial
UNION ALL SELECT 'simulacoes',COUNT(*) FROM gold.vw_bi_custo_viagem_simulado;
SELECT c.sequencia_sugerida,c.varejo_especializado_2024,f.receita_equilibrio_estimada_brl,f.status_pedagio
FROM gold.vw_bi_circuito c JOIN gold.vw_bi_custo_viagem_simulado f ON f.circuito_chave=c.circuito_chave
JOIN gold.vw_bi_cenario_comercial s ON s.cenario_chave=f.cenario_chave
WHERE s.cenario_referencia=1 ORDER BY c.varejo_especializado_2024 DESC;
