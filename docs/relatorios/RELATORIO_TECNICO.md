# Relatório técnico

Potencial de mercado e expansão comercial • Fechamento em 04/10/2026

## 1 Objetivo e escopo

A análise apoia o vendedor na escolha de cidades para prospecção e na formação de pedidos que justifiquem viagens a partir de Ribeirão Preto. Abrange 12 municípios de São Paulo e Minas Gerais e cinco circuitos comerciais sugeridos. A definição das rotas reais, disponibilidade dos veículos e programação de entregas cabe ao gerente do centro de distribuição.

A entrega reúne o dashboard Power BI, o modelo SQL e referências simuladas de custo incremental e faturamento de equilíbrio. Não estima vendas futuras, participação da empresa no mercado ou probabilidade de conversão. A qualidade do produto, informada pelo usuário, é uma hipótese comercial a ser testada em prospecção.

## 2 Dados e interpretação

| Indicador | Referência | Uso e restrição |
| --- | --- | --- |
| População | 2024 | Denominador das taxas de estabelecimentos de 2024. |
| Varejo especializado | 2024 | CNAE 47.2: comércio especializado de alimentos, bebidas e fumo; exclui supermercados do grupo 47.1. |
| Alimentação | 2024 | Serviços de alimentação, CNAE 56; segmento distinto do varejo. |
| Renda mediana | 2022 | Contexto socioeconômico municipal; não é renda atual nem previsão de consumo. |
| Urbanização | 2022 | Contexto territorial disponível na base. |
| População mais recente | 2026 na base | Informação separada; não substitui o denominador de 2024. |
| Preços de produtos | Vigência não confirmada | Referências documentais; não determinam margem de contribuição. |

O universo soma 1.437 estabelecimentos de varejo especializado e 721.754 habitantes em 2024. A taxa regional é 19,91 estabelecimentos por 10 mil habitantes. Estabelecimento não equivale a cliente confirmado, rede, capacidade de compra ou ponto elegível para todos os produtos. Supermercados são relevantes ao negócio, mas sua cobertura não está representada por esta contagem.

Exemplo: Sales Oliveira tem 26 estabelecimentos de alimentação e 32 de varejo alimentar especializado. São universos de atividades distintos; a soma não foi usada como número de clientes potenciais. Sua participação regional no varejo é 32 / 1.437 × 100 = 2,23%.

## 3 Arquitetura e rastreabilidade

O processamento organiza dados nas camadas Bronze, Silver e Gold, com execução incremental em Python, arquivos de dados e evidências de qualidade. As etapas 19 e 20 estruturam e carregam o modelo dimensional; a 21 publica views comerciais. As etapas 22 a 29 desenvolvem prioridades, carga, custos, jornada, trajetos, pedágios e cinco circuitos. A 30 carrega as simulações no SQL Server e a 31 publica as views para Power BI.

Os registros de conclusão preservam identificadores de execução e hashes SHA-256 das entradas e scripts. A seleção das views de BI é vinculada à execução comercial compatível com a carga aprovada. Chaves compostas com run e identificador evitam relacionar registros de execuções diferentes.

| Marco | Identificador |
| --- | --- |
| Carga Gold / execução SQL 1 | 20261003T172330Z_8fa91976 |
| Trajetos e pedágios — etapa 28 | 20261003T233002Z_b140700e |
| Priorização — etapa 29 | 20261003T235010Z_0008bbdd |
| Carga comercial SQL — etapa 30 | 20261004T001537Z_2f312086 |
| Views Power BI — etapa 31 | 20261004T002348Z_e1c3260d |

Ambiente local: SQL Server DESKTOP-MAMEBQ8\SQLEXPRESS, ODBC Driver 17 for SQL Server e autenticação do Windows. O armazenamento Azure e o GitHub preservam os artefatos do projeto; a sincronização informada antes desta entrega verificou 547 arquivos, dos quais 422 já eram idênticos e 125 foram enviados. Esse registro não comprova o envio dos relatórios finais ou do PBIX.

## 4 Modelo semântico e medidas

| View | Grão | Linhas |
| --- | --- | --- |
| vw_bi_circuito | Um circuito por execução | 5 |
| vw_bi_municipio_comercial | Um município por execução | 12 |
| vw_bi_cenario_comercial | Um conjunto de parâmetros por execução | 27 |
| vw_bi_custo_viagem_simulado | Um circuito × cenário por execução | 135 |

| Lado 1 | Lado muitos | Chave |
| --- | --- | --- |
| vw_bi_circuito | vw_bi_municipio_comercial | circuito_chave |
| vw_bi_circuito | vw_bi_custo_viagem_simulado | circuito_chave |
| vw_bi_cenario_comercial | vw_bi_custo_viagem_simulado | cenario_chave |

Os três relacionamentos ficam ativos, com direção única da dimensão para o lado muitos. Relações automáticas adicionais foram retiradas para eliminar caminhos ambíguos. A segmentação de cenário filtra as simulações; a segmentação de circuito filtra municípios e custos. Um filtro municipal não deve ser interpretado como cálculo de custo individual da cidade.

