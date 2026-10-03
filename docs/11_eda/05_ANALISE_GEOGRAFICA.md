# EDA — bloco 5: análise geográfica

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo

Descrever a distribuição territorial das 12 cidades de expansão e sua proximidade em relação à fábrica em São Carlos e aos CDs em Ribeirão Preto, Campinas, Sorocaba e São Paulo. Investigar conjuntamente dimensão de mercado e proximidade, sem criar escore de potencial ou recomendação operacional.

## Execução

Na raiz do projeto:

```powershell
python src/etapa_15_eda_geografica.py
```

Pela pipeline, que também executa as etapas locais 01 a 05:

```powershell
python src/run_pipeline.py --eda-geografica
```

A etapa exige uma conclusão temporal bem-sucedida para a mesma base EDA. Não executa automaticamente os blocos anteriores e não realiza consulta externa. `--base CAMINHO` seleciona outra base explicitamente, mantendo as verificações de linhagem.

Scripts em `src`; guia de execução em `docs/execucoes/COMO_EXECUTAR.md`. Cada execução cria novo run_id com horário UTC e identificador aleatório. Execuções anteriores não são sobrescritas.

## Entradas e qualidade

O manifesto da base aponta a Silver municipal utilizada. A etapa confere o hash desse manifesto, depois valida todos os pares JSON/Parquet da Silver usando o carregador existente. Usa municípios, distâncias, dicionário e séries municipais. A conclusão temporal é vinculada por SHA-256; pendências de PIB continuam registradas, sem uso de PIB ou perfil setorial neste bloco.

Verifica 17 municípios únicos, 12 destinos, as cinco origens autorizadas, coordenadas numéricas finitas e limites de latitude/longitude. Confere as 60 combinações origem–destino, recalcula as distâncias e verifica os hashes das coordenadas de cada par. Verifica nomes municipais, 66 pares distintos entre destinos e unicidade dos indicadores/anos do painel de mercado. Exportações JSON e Parquet são reconciliadas.

## Métodos

A Silver contém centroides dos municípios, obtidos dos metadados de malhas municipais do IBGE. Eles não são os endereços das instalações, os centros urbanos ou os clientes. A versão da malha não foi explicitada pelo endpoint coletado e essa limitação permanece na tabela de pontos.

A distância usa Haversine, com raio médio de 6.371,0088 km:

`a = sen²(Δlatitude/2) + cos(latitude1) × cos(latitude2) × sen²(Δlongitude/2)`

`distância = 2 × raio × arcsen(√a)`

Ângulos em radianos. Trata-se de aproximação esférica de distância sobre a superfície terrestre; não é geodésica elipsoidal de alta precisão. Não representa comprimento de estrada. Valores publicados são arredondados a três casas decimais, com tolerância de reconciliação de 0,000501 km.

Para cada cidade, compara-se o mínimo das cinco origens e, separadamente, dos quatro CDs. A diferença entre fábrica e CD descreve a diferença de distâncias entre centroides. Não representa economia de frete. Empates na precisão publicada são registrados; o primeiro código ordenado é usado apenas como desempate técnico, sem preferência operacional.

Os 66 pares de destinos correspondem a `12 × 11 / 2`, sem duplicar direções. A lista ordenada ajuda a levantar hipóteses de conjuntos territoriais; não otimiza roteiro de visitas ou entregas. Não criaremos faixas arbitrárias de atendimento ou clusters geográficos nesta etapa.

O resumo por origem contém mínimo, média, mediana e máximo das 12 distâncias e contagens de origens mais próximas. Não pondera por população, demanda ou volume, e não constitui função de custo logístico.

O painel `mercado_proximidade` combina população estimada de 2026, unidades locais de alimentação CNAE 56 de 2024 e distância até o CD geograficamente mais próximo. Os períodos ficam no nome das colunas e nas referências. Esses valores não são contemporâneos; unidades cadastradas não equivalem a clientes, concorrentes ou compradores de salgados. Ausências permanecem nulas, sem buscar outro ano ou imputar zero.

O mapa é um desenho de posições relativas, com x igual à longitude multiplicada pelo cosseno da latitude média, y igual à latitude e a mesma escala local nos dois eixos. Tem 17 pontos numerados, legenda, identificação de origem/destino e orientação norte. Não inclui limites municipais, rodovias ou fundo cartográfico. Os números evitam sobreposição de nomes, que aparecem na legenda e ao passar o mouse sobre o ponto.

## Saídas

Em `datalake/03_gold/<run_id>/eda_geografica/`:

| Tabela | Linhas | Conteúdo |
|---|---:|---|
| pontos_geograficos | 17 | Coordenadas, papéis, regiões e referências |
| matriz_origem_destino | 60 | Distância por origem e destino; distância rodoviária e tempo nulos |
| proximidade_por_cidade | 12 | Menor distância entre origens e CDs, fábrica e diferenças |
| pares_cidades_expansao | 66 | Proximidade entre destinos |
| resumo_por_origem | 5 | Estatísticas descritivas das distâncias |
| pendencias_logisticas | 17 | Necessidade de pontos reais de instalação/atendimento |
| mercado_proximidade | 12 | População, unidades de alimentação e proximidade |

Todas as tabelas são exportadas em JSON e Parquet. Há também `mapa_centroides.svg`, `relatorio_geografico.html` e `manifesto_eda_geografica.json`.

Qualidade: `quality/15_eda_geografica/<run_id>/conclusao_15_eda_geografica.json` e `execucao.log`. Status esperado: `EDA_GEOGRAFICA_CONCLUIDA_COM_LIMITACOES`.

## Achados preliminares nos dados locais usados na validação

Ribeirão Preto tem o centroide mais próximo das 12 cidades, considerando as cinco origens. As menores distâncias até esse centroide são Sales Oliveira (42,318 km), Nuporanga (57,062 km) e Orlândia (57,703 km). As maiores são Frutal (179,255 km), Planura (152,128 km) e Colômbia (140,651 km).

Entre destinos, destacam-se os pares Orlândia–Sales Oliveira (15,781 km), Nuporanga–Orlândia (18,396 km), Nuporanga–Sales Oliveira (19,194 km), Cristais Paulista–Franca (20,553 km) e Planura–Colômbia (22,087 km). São hipóteses de proximidade territorial para aprofundamento; não definem itinerário nem conectividade por estrada.

Franca e Barretos devem ser examinadas como exemplos de dimensão de mercado maior combinada a distâncias diferentes. O painel permite comparar essa dimensão com cidades menores próximas ao CD, sem presumir que maior população ou menor distância determine o potencial de vendas.

Os resultados devem ser conferidos com a execução no ambiente do projeto antes de consolidação definitiva. A análise original será comparada somente no encerramento.

## Requisitos para o aprofundamento rodoviário

Registrar endereços reais ou coordenadas verificadas da fábrica e dos quatro CDs. Para destinos, definir clientes específicos ou pontos urbanos de referência explícitos, sem tratar o centroide municipal como endereço. Registrar provedor, perfil de veículo, data da consulta, pontos enviados, resultado bruto, distância, duração estimada e restrições de rota.

Uma decisão operacional exigirá também estoque, cobertura e regras de atendimento do CD, frequência de entrega, pedido mínimo e condições do transporte refrigerado. Esta etapa não estima tempo, pedágios, frete, custo fabril ou retorno. As 17 pendências são requisitos de localização; não indicam falha na EDA geográfica preliminar.
