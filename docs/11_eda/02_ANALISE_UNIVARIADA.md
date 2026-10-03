# EDA — bloco 2: análise univariada municipal

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo

Descrever a distribuição de cada indicador/classificação entre as 12 cidades, identificar diferenças de escala e sinalizar extremos para investigação. Usa o painel de período comum; não mistura valores antigos para preencher ausências.

## Execução

Após concluir a etapa 11 sobre a mesma base:

```powershell
python src/etapa_12_eda_univariada.py
```

Pela pipeline local:

```powershell
python src/run_pipeline.py --eda-univariada
```

Para preparar uma nova base e executar os dois primeiros blocos:

```powershell
python src/run_pipeline.py --preparar-eda --eda-estrutura --eda-univariada
```

Essas opções não fazem nova coleta pela internet. A pipeline também executa as etapas locais 01 a 05. O bloco univariado exige conclusão da etapa 11 com o mesmo hash do manifesto da base, evitando misturar versões. A seleção padrão considera o manifesto e a conclusão da etapa 10. `--base CAMINHO` permite escolher uma base manualmente, mantendo a exigência da etapa 11 correspondente.

## Métodos

- Quantidade de cidades com valor e com ausência, unidade, classificação e ano.
- Mínimo, máximo, amplitude, média, mediana, quartis, IQR, variância e desvio padrão.
- Quartis por interpolação linear: posição h = (n − 1)p, quantil tipo 7.
- Variância com divisor n: descrição do conjunto de cidades observado, sem estimar uma população maior.
- Assimetria pelo terceiro momento central dividido pelo segundo momento elevado a 1,5; sem correção de viés, calculada com pelo menos três valores e variância positiva.
- Curtose de excesso pelo quarto momento central dividido pelo quadrado do segundo momento, menos três; sem correção de viés, calculada com pelo menos quatro valores e variância positiva.
- Extremos: valor estritamente menor que Q1 − 1,5 IQR ou maior que Q3 + 1,5 IQR. Não há exclusão automática.

As estatísticas consideram apenas valores numéricos disponíveis. Média e dispersão descrevem cidades com o mesmo peso, não moradores com pesos proporcionais à população. A média municipal de renda, por exemplo, não é uma estimativa da renda média de todos os residentes das 12 cidades.

Indicadores sem variabilidade têm assimetria e curtose nulas no sentido de ausência de resultado (null), não igual a zero. A pequena quantidade de cidades limita a interpretação da forma da distribuição. Quando IQR = 0, valores distintos dos limites podem ser sinalizados e exigem cuidado adicional.

## Saídas

`datalake/03_gold/<run_id>/eda_univariada/`:

| Tabela/arquivo | Conteúdo |
|---|---|
| estatisticas_indicadores | Resumo por indicador/classificação e período |
| valores_cidades | Valores e ausências originais, fontes, pendências e sinalização IQR |
| extremos_investigar | Apenas os registros sinalizados, sem exclusão da base |
| relatorio_univariado.html | Estatísticas e gráficos de pontos ordenados por cidade |
| manifesto_eda_univariada.json | Entradas, hashes, métodos, regras e limitações |

As três tabelas são exportadas em JSON e Parquet. Os gráficos usam escala linear independente por indicador, incluindo zero. Azul indica valor preservado; laranja indica extremo IQR. Ausências e pendências são apresentadas junto a cada gráfico. Os números dos gráficos usam ponto decimal.

Qualidade: `quality/12_eda_univariada/<run_id>/conclusao_12_eda_univariada.json` e `execucao.log`. Status esperado: `EDA_UNIVARIADA_CONCLUIDA_COM_LIMITACOES`.

## Validação da reprodução

Com os dados reais anteriormente recebidos e extraídos: 56 resumos, 672 registros, 597 valores numéricos, 70 extremos em 41 combinações de indicador/classificação e 24 combinações com ressalva de conferência de renda. Foram aprovadas 130 verificações técnicas. Esses números devem ser conferidos na execução do usuário.

Os 70 extremos são registros cidade × indicador/classificação, não 70 cidades nem 70 erros. Os indicadores possuem dependências entre si; não se deve interpretar o número de sinalizações como eventos independentes. Cada extremo exige conferir o valor, a fonte, a cobertura, a escala e o contexto do município.

## Limitações e continuidade

A disponibilidade de dados não elimina as pendências de renda. As distribuições são descritas com sinalizações, sem liberar essas faixas para recomendação definitiva. A etapa não calcula ranking de expansão, testes de hipótese, correlações, previsão ou demanda.

Preços e estudos documentais serão explorados em blocos específicos. As análises temporal, geográfica, bivariada e multivariada continuam previstas no escopo. A comparação com a análise original permanece reservada ao encerramento.
