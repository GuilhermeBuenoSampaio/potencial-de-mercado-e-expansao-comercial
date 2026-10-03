# EDA — bloco 4: análise temporal municipal

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo e execução

Descrever a evolução dos indicadores disponíveis, distinguindo variação anual, crescimento acumulado e taxa anualizada. Os valores monetários continuam a preços correntes; não há estimativa de crescimento real, previsão ou demanda.

Na raiz do projeto:

```powershell
python src/etapa_14_eda_temporal.py
```

Pela pipeline local (também executa etapas 01 a 05):

```powershell
python src/run_pipeline.py --eda-temporal
```

Para executar os quatro blocos sobre uma base nova:

```powershell
python src/run_pipeline.py --preparar-eda --eda-estrutura --eda-univariada --eda-bivariada --eda-temporal
```

As opções não fazem nova consulta externa. A etapa exige conclusão bivariada para a mesma base. Verifica o manifesto da Silver municipal registrada na linhagem da etapa 10 e todos os pares JSON/Parquet dessa Silver. `--base CAMINHO` permite seleção manual, mantendo as verificações e a conclusão anterior correspondente.

## Indicadores e períodos

| Indicador | Blocos de análise | Interpretação |
|---|---|---|
| População estimada | 2019–2021 e 2024–2026, separados | Não conecta o intervalo 2021–2024; não intercala o Censo de 2022 como estimativa |
| PIB a preços correntes | 2018–2023 | Crescimento nominal; não desconta inflação |
| Número de unidades locais | 2022–2024 | Estrutura cadastral no CEMPRE da série mais recente |
| Pessoal ocupado total | 2022–2024 | Ocupação no local de trabalho, não taxa dos moradores |
| Salário médio mensal em reais | 2022–2024 | Variação nominal, não ganho de poder de compra |
| Salários e outras remunerações | 2022–2024 | Massa de remuneração nominal; não renda domiciliar |
| Quatro participações setoriais do PIB | Períodos históricos numericamente disponíveis | Contexto separado; último dado numérico de 2021 nas entradas atuais |

Os blocos são escolhas analíticas conservadoras. Separar períodos evita misturas conhecidas, mas não certifica ausência de revisões dentro de cada bloco. O CEMPRE não é concatenado com tabelas antigas anteriores a 2022. Participações históricas não preenchem o painel de 2023.

## Métodos

- Variação absoluta: valor final menos valor inicial, na unidade do indicador.
- Variação percentual: `(final / inicial − 1) × 100`, quando o valor inicial é diferente de zero.
- Taxa anualizada: `[(final / inicial)^(1/n) − 1] × 100`, com n igual ao intervalo efetivo em anos, inicial positivo e final não negativo.
- Variação anual exige valores em dois anos consecutivos no mesmo bloco; não pula anos ausentes.
- Resumo de bloco usa seus extremos planejados e registra cobertura dos anos internos. Uma taxa anualizada não implica trajetória regular.
- Participações setoriais: diferença entre a última e a primeira participação numérica disponível, em pontos percentuais. Anos efetivos e ausências ficam explícitos.
- Nenhum valor ausente é interpolado ou convertido em zero.
- O crescimento do PIB de 2018–2023 é reconciliado com a tabela correspondente da Silver.

Não são realizados testes de hipótese ou previsão. Crescimento de valor monetário nominal pode refletir quantidades, preços ou ambos. Avaliação de crescimento real exige uma estratégia de deflação definida e documentada.

## Saídas

`datalake/03_gold/<run_id>/eda_temporal/`:

| Tabela/arquivo | Conteúdo |
|---|---|
| catalogo_temporal | Indicadores, unidades, natureza e blocos planejados |
| series_temporais | Valores anuais preservados com fontes e identificação dos blocos |
| variacoes_anuais | Variações entre anos consecutivos, com status e hashes |
| crescimento_por_bloco | Valores inicial/final, acumulado, anualizado, cobertura e anos |
| perfil_setorial_historico | Participações disponíveis, mudança em pontos percentuais e anos sem valor |
| relatorio_temporal.html | Gráficos e tabelas de valores por indicador e cidade |
| manifesto_eda_temporal.json | Entradas, hashes, métodos, controles e limitações |

As sete tabelas são exportadas em JSON e Parquet. Qualidade: `quality/14_eda_temporal/<run_id>/conclusao_14_eda_temporal.json` e `execucao.log`. Status esperado: `EDA_TEMPORAL_CONCLUIDA_COM_LIMITACOES`.

Os gráficos usam o ano efetivo no eixo horizontal e segmentos separados para os blocos. Linhas não atravessam anos ausentes. As escalas são independentes por cidade; tabelas devem ser usadas para comparação dos níveis absolutos. Cada cidade pode ser aberta no relatório HTML.

## Leitura e continuidade

Comparar trajetória e porte sem confundir crescimento de uma base pequena com dimensão de mercado. Examinar taxas anuais junto ao acumulado. Não usar os resultados nominais como evidência de aumento de poder de compra ou de consumo de salgados.

O próximo bloco será geográfico. Análise multivariada, exploração de preços e documentos e síntese da EDA seguem pendentes. A comparação com a análise original permanece reservada ao encerramento.

A evidência dos testes de reprodução será registrada em `VALIDACAO_TEMPORAL.json`; a execução do usuário deverá ser conferida pela sua própria conclusão e log.


## Conferência de versões do PIB

Consulte `CONFERENCIA_PIB_SALES_OLIVEIRA.md` e `evidencias_pib/` para a comparação das edições oficiais. Sales Oliveira, Guaíra e Nuporanga estão com uso interpretativo do PIB e do contexto setorial bloqueado, preservando os valores calculados. `status=CALCULADO` não libera seu uso em recomendações: verificar `uso_interpretativo` e `status_conferencia`.

Duas novas saídas JSON/Parquet: `pendencias_fontes` (3 incidentes) e `alertas_variacoes_pib` (triagem operacional de variações anuais nominais com magnitude >=30%). O relatório HTML evidencia a restrição. A pipeline já chama a etapa atualizada pelo mesmo parâmetro `--eda-temporal`.
