# Relatório descritivo parcial da EDA

**Projeto:** `potencial-de-mercado-e-expansao-comercial`  
**Data:** 30/09/2026 — horário de São Paulo  
**Abrangência:** estrutura e cobertura, análise univariada e análise bivariada municipal.  
**Status:** EDA em andamento; este relatório não constitui recomendação definitiva de expansão.

## 1. Objetivo e contexto comercial

A análise investiga diferenças entre 12 cidades para apoiar a abertura de mercado de um vendedor de salgados congelados. O objetivo é compreender a dimensão dos municípios, o perfil de renda dos moradores, a estrutura de estabelecimentos e, nos próximos blocos, a evolução e a localização dos mercados.

As cidades são Franca, Cristais Paulista, Morro Agudo, Sales Oliveira, Orlândia, Nuporanga, Ipuã, Guaíra, Barretos e Colômbia, em São Paulo; Frutal e Planura, em Minas Gerais. A fábrica fica em São Carlos, com CDs em Ribeirão Preto, Campinas, Sorocaba e São Paulo.

A perspectiva é comercial. Preços pertencem a cada produto/pacote; custos fabris não são o eixo desta investigação. Estudos históricos de consumo servem como contexto e não foram convertidos em demanda municipal atual.

## 2. Evidências e estado das conferências

O relatório utiliza os resultados enviados pelo usuário, com seus períodos e definições preservados.

| Bloco | Evidência conferida | Situação |
|---|---|---|
| Etapa 11 — estrutura | Conclusão e log da execução `20260930T224655Z_588a76d1` | 77 regras aprovadas; nenhuma reprovada; registros consistentes |
| Etapa 12 — univariada | Conclusão, log e três tabelas JSON da execução `20260930T230134Z_f742a1e5` | 130 regras aprovadas; hashes dos JSON coincidem com a conclusão; estatísticas recalculadas e extremos reconciliados |
| Etapa 13 — bivariada | Oito correlações, 104 cenários de sensibilidade e documento de método | Resultados e diferenças dos coeficientes conferidos; conclusão e log desta execução ainda não recebidos |

As etapas 11 e 12 utilizaram a base EDA `20260930T221011Z_112bce2b`. A etapa 13 teve 157 verificações aprovadas na reprodução local de desenvolvimento; isso não substitui a conferência da conclusão e do log da execução do usuário.

Os JSON recebidos permitiram examinar os resultados analíticos. Os Parquet de saída dessas execuções não foram anexados para conferência física independente; suas reconciliações são registradas pelos controles das etapas.

## 3. Estrutura, cobertura e períodos

| Medida | Resultado |
|---|---:|
| Cidades de expansão | 12 |
| Combinações de indicador/classificação | 56 |
| Registros cidade × indicador no painel | 672 |
| Registros com valor numérico | 597 |
| Registros sem valor numérico | 75 |
| Cobertura numérica | 88,84% |
| Indicadores/classificações com cobertura completa | 43 |
| Indicadores/classificações com cobertura incompleta | 13 |
| Últimos valores disponíveis em anos anteriores ao período comum | 49 |
| Pendências documentais preservadas | 6 |

A cobertura é suficiente para iniciar várias comparações, mas não significa que todos os indicadores sejam igualmente adequados para decisões comerciais. As 56 combinações incluem categorias de uma mesma variável e indicadores equivalentes em tabelas distintas; não são 56 dimensões independentes.

Os 75 registros sem valor mantêm marcadores da fonte. Não foram convertidos em zero, nem foi inferido um mecanismo MCAR, MAR ou MNAR. Os 49 valores mais antigos permanecem disponíveis como contexto e não substituem silenciosamente os registros ausentes no período comum.

### Limitação concentrada na composição setorial do PIB

As quatro participações setoriais do PIB não possuem valores numéricos no painel de 2023 para nenhuma das 12 cidades. Isso corresponde a 48 das 75 ausências, ou 64% delas. Assim, essa ausência de cobertura não está distribuída uniformemente entre indicadores.

Uma análise histórica poderá examinar o período com dados disponíveis, identificando-o separadamente. Não será feita substituição silenciosa de 2023 por outro ano.

