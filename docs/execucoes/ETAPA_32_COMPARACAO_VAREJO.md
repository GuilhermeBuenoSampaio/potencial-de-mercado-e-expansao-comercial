# Etapa 32 — Comparação do varejo atual e ampliado

Esta etapa acrescenta a cobertura comercial sem substituir as etapas 01–31, o run_29, as rotas ou os cenários. Execute o script próprio da etapa 32; o arquivo run_pipeline.py existente permanece preservado.

## Executar na raiz do projeto

```powershell
python src/etapa_32_comparacao_varejo.py --servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --driver 'ODBC Driver 17 for SQL Server' --confiar-certificado
```

Requer internet, pyodbc e as views BI verificadas da etapa 31. A confiança de certificado refere-se ao servidor local informado.

## Fonte e composição

IBGE, tabela 9528, variável 706 (Número de unidades locais), ano 2024, classificação 12762. O script confirma as definições pelos metadados oficiais antes de carregar os dados.

- 117443: 47.2, varejo especializado atual.
- 117440: 47.11-3, supermercados e hipermercados.
- 117441: 47.12-1, minimercados, mercearias e armazéns.

O varejo alimentar ampliado desta análise soma essas três categorias distintas. Não representa todo o comércio varejista não especializado nem engloba toda atividade alimentar. Não somar o grupo pai 47.1 ou Total a seus componentes. Categoria principal não comprova interesse ou volume de compra. Alimentação CNAE 56 permanece separada.

## Arquivos e rastreabilidade

O script salva dados e metadados originais em datalake/01_bronze_raw/<run>/comparacao_varejo, dados normalizados em datalake/02_silver/<run>/comparacao_varejo e comparações exportadas em datalake/03_gold/<run>/comparacao_varejo. O registro quality/32_comparacao_varejo/<run>/conclusao_32.json contém URLs, hashes SHA-256, execução comercial vinculada, verificações, totais e status.

Supressões, ausências, categorias duplicadas ou cobertura diferente dos 12 municípios interrompem a etapa. Nenhum valor ausente é convertido em zero. A categoria 47.2 recém-consultada deve coincidir com o indicador no SQL; revisão da fonte exige investigação e não é absorvida silenciosamente.

## SQL aditivo

Novas tabelas: gold.execucao_comparacao_varejo e gold.complemento_varejo_municipal. Cada coleta usa run_32 único e referencia run_29. São inserções históricas, sem atualização dos valores anteriores.

Novas views:

- gold.vw_bi_execucao_comparacao_varejo: última execução verificada compatível com o run_29 ativo.
- gold.vw_bi_municipio_varejo_comparado: 12 linhas, informações originais e indicadores comparativos.
- gold.vw_bi_circuito_varejo_comparado: 5 linhas, informações originais e indicadores comparativos.

Se o run_29 ativo mudar sem complemento correspondente, as views comparativas não reaproveitam dados silenciosamente. Reexecutar a etapa 32.

Publicação, inserções e reconciliação SQL são transacionais. Erros antes do commit desfazem a carga; os arquivos locais e o registro de falha ficam como evidência. A execução não altera as views antigas nem a fato de custos. Não executar o DDL manualmente: a etapa Python coordena e valida a carga.

## Resultado de referência conferido em 05/10/2026

Especializado: 1.437. Ampliado: 2.589. Acréscimo: 1.152 (80,17%). Totais ampliados por circuito: Franca 1.288; Barretos 678; Orlândia e demais 372; Frutal 190; Planura/Colômbia 61. Não há mudança na ordem dos cinco circuitos. Ipuã supera Sales Oliveira; Planura supera Cristais Paulista. Esses são controles históricos, não substituem a coleta nem garantem que a fonte não revise os dados.

## Cálculos e Power BI

Acréscimo percentual = (ampliado − especializado) / especializado × 100. Participação de cada recorte usa seu próprio total. Densidade usa população 2024. Os percentuais SQL estão em escala 0–100; dividir por 100 antes de usar o formato percentual no Power BI, ou calcular pelas medidas DAX.

Os rankings das views são regionais e não mudam com filtros no relatório. Para totais e participações filtrados, usar medidas adequadas. Densidades totais devem ser razão das somas e não soma/média de taxas. Rankings, percentuais e densidades das colunas não devem ser somados.

Após status COMPARACAO_VAREJO_VERIFICADA, importar as duas novas views. Manter a página anterior para comparação e criar página nova. Na nova modelagem, relacionar circuito_chave (circuito comparado 1 → município comparado muitos), com filtro único. A dimensão cenário e a fato de custos existentes permanecem utilizáveis, com circuito comparado 1 → fato de custos muitos. Evitar caminhos duplicados: não manter simultaneamente as duas dimensões de circuito filtrando os mesmos visuais de comparação.

O faturamento de equilíbrio e os custos permanecem os mesmos para cada cenário: mais estabelecimentos não implica redução automática do custo nem venda efetiva. Pedágios continuam não homologados e consumo, desgaste e margem permanecem hipotéticos. Relatórios e textos de divulgação serão atualizados após verificação da carga e do dashboard.

## Verificação local do pacote

Sintaxe Python e casos de validação de cobertura, duplicidade e supressão testados. A conexão ODBC e o DDL precisam ser executados no SQL Server do usuário; não foram testados contra uma instância SQL nesta sessão.
