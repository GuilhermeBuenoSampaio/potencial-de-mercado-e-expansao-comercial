# Resultados preliminares da coleta local

Consulta online em 03/10/2026, sobre coordenadas da Silver local e sequências equivalentes às enviadas pelo usuário. A execução no computador do usuário ainda deve ser conferida.

Gasolina oficial ANP: R$ 6,70/l, 24 postos, semana 27/09–03/10/2026. 8/10/12 km/l são hipóteses não calibradas de consumo carregado.

| Circuito | km rodoviários preliminares | horas modeladas | Só gasolina a 8 km/l | Só gasolina a 10 km/l | Só gasolina a 12 km/l |
|---|---:|---:|---:|---:|---:|
| TODAS_PROXIMAS_PRIMEIRO | 958.78 | 15.17 | R$ 802.97 | R$ 642.38 | R$ 535.32 |
| TODAS_DISTANTES_PRIMEIRO | 958.62 | 15.18 | R$ 802.84 | R$ 642.28 | R$ 535.23 |
| TODAS_MENOR_CICLO | 773.43 | 13.11 | R$ 647.75 | R$ 518.20 | R$ 431.83 |
| ANCORA_3516200 | 322.38 | 5.21 | R$ 270.00 | R$ 216.00 | R$ 180.00 |
| ANCORA_3505500 | 574.91 | 9.57 | R$ 481.49 | R$ 385.19 | R$ 320.99 |

Franca é o primeiro circuito candidato para aprofundamento: 848 unidades de varejo especializado de 2024 no grupo e menor deslocamento preliminar. Isso não comprova pedidos, faturamento ou rentabilidade. Barretos tem 589 unidades no grupo e 9,57 horas modeladas; precisa de divisão em circuitos menores antes de uma agenda diária. Todos os municípios devem permanecer contemplados no planejamento.

O ciclo TODAS_MENOR_CICLO é o menor ciclo GEODÉSICO da etapa 22. Aqui avaliamos sua sequência na malha; não afirmamos que seja o menor ciclo rodoviário. Perto-primeiro e distante-primeiro diferem na malha direcionada.

Os pontos de Cristais Paulista (~1.360 m), Barretos (~764 m) e Morro Agudo (~682 m) foram sinalizados por ajuste à malha acima de 500 m. Todos os pontos, inclusive a origem, precisam ser substituídos por endereços operacionais para planejamento de entrega.

Testes aprovados: coleta online ANP/OSRM; 1 registro de gasolina; 5 circuitos; 53 trechos; 13 pontos; 15 cenários; reconciliação integral JSON/Parquet; rejeição de preço antigo, matriz nula/negativa/NaN e fallback em linha reta; compilação do script e orquestrador.

Pedágios, manutenção/desgaste, margem e mix continuam pendentes. Valores acima são gasto apenas com gasolina, não custo total ou faturamento mínimo.