Medidas: população e varejo somam as observações municipais; municípios usa contagem distinta de código IBGE. Densidade = varejo × 10.000 / população. Participação = varejo municipal / varejo dos 12 municípios, removendo filtros de município e circuito no denominador. Ranking regional ordena o varejo em ordem decrescente, com empate denso; Cristais Paulista e Planura empatam na posição 11.

Valores monetários das simulações só são exibidos quando há exatamente um cenário selecionado; sem seleção ficam em branco para evitar somar hipóteses diferentes. Renda mediana não é somada entre municípios. O total de densidade é recalculado pela razão dos totais, não pela soma de taxas. Totais de custos entre circuitos foram retirados do visual para não sugerir uma viagem única.

## 5 Modelo de custo incremental

Custo da viagem = (distância / consumo em km/l × preço da gasolina) + (distância × desgaste por km) + pedágio estimado. Receita de equilíbrio = custo da viagem / margem de contribuição. A distância contempla saída e retorno a Ribeirão Preto. Salário fixo do motorista e financiamento fixo do veículo foram excluídos do cálculo incremental, conforme o escopo acordado.

| Parâmetro | Valores considerados | Natureza |
| --- | --- | --- |
| Gasolina | R$ 6,70/l | Referência histórica ANP, semana 27/09 a 03/10/2026, registrada na etapa 24. |
| Consumo | 8, 10 ou 12 km/l | Hipótese para Fiorino nova a gasolina, saída com carga máxima. |
| Desgaste | R$ 0,10, 0,20 ou 0,30/km | Provisão hipotética de manutenção e desgaste. |
| Margem de contribuição | 15%, 25% ou 35% | Hipótese; sem custos reais de produção e venda. |
| Cenário de referência | 10 km/l; R$ 0,20/km; 25% | Referência comparável entre os cinco circuitos. |

As combinações produzem 27 cenários e 135 simulações. Carga máxima foi considerada na escolha de cenários de consumo; não existe ensaio que comprove o consumo nessas condições nem validação de peso, volume, descarga e capacidade real para cada pedido. O veículo sem refrigeração exige validação operacional de conservação e acondicionamento dos produtos antes de entregas; essa análise não certifica adequação do transporte.

A margem precisa representar receita menos custos variáveis de produto e venda antes do custo da rota, evitando dupla contagem. O desgaste é uma reserva por quilômetro, não uma estimativa comprovada de quebra. Custos fixos, horas extras, despesas adicionais e lucro desejado não estão integralmente modelados. A receita de equilíbrio cobre apenas os custos incrementais considerados; não representa lucro líquido ou meta comercial definitiva.

## 6 Distâncias, pedágios e limitações operacionais

As trajetórias foram estimadas com OSRM, usando referências geográficas municipais, e os candidatos a pedágio foram pesquisados no OpenStreetMap/Overpass. A metodologia da etapa 28 compara pontos próximos à geometria do trajeto, mas isso não confirma cobrança, sentido, tarifa e classe aplicável. O status preservado é PEDAGIOS_OSM_NAO_HOMOLOGADOS; o total oficial homologado permanece ausente.

Ausência de um ponto ou tarifa na fonte não comprova isenção. Descontos TAG/DUF não foram presumidos. Antes de orçamento, devem ser confirmados preço do combustível, rota efetiva, endereço do centro de distribuição, categoria tarifária e tarifas oficiais. Tempos estimados não incorporam trânsito real, filas e duração de descarga por cliente. Os cinco agrupamentos são referências comerciais, não rotas operacionais aprovadas.

## 7 Resultados dos circuitos

| Cidades do circuito | Varejo 2024 | Km ida e volta | Receita de equilíbrio |
| --- | --- | --- | --- |
| Cristais Paulista / Franca / Ipuã | 733 | 339,7 | R$ 1.335,60 |
| Barretos / Guaíra | 364 | 328,6 | R$ 1.337,52 |
| Sales Oliveira / Nuporanga / Morro Agudo / Orlândia | 201 | 233,8 | R$ 933,58 |
| Frutal | 113 | 419,1 | R$ 1.726,42 |
| Planura / Colômbia | 26 | 382,6 | R$ 1.599,53 |

Todas as sequências começam e terminam em Ribeirão Preto. Os dois maiores agrupamentos reúnem 1.097 estabelecimentos, ou 76,34% do universo. O circuito Sales Oliveira / Nuporanga / Morro Agudo / Orlândia combina 201 estabelecimentos com a menor receita de equilíbrio de referência. Os trajetos de Frutal e Planura / Colômbia têm maior esforço relativo e devem depender de formação de pedidos e encaixe logístico.

| Circuito | Receita mínima simulada | Receita máxima simulada |
| --- | --- | --- |
| Cristais Paulista / Franca / Ipuã | R$ 748,59 | R$ 2.831,73 |
| Barretos / Guaíra | R$ 756,65 | R$ 2.815,20 |
| Sales Oliveira / Nuporanga / Morro Agudo / Orlândia | R$ 525,45 | R$ 1.972,88 |
| Frutal | R$ 979,71 | R$ 3.624,74 |
| Planura / Colômbia | R$ 911,13 | R$ 3.348,23 |

