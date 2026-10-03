# Etapa 29 — Prioridades comerciais

Projeto: potencial-de-mercado-e-expansao-comercial.

A etapa lê gold.vw_perfil_comercial e a carga aprovada no SQL, sem modificar tabelas. Cruza os 12 municípios com os cinco circuitos e as 135 simulações da etapa 28, verificando hashes, cobertura e cálculos. Exporta JSON, Parquet e relatório; registra execução em quality/29_priorizacao_comercial.

Critérios separados: escala de varejo especializado, renda mediana municipal de 2022 e menor referência de faturamento por circuito. Não cria nota composta com pesos arbitrários. A fronteira de Pareto considera apenas escala e limiar simulado de receita; não é otimização operacional. Um circuito dominado nesses dois critérios continua fazendo parte da cobertura, pois custos e oportunidades reais podem diferir.

Cenário de referência: gasolina da coleta ANP, 10 km/l com carga (hipótese), desgaste de R$ 0,20/km (hipótese), margem de contribuição de 25% (hipótese) e pedágios candidatos OSM. Intervalos mínimo/máximo representam sensibilidade, não confiança estatística. Faturamento de referência cobre custos incrementais modelados; não constitui meta definitiva ou previsão de demanda.

A categoria disponível é CNAE 47.2; supermercados CNAE 47.1 não estão cobertos. Renda municipal nominal de 2022 não representa renda do comprador nem probabilidade de conversão. Não somar medianas de renda, inferir compras ou repartir metas por população.

Os cinco circuitos são sugestões para o vendedor dimensionar prospecção e receita compartilhada. Gerente do CD define logística, frequência e viagens dedicadas. Todas as cidades permanecem incluídas.

Leitura inicial: o grupo Franca/Cristais Paulista/Ipuã concentra 733 estabelecimentos e o Barretos/Guaíra 364. O grupo Sales Oliveira/Nuporanga/Morro Agudo/Orlândia reúne 201 e tem menor referência financeira entre os cinco. São alternativas de entrada por escala e por menor custo simulado; não prova de maior venda realizável.
