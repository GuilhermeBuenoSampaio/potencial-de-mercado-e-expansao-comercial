# Etapa 25 — Divisão de circuitos por tempo

Projeto: potencial-de-mercado-e-expansao-comercial

A etapa consome a matriz OSRM arquivada pela 24, verifica hashes, ordem dos pontos e rotas válidas. Não faz nova consulta à internet, não altera SQL ou fontes e não substitui os centroides por endereços inventados.

## Algoritmo e objetivo

Held–Karp por programação dinâmica calcula o ciclo de menor TEMPO para cada subconjunto das 12 cidades, com retorno a Ribeirão Preto e matriz dirigida. Distância é desempate: não é objetivo de menor combustível/pedágio.
Outro algoritmo de programação dinâmica cobre todas as cidades por subconjuntos disjuntos dentro do limite. Objetivo lexicográfico: primeiro minimizar número de circuitos; depois tempo total de deslocamento; depois distância total dos ciclos de menor tempo para desempate.
O particionamento é exato quanto a número de circuitos e tempo na matriz fornecida. O desempate de km opera nos ciclos de menor tempo escolhidos, sem afirmar ótimo global de custo ou de distância.
Com 12 municípios, são 4.095 subconjuntos possíveis, em vez de escolher grupos arbitrários por intuição. Todo cenário declarado completo cobre cada cidade exatamente uma vez.
Cada ciclo pode exigir visitas a vários estabelecimentos na mesma cidade; o modelo trabalha na granularidade municipal, sem representar essas visitas.

## Cenários de limite

4, 6 e 8 horas de DESLOCAMENTO são hipóteses para análise de sensibilidade, não limites operacionais informados pela empresa, nem jornadas de trabalho confirmadas.
Não incluem tempo de entrega/prospecção, espera, trânsito atual ou pausas. Planejar jornada exige somar esses componentes.
Se nem a viagem isolada cabe no limite, o cenário é inviável e registra as cidades afetadas. Não excluir cidades para apresentar uma cobertura artificialmente completa.
Dividir rotas normalmente aumenta retorno ao CD, km e combustível; esse custo é contrapartida do limite de tempo. Menos km não garante melhor atendimento, maior venda ou maior lucro.
Os três pontos acima de 500 m de ajuste à malha continuam em pontos_revisao. Todos os pontos, inclusive o CD, seguem como aproximações por centroides. Nenhuma correção geográfica foi efetuada nesta etapa.

## Interpretação comercial

O circuito que passa por Franca pode ser candidato inicial, mas sua ordem de execução não é escolhida por este algoritmo: ele considera deslocamento, não conversão, volume comprado ou margem. A prioridade comercial deve combinar a evidência de varejo especializado, contexto de renda e custos ainda pendentes.
Franca e Barretos não são impostas como centros de distribuição. As novas divisões podem misturar cidades dos antigos grupos se isso melhorar o objetivo matemático.
Pedágios, consumo com carga, desgaste, mix, capacidade líquida e margens permanecem fora do objetivo. Não há faturamento mínimo calculado.
O próximo aprofundamento será comparar circuitos candidatos com tempo de atendimento e custos documentados, mantendo todas as cidades contempladas.