Esses extremos resultam da variação conjunta de consumo, desgaste e margem. Não são intervalos de confiança nem probabilidades de faturamento. Diferenças pequenas de custo entre circuitos não justificam conclusões definitivas diante de tarifas e parâmetros não homologados.

## 8 Perfil municipal e priorização

| Município | Varejo | Participação | Por 10 mil | Renda 2022 |
| --- | --- | --- | --- | --- |
| Franca | 690 | 48,02% | 18,94 | R$ 1.250,00 |
| Barretos | 295 | 20,53% | 23,30 | R$ 1.328,00 |
| Frutal | 113 | 7,86% | 18,54 | R$ 1.200,00 |
| Orlândia | 93 | 6,47% | 23,73 | R$ 1.266,67 |
| Guaíra | 69 | 4,80% | 17,07 | R$ 1.250,00 |
| Morro Agudo | 55 | 3,83% | 19,26 | R$ 1.120,00 |
| Sales Oliveira | 32 | 2,23% | 27,46 | R$ 1.333,33 |
| Ipuã | 31 | 2,16% | 21,10 | R$ 1.178,00 |
| Nuporanga | 21 | 1,46% | 27,81 | R$ 1.333,33 |
| Colômbia | 14 | 0,97% | 20,65 | R$ 1.070,67 |
| Planura | 12 | 0,84% | 10,45 | R$ 1.050,00 |
| Cristais Paulista | 12 | 0,84% | 12,57 | R$ 1.200,00 |

Franca e Barretos lideram a escala observada, com 985 estabelecimentos e 68,55% do universo. Nuporanga e Sales Oliveira apresentam as maiores densidades e rendas medianas desta seleção, mas menor escala absoluta. A renda contextualiza a análise; não foi convertida em demanda, ticket ou pontuação arbitrária. Concorrência, compradores ativos e volume por cliente são desconhecidos.

A orientação combina prospecção dos polos Franca e Barretos com desenvolvimento do circuito próximo de Orlândia, Morro Agudo, Sales Oliveira e Nuporanga. Cristais Paulista e Ipuã entram no agrupamento de Franca; Guaíra no de Barretos. Frutal, Planura e Colômbia permanecem no plano, condicionadas à consolidação de pedidos. Não existe um valor mínimo igual por cidade: uma venda maior pode sustentar paradas menores no mesmo circuito, desde que a contribuição conjunta cubra a viagem e a logística permita.

## 9 Verificação e conclusão

O registro da etapa 31 apresenta nove regras com zero divergências: unicidade de chaves de circuito, município e cenário; unicidade do grão da fato; fatos sem dimensão; municípios sem circuito; agregação de varejo; receita de referência; e equilíbrio. O dashboard foi conferido pelo usuário quanto aos totais, seleção de cenário e limpeza do filtro de circuito, retornando aos 12 municípios.

Valores ausentes continuam ausentes, sem substituição automática por zero. A população histórica de 2024 foi admitida como denominador do painel pela exceção DENOMINADOR_HISTORICO_2024, preservando a restrição FORA_CANDIDATO_EDA. As 67 referências de preço mantêm vigência não confirmada e lacunas de peso ou quantidade de pacote; não foram usadas para inventar margens.

A análise está concluída como referência comercial com limitações explícitas. Para uso operacional, registrar pedidos, margem efetiva, consumo com carga, manutenção e tarifas confirmadas; recalcular o equilíbrio com esses dados. Grandes entregas com descarga demorada podem justificar veículo dedicado, como sugestão ao gestor e condicionada à existência de pedidos reais.

## 10 Fontes e reprodução

Fontes internas verificadas: circuitos_comerciais.json e municipios_prioridades.json da etapa 29; conclusao_30.json; conclusao_31.json; sql/32_views_power_bi.sql e documentação das etapas 27 a 29. Os números publicados neste relatório correspondem ao run_29 indicado acima. Os arquivos de conclusão preservam a rastreabilidade das fontes municipais e documentais.

Fontes externas arquivadas pelo pipeline: ANP para gasolina; OSRM para trajetórias; OpenStreetMap/Overpass para candidatos a pedágio; portais de concessionárias e ARTESP para tentativas de conferência. Consulta de rotas: https://project-osrm.org/docs/v26.4.0/http/ . Overpass: https://overpass-api.de/api/interpreter . Os dados OSM têm atribuição a OpenStreetMap contributors e licença ODbL. Este relatório não realizou nova pesquisa de tarifas.

Reprodução no ambiente original: python src/run_pipeline.py --views-power-bi --sql-servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --sql-driver 'ODBC Driver 17 for SQL Server' --confiar-certificado. Requer as cargas aprovadas das etapas anteriores e o ambiente configurado. No Power BI, atualizar as views, selecionar um cenário e conferir os totais 12 / 1.437 / 721.754 / 19,91. A autorização de confiança de certificado corresponde ao ambiente local informado.
