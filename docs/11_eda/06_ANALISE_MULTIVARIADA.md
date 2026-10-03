# EDA — bloco 6: perfis municipais e associações com controle

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo

Comparar as cidades em várias dimensões simultaneamente, distinguindo dimensão absoluta, concentração comercial, renda e proximidade. Investigar redundâncias entre indicadores e a sensibilidade de associações a uma variável de controle. Não estima demanda, efeito causal ou ranking de expansão.

## Execução e linhagem

Na raiz do projeto:

```powershell
python src/etapa_16_eda_multivariada.py
```

Pela pipeline local:

```powershell
python src/run_pipeline.py --eda-multivariada
```

Exige etapas 13 e 15 concluídas para a mesma base EDA e com a mesma Silver municipal na linhagem. Não coleta dados novos nem executa automaticamente as etapas anteriores. `--base CAMINHO` seleciona uma base explicitamente, mantendo os requisitos.

Valida as conclusões e os manifestos dos dois blocos, os hashes, contagens e conteúdo dos pares JSON/Parquet. Usa os códigos IBGE para unir registros, verifica chaves, cidades e anos. Não depende dos caminhos Windows armazenados em uma conclusão de outro ambiente: recompõe a pasta pelo run_id relativo à raiz do projeto.

Não usa o PIB nem a composição setorial de nenhuma cidade, mantendo um conjunto de dimensões consistente e respeitando as pendências do bloco temporal. As tabelas originais não são alteradas.

## Dimensões do perfil

| Variável | Referência | Papel |
|---|---|---|
| População estimada | 2024 | Dimensão absoluta de mercado |
| Renda mensal domiciliar per capita mediana | 2022 | Condição de renda dos moradores |
| Urbanização | Censo 2022 | Proporção da população urbana |
| Unidades locais de alimentação, CNAE 56 | 2024 | Estrutura comercial absoluta |
| Unidades de alimentação por 10 mil habitantes | 2024 | Concentração relativa de unidades |
| Unidades de varejo alimentar por 10 mil habitantes | 2024 | Concentração relativa de varejo |
| Distância ao centroide do CD mais próximo | Metadados geográficos | Proximidade territorial preliminar |

População de 2024 foi escolhida para manter o denominador das taxas alinhado ao ano de referência dos estabelecimentos. A população de 2026 permanece disponível no bloco geográfico; não substitui o denominador dessas taxas.

Unidades locais de alimentação não equivalem a clientes interessados, concorrentes ou demanda por salgados. A ocupação no local de trabalho não é taxa de emprego dos residentes. Renda domiciliar e salário no trabalho têm universos distintos. O painel combina indicadores de 2022 e 2024 como contexto exploratório, sem alegar contemporaneidade integral.

## Transformação e posição relativa

Aplicar `log1p(valor)` somente à população e à contagem absoluta de unidades de alimentação para visualizar os perfis. O log comprime diferenças de escala entre cidades grandes e pequenas; não modifica os valores originais ou as correlações calculadas sobre eles.

Em cada dimensão:

`posição robusta = (valor transformado − mediana transformada) / IQR transformado`

IQR é Q3−Q1; quartis usam interpolação linear tipo 7, como na etapa univariada. Um valor +1 indica uma unidade de IQR acima da mediana transformada, não um desvio padrão. Não é o z-score clássico. Valores ausentes permanecem nulos; IQR zero produz posição indefinida, sem divisão por zero ou imputação.

O relatório usa azul para valores acima da mediana e laranja para abaixo. A cor satura visualmente em ±2 IQR; os valores completos continuam na tabela. Maior distância significa mais distante, não melhor. Nenhuma dimensão é invertida para simular desejabilidade. Não somar posições, não atribuir pesos comerciais e não converter a tabela em ranking.

As sete dimensões geram 84 posições (12×7). O painel preserva nove indicadores bivariados, incluindo os três controles auxiliares, mais a distância. A linhagem de 108 observações registra anos, unidades, fórmulas e fontes dos indicadores; a distância é rastreada à conclusão geográfica e às exportações validadas desse bloco.

## Redundância e dependência matemática

As 21 combinações entre sete dimensões recebem Pearson e Spearman sobre os valores originais, com cobertura e referências temporais. Esses pares servem para investigar redundância, não para selecionar indicadores automaticamente por um limiar arbitrário.

