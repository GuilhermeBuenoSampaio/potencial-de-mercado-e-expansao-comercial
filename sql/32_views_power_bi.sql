CREATE OR ALTER VIEW gold.vw_bi_execucao_comercial AS
SELECT TOP(1) s.run_29,s.run_28,s.sql_execucao_id,s.carregado_utc,s.status
FROM gold.sim_execucao_comercial s
JOIN gold.vw_carga_aprovada a ON a.execucao_id=s.sql_execucao_id
WHERE s.status='REFERENCIAS_COMERCIAIS_COM_LIMITACOES'
ORDER BY s.carregado_utc DESC,s.run_29 DESC;
GO
CREATE OR ALTER VIEW gold.vw_bi_circuito AS
SELECT c.*,CONCAT(c.run_29,'|',c.circuito_id) AS circuito_chave,
 CAST('Ribeirão Preto' AS nvarchar(150)) AS origem_referencia,
 CAST('AGRUPAMENTO_COMERCIAL_SUGERIDO' AS varchar(80)) AS natureza_circuito
FROM gold.dim_circuito_sugerido c
JOIN gold.vw_bi_execucao_comercial a ON a.run_29=c.run_29;
GO
CREATE OR ALTER VIEW gold.vw_bi_municipio_comercial AS
SELECT m.*,CONCAT(m.run_29,'|',m.codigo_ibge) AS municipio_chave,
 CONCAT(m.run_29,'|',m.circuito_id) AS circuito_chave,
 CAST(m.varejo_alimentar_2024*10000.0/NULLIF(m.populacao_2024,0) AS decimal(20,8)) AS varejo_por_10mil_2024
FROM gold.ponte_circuito_municipio m
JOIN gold.vw_bi_execucao_comercial a ON a.run_29=m.run_29;
GO
CREATE OR ALTER VIEW gold.vw_bi_cenario_comercial AS
SELECT s.*,CONCAT(s.run_29,'|',s.cenario_id) AS cenario_chave,
 CAST(CASE WHEN consumo_km_l=10 AND desgaste_brl_km=0.20 AND margem_contribuicao=0.25 THEN 1 ELSE 0 END AS bit) AS cenario_referencia,
 CAST('PARAMETROS_HIPOTETICOS' AS varchar(80)) AS natureza_parametros
FROM gold.dim_cenario_comercial s
JOIN gold.vw_bi_execucao_comercial a ON a.run_29=s.run_29;
GO
CREATE OR ALTER VIEW gold.vw_bi_custo_viagem_simulado AS
SELECT f.*,CONCAT(f.run_29,'|',f.circuito_id) AS circuito_chave,
 CONCAT(f.run_29,'|',f.cenario_id) AS cenario_chave,
 CAST('PEDAGIOS_OSM_NAO_HOMOLOGADOS' AS varchar(80)) AS status_pedagio
FROM gold.fato_custo_viagem_simulado f
JOIN gold.vw_bi_execucao_comercial a ON a.run_29=f.run_29;
GO
