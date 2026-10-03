# potencial-de-mercado-e-expansao-comercial — Etapa 22

Data: 03/10/2026. Aprofundamento comercial: prioridades e circuitos.

## Decisão a apoiar

Por onde iniciar a prospecção do varejo especializado e como incluir as 12 cidades em circuitos. Depois, estimar combustível, pedágios e desgaste incremental e o faturamento que cobre a viagem. Todas as cidades permanecem no escopo, sem inventar vendas, clientes ou quantidades por pacote.

O foco atual é CNAE 47.2: comércio varejista de produtos alimentícios, bebidas e fumo. O conjunto não representa todo o varejo alimentar: supermercados/hipermercados e minimercados/mercearias têm classes no grupo 47.1, ausentes desta etapa. Serviços de alimentação CNAE 56 são contexto complementar. Não ampliar a coleta nesta execução.

População atual/2026 e população de 2024 são conceitos separados. Taxas CNAE de 2024 usam população de 2024. Renda domiciliar mediana e urbanização são de 2022; não se acrescenta uma segunda renda familiar equivalente nem se chama renda mediana de renda atual. Renda é contexto, não previsão de compra ou limite de preço.

A vantagem de qualidade e o efeito de um cliente atrair outros foram relatados pelo usuário. São hipóteses comerciais; não alteram contagens, não recebem coeficiente fictício de conversão e não acrescentam receita esperada. Não temos fornecedores, compras, tamanho das redes, lista de clientes ou intenção de compra.

## Comparação de prioridades

11_prioridades_varejo_e_proximidade.sql reúne escala do varejo, participação, acumulado, renda, população, densidade e proximidade ao CD. Não produz escore ponderado.

A fronteira escala/proximidade identifica cidades para as quais não existe outra com pelo menos tantas unidades e distância ao CD não maior, com vantagem estrita em um dos dois critérios. Não é recomendação final e não mede renda, rodovias, concorrência ou compra. Estar fora dessa fronteira não exclui uma cidade do planejamento.

Na conferência local, Franca, Orlândia e Sales Oliveira compõem essa fronteira. Barretos continua uma âncora candidata por seu segundo maior universo de varejistas e pela composição dos circuitos. Priorização comercial e posição na sequência são decisões distintas; o cálculo não prova que a maior cidade produzirá mais vendas.

## Circuitos e resultados preliminares

Hipótese explícita: saída e retorno ao centroide de Ribeirão Preto. É uma referência, não um endereço confirmado de depósito ou saída do vendedor. Matriz simétrica Haversine, raio 6371,0088 km, com centroides da base geográfica.

| Alternativa | Cidades | Varejistas no escopo | Distância geodésica total |
|---|---:|---:|---:|
| Todas em ordem crescente de distância ao CD | 12 | 1.437 | 735,08 km |
| Ordem anterior invertida | 12 | 1.437 | 735,08 km |
| Menor ciclo geodésico fechado | 12 | 1.437 | 503,21 km |
| Subconjunto associado a Franca | 5 | 848 | 233,54 km |
| Subconjunto associado a Barretos | 7 | 589 | 391,65 km |

A redução entre o ciclo ordenado por distância ao CD e o menor ciclo é de aproximadamente 31,54%. É redução geodésica, não economia comprovada de combustível. A ordem inversa tem a mesma distância por simetria e retorno ao mesmo ponto; trânsito, sentidos, pedágios, horários e visitas podem mudar a comparação real.

Duas âncoras foram escolhidas pelo maior número de unidades de varejo. Cada cidade é associada à âncora cujo centroide está mais próximo. Cada subconjunto recebe seu menor ciclo fechado. Essa divisão é exploratória e não é uma partição ótima. Juntos, os dois percursos somam 625,20 km geodésicos e cobrem as 12 cidades sem duplicar sua contagem. Podem orientar agendas separadas, mas não se afirma que um percurso caiba em um dia. Número de visitas, horários, capacidade, carga, prazo e tempo de deslocamento ainda não estão modelados.

Usamos programação dinâmica Held-Karp, exata para o ciclo de cada subconjunto na matriz geodésica. Com apenas 12 cidades, não é necessário limitar a análise a uma heurística. O resultado ótimo geodésico não estabelece a melhor rota rodoviária.

Desvio isolado de inserir C entre CD e âncora A: d(CD,C)+d(C,A)-d(CD,A). Os desvios são diagnósticos separados, não podem ser somados como se fossem uma rota. Unidades comerciais de um circuito são presença territorial, não visitas realizadas ou clientes acessíveis em um dia.

## Modelo de custo

Custo adicional = km rodoviários totais * (preço por litro / km por litro + desgaste por km) + pedágios totais.

Faturamento de equilíbrio = custo adicional / margem de contribuição disponível. A margem deve ser após os demais custos variáveis da venda e antes dos custos da rota explicitamente modelados, evitando dupla contagem. Não usar receita bruta como contribuição nem inferir margem do preço de catálogo. Margens não confirmadas são cenários explícitos, não valores reais da empresa. O equilíbrio cobre apenas o custo modelado; não é lucro total ou garantia de viabilidade. Para uma meta de contribuição adicional M, o limiar passa a (custo adicional + M) / margem.

