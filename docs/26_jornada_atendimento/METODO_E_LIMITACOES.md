# Etapa 26 — Jornada total e atendimento

Projeto: potencial-de-mercado-e-expansao-comercial

## Mudança solicitada

O usuário considerou apertados os circuitos definidos apenas por horas dirigindo. Esta etapa incorpora atendimento, pausas e reserva dentro da restrição de tempo.
Tempo total modelado = deslocamento OSRM + quantidade de atendimentos × minutos por atendimento + pausas + reserva.
A configuração inicial usa HIPÓTESES: jornada de 8 h, pausas de 1 h, reserva de 1 h, atendimento de 20 minutos, com 1/3/5 atendimentos por cidade. Esses valores não são medições nem jornada informada pela empresa.
A quantidade uniforme por município facilita a comparação; não representa pedidos, clientes conquistados ou demanda prevista.
Um atendimento por município é cenário mínimo de cobertura geográfica, não uma rota comercial cheia ou economicamente suficiente.

## Otimização

A matriz OSRM dirigida da etapa 24 é reutilizada, com hashes e ordem dos pontos conferidos. Held–Karp calcula o ciclo de menor tempo de cada subconjunto. Só são admitidos os subconjuntos cujo tempo de deslocamento + atendimento + pausas + reserva cabe na jornada hipotética.
A cobertura por programação dinâmica minimiza número de circuitos e depois deslocamento total, com km como desempate nos ciclos de menor tempo escolhidos. Todas as 12 cidades devem aparecer exatamente uma vez em um plano completo.
Se uma cidade não cabe nem em viagem isolada, o cenário completo é inviável. Nenhuma cidade é excluída para declarar cobertura completa. A tabela viagens_isoladas mostra a causa e a capacidade teórica de atendimentos na viagem exclusiva.
O máximo de atendimentos é teto matemático de tempo nesta aproximação; não é promessa de produtividade. O tempo entre estabelecimentos dentro da cidade, carregamento no CD, restrições de horário e volume descarregado não foram medidos. Esses componentes poderão consumir a reserva ou exigir redução adicional da capacidade calculada.
Não se considera entrega nem pausa como zero: valores são hipóteses editáveis. Os campos de custo e faturamento permanecem nulos.

## Limitações preservadas

Centroides ajustados à malha ainda representam os pontos. Cristais Paulista, Morro Agudo e Barretos continuam sinalizados; nenhum endereço operacional foi corrigido nesta etapa.
Consumo carregado, peso por pedido, mix, capacidade líquida, pedágios e desgaste não integram esta otimização. A Fiorino cheia não implica número conhecido de entregas: depende do volume de cada pedido.
Não é possível garantir viabilidade real ou indicar jornada apropriada sem dados operacionais. Uma mudança de reserva, atendimento, origem ou pontos pode alterar o resultado.
O procedimento não separa automaticamente dias, vendedores e veículo: cada circuito é uma viagem independente. Frequência e ordem comercial ainda serão definidas.
Em cidades distantes, consolidação de pedidos pode melhorar a contribuição por parada, mas não elimina o tempo de ida/volta. Qualidade dos produtos e efeito de indicação permanecem hipóteses comerciais, sem conversão prevista.
