# potencial-de-mercado-e-expansao-comercial

## Fonte confiável: requisitos do projeto

A fonte deve identificar instituição e autoria, metodologia, universo, definição, unidade, território, período de referência e limitações. A consulta precisa ser reproduzível e a resposta original preservada com URL, data de coleta e SHA-256. Preferimos o produtor oficial do indicador. Ser oficial não elimina revisões, supressões, resultados preliminares ou diferenças de conceito.

Dados de outra escala territorial não podem ser apresentados como municipais. Dado ausente não vira zero. Fonte secundária sem período ou metodologia serve como pista de pesquisa, não como substituição automática da fonte primária. Divergências permanecem registradas até conferência.

Caravela é fonte secundária da análise original. Registrar a página de cada cidade, indicador, referência declarada, data de consulta e metodologia, quando disponíveis. Sem esses elementos, o dado permanece pendente. As publicações antigas de consumo também ficam identificadas como históricas.

## Atualidade: limites propostos para este projeto

| Grupo | Critério | Uso quando ultrapassado |
|---|---|---|
| População estimada anual | Último ano oficial disponível; até 1 ano de defasagem | Contexto com alerta |
| PIB municipal | Último ano disponível; até 3 anos | Contexto; não tratar como atividade corrente |
| Emprego, salários e estabelecimentos anuais | Último ano disponível; até 2 anos | Contexto com alerta |
| Renda, idade, urbanização e densidade censitárias | Último Censo disponível; explicitar ano e caráter estrutural | Revisar quando houver nova divulgação; não atualizar artificialmente |
| Geografia e área | Última versão oficial identificável | Endpoint sem versão explícita: conferência pendente |
| Distância, tempo e pedágio rodoviários | Revisão até 90 dias; antecipar se houver alteração de rota/origem | Recalcular antes da decisão operacional |
| Preço de combustível | Referência de até 30 dias; idealmente última semana disponível | Atualizar antes do orçamento |
| Preços comerciais, frete e comissão | Última tabela vigente; conferir na data da proposta | Não presumir validade pela data do arquivo |
| Consumo do veículo | Mesma versão/ano/motor; validar com uso real | Não substituir por outro modelo/ano |

Estes limites são decisões metodológicas do projeto, não exigências do IBGE. A data de consulta não substitui o ano do dado. O coletor registra a defasagem de cada observação, preserva séries anteriores e separa o último valor numérico disponível. Um setor pode ter última observação em 2021 mesmo que a tabela tenha PIB total de 2023.

## Coleta implementada

APIs oficiais: https://servicodados.ibge.gov.br/api/docs/agregados?versao=3 e https://servicodados.ibge.gov.br/api/docs/localidades . Geografia: https://servicodados.ibge.gov.br/api/docs/malhas?versao=3 . Metadados e períodos são consultados antes dos valores.

| Tabela | Indicadores | Cuidados |
|---|---|---|
| 6579 | População estimada e série recente | Pessoas, não milhares |
| 5938 | PIB nominal e participação setorial no VAB | Mil reais convertidos em reais com multiplicador registrado; serviços excluem administração pública; comércio não é uma parcela separada nessa seleção |
| 9509 | Unidades locais, pessoal ocupado, assalariados, salário médio em reais/SM e massa salarial | Postos locais não equivalem a residentes ocupados; não concatenar automaticamente com a série anterior à mudança de metodologia |
| 4714 | População censitária, área e densidade | Referência censitária |
| 10295 | Renda domiciliar mensal per capita média e mediana | Não é PIB por habitante; resultados censitários, universo restrito conforme metadados |
| 10296 | Quantidade e percentual de moradores por faixas de renda per capita | Preservar classificação e denominador; não transformar em classes familiares A–E |
| 9923 | População urbana e rural | Dados censitários |
| 9528 | Unidades e empregos em alimentação, varejo alimentar e fabricação de outros alimentos | Categorias CNAE distintas; não somar níveis sobrepostos; não implica clientes ou concorrentes confirmados |
| Pesquisa 38, indicador 47001 | PIB per capita oficial | Unidade validada nos metadados; não é renda mensal |
| Malhas/metadados | Centroides municipais e área; regionalização via Localidades | Versão não explicitada pelo endpoint; centroide não é endereço do CD |

