# potencial-de-mercado-e-expansao-comercial — Etapa 21

Views e primeira exploração comercial em SQL. Data: 03/10/2026.

A carga SQL 1 foi reconciliada com 14 regras aprovadas. As views selecionam a maior execucao_id com status APROVADA, 14 registros de reconciliação e nenhum reprovado. Não somam snapshots. Uma carga nova aprovada muda a seleção; para reproduzir uma análise antiga, consultar as fatos filtrando a execucao_id registrada. A aprovação de carga não garante que edições/períodos sejam comercialmente atuais.

## Views

- `gold.vw_carga_aprovada`
- `gold.vw_indicadores_serie`
- `gold.vw_indicadores_ultimo_disponivel`
- `gold.vw_catalogo_comercial`
- `gold.vw_painel_comercial`
- `gold.vw_perfil_comercial`
- `gold.vw_distancias_origens`
- `gold.vw_preco_referencia`
- `gold.vw_estudo_publicado`

## Indicadores e período

O catálogo usa cinco identificadores completos do dicionário Silver, incluindo sua classificação: população estimada 2024, renda domiciliar mediana 2022, urbanização 2022, unidades locais de alimentação 2024 e varejo alimentar 2024. São os mesmos conceitos da EDA. Anos ficam fixos nesta versão para reproduzir o diagnóstico e manter o denominador populacional de 2024 nas taxas. Atualização de período exige conferir cobertura e metadados antes de versionar catálogo, consultas e DAX.

vw_indicadores_ultimo_disponivel mantém o último valor numérico registrado por cidade/indicador, inclusive restrições. Não significa observação do mesmo ano para todos. vw_painel_comercial cria o cruzamento das cidades com o catálogo, mantendo ausência como NULL. valor_publicado conserva o número; valor_comercial fica NULL quando a flag da Gold não libera o uso, salvo a exceção explícita e documentada para o denominador populacional histórico de 2024. Não retrocede anos para preencher faltantes.

vw_perfil_comercial usa MAX apenas para transpor uma observação única por alias, não para selecionar o maior valor entre várias categorias. Validar duplicatas e contagens antes da análise. As duas taxas são unidades_2024 / populacao_2024 * 10000, com NULLIF para bloquear denominador zero.

## Perguntas iniciais

1. Quais cidades concentram unidades locais de alimentação dentro das 12 cidades do escopo?
2. Como porte populacional, renda mediana e concentração comercial diferenciam seus perfis?
3. Qual CD é mais próximo por centroides e qual a diferença para a fábrica?
4. Como o catálogo varia por categoria, estado e peso de apresentação?
5. Qual a cobertura e quais as pendências dos estudos históricos?

Posição por volume CNAE descreve escala; não é ranking final de oportunidade. Unidades locais não são lista de clientes interessados e podem representar canais, compradores ou concorrentes. Densidade baixa não prova mercado disponível. A participação só é calculada quando a cobertura está completa. Proximidade preserva empates e não é rota, tempo, custo ou economia logística comprovada.

PIB permanece fora do painel comercial inicial. Preços sem vigência não são orçamento atual. Estudos são contexto histórico sem vínculo municipal criado. Nenhum escore com pesos, previsão de vendas, elasticidade ou headroom foi produzido.

## Execução

Na mesma instância e banco já usados, executar em ordem:

1. sql/04_criar_views_comerciais.sql
2. sql/05_validar_views_comerciais.sql
3. sql/06_analise_comercial_inicial.sql, após conferir a validação.

04 cria/altera somente nove views; não altera fatos, dimensões nem auditoria. Pode ser repetido para instalar a mesma versão. 05/06 são leitura. CREATE OR ALTER VIEW requer SQL Server 2016 SP1 ou posterior.

Enviar primeiro os resultados de 05: carga selecionada, contagens, duplicatas, catálogo, ausências e imagens. Esperado na base atual: 1 carga; 1.524 na série, 646 últimos valores, 60 no painel, 12 perfis, 60 distâncias, 67 preços, 622 estudos; duplicatas e catálogo inválido sem linhas. Ausências podem existir e exigem interpretação.

## Automação e Power BI

