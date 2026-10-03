-- potencial-de-mercado-e-expansao-comercial | etapa 21
USE [potencial-de-mercado-e-expansao-comercial];
GO
CREATE OR ALTER VIEW gold.vw_carga_aprovada AS
SELECT TOP (1) a.execucao_id,a.run_id,a.fim_utc,a.silver_municipal_run_id,a.silver_documental_run_id
FROM audit.execucao_carga a
WHERE a.status='APROVADA'
  AND (SELECT COUNT(*) FROM quality.reconciliacao_carga q WHERE q.execucao_id=a.execucao_id)=14
  AND NOT EXISTS (SELECT 1 FROM quality.reconciliacao_carga q WHERE q.execucao_id=a.execucao_id AND q.aprovado=0)
ORDER BY a.execucao_id DESC;
GO

CREATE OR ALTER VIEW gold.vw_indicadores_serie AS
SELECT f.execucao_id,f.observacao_id,f.municipio_id,m.codigo_ibge,m.municipio,m.uf,
 f.indicador_id,i.indicador_chave,i.nome_oficial,i.grupo,i.unidade,i.escala_percentual,i.classificacoes_json,
 f.periodo_id,p.ano_inicial AS ano_referencia,f.fonte_id,s.fonte_url,s.fonte_sha256,
 f.valor,f.status_valor,f.status_atualidade,f.ultimo_valor_numerico,f.candidato_eda,
 f.conferencia_renda_pendente,f.revisao_pib_pendente,f.liberado_analise_comercial,f.motivo_restricao
FROM gold.fato_indicador_municipal f
JOIN gold.vw_carga_aprovada a ON a.execucao_id=f.execucao_id
JOIN gold.dim_municipio m ON m.municipio_id=f.municipio_id
JOIN gold.dim_indicador i ON i.indicador_id=f.indicador_id
JOIN gold.dim_periodo p ON p.periodo_id=f.periodo_id
JOIN gold.dim_fonte s ON s.fonte_id=f.fonte_id;
GO

CREATE OR ALTER VIEW gold.vw_indicadores_ultimo_disponivel AS
SELECT * FROM gold.vw_indicadores_serie WHERE ultimo_valor_numerico=1;
GO

CREATE OR ALTER VIEW gold.vw_catalogo_comercial AS
SELECT v.alias,v.indicador_chave,v.ano_referencia FROM (VALUES
 ('populacao_2024','6579_9324_4f53cda18c2baa0c',2024),
 ('renda_mediana_2022','10295_13534_514d2f15b03e1a4f',2022),
 ('urbanizacao_2022','9923_1000093_53d811c101e6bf12',2022),
 ('alimentacao_2024','9528_706_c9f43c6c0bd8d19e',2024),
 ('varejo_alimentar_2024','9528_706_6c4b6ec4c3a13cf3',2024)
) v(alias,indicador_chave,ano_referencia);
GO

CREATE OR ALTER VIEW gold.vw_painel_comercial AS
SELECT a.execucao_id,m.municipio_id,m.codigo_ibge,m.municipio,m.uf,
 c.alias,c.indicador_chave,c.ano_referencia,i.nome_oficial,i.unidade,
 f.valor AS valor_publicado,
 CASE WHEN f.liberado_analise_comercial=1 OR (
 c.alias='populacao_2024' AND f.indicador_chave='6579_9324_4f53cda18c2baa0c'
 AND f.ano_referencia=2024 AND f.status_valor='NUMERICO' AND f.valor>0
 AND f.motivo_restricao='FORA_CANDIDATO_EDA'
 AND f.conferencia_renda_pendente=0 AND f.revisao_pib_pendente=0) THEN f.valor ELSE NULL END AS valor_comercial,
 CAST(CASE WHEN f.liberado_analise_comercial=1 OR (
 c.alias='populacao_2024' AND f.indicador_chave='6579_9324_4f53cda18c2baa0c'
 AND f.ano_referencia=2024 AND f.status_valor='NUMERICO' AND f.valor>0
 AND f.motivo_restricao='FORA_CANDIDATO_EDA'
 AND f.conferencia_renda_pendente=0 AND f.revisao_pib_pendente=0) THEN 1 ELSE 0 END AS bit) AS elegivel_uso_painel,
 CASE WHEN f.liberado_analise_comercial=1 THEN 'LIBERADO_GOLD'
 WHEN f.liberado_analise_comercial=1 OR (
 c.alias='populacao_2024' AND f.indicador_chave='6579_9324_4f53cda18c2baa0c'
 AND f.ano_referencia=2024 AND f.status_valor='NUMERICO' AND f.valor>0
 AND f.motivo_restricao='FORA_CANDIDATO_EDA'
 AND f.conferencia_renda_pendente=0 AND f.revisao_pib_pendente=0) THEN 'DENOMINADOR_HISTORICO_2024'
 ELSE 'RESTRITO_OU_AUSENTE' END AS criterio_uso_painel,
 COALESCE(f.liberado_analise_comercial,CAST(0 AS bit)) AS liberado_analise_comercial,
 COALESCE(f.status_valor,'SEM_REGISTRO_NO_PERIODO') AS status_valor,
 f.motivo_restricao,f.fonte_url,f.fonte_sha256