Foram identificados na consulta de teste de 30/09/2026 população de 2026, PIB de 2023 e CEMPRE de 2024. O script não fixa esses anos: consulta os períodos disponíveis em cada execução. Detalhamento setorial do PIB pode permanecer em 2021, com anos posteriores sem valor.

## Índices e cálculos

Recalculamos crescimento nominal acumulado do PIB em cinco anos e taxa anualizada, usando um par exato de anos separado por cinco anos. Não aplicar crescimento acumulado de cinco anos como se fosse taxa anual. Não inferir crescimento real sem deflator adequado, nem vendas futuras a partir do PIB sem validar a relação.

Calculamos distâncias geodésicas entre centroides das 12 cidades e os cinco municípios de origem, incluindo a fábrica. Essas distâncias ajudam a triagem geográfica, mas não determinam o melhor CD, quilômetros rodados, consumo ou custo de entrega. Para isso são necessários endereços reais e rotas rodoviárias.

A comparação registra as células originais de população, PIB, salário em SM e pessoal ocupado, seu hash e a observação oficial mais recente. Comparabilidade permanece pendente até validar ano, unidade e definição da base antiga. Não alteramos o XLSX original.

Permanecem pendentes: significado de renda per capita original; classes A–E; conceito das proporções setoriais; percentual original de ocupação; fonte e validade dos rankings de produtos; consumo Fiorino por versão; alegação de mercado de R$ 81 bilhões; projeções de venda e de PIB. Dados censitários de renda não devem ser atualizados por inflação e tratados como uma nova medição oficial.

## Indicadores adicionais recomendados

1. Número de estabelecimentos compatíveis com cada produto: lanchonetes, restaurantes, padarias, mercados e distribuidores, com validação por CNAE e situação cadastral. CEMPRE oferece contexto agregado; CNPJ ativo pode aprofundar a prospecção.
2. Renda mediana, faixas de renda e população urbana: ajudam a segmentar demanda sem confundir PIB com renda disponível.
3. Estrutura etária e domicílios: incluir na próxima ampliação, com a tabela censitária e classificação documentadas.
4. Densidade de potenciais compradores por 10 mil habitantes e crescimento de unidades locais, usando períodos compatíveis.
5. Tempo de viagem, pedágio, preço de combustível, frequência de visitas e volume por entrega, a partir dos endereços efetivos.
6. Indicadores comerciais observados: conversão de visitas, recompra, ticket, mix, sazonalidade, preços de concorrentes, comissão e margem do vendedor por produto.

Um índice de prioridade comercial será definido depois da validação: critérios separados de demanda, acesso logístico e esforço comercial, pesos explícitos e análise de sensibilidade. A razão potencial/custo da planilha não deve ser chamada de ROI ou lucro sem períodos e custos completos. Custos fabris não são o foco desta análise comercial.

## Saídas e execução

Todos os scripts ficam em `src`. Executar a etapa isolada no terminal aberto na raiz:

```powershell
python src/etapa_06_coleta_municipal.py
```

Executar todas as etapas e acrescentar a coleta:

```powershell
python src/run_pipeline.py --coletar-externos
```

A coleta requer internet, usa apenas biblioteca padrão para HTTP e mantém openpyxl já previsto para ler o original. Três tentativas por URL, timeout de 45 segundos. Falhas são registradas; uma coleta parcial não é marcada como completa. O coletor não usa login, SQL Server ou Azure nesta etapa.

Cada execução gera uma pasta própria. Respostas oficiais e manifesto ficam em `datalake/00_landing/fontes_externas/<run_id>/ibge`. Tabelas em JSON, comparação, índices, geografia, distâncias e consulta HTML ficam em `datalake/01_bronze/<run_id>/coleta_municipal`. O HTML abre no navegador para conferência. Nenhum CSV é criado. A exportação para XLSX e a promoção para Silver serão tratadas após validar os conceitos.

Conclusão e política ficam em `quality/06_coleta_municipal/<run_id>`. Conferir falhas, marcadores, pendências, ano, unidade, classificação e atualização antes de usar os dados em recomendações comerciais.
