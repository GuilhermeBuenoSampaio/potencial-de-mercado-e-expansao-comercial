# Custo incremental e equilíbrio das viagens

Esta etapa não escolhe uma rota definitiva. Avalia os cinco circuitos da etapa 26 e preserva a referência de tempo das viagens isoladas. A cobertura das 12 cidades continua sendo requisito; dividir para caber no dia não comprova vantagem econômica.

## O que é observado e o que é hipótese

- Gasolina: preço da fonte ANP coletada e validada na etapa 24; semana de referência preservada. Atualizar a coleta em outra data antes de orçamento operacional.
- Distâncias: OSRM preliminar entre centroides, reaproveitadas da etapa 26.
- Consumo com carga máxima: 8/10/12 km/l são hipóteses, sem medição da frota.
- Desgaste: R$ 0,10/0,20/0,30 por km são apenas uma grade de sensibilidade escolhida para testar a decisão. Não são estimativas comprovadas de manutenção de Fiorino.
- Margens de 15%/25%/35% são hipóteses. Não usar média global dos preços do catálogo para inferir margem ou receita.
- Pedágios ficam nulos até verificar tarifa, categoria, vigência e todas as passagens da sequência, inclusive retorno. Nunca preencher zero por ausência de informação.

Para calibrar desgaste: somar custos de pneus e manutenção ligados ao uso e dividir pelos km do período; ou somar custo de cada intervenção dividido por seu intervalo previsto. Não somar duas vezes as mesmas despesas. Veículo novo também tem desgaste, mas isso não determina sozinho seu valor por km. Financiamento e salário fixo do motorista não entram no custo incremental desta etapa. Não há otimização de consumo por descarga gradual.

## Decisão por viagem

Contribuição dos pedidos = receita menos demais custos variáveis, antes da logística desta viagem. Cobertura = contribuição/custo da viagem. Cobertura igual a 1 é equilíbrio, não margem de segurança. Sem pedidos e margem conhecidos, calcular limiares hipotéticos, sem declarar lucro.

Alternativas condicionais:
1. Rota compartilhada: contribuição dos pedidos das várias cidades cobre o custo conjunto, dentro de jornada, volume e peso.
2. Consolidação: menor frequência e maior pedido por visita, se prazos e necessidades dos clientes permitirem.
3. Entrega dedicada: pedido grande que cobre sozinho a viagem e exige tempo de descarga ou capacidade relevante. Os tempos isolados da etapa 26 não incluem uma descarga longa medida e não autorizam a operação.

A capacidade líquida, volume ocupado, pedidos e endereços reais são desconhecidos. Não imputar automaticamente 650 kg vendáveis. Viagens dedicadas ainda não têm custo calculado nesta etapa, pois a tabela de referência isolada não possui km.

## Pedágios: fonte encontrada e trabalho pendente

Fonte primária consultada em 03/10/2026: https://www.ecoviasnoroestepaulista.com.br/noticias/novas-tarifas-de-pedagio-entram-em-vigor-em-1o-de-maio-nas-rodovias-da-ecovias-noroeste-paulista/

A publicação apresenta tarifas vigentes desde 01/05/2026. Isso não comprova que os circuitos atravessam todas as praças listadas. Nenhuma tarifa foi atribuída a circuito neste pacote. Ainda verificar Entrevias e demais operadores conforme geometria rodoviária; não usar somatório regional genérico.

O campo `pedagios_por_circuito` aceita o ID exato do circuito e objeto com `total_brl`, `fonte`, `vigencia` e `passagens_verificadas: true`. O valor deve representar a viagem inteira. A declaração é fornecida pelo analista e não verificada automaticamente em mapa pelo script.

Os cinco circuitos geram 135 combinações (5 × 3 consumos × 3 desgastes × 3 margens). O custo parcial e o limiar de receita sem pedágio são explicitamente separados do custo modelado com pedágio. Mesmo após preencher pedágio, hipóteses não calibradas e ausência de pedidos impedem confirmar viabilidade.

Varejo especializado CNAE 47.2 não inclui supermercados CNAE 47.1. A sugestão de entrega dedicada a supermercado vem da experiência operacional relatada pelo usuário, sem inferir quantidade de supermercados pelos indicadores disponíveis.
