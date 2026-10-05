# Etapa 30 — Carga SQL de referencias comerciais

Projeto: potencial-de-mercado-e-expansao-comercial.

Extraia na raiz, adicionando src/etapa_30_carga_circuitos_sql.py e substituindo src/run_pipeline.py. Preserve os demais scripts. A criacao das tabelas e automatica; nao precisa executar o DDL separadamente.

```powershell
python src/run_pipeline.py --carregar-circuitos-sql --sql-servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --sql-driver 'ODBC Driver 17 for SQL Server' --confiar-certificado
```

Saida: quality/30_carga_circuitos_sql/<run_id>/conclusao_30.json.
Status esperado: CARGA_CIRCUITOS_SQL_VERIFICADA.

| Objeto SQL | Grao | Linhas da execucao |
|---|---|---:|
| gold.sim_execucao_comercial | Execucao de origem da etapa 29 | 1 |
| gold.dim_circuito_sugerido | Execucao × circuito sugerido | 5 |
| gold.ponte_circuito_municipio | Execucao × municipio vinculado a um circuito | 12 |
| gold.dim_cenario_comercial | Execucao × combinacao consumo/desgaste/margem | 27 |
| gold.fato_custo_viagem_simulado | Execucao × circuito × cenario | 135 |

As tabelas anteriores permanecem preservadas. As novas tabelas usam chaves compostas com run_29 para evitar mistura de versoes. A ponte guarda codigo IBGE e perfil municipal da execucao 29; o vinculo com gold.dim_municipio sera feito pelo codigo IBGE ao preparar o modelo de consumo. Ainda nao ha FK da ponte para essa dimensao. Nao usar relacionamento apenas pelo nome da cidade.

A carga valida hashes, recalcula a etapa 29 e confirma que a carga municipal SQL ativa e a mesma da origem. Usa transacao, bloqueio exclusivo de carga e reconciliacao de todas as colunas com valores decimais em oito casas. Repeticao identica e idempotente; conflitos interrompem a carga. Historico mantido, sem DELETE/TRUNCATE.

A coluna de pedagio e explicitamente estimada OSM, e valores pendentes permanecem NULL. A natureza REFERENCIA_COMERCIAL_SIMULADA identifica todos os fatos. Valores sao referencias de faturamento para o vendedor, nao previsao de venda nem rota fixa do CD.

No SSMS, abra sql/31_conferir_circuitos_comerciais.sql para conferir contagens e o cenario 10 km/l, desgaste R$ 0,20/km, margem 25%. A consulta seleciona a carga comercial mais recentemente carregada que corresponde a carga municipal ativa. Nao somar cenarios diferentes no dashboard. Nao replicar a receita inteira do circuito em cada municipio ao agregar.

Envie conclusao_30.json e os resultados da consulta de conferencia. Preparacao, recalculo e compilacao testados localmente. Conexao, DDL e transacao SQL precisam ser validados no servidor Windows do projeto.
