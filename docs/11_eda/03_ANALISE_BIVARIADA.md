# EDA — bloco 3: análise bivariada municipal

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo e execução

Investigar oito relações previamente definidas por perguntas comerciais, com população, renda, urbanização, ocupação e estabelecimentos. O bloco verifica a linhagem da Silver municipal da base EDA e exige conclusão da etapa 12 sobre a mesma base.

Na raiz do projeto:

```powershell
python src/etapa_13_eda_bivariada.py
```

Pela pipeline (também executa etapas locais 01 a 05):

```powershell
python src/run_pipeline.py --eda-bivariada
```

Para preparar a base e executar os blocos municipais em sequência:

```powershell
python src/run_pipeline.py --preparar-eda --eda-estrutura --eda-univariada --eda-bivariada
```

Não há nova coleta externa nessas opções. As duas Silver precisam existir. `--base CAMINHO` permite escolher a base manualmente, mantendo as verificações de linhagem e a exigência de conclusão univariada correspondente.

## Relações previstas

| X | Y | Período e interpretação |
|---|---|---|
| População estimada | Unidades locais de alimentação, CNAE 56 | 2024 × 2024; dimensão e estrutura comercial |
| População estimada | Unidades locais de varejo alimentar, CNAE 47.2 | 2024 × 2024; dimensão e estrutura comercial |
| População estimada | Pessoal ocupado total | 2024 × 2024; ocupação no local de trabalho, não taxa de emprego dos moradores |
| População do Censo | Renda domiciliar mensal per capita mediana | 2022 × 2022; dimensão e renda |
| Percentual urbano | Renda domiciliar mensal per capita mediana | 2022 × 2022; urbanização e renda |
| Renda domiciliar per capita média | Renda domiciliar per capita mediana | 2022 × 2022; comparação de medidas relacionadas |
| Salário médio mensal no trabalho | Unidades locais de alimentação por 10 mil habitantes | 2024 × 2024; salário e concentração cadastral |
| PIB por habitante | Renda domiciliar per capita média | 2023 × 2022; contraste de conceitos não contemporâneo |

As faixas de renda com conferência pendente não entram nesses pares. Renda média e mediana são variáveis distintas das faixas. Indicadores com definições relacionadas não serão tratados como evidências independentes.

## Métodos

Pearson descreve associação linear. Spearman é calculado como Pearson dos postos, com postos médios para empates. Não há coeficiente quando menos de três pares estão disponíveis ou quando uma variável é constante. Apenas cidades com os dois valores numéricos entram na relação; ausências são registradas e não imputadas.

As razões de alimentação e varejo por 10 mil habitantes são calculadas como `(unidades locais de 2024 / população estimada de 2024) × 10.000`. Nenhuma estimativa de 2026 substitui o denominador. Os componentes, unidades, fórmulas e hashes das fontes permanecem registrados. Razões descrevem concentração, não oportunidade confirmada, demanda ou saturação.

A sensibilidade recalcula cada relação retirando uma cidade por vez e, adicionalmente, Franca e Barretos juntas. O relatório apresenta a maior mudança absoluta de coeficiente na retirada individual. A retirada é apenas diagnóstica e não modifica as bases oficiais. Não foi definido um limiar automático de estabilidade ou significância.

Não são realizados testes de hipótese, p-valores ou inferência para outras cidades. As correlações são exploratórias; não demonstram causalidade nem o comportamento individual dos moradores. Gráficos usam escalas lineares e mostram valores em tabelas para permitir conferência dos pontos.

## Saídas

`datalake/03_gold/<run_id>/eda_bivariada/`:

| Tabela/arquivo | Uso |
|---|---|
| catalogo_variaveis | Definição, categoria, unidade, ano e fórmula dos 12 indicadores usados ou derivados |
| indicadores_alinhados | 144 registros cidade × variável, com fontes e períodos |
| correlacoes_exploratorias | Oito pares, coeficientes, cobertura e condição temporal |
| pontos_relacoes | Valores usados em cada gráfico e suas fontes |
| sensibilidade_correlacoes | Coeficientes e mudanças em cada cenário diagnóstico |
| relatorio_bivariado.html | Dispersões por cidade, coeficientes, períodos e ressalvas |
| manifesto_eda_bivariada.json | Linhagem, hashes, métodos e verificações |

As cinco tabelas são exportadas em JSON e Parquet. O controle fica em `quality/13_eda_bivariada/<run_id>/conclusao_13_eda_bivariada.json` e `execucao.log`. Status esperado: `EDA_BIVARIADA_CONCLUIDA_COM_LIMITACOES`.

## Validação e continuidade

Na reprodução com os dados reais anteriormente recebidos: 12 cidades, 12 variáveis, oito pares (sete contemporâneos e um com anos diferentes), 96 pontos e 104 cenários de sensibilidade. Foram aprovadas 157 verificações técnicas. Os detalhes da reprodução estão em `VALIDACAO_BIVARIADA.json`; a execução no computador do usuário deve ser conferida pelo seu relatório.

Interpretar coeficientes junto com gráficos, cobertura e sensibilidade. Correlações altas entre totais podem refletir a dimensão populacional. Relações com renda e razões precisam de cuidado com os conceitos e períodos. Os achados não constituem ranking de expansão.

A exploração temporal, geográfica, multivariada e documental continuará conforme o escopo aprovado. A comparação com a análise original permanece para o encerramento.
