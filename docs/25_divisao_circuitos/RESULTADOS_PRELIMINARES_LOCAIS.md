# Resultados preliminares locais da etapa 25

Matriz OSRM da validação local da etapa 24, com coordenadas equivalentes às enviadas pelo usuário. Ainda requer execução no computador do usuário.

| Limite de deslocamento por circuito | Resultado | Circuitos | km totais | horas totais |
|---|---|---:|---:|---:|
| 4 h | INVIAVEL_NESTE_LIMITE | None | None | None |
| 6 h | COBERTURA_COMPLETA_PRELIMINAR | 4 | 1407.0266000000001 | 20.934583333333332 |
| 8 h | COBERTURA_COMPLETA_PRELIMINAR | 2 | 951.232 | 15.359194444444446 |

- LIMITE_DESLOCAMENTO_6H_C01: Ribeirão Preto -> Planura -> Frutal -> Ribeirão Preto; 436.40 km; 5.60 h.

- LIMITE_DESLOCAMENTO_6H_C02: Ribeirão Preto -> Colômbia -> Barretos -> Ribeirão Preto; 343.19 km; 4.80 h.

- LIMITE_DESLOCAMENTO_6H_C03: Ribeirão Preto -> Franca -> Cristais Paulista -> Nuporanga -> Sales Oliveira -> Ribeirão Preto; 293.28 km; 4.58 h.

- LIMITE_DESLOCAMENTO_6H_C04: Ribeirão Preto -> Morro Agudo -> Guaíra -> Ipuã -> Orlândia -> Ribeirão Preto; 334.15 km; 5.96 h.

- LIMITE_DESLOCAMENTO_8H_C01: Ribeirão Preto -> Planura -> Frutal -> Colômbia -> Barretos -> Morro Agudo -> Ribeirão Preto; 499.89 km; 7.60 h.

- LIMITE_DESLOCAMENTO_8H_C02: Ribeirão Preto -> Cristais Paulista -> Franca -> Ipuã -> Guaíra -> Orlândia -> Nuporanga -> Sales Oliveira -> Ribeirão Preto; 451.35 km; 7.76 h.

No limite de 4 h, Frutal, Planura, Colômbia e Guaíra já ultrapassam o limite em viagens isoladas. A cobertura completa é inviável nesse cenário.

No limite de 6 h, mais retornos aumentam o percurso total: 1.407,03 km em quatro circuitos. No de 8 h, são 951,23 km em dois circuitos, com menos espaço para entregas e pausas. Não é recomendação de jornada ou rentabilidade.

Testes locais aprovados: exportação JSON/Parquet reconciliada na matriz real; teste sintético com ótimo conhecido (4/3/2 circuitos); cobertura única de todas as cidades; cenário inviável; matriz inválida rejeitada; compilação dos scripts. Dados sintéticos não integram as saídas do projeto.
