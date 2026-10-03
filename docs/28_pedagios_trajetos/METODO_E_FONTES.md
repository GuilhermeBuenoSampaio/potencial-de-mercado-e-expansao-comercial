# Pedágios e trajetos: etapa 28

Objetivo: acrescentar estimativa provisória de pedágios, com evidência cartográfica reproduzível, sem transformar tarifa colaborativa em homologação oficial. Usa as etapas 24, 26 e 27 vinculadas; mantém as execuções anteriores intactas.

## Coleta e cálculo

1. Verifica os hashes dos circuitos, coordenadas e referência de gasolina anteriores.
2. Consulta cada circuito completo no serviço público OSRM, com geometrias e instruções por trecho. Recalcula km e horas do caminho retornado. O motor busca seu caminho segundo perfil/peso rodoviário, não menor pedágio nem consumo.
3. Consulta cabines e pórticos no OpenStreetMap pela API pública Overpass, dentro de uma área que engloba os novos trajetos. Arquiva os JSONs originais, URLs, horários e hashes na Bronze.
4. Identifica candidatos a até 3 metros dos segmentos das geometrias. A tolerância pequena evita contar também a cabine da pista oposta. Conta cada ID de nó uma vez por trecho. Não confirma cobrança operacional, sentido ou atualização do cadastro; uma eventual passagem repetida dentro do mesmo trecho requer revisão manual.
5. Extrai `charge` para `motorcar` no OSM como tarifa provisória, preservando `check_date`. Não aplica desconto de TAG nem DUF. A classificação supõe Fiorino comum sem reboque, dois eixos e rodagem simples; conferir categoria aplicável em cada concessionária.
6. Calcula cenários usando os NOVOS km e a soma dos valores dos pontos identificados. Não mistura pedágio de um trajeto novo com quilometragem da matriz antiga.

O cadastro OSM é colaborativo, pode omitir portais, conter praças extintas ou tarifas vencidas. Ausência de ponto não é prova de viagem gratuita. Pórticos modelados como linhas são registrados como pendência e não entram no cruzamento de nós. Não se declara cobertura integral. Campo `pedagio_total_homologado_brl` permanece nulo em todos os circuitos.

Para manter a interpretação clara, a tabela de sensibilidade usa campos específicos `pedagio_estimado_pontos_osm_brl`, `custo_estimado_com_pontos_osm_brl` e `receita_estimada_com_pontos_osm_brl`. Os campos de equilíbrio homologado herdados da etapa 27 permanecem nulos. São cenários aproximados, não orçamento ou pedido mínimo aprovado.

## Fontes e situação da pesquisa em 03/10/2026

- OSRM: https://router.project-osrm.org ; documentação https://project-osrm.org/docs/v26.4.0/http/ . Tempos sem trânsito ao vivo, descarga real ou endereços de clientes.
- OpenStreetMap/Overpass: https://overpass-api.de/api/interpreter ; licença ODbL, atribuição aos contribuidores do OpenStreetMap. Cada passagem candidata traz URL do nó.
- Ecovias Noroeste Paulista, publicação de 29/04/2026, vigência desde 01/05/2026: https://www.ecoviasnoroestepaulista.com.br/noticias/novas-tarifas-de-pedagio-entram-em-vigor-em-1o-de-maio-nas-rodovias-da-ecovias-noroeste-paulista/
- Tabela oficial de categorias: https://www.ecoviasnoroestepaulista.com.br/wp-content/uploads/sites/15/2026/04/2026-Tarifas-Site.pdf . O script arquiva o PDF e tabula as dez tarifas publicadas no comunicado. Encontrar uma tarifa não confirma que a praça foi atravessada.
- Entrevias: https://entrevias.com.br/ . Consulta direta retornou HTTP 406 durante a pesquisa; tabela atual não homologada neste pacote.
- ViaPaulista: https://www.arteris.com.br/viapaulista/tarifas . Consulta direta indisponível durante a pesquisa; tabela atual não homologada neste pacote.
- Regulador: https://dadosabertos.artesp.sp.gov.br/dataset/pedagio . Recurso aponta para página institucional, cuja consulta direta também ficou indisponível.

A pesquisa encontrou as referências cartográficas de Sertãozinho, Pitangueiras, Colina, Batatais, Restinga e Sales Oliveira nos cinco caminhos. Valores e quantidades devem ser confirmados nas saídas da execução; podem mudar conforme atualização do roteador e do OSM. A confirmação oficial deve checar tarifas atuais, categoria, vigência, sentidos, inclusão de todos os pórticos e geometria usada. Nenhuma configuração aprovada da etapa 27 é sobrescrita.

## Uso na decisão comercial

Compartilhar viagens ou dedicar veículo a um pedido grande continua uma sugestão condicionada à contribuição dos pedidos, tempo e capacidade. População e quantidade CNAE não geram pedidos previstos. O catálogo não permite inferir margem global. Consumo com carga máxima, desgaste e margem continuam hipóteses explícitas.

Diferenças entre etapa 26 e 28 ficam em km e percentual. A jornada total é recalculada substituindo apenas o tempo de direção pelo tempo da nova geometria, preservando hipóteses de atendimento, pausas e reserva. Isso não equivale a agenda operacional confirmada.
