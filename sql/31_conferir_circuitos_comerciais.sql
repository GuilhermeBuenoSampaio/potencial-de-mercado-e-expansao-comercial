USE [potencial-de-mercado-e-expansao-comercial];
DECLARE @run varchar(80) = (
 SELECT TOP(1) s.run_29 FROM gold.sim_execucao_comercial s
 JOIN gold.vw_carga_aprovada a ON a.execucao_id=s.sql_execucao_id
 ORDER BY s.carregado_utc DESC,s.run_29 DESC
);
SELECT @run AS run_29;
SELECT 'circuitos' AS objeto,COUNT(*) AS linhas FROM gold.dim_circuito_sugerido WHERE run_29=@run
UNION ALL SELECT 'municipios',COUNT(*) FROM gold.ponte_circuito_municipio WHERE run_29=@run
UNION ALL SELECT 'cenarios',COUNT(*) FROM gold.dim_cenario_comercial WHERE run_29=@run
UNION ALL SELECT 'simulacoes',COUNT(*) FROM gold.fato_custo_viagem_simulado WHERE run_29=@run;
SELECT c.sequencia_sugerida,c.varejo_especializado_2024,c.participacao_varejo_percentual,
 c.km_sugeridos,f.receita_equilibrio_estimada_brl,f.natureza
FROM gold.dim_circuito_sugerido c
JOIN gold.fato_custo_viagem_simulado f ON f.run_29=c.run_29 AND f.circuito_id=c.circuito_id
JOIN gold.dim_cenario_comercial s ON s.run_29=f.run_29 AND s.cenario_id=f.cenario_id
WHERE c.run_29=@run AND s.consumo_km_l=10 AND s.desgaste_brl_km=0.20 AND s.margem_contribuicao=0.25
ORDER BY c.varejo_especializado_2024 DESC;
