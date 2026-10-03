# Resultados preliminares locais — jornada e atendimento

Hipóteses: 8 h totais, 1 h de pausa, 1 h de reserva; atendimento de 20 minutos. Os valores não foram medidos na empresa.

| Atendimentos por cidade | Cobertura completa | Circuitos | Cidades que não cabem nem isoladamente |
|---|---|---:|---|
| 1 | COBERTURA_COMPLETA_PRELIMINAR | 5 | Nenhuma |
| 3 | INVIAVEL_NESTE_LIMITE | None | Frutal |
| 5 | INVIAVEL_NESTE_LIMITE | None | Frutal; Planura; Guaíra |

Um atendimento por cidade cobre as 12 cidades em cinco viagens, totalizando 1.691,75 km preliminares. Isso é cobertura geográfica mínima, não comprovação de rota carregada ou viabilidade econômica.

Três atendimentos por cidade tornam a cobertura completa inviável neste cenário por causa de Frutal. Cinco atendimentos tornam inviáveis Frutal, Planura e Guaíra. Mais divisão não resolve uma viagem isolada que já excede o tempo.

Limitações: tempo entre clientes e carregamento não medidos; centroides mantidos; nenhum custo total ou venda mínima disponível.

Testes aprovados: exportação JSON/Parquet na matriz real; simulação sintética com resultado conhecido (4/6/12 circuitos); soma de deslocamento, atendimento e reservas dentro da jornada; teto de atendimentos; 36 viagens isoladas; cobertura das 12 cidades. Dados sintéticos não integram a base do projeto.
