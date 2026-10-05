-- 1. Localizar colunas relacionadas ao comércio.
USE [potencial-de-mercado-e-expansao-comercial];
GO
SELECT
    TABLE_SCHEMA AS esquema,
    TABLE_NAME AS objeto,
    COLUMN_NAME AS coluna
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA IN ('gold', 'silver')
  AND (
      COLUMN_NAME LIKE '%varejo%'
      OR COLUMN_NAME LIKE '%mercado%'
      OR COLUMN_NAME LIKE '%aliment%'
      OR COLUMN_NAME LIKE '%comercio%'
  )
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;

-- 2. Conferir os indicadores e suas classificações.
-- A busca no JSON evita presumir nomes de campos do catálogo.
SELECT i.*
FROM gold.dim_indicador AS i
CROSS APPLY (
    SELECT i.*
    FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
) AS j(definicao_json)
WHERE j.definicao_json LIKE '%9528%'
   OR j.definicao_json LIKE '%supermerc%'
   OR j.definicao_json LIKE '%minimerc%'
   OR j.definicao_json LIKE '%mercearia%'
ORDER BY i.indicador_chave;