A etapa 21 agora possui executor src/etapa_21_views_comerciais.py e integração à pipeline pela flag --views-comerciais. Instala as nove views e verifica os nove resultados de SQL 05 antes de confirmar a transação. Reprovação reverte as alterações das views. A flag --prioridades-circuitos executa e valida a etapa 21 antes da 22. As etapas 19/20 permanecem automatizadas.

No Power BI, definir medidas sobre uma única carga. Não somar renda mediana, percentuais, distâncias ou preços de produtos distintos. A view de perfil é uma saída descritiva para comparar cidades; o modelo dimensional permanece disponível para filtros. Ainda não conectar o dashboard antes de validar as consultas.

Validação nesta entrega: seleção de cada indicador/classificação conferida como única contra o dicionário local; referências às colunas conferidas com o contrato. Execução das views no SQL Server do usuário ainda pendente. Não há resultado comercial novo confirmado só pela criação dos scripts.

## Correção da população — 03/10/2026

O resultado real do SQL confirmou população numérica em 2024 para as 12 cidades, mas com candidato_eda=0 e motivo FORA_CANDIDATO_EDA. A versão inicial solicitava esse período e exigia a liberação geral da Gold; por isso a população e as taxas ficaram NULL.

A view de painel admite o denominador de 2024 exclusivamente para a chave populacional completa, ano 2024, valor numérico positivo, restrição exatamente FORA_CANDIDATO_EDA e sem pendências de renda ou PIB. Não altera as tabelas nem as flags da Gold. elegivel_uso_painel e criterio_uso_painel tornam essa exceção auditável; liberado_analise_comercial mantém a flag original. O uso histórico é específico à análise das unidades comerciais de 2024 e não constitui liberação geral do dado como atual.

O perfil também mostra populacao_mais_recente e ano_populacao_mais_recente, selecionados pelo marcador de último valor e pela liberação da Gold. Na carga conferida, o ano é 2026. As taxas de 2024 continuam usando exclusivamente população de 2024; nenhum valor é imputado ou trocado por zero. Indicadores disponíveis esperados: cinco por cidade. Os períodos de renda e urbanização continuam explícitos como 2022.

Reexecutar 04 e 05 antes de 06. Os checks adicionais 7–9 mostram as 12 exceções históricas, a população atual em separado e o limite da exceção. A definição nova foi conferida localmente com a Silver; execução e confirmação no SQL Server ainda pendentes.

## Executor Python — complementação em 03/10/2026

O arquivo src/etapa_21_views_comerciais.py executa SQL 04 e SQL 05 no banco exato do projeto. Não altera tabelas de dados nem reconciliação SQL. As regras desta versão são estritas para a carga atual: 1.524/646/60/12/60/67/622 registros, população histórica de 2024 e população mais recente de 2026. Outra cobertura ou período exige revisar contrato/catálogo e regras; não é aprovado silenciosamente.

As views e checks são executados com transação e isolamento SERIALIZABLE; mudanças nas views só são confirmadas após as nove regras aprovadas. Limite de espera de bloqueio: 15 segundos. Execução repetida reinstala as mesmas definições, com uma nova pasta de auditoria por run_id. Execução real requer permissão para criar/alterar views no schema gold.

Comando isolado, na raiz do projeto:

```powershell
python src/etapa_21_views_comerciais.py --servidor "DESKTOP-MAMEBQ8\SQLEXPRESS" --driver "ODBC Driver 17 for SQL Server" --confiar-certificado
```

Saídas: quality/21_views_comerciais/<run_id>/conclusao_21.json, resultados_validacao.json e execucao.log. Conclusão inclui hashes dos SQLs/executor, regras, contagens, execução SQL selecionada e horários UTC. Resultados completos das nove consultas são preservados. Aprovação estrutural não resolve vigência de preços, revisão de PIB ou custo rodoviário.

Pipeline completa: adicionar --views-comerciais --sql-servidor "DESKTOP-MAMEBQ8\SQLEXPRESS" --sql-driver "ODBC Driver 17 for SQL Server" --confiar-certificado. A pipeline completa também executa extrações iniciais; usar o executor isolado para esta conferência. A etapa 22 ainda não precisa ser executada agora.

Verificação do executor: compilação, nove regras e simulação de sucesso/commit e reprovação/rollback com registro de falha. Não equivale a executar a transação DDL no SQL Server. As views já foram conferidas manualmente pelo usuário; o executor Python ainda aguarda sua execução real.
