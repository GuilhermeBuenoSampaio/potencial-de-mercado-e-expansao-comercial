USE [potencial-de-mercado-e-expansao-comercial];
GO
-- 1. Uma carga selecionada: deve corresponder a audit.execucao_carga aprovada.
SELECT * FROM gold.vw_carga_aprovada;
-- 2. Contagens da base atual: 1524,646,60,12,60,67,622.
SELECT 'serie' AS objeto,COUNT_BIG(*) AS linhas FROM gold.vw_indicadores_serie
UNION ALL SELECT 'ultimo_disponivel',COUNT_BIG(*) FROM gold.vw_indicadores_ultimo_disponivel
UNION ALL SELECT 'painel_comercial',COUNT_BIG(*) FROM gold.vw_painel_comercial
UNION ALL SELECT 'perfil_comercial',COUNT_BIG(*) FROM gold.vw_perfil_comercial
UNION ALL SELECT 'distancias',COUNT_BIG(*) FROM gold.vw_distancias_origens
UNION ALL SELECT 'precos',COUNT_BIG(*) FROM gold.vw_preco_referencia
UNION ALL SELECT 'estudos',COUNT_BIG(*) FROM gold.vw_estudo_publicado;
-- 3. Zero linhas: pares duplicados no painel.
SELECT codigo_ibge,alias,COUNT(*) AS ocorrencias FROM gold.vw_painel_comercial
GROUP BY codigo_ibge,alias HAVING COUNT(*)<>1;
-- 4. Zero linhas: categoria inexistente ou mais de uma fonte para mesmo grao no catalogo.
SELECT c.alias,COUNT(i.indicador_id) AS indicadores_encontrados
FROM gold.vw_catalogo_comercial c LEFT JOIN gold.dim_indicador i ON i.indicador_chave=c.indicador_chave
GROUP BY c.alias HAVING COUNT(i.indicador_id)<>1;
-- 5. Explicitar ausencias/restricoes. Nao substituir por zero.
SELECT codigo_ibge,municipio,alias,status_valor,motivo_restricao
FROM gold.vw_painel_comercial WHERE valor_comercial IS NULL;
-- 6. Zero linhas: imagens nunca liberadas como novas observacoes.
SELECT q.registro_id FROM quality.evidencia_imagem q JOIN gold.vw_carga_aprovada a ON a.execucao_id=q.execucao_id
WHERE q.incluir_como_nova_observacao=1;

-- 7. Doze denominadores historicos, com restricao original preservada.
SELECT municipio,ano_referencia,valor_publicado,valor_comercial,
 liberado_analise_comercial,elegivel_uso_painel,criterio_uso_painel,motivo_restricao
FROM gold.vw_painel_comercial WHERE alias='populacao_2024' ORDER BY municipio;
-- 8. Doze perfis completos: comparar periodos e taxas.
SELECT municipio,populacao_2024,populacao_mais_recente,ano_populacao_mais_recente,
 indicadores_disponiveis,alimentacao_por_10mil_2024,varejo_alimentar_por_10mil_2024
FROM gold.vw_perfil_comercial ORDER BY municipio;
-- 9. Zero linhas: excecao nunca deve atingir outro indicador/periodo.
SELECT * FROM gold.vw_painel_comercial
WHERE liberado_analise_comercial=0 AND valor_comercial IS NOT NULL
 AND (alias<>'populacao_2024' OR ano_referencia<>2024
 OR motivo_restricao IS NULL OR motivo_restricao<>'FORA_CANDIDATO_EDA');