FROM gold.dim_municipio m CROSS JOIN gold.vw_carga_aprovada a
CROSS JOIN gold.vw_catalogo_comercial c
LEFT JOIN gold.dim_indicador i ON i.indicador_chave=c.indicador_chave
LEFT JOIN gold.vw_indicadores_serie f ON f.execucao_id=a.execucao_id
 AND f.municipio_id=m.municipio_id AND f.indicador_chave=c.indicador_chave AND f.ano_referencia=c.ano_referencia
WHERE m.cidade_expansao=1;
GO

CREATE OR ALTER VIEW gold.vw_perfil_comercial AS
WITH p AS (
 SELECT execucao_id,municipio_id,codigo_ibge,municipio,uf,
 MAX(CASE WHEN alias='populacao_2024' THEN valor_comercial END) AS populacao_2024,
 MAX(CASE WHEN alias='renda_mediana_2022' THEN valor_comercial END) AS renda_mediana_2022,
 MAX(CASE WHEN alias='urbanizacao_2022' THEN valor_comercial END) AS urbanizacao_percentual_2022,
 MAX(CASE WHEN alias='alimentacao_2024' THEN valor_comercial END) AS alimentacao_2024,
 MAX(CASE WHEN alias='varejo_alimentar_2024' THEN valor_comercial END) AS varejo_alimentar_2024,
 SUM(CASE WHEN valor_comercial IS NOT NULL THEN 1 ELSE 0 END) AS indicadores_disponiveis
 FROM gold.vw_painel_comercial GROUP BY execucao_id,municipio_id,codigo_ibge,municipio,uf
)
SELECT p.*,
 atual.valor AS populacao_mais_recente,atual.ano_referencia AS ano_populacao_mais_recente,
 CAST(alimentacao_2024 / NULLIF(populacao_2024,0) * 10000 AS decimal(18,6)) AS alimentacao_por_10mil_2024,
 CAST(varejo_alimentar_2024 / NULLIF(populacao_2024,0) * 10000 AS decimal(18,6)) AS varejo_alimentar_por_10mil_2024
FROM p
LEFT JOIN gold.vw_indicadores_ultimo_disponivel atual
 ON atual.execucao_id=p.execucao_id AND atual.municipio_id=p.municipio_id
 AND atual.indicador_chave='6579_9324_4f53cda18c2baa0c'
 AND atual.liberado_analise_comercial=1;
GO

CREATE OR ALTER VIEW gold.vw_distancias_origens AS
SELECT f.execucao_id,f.distancia_id,m.codigo_ibge,m.municipio,m.uf,
 p.ponto_id,p.nome AS origem,p.tipo AS tipo_origem,f.tipo_distancia,f.metodo,f.distancia_km,f.tempo_minutos,
 DENSE_RANK() OVER(PARTITION BY f.execucao_id,f.municipio_id,f.tipo_distancia ORDER BY f.distancia_km) AS posicao_proximidade
FROM gold.fato_distancia_municipio_origem f
JOIN gold.vw_carga_aprovada a ON a.execucao_id=f.execucao_id
JOIN gold.dim_municipio m ON m.municipio_id=f.municipio_id
JOIN gold.dim_ponto_distribuicao p ON p.ponto_id=f.ponto_id;
GO

CREATE OR ALTER VIEW gold.vw_preco_referencia AS
SELECT f.execucao_id,f.preco_id,f.produto_id,p.categoria,p.descricao_original,p.estado,
 p.peso_pacote_kg,p.quantidade_pacote,p.quantidade_aproximada,f.preco_pacote_brl,f.preco_unidade_brl,
 f.vigencia_original,f.vigencia_confirmada,f.liberado_orcamento_atual,f.registro_id,f.fonte_id
FROM gold.fato_preco_referencia f
JOIN gold.vw_carga_aprovada a ON a.execucao_id=f.execucao_id
JOIN gold.dim_produto p ON p.produto_id=f.produto_id;
GO

CREATE OR ALTER VIEW gold.vw_estudo_publicado AS
SELECT f.execucao_id,f.observacao_estudo_id,f.registro_id,f.tabela_silver,
 e.estudo,e.tabela_original,e.abrangencia,e.regiao,e.dimensao,e.estrato,e.grupo_alimento,e.curso,e.grupo,e.frequencia,e.indicador_publicado,
 p.rotulo_original AS periodo_referencia,f.percentual,f.n_publicado,f.denominador_publicado,
 f.ic95_inferior,f.ic95_superior,f.p_valor_original,f.pendencia_publicada,f.uso_previsao_vendas_atual,f.fonte_id
FROM gold.fato_estudo_publicado f
JOIN gold.vw_carga_aprovada a ON a.execucao_id=f.execucao_id
JOIN gold.dim_estrato_estudo e ON e.estrato_id=f.estrato_id
JOIN gold.dim_periodo p ON p.periodo_id=f.periodo_id;
GO