Uma rota compartilhada pode ser coberta pela soma das contribuições das cidades. Uma cidade pequena não precisa sustentar uma viagem exclusiva para justificar uma parada com baixo custo adicional. O modelo atual não aloca o custo completo arbitrariamente por cidade nem estima vendas futuras. A inclusão de mais visitas também tem tempo e limitações operacionais, ainda não quantificados.

Salário fixo, parcela do veículo, impostos e seguro ficam fora do custo incremental desta versão. Horas extras, outro veículo ou outra despesa provocada pelo circuito exigem ampliar o modelo antes da decisão. Desgaste inclui pneus, preventiva e corretiva representativa sem dupla contagem. Não aplicar coeficientes de caminhões a uma Fiorino. Se houver refrigeração, avaliar seu consumo/manutenção no parâmetro operacional.

PARAMETROS_CUSTO.json inicia com valores nulos. Pedágio zero só é válido se for confirmado para o percurso/categoria. Combustível, consumo e desgaste desconhecidos não viram zero. Não aplicar um multiplicador arbitrário à distância geodésica para apresentá-la como rodoviária. Sem parâmetros completos, custo e faturamento ficam pendentes.

## Fontes e atualidade dos novos parâmetros

ANP: https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-de-precos-de-combustiveis-ultimas-semanas-pesquisadas

Página consultada em 03/10/2026: disponível referência semanal 27/09/2026 a 03/10/2026, atualização indicada 02/10/2026. Essa verificação identifica a fonte e período disponível; não extraiu preço municipal nem confirma abastecimento da frota. Escolher combustível do veículo e local de abastecimento; guardar planilha bruta, URL, período, data de coleta e SHA-256 antes de liberar valor. Preferir última semana publicada e atualizar se tiver mais de 14 dias; manter data do valor.

Pedágios: conferir páginas oficiais de concessionárias/ARTESP/ANTT conforme trechos efetivamente percorridos, praça, sentido, categoria e vigência da tarifa. Não presumir categoria ou pagamento por cidade. Retorno e eventuais isenções precisam constar. Fontes de desgaste: histórico representativo da frota, revisão/orçamento e vida útil documentada; qualquer hipótese deve ser nomeada.

Referência metodológica de separação fixo/variável: https://www.gov.br/antt/pt-br/assuntos/cargas/politica-nacional-de-pisos-minimos-de-frete/perguntas-frequentes-pmf/7-metodologia-de-calculo-2014-custos-fixos-variaveis-insumos-de-referencia-e-itens-nao-previstos/7-2-o-que-sao-custos

## Execução no computador

1. Extrair arquivos na raiz, preservando src, sql e docs. O run_pipeline.py entregue acrescenta a flag da etapa 22 às etapas anteriores.
2. Executar primeiro SQL 11 e enviar suas 12 linhas para comparar o resultado no servidor.
3. Para gerar os circuitos diretamente a partir das views aprovadas, usar a etapa isolada, sem repetir a extração inicial:

```powershell
python src/etapa_22_prioridades_circuitos.py --servidor "DESKTOP-MAMEBQ8\SQLEXPRESS" --driver "ODBC Driver 17 for SQL Server" --confiar-certificado
```

Saída nova por run_id: datalake/03_gold/<run_id>/prioridades_circuitos com JSON, Parquet, manifesto e relatório Markdown. Auditoria: quality/22_prioridades_circuitos/<run_id>/conclusao_22.json. Não escreve tabelas SQL, não recarrega dados, não altera views e não sobrescreve execuções anteriores.

A execução futura com parâmetros preenchidos acrescenta:

```powershell
--parametros docs/22_prioridades_circuitos/PARAMETROS_CUSTO.json
```

Na pipeline completa: --prioridades-circuitos --sql-servidor "DESKTOP-MAMEBQ8\SQLEXPRESS" --sql-driver "ODBC Driver 17 for SQL Server" --confiar-certificado. A pipeline completa também executa seu fluxo inicial; para esta conferência, preferir a etapa isolada. As definições de views da etapa 21 permanecem instaladas via SQL 04; etapa 22 pressupõe essas views corrigidas.

Enviar conclusao_22.json e circuitos.json. Resultado preliminar local é arquivo separado de metodologia, não execução real do servidor e não conclusão final. XLSX de leitura e integração de novas tabelas ao SQL/Power BI podem ser preparados após conferir a nova saída. Nenhuma atualização ao GitHub/Azure foi executada por esta entrega.

## Verificações desta entrega

Algoritmo confrontado com enumeração de todas as permutações em quatro cidades; cobertura integral das 12 cidades nos dois grupos; inversão de ciclo simétrico conserva distância; menor ciclo não supera o circuito de referência; custos ausentes permanecem pendentes; cálculo de custo e equilíbrio conferido em exemplo exclusivamente de teste. Compilação dos scripts verificada. Execução no SQL Server e entradas rodoviárias reais ainda pendentes.
