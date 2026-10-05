USE [potencial-de-mercado-e-expansao-comercial];
GO

-- Complemento IBGE: tabela 9528, variável 706, ano 2024.
-- Categorias 117440 e 117441.
-- Consulta de conferência: não altera tabelas ou views.

WITH complemento AS (
    SELECT *
    FROM (VALUES
        ('3516200', 499),
        ('3513207',  13),
        ('3127107',  77),
        ('3531902',  39),
        ('3544905',  17),
        ('3534302',  94),
        ('3533601',  21),
        ('3521309',  43),
        ('3517406',  97),
        ('3505500', 217),
        ('3151602',  18),
        ('3512100',  17)
    ) AS v (codigo_ibge, complemento_varejo_2024)
),
totais AS (
    SELECT
        m.circuito_chave,
        COUNT(*) AS municipios,
        SUM(m.varejo_alimentar_2024)
            AS varejo_especializado_2024,
        SUM(c.complemento_varejo_2024)
            AS acrescimo_unidades,
        SUM(
            m.varejo_alimentar_2024
            + c.complemento_varejo_2024
        ) AS varejo_alimentar_ampliado_2024
    FROM gold.vw_bi_municipio_comercial AS m
    INNER JOIN complemento AS c
        ON m.codigo_ibge = c.codigo_ibge
    GROUP BY m.circuito_chave
)
SELECT
    c.sequencia_sugerida,
    t.municipios,
    t.varejo_especializado_2024,
    t.varejo_alimentar_ampliado_2024,
    t.acrescimo_unidades,

    CAST(
        100.0 * t.acrescimo_unidades
        / NULLIF(t.varejo_especializado_2024, 0)
        AS decimal(10,2)
    ) AS acrescimo_percentual,

    CAST(
        100.0 * t.varejo_especializado_2024
        / NULLIF(
            SUM(t.varejo_especializado_2024) OVER (), 0
        )
        AS decimal(10,2)
    ) AS participacao_especializado_percentual,

    CAST(
        100.0 * t.varejo_alimentar_ampliado_2024
        / NULLIF(
            SUM(t.varejo_alimentar_ampliado_2024) OVER (), 0
        )
        AS decimal(10,2)
    ) AS participacao_ampliado_percentual,

    DENSE_RANK() OVER (
        ORDER BY t.varejo_especializado_2024 DESC
    ) AS posicao_especializado,

    DENSE_RANK() OVER (
        ORDER BY t.varejo_alimentar_ampliado_2024 DESC
    ) AS posicao_ampliado,

    c.km_sugeridos

FROM totais AS t
INNER JOIN gold.vw_bi_circuito AS c
    ON t.circuito_chave = c.circuito_chave

ORDER BY t.varejo_alimentar_ampliado_2024 DESC;