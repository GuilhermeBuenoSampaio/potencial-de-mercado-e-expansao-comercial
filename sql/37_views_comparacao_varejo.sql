IF OBJECT_ID('gold.execucao_comparacao_varejo','U') IS NULL
CREATE TABLE gold.execucao_comparacao_varejo (
 run_32 varchar(40) PRIMARY KEY, run_29 varchar(40) NOT NULL,
 ano int NOT NULL, fonte_url nvarchar(2000) NOT NULL,
 fonte_sha256 char(64) NOT NULL, carregado_utc datetime2 NOT NULL,
 status varchar(50) NOT NULL);
IF OBJECT_ID('gold.complemento_varejo_municipal','U') IS NULL
CREATE TABLE gold.complemento_varejo_municipal (
 run_32 varchar(40) NOT NULL REFERENCES gold.execucao_comparacao_varejo(run_32),
 codigo_ibge varchar(7) NOT NULL, ano int NOT NULL,
 categoria_117440 decimal(20,0) NOT NULL CHECK(categoria_117440>=0),
 categoria_117441 decimal(20,0) NOT NULL CHECK(categoria_117441>=0),
 categoria_117443 decimal(20,0) NOT NULL CHECK(categoria_117443>=0),
 PRIMARY KEY(run_32,codigo_ibge));
GO
CREATE OR ALTER VIEW gold.vw_bi_execucao_comparacao_varejo AS
SELECT TOP(1) e.*
FROM gold.execucao_comparacao_varejo e
JOIN gold.vw_bi_execucao_comercial a ON a.run_29=e.run_29
WHERE e.status='COMPARACAO_VAREJO_VERIFICADA'
ORDER BY e.carregado_utc DESC,e.run_32 DESC;
GO
CREATE OR ALTER VIEW gold.vw_bi_municipio_varejo_comparado AS
WITH base AS (
 SELECT m.*,e.run_32,
 m.varejo_alimentar_2024 AS varejo_especializado_2024,
 x.categoria_117440+x.categoria_117441 AS acrescimo_unidades,
 m.varejo_alimentar_2024+x.categoria_117440+x.categoria_117441
 AS varejo_alimentar_ampliado_2024
 FROM gold.vw_bi_municipio_comercial m
 JOIN gold.vw_bi_execucao_comparacao_varejo e ON e.run_29=m.run_29
 JOIN gold.complemento_varejo_municipal x ON x.run_32=e.run_32
 AND x.codigo_ibge=m.codigo_ibge AND x.ano=e.ano
)
SELECT b.*,
 CAST(100.0*acrescimo_unidades/NULLIF(varejo_especializado_2024,0) AS decimal(20,8)) AS acrescimo_percentual,
 CAST(100.0*varejo_especializado_2024/NULLIF(SUM(varejo_especializado_2024) OVER(),0) AS decimal(20,8)) AS participacao_especializado_percentual,
 CAST(100.0*varejo_alimentar_ampliado_2024/NULLIF(SUM(varejo_alimentar_ampliado_2024) OVER(),0) AS decimal(20,8)) AS participacao_ampliado_percentual,
 CAST(10000.0*varejo_alimentar_ampliado_2024/NULLIF(populacao_2024,0) AS decimal(20,8)) AS ampliado_por_10mil,
 DENSE_RANK() OVER(ORDER BY varejo_especializado_2024 DESC) AS posicao_especializado,
 DENSE_RANK() OVER(ORDER BY varejo_alimentar_ampliado_2024 DESC) AS posicao_ampliado
FROM base b;
GO
CREATE OR ALTER VIEW gold.vw_bi_circuito_varejo_comparado AS
WITH totais AS (
 SELECT circuito_chave,run_32,COUNT(*) AS municipios_comparados,
 SUM(varejo_alimentar_ampliado_2024) AS varejo_alimentar_ampliado_2024,
 SUM(acrescimo_unidades) AS acrescimo_unidades
 FROM gold.vw_bi_municipio_varejo_comparado
 GROUP BY circuito_chave,run_32
)
SELECT c.*,t.run_32,t.municipios_comparados,
 t.varejo_alimentar_ampliado_2024,t.acrescimo_unidades,
 CAST(100.0*t.acrescimo_unidades/NULLIF(c.varejo_especializado_2024,0) AS decimal(20,8)) AS acrescimo_percentual,
 CAST(100.0*t.varejo_alimentar_ampliado_2024/NULLIF(SUM(t.varejo_alimentar_ampliado_2024) OVER(),0) AS decimal(20,8)) AS participacao_ampliado_percentual,
 DENSE_RANK() OVER(ORDER BY c.varejo_especializado_2024 DESC) AS posicao_especializado,
 DENSE_RANK() OVER(ORDER BY t.varejo_alimentar_ampliado_2024 DESC) AS posicao_ampliado
FROM gold.vw_bi_circuito c
JOIN totais t ON t.circuito_chave=c.circuito_chave;
GO