Taxas por 10 mil habitantes dividem a contagem de estabelecimentos pela população. Elas compartilham denominador entre si e numerador com a contagem bruta. Uma associação envolvendo essas variáveis pode decorrer parcialmente da construção matemática. Não interpretar taxa alta como mercado desatendido: pode indicar oferta existente, atratividade regional ou estrutura cadastral, hipóteses que exigem evidência adicional.

## Associações parciais: três variáveis de cada vez

| Relação | Controle | Ano comum |
|---|---|---:|
| População × unidades de alimentação | Pessoal ocupado total | 2024 |
| População × unidades de varejo alimentar | Pessoal ocupado total | 2024 |
| Urbanização × renda mediana domiciliar | População residente | 2022 |

Para uma relação X,Y controlada por Z, ajustar separadamente `X = intercepto + coeficiente×Z + resíduoX` e `Y = intercepto + coeficiente×Z + resíduoY`. Calcular Pearson entre os dois resíduos. Essa é a correlação parcial linear com um controle.

Se o controle for constante ou deixar resíduos praticamente nulos, o resultado é indefinido. A tolerância para resíduos quase nulos é `soma(resíduos²) <= soma((valor−média)²) × 10⁻¹²`. Observações incompletas são excluídas somente da conta específica, com n registrado; não são preenchidas.

São registrados os coeficientes X×controle e Y×controle e a fração de variância residual `1−r²`. Quanto menor essa fração, menos variação sobra para calcular a associação ajustada, tornando a interpretação mais sensível. Isso não mede importância causal do controle.

Pessoal ocupado é fortemente relacionado ao tamanho da cidade e pode incluir trabalhadores do próprio setor de alimentação. Portanto, seu uso não identifica um efeito independente de população, nem garante que seja um controle causalmente adequado. O ajuste é uma investigação exploratória predefinida.

Cada tripla é recalculada excluindo uma cidade por vez: 36 resultados, com delta em relação ao coeficiente completo. Não definimos estabilidade por uma regra automática. Sem teste de hipótese, p-valor, generalização populacional ou modelo preditivo.

## Primeiros resultados na validação local

População × alimentação passa de Pearson 0,981 para parcial −0,101 quando se ajusta pessoal ocupado. Na retirada individual de cidades, o parcial varia aproximadamente de −0,449 a +0,692. Assim, a inversão de sinal não sustenta uma conclusão de relação econômica negativa; o resultado é sensível e o controle está muito ligado à dimensão municipal.

População × varejo alimentar passa de 0,996 para parcial 0,387; a sensibilidade varia de −0,156 a +0,821. Urbanização × renda mediana passa de 0,398 para parcial 0,352 com controle de população; a sensibilidade varia de −0,063 a +0,554.

Esses resultados não invalidam as correlações brutas. Eles mostram que a interpretação depende da estrutura entre as variáveis e das cidades presentes. Os resultados do ambiente do projeto devem ser conferidos antes da consolidação definitiva.

## Por que não executar PCA ou clustering neste bloco

PCA e agrupamentos são possibilidades previstas no escopo, condicionadas à utilidade e estabilidade. Esta versão prioriza perfis interpretáveis e controles exploratórios. Há apenas 12 cidades, forte diferença de tamanho, indicadores com dependência matemática e períodos distintos. Uma segmentação automática exigiria seleção de variáveis, estratégia de escala e avaliação de estabilidade próprias. Não se conclui que essas técnicas sejam proibidas ou impossíveis; apenas não são necessárias para cumprir este bloco de comparação integrada.

## Saídas

Pasta: `datalake/03_gold/<run_id>/eda_multivariada/`.

| Tabela | Linhas previstas |
|---|---:|
| catalogo_perfis | 7 |
| painel_integrado | 12 |
| linhagem_indicadores | 108 |
| parametros_perfis | 7 |
| perfis_padronizados | 84 |
| associacoes_dimensoes | 21 |
| associacoes_parciais | 3 |
| sensibilidade_parcial | 36 |

Exportações em JSON/Parquet, `relatorio_multivariado.html` e `manifesto_eda_multivariada.json`. Qualidade em `quality/16_eda_multivariada/<run_id>/conclusao_16_eda_multivariada.json` e `execucao.log`. Status: `EDA_MULTIVARIADA_CONCLUIDA_COM_LIMITACOES`. Cada execução tem novo run_id, sem sobrescrever resultados anteriores.

A próxima etapa é a exploração documental de preços e estudos; a síntese da EDA vem depois. Recomendação comercial, escores e comparação com a análise original permanecem para o aprofundamento e encerramento previstos.