## 4. Dimensão dos mercados e estrutura de estabelecimentos

| Cidade | População estimada — 2026 | Unidades locais CNAE 56 — Alimentação — 2024 |
|---|---:|---:|
| Franca | 366.534 | 869 |
| Barretos | 127.276 | 474 |
| Frutal | 61.588 | 166 |

Franca representa 50,52% da população estimada das 12 cidades. Franca e Barretos representam juntas 69,88% das unidades locais da divisão CNAE 56 — Alimentação no conjunto analisado.

A população média entre cidades é de aproximadamente 60.466 habitantes, enquanto a mediana é de 21.598. As cidades maiores elevam a média; ela não representa bem o porte da cidade típica desse conjunto. As duas medidas são descritivas dos municípios selecionados.

**Interpretação comercial:** Franca e Barretos oferecem maior escala demográfica e mais estabelecimentos para investigar como canais de venda. A quantidade cadastral não confirma compra de salgados congelados, abertura para fornecedores, volume de pedidos, concorrência ou demanda não atendida.

**Limitação temporal:** população de 2026 e estabelecimentos de 2024 aparecem lado a lado para descrever escalas, não para calcular uma razão. Na análise bivariada, as razões usam população de 2024, alinhada ao ano dos estabelecimentos.

## 5. Produção econômica e renda dos moradores

| Cidade | PIB por habitante — 2023 | Renda domiciliar mensal per capita média — 2022 |
|---|---:|---:|
| Nuporanga | R$ 167.167,74 | R$ 1.765,43 |
| Colômbia | R$ 112.148,60 | R$ 1.282,70 |
| Barretos | R$ 54.826,42 | R$ 1.844,44 |
| Franca | R$ 40.777,87 | R$ 1.734,79 |

Nuporanga tem o maior PIB por habitante do conjunto, mas Barretos apresenta a maior renda domiciliar per capita média. Colômbia tem o segundo maior PIB por habitante e a menor renda domiciliar per capita média.

Essas diferenças mostram por que produção econômica por habitante e renda dos moradores devem ser tratadas como conceitos distintos. PIB por habitante não equivale a rendimento mensal disponível para consumo. Os indicadores também pertencem a anos diferentes.

A renda domiciliar per capita mediana varia de R$ 1.050,00 em Planura a R$ 1.333,33 em Nuporanga e Sales Oliveira, em 2022. Ela descreve o ponto central da distribuição de renda na população de referência de cada município, não a mediana de salários dos trabalhadores locais.

Orlândia apresenta o maior salário médio mensal do conjunto em 2024, R$ 4.170,32. Salário no local de trabalho e renda domiciliar não são intercambiáveis: possuem universos e definições diferentes.

**Implicação:** o aprofundamento precisa avaliar dimensão de mercado e renda separadamente. Um ranking baseado somente no PIB por habitante produziria uma leitura inadequada do poder de compra dos moradores.

## 6. Urbanização e localização dos públicos

Em 2022, a participação urbana era de 98,52% em Franca, 82,28% em Cristais Paulista e 70,66% em Colômbia. A mediana desse percentual entre as cidades era de 96,535%.

Essas diferenças justificam investigar a distribuição dos estabelecimentos e os endereços efetivos de atendimento. O percentual urbano, sozinho, não determina custo de entrega, facilidade de acesso ou renda.

Ser um município do interior não significa ter baixa urbanização. O indicador mede a parcela dos moradores em domicílios urbanos, não produtividade, diversificação econômica ou qualidade dos empregos. A ideia de que características econômicas das cidades do interior expliquem a relação com renda é uma hipótese para aprofundamento, não uma conclusão obtida até aqui.

## 7. Valores extremos na análise univariada

Foram sinalizados 70 registros cidade × indicador/classificação em 41 combinações. Franca aparece em 32 sinalizações e Barretos em 24, concentrando juntas 80% dos extremos.

O critério foi valor estritamente abaixo de Q1 − 1,5 × IQR ou acima de Q3 + 1,5 × IQR, com quartis calculados por interpolação linear. Nenhum registro foi excluído ou alterado por esse critério.

