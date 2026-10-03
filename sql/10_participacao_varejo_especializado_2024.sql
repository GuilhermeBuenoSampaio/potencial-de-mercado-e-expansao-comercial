USE [potencial-de-mercado-e-expansao-comercial];
GO

SELECT
    codigo_ibge,
    municipio,
    uf,
    varejo_alimentar_2024 AS unidades_varejo_especializado_2024,

    SUM(varejo_alimentar_2024) OVER ()
        AS total_varejo_especializado_escopo_2024,

    CASE
        WHEN COUNT(varejo_alimentar_2024) OVER () = COUNT(*) OVER ()
        THEN CAST(
            CAST(varejo_alimentar_2024 AS decimal(18, 6))
            * 100.0
            / NULLIF(SUM(varejo_alimentar_2024) OVER (), 0)
            AS decimal(10, 4)
        )
        ELSE NULL
    END AS participacao_varejo_especializado_percentual,

    DENSE_RANK() OVER (
        ORDER BY varejo_alimentar_2024 DESC
    ) AS posicao_volume_varejo_especializado

FROM gold.vw_perfil_comercial
ORDER BY
    varejo_alimentar_2024 DESC,
    municipio;