# Etapa 23 — Custos de rota com carga máxima

Projeto: potencial-de-mercado-e-expansao-comercial

## Premissas confirmadas pelo usuário

Fiorino nova, gasolina, sem refrigeração; saída com capacidade máxima de peso.
O motorista e os pagamentos fixos do veículo não entram no custo incremental desta decisão.
Capacidade líquida de produtos e ano/motor da frota ainda não foram confirmados.

## Consumo

Fiat divulga 12,4 km/l urbano e 13,6 km/l rodoviário para a Fiorino GSE 1.3 atual.
Esses números não comprovam o consumo da frota carregada.
8, 10 e 12 km/l são hipóteses escolhidas apenas para análise de sensibilidade, sem atribuir probabilidades ou afirmar que abrangem o consumo real.
O script considera o mesmo consumo carregado no percurso inteiro, incluindo retorno: aproximação conservadora quanto à redução de carga, sem garantia de cobrir trânsito, relevo ou estilo de condução.
Não aplica um percentual de penalização por peso inventado. Calibração futura: km percorridos/litros repostos em viagens comparáveis, com registro de carga.

## Custo e equilíbrio

Custo incremental = km rodoviários × (gasolina R$/l ÷ km/l + desgaste R$/km) + pedágios.
Faturamento de equilíbrio = custo incremental ÷ margem de contribuição disponível antes do custo de rota.
Margem deve descontar os demais custos variáveis uma única vez. Exemplos de margem serão cenários, não resultados financeiros da empresa.
Desgaste: pneus (custo líquido do jogo/vida útil em km), manutenção periódica (custo/intervalo), reserva de reparos (histórico/km). Não duplicar itens nem tratar garantia ou veículo novo como custo zero.
Financiamento, salário fixo e depreciação por tempo ficam fora; eventual perda de valor atribuída à quilometragem precisa de estimativa própria para ser incluída sem duplicação.

## Restrição de carga

kg no equilíbrio = faturamento de equilíbrio/receita média por kg do mix específico.
Faturamento máximo por peso = capacidade líquida de produtos × receita média por kg desse mix.
Capacidade líquida deve respeitar a definição do manual e descontar ocupantes/equipamentos quando aplicável; não pressupor um valor nominal do modelo.
Não usar média global dos preços do catálogo: apresentações e pesos diferem, vigência não confirmada e parte dos pesos está ausente.
O teste de peso não verifica espaço cúbico, demanda, horários ou viabilidade diária.

## Fontes e pendências

REGISTRO_FONTES.json registra URLs, consulta e status. Valores secundários de gasolina divergentes não entram no cálculo. Usar tabela municipal ANP recente ou preço efetivamente pago documentado, com período.
Distância geodésica não é substituída por um multiplicador arbitrário. Distância rodoviária e pedágios devem representar a sequência inteira, ida e retorno, e a categoria correta de veículo. Zero pedágio exige fonte também.
O custo de uma cidade adicional deve usar o desvio rodoviário da rota conjunta, não necessariamente uma viagem exclusiva. O equilíbrio principal é do circuito: cidades maiores podem cobrir paradas menores, dependendo das contribuições efetivas.
A etapa 23 consome os circuitos da 22 e gera JSON, Parquet e relatório MD com execução única e hashes, sem alterar SQL, Azure ou GitHub.