Parte dos extremos reflete diferenças legítimas de escala. População total, população urbana, unidades locais e pessoal ocupado possuem relações entre si; alguns totais também reaparecem em diferentes tabelas. Por isso, 70 sinalizações não significam 70 erros independentes, e sua contagem não deve se tornar uma pontuação de potencial comercial.

As 24 combinações associadas às faixas de renda receberam ressalva de conferência. Seus resultados descritivos não encerram as pendências nem liberam essas faixas para recomendações definitivas.

## 8. Relações bivariadas observadas

Todos os oito pares possuem 12 cidades com valores numéricos. Sete pares usam o mesmo ano; um compara PIB de 2023 com renda de 2022.

| Relação | Ano(s) | Pearson | Spearman |
|---|---|---:|---:|
| População × unidades de alimentação | 2024 | 0,981 | 0,916 |
| População × varejo alimentar | 2024 | 0,996 | 0,928 |
| População × pessoal ocupado | 2024 | 0,997 | 0,818 |
| População × renda domiciliar per capita mediana | 2022 | 0,234 | 0,250 |
| Urbanização × renda domiciliar per capita mediana | 2022 | 0,398 | 0,060 |
| Renda domiciliar per capita média × mediana | 2022 | 0,939 | 0,893 |
| Salário médio × alimentação por 10 mil habitantes | 2024 | 0,275 | 0,217 |
| PIB por habitante × renda domiciliar per capita média | 2023 × 2022 | 0,001 | −0,007 |

Pearson descreve associação linear; Spearman descreve a associação dos postos, com tratamento dos empates por postos médios. Não foram aplicados testes de hipótese ou p-valores. Os resultados descrevem 12 municípios selecionados, sem provar causalidade ou comportamentos individuais dos moradores.

### Dimensão populacional e estrutura comercial

As associações positivas elevadas entre população, unidades de alimentação e varejo alimentar permanecem quando Franca e Barretos são retiradas juntas: Pearson fica em aproximadamente 0,970 nos dois pares, considerando as dez cidades restantes.

Isso mostra que as relações não dependem exclusivamente dos dois maiores municípios. Ainda assim, a dimensão municipal ajuda a explicar a associação entre totais; ela não comprova oportunidade não atendida ou retorno de vendas.

### Dimensão populacional e renda

A associação entre população e renda mediana é pequena. Sem Franca e Barretos, Pearson cai de 0,234 para 0,120. Ter mais moradores não implica, neste conjunto, maior renda domiciliar per capita mediana. Porte e renda devem permanecer como dimensões distintas.

### Urbanização e renda mediana

Pearson é 0,398, mas Spearman é apenas 0,060. Ao retirar Colômbia, Pearson cai para aproximadamente 0,001 e Spearman passa a −0,151.

O percentual de urbanização não apresentou associação monotônica relevante com a renda mediana neste conjunto. A associação linear observada mostrou sensibilidade à presença de Colômbia. Não há suporte para afirmar uma relação consistente ou atribuir sua explicação ao fato de os municípios serem do interior.

### Renda média e mediana

As duas medidas possuem associação positiva elevada e mantêm Pearson próximo de 0,94 sem Franca e Barretos. Isso indica ordenações semelhantes entre municípios, mas ambas descrevem aspectos da mesma distribuição de renda; não constituem evidências independentes para somar em um índice.

### Salário e concentração de estabelecimentos

A relação entre salário médio e unidades de alimentação por 10 mil habitantes é pequena no conjunto completo. Sem Nuporanga, Pearson sobe de 0,275 para 0,673; Spearman sobe de 0,217 para 0,491.

A interpretação depende de uma cidade específica. Nuporanga merece investigação de sua estrutura e cobertura cadastral, preservando seus valores. Não há justificativa para excluí-la apenas para obter uma correlação maior.

### PIB por habitante e renda média

Os coeficientes ficam próximos de zero com todas as cidades. Sem Nuporanga, Pearson passa a −0,432. Como os anos são diferentes e os resultados são sensíveis, isso não prova ausência de relação entre produção econômica e renda. Reforça a necessidade de manter os conceitos separados e investigar a estrutura econômica municipal.

## 9. O que os cenários de sensibilidade acrescentam

Foram calculados 104 cenários: retirada de cada uma das 12 cidades, separadamente, e retirada conjunta de Franca e Barretos em cada um dos oito pares. As retiradas alteram apenas o diagnóstico; as bases oficiais continuam com todas as cidades.

A sensibilidade ajuda a distinguir associações que permanecem após mudanças no conjunto de outras fortemente influenciadas por observações específicas. Não é um teste formal de estabilidade ou significância, nem uma autorização para eliminar municípios.

As relações de escala comercial apresentaram pequenas mudanças de Pearson na retirada individual. Urbanização × renda e salário × concentração apresentaram mudanças relevantes na magnitude dos coeficientes. A leitura deverá continuar acompanhada dos gráficos e da investigação das cidades influentes.

## 10. Implicações comerciais e limites da decisão

| Evidência observada | Implicação para a próxima investigação | O que ainda falta |
|---|---|---|
| Franca e Barretos têm maior escala | Examinar canais e capacidade de atendimento nesses mercados | Estabelecimentos identificados, compras, fornecedores e condições de entrega |
| Cidades menores possuem perfis de renda distintos | Avaliar mercados menores por medidas relativas e contexto | Informações comerciais locais e localização dos clientes |
| PIB por habitante difere da renda domiciliar | Evitar usá-lo como substituto de poder de compra | Estrutura produtiva e evidências adicionais sobre consumo |
| Urbanização × renda é sensível a Colômbia | Investigar mecanismos econômicos e territoriais | Atividades, trabalho e distribuição espacial dos públicos |
| Salário × concentração é sensível a Nuporanga | Investigar o perfil desse município | Cobertura cadastral e características dos estabelecimentos |
| Parte dos indicadores depende de dados históricos | Separar períodos e documentar limitações | Séries comparáveis e conferência dos anos disponíveis |

Não temos, até aqui, mensuração de demanda não atendida, previsão de vendas, sensibilidade a preço, aderência dos produtos ou retorno comercial. Contagens CNAE não representam clientes confirmados; menor concentração de estabelecimentos pode ter várias explicações e não será denominada oportunidade automaticamente.

A hipótese de Ribeirão Preto ser a melhor origem logística ainda não foi concluída. Distâncias entre centroides não substituem endereços efetivos, trajetos rodoviários, tempo, disponibilidade de produtos ou condições de entrega.

## 11. Continuidade prevista

- Explorar evolução temporal com séries metodologicamente comparáveis, distinguindo crescimento nominal de real.
- Explorar localização e proximidade geográfica com suas limitações operacionais explícitas.
- Integrar dimensão, renda e estrutura comercial sem contar indicadores equivalentes duas vezes.
- Explorar preços por produto/pacote e os estudos documentais em seus próprios universos.
- Resolver ou delimitar o uso das pendências antes de recomendações definitivas.
- Consolidar a EDA e aprofundar a análise comercial com dados de clientes, concorrência e atendimento.

A comparação com a análise original permanece reservada ao encerramento do projeto. Este documento consolida os achados disponíveis até agora; não declara a EDA concluída.

## 12. Rastreabilidade dos arquivos recebidos

| Arquivo | SHA-256 |
|---|---|
| conclusao_11_eda_estrutura.json | `ea4774620bfa0ecf0a52c232a03d3f74a0629068a8bc1dd1b1fef3d3b4b8e718` |
| conclusao_12_eda_univariada.json | `4db1f015dae73cbcf4a9bd45e845642292596011f1bc227968f8c47f892ff50d` |
| estatisticas_indicadores.json | `4d4b904290159ba1beae7df2e87e0033a5f515d829275e9736aacd910cbb93bd` |
| valores_cidades.json | `8a7fd61a85f671a974836b19bc6f83c66a31b2994e6e7282f4ee408dba998541` |
| extremos_investigar.json | `b972fc09a53078bbaf1ff6bbb821c655a789fb357b444df511d275c5482b9c0f` |
| correlacoes_exploratorias.json | `dfc32aace12f2d865427d6584dfb72599e7d46abb2180d40c9a2f0d1c15dc5e1` |
| sensibilidade_correlacoes.json | `9b24477ae002daa9aec9927a97e95d12fdc45a42bd06055a530f174b0e466ac4` |
