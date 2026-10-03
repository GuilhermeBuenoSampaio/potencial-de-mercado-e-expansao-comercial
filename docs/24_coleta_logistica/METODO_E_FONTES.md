# Etapa 24 — Coleta logística

Projeto: potencial-de-mercado-e-expansao-comercial

## Coleta reproduzível

1. Verificar manifesto, hashes de circuitos e coordenadas da etapa 22.
2. Consultar página oficial ANP, localizar a planilha resumo semanal mais recente e arquivar HTML/XLSX originais com URL, data e SHA-256.
3. Ler aba MUNICIPIOS por cabeçalhos, filtrar São Paulo, Ribeirão Preto e GASOLINA COMUM. Exigir registro único, unidade R$/l e semana encerrada há no máximo sete dias (semana em curso permitida).
4. Consultar matriz OSRM driving de distâncias e durações entre os 13 pontos existentes. Conservar a resposta original. Rejeitar rota ausente, valores não finitos e fallback por linha reta. Não preencher distância ausente por Haversine.
5. Somar trechos direcionais de cada uma das cinco sequências, incluindo retorno. Não assumir que ida e volta têm a mesma distância.
6. Gerar cenários de gasolina para os consumos hipotéticos da etapa 23, sem chamar esse gasto parcial de custo total ou faturamento mínimo.

## Distâncias e tempo

OSRM fornece distâncias em metros e durações em segundos nos caminhos escolhidos pelo motor. A matriz driving usa caminhos de seu perfil de roteamento; não equivale automaticamente à menor distância possível, à menor tarifa ou ao melhor circuito comercial.
As sequências da etapa 22 são avaliadas, não reotimizadas. Um ciclo ótimo em linha reta não é necessariamente ótimo na malha rodoviária.
Os pontos são centroides do IBGE já disponíveis; não são endereços de clientes ou do CD. O ajuste do ponto à malha fica tabulado. Mais de 500 m aciona revisão; essa é uma regra de triagem, não garantia de precisão para valores menores. Pode haver acesso rural ou via inadequada para entrega.
O tempo modelado não inclui trânsito atual, entregas, visitas ou pausas. Não autoriza agenda diária. O circuito amplo de Barretos merece divisão posterior por tempo e capacidade.
Nenhuma distância preliminar é automaticamente transferida para o campo final de custos da etapa 23.

## Combustível

Conferência inicial local em 03/10/2026: R$ 6,70/l de gasolina comum em Ribeirão Preto, semana 27/09–03/10/2026, 24 postos, mínimo R$ 6,42 e máximo R$ 7,19. A coleta atualiza esses números; não fixa esse valor para sempre.
A média dos postos é referência de mercado, não comprovante do preço pago pela empresa.
Fonte oficial: https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-de-precos-de-combustiveis-ultimas-semanas-pesquisadas

## Fontes rodoviárias

Motor: https://router.project-osrm.org
Documentação: https://project-osrm.org/docs/v26.4.0/http
Malha: OpenStreetMap, consultada via OSRM, com versão registrada quando o serviço informar. Se não informar, versão permanece nula.
Servidor público pode apresentar indisponibilidade. Falhas geram coleta parcial com causa registrada; nenhuma fonte secundária é usada silenciosamente.

## Pedágios e veículo

OSRM não informa tarifas. Conferir praças/pórticos efetivamente atravessados, direção, tarifa vigente, categoria da Fiorino e modalidade de pagamento. Não presumir zero por ausência de retorno do motor, nem aplicar automaticamente desconto de TAG.
Fonte localizada para pesquisa de tarifas regionais: https://www.ecoviasnoroestepaulista.com.br/servicos/
Entrevias deve ser conferida em https://entrevias.com.br/ ; nenhum total foi atribuído ao circuito sem confirmar as passagens.
Fiat divulga capacidade nominal de até 650 kg e 3,3 m³ na referência atual: https://www.media.stellantis.com/br-pt/fiat/press/fiat-fiorino-vence-premio-campeao-de-revenda-2026-com-a-menor-depreciacao-entre-as-furgonetas-de-carga
Essa divulgação não foi usada como capacidade líquida de produtos da frota; falta confirmar modelo e convenção do manual.

## Saídas

Fontes originais em datalake/01_bronze/<run_id>/logistica; tabelas JSON/Parquet e relatório em datalake/03_gold/<run_id>/logistica; conclusão em quality/24_coleta_logistica/<run_id>.
PARAMETROS_23_COM_COMBUSTIVEL.json incorpora somente o preço oficial coletado. Não altera a configuração original, nem as bases SQL. Mantém distância final, pedágios, desgaste, margens e mix sem preenchimento automático.
