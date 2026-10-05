USE [potencial-de-mercado-e-expansao-comercial];
GO

-- Complemento IBGE: tabela 9528, variável 706, ano 2024.
-- Categorias 117440 e 117441.
-- Valores consultados em 05/10/2026.

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
    ) AS v (
        codigo_ibge,
        complemento_varejo_2024
    )
),
base AS (
    SELECT
        p.codigo_ibge,
        p.municipio,
        p.populacao_2024,
        p.varejo_alimentar_2024
            AS varejo_especializado_2024,
        p.varejo_alimentar_2024
            + c.complemento_varejo_2024
            AS varejo_alimentar_ampliado_2024
    FROM gold.vw_perfil_comercial AS p
    INNER JOIN complemento AS c
        ON p.codigo_ibge = c.codigo_ibge
)
SELECT
    codigo_ibge,
    municipio,
    populacao_2024,
    varejo_especializado_2024,
    varejo_alimentar_ampliado_2024,

    DENSE_RANK() OVER (
        ORDER BY varejo_especializado_2024 DESC
    ) AS posicao_varejo_especializado,

    DENSE_RANK() OVER (
        ORDER BY varejo_alimentar_ampliado_2024 DESC
    ) AS posicao_varejo_ampliado,

    CAST(
        100.0 * varejo_especializado_2024
        / NULLIF(
            SUM(varejo_especializado_2024) OVER (), 0
        )
        AS decimal(10,2)
    ) AS participacao_especializado_percentual,

    CAST(
        100.0 * varejo_alimentar_ampliado_2024
        / NULLIF(
            SUM(varejo_alimentar_ampliado_2024) OVER (), 0
        )
        AS decimal(10,2)
    ) AS participacao_ampliado_percentual,

    CAST(
        10000.0 * varejo_especializado_2024
        / NULLIF(populacao_2024, 0)
        AS decimal(10,2)
    ) AS especializado_por_10mil,

    CAST(
        10000.0 * varejo_alimentar_ampliado_2024
        / NULLIF(populacao_2024, 0)
        AS decimal(10,2)
    ) AS ampliado_por_10mil

FROM base
ORDER BY varejo_alimentar_ampliado_2024 DESC;