USE [potencial-de-mercado-e-expansao-comercial];
GO
-- Estrutura, colunas e relacionamentos; executar apos a criacao.
SELECT s.name AS esquema,t.name AS tabela,COUNT(c.column_id) AS colunas
FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
JOIN sys.columns c ON c.object_id=t.object_id
WHERE s.name IN ('gold','audit','quality')
GROUP BY s.name,t.name ORDER BY s.name,t.name;
SELECT s.name AS esquema,t.name AS tabela,c.name AS coluna,ty.name AS tipo,
       c.max_length,c.precision,c.scale,c.is_nullable,c.is_identity
FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
JOIN sys.columns c ON c.object_id=t.object_id JOIN sys.types ty ON ty.user_type_id=c.user_type_id
WHERE s.name IN ('gold','audit','quality') ORDER BY s.name,t.name,c.column_id;
SELECT fk.name AS relacionamento,OBJECT_SCHEMA_NAME(fk.parent_object_id) AS esquema,
       OBJECT_NAME(fk.parent_object_id) AS tabela,OBJECT_NAME(fk.referenced_object_id) AS referencia,
       fk.is_disabled,fk.is_not_trusted
FROM sys.foreign_keys fk WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) IN ('gold','audit','quality')
ORDER BY tabela,relacionamento;
