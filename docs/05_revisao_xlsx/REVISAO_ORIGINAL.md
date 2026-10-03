# potencial-de-mercado-e-expansao-comercial

## Revisão do XLSX original

Arquivo: `01 - BASE DE DADOS.xlsx`. SHA-256: `ee262a683bae0db283c645a2e85f8261545c3ba96775f602f8af7c0261e336e4`. A revisão inicial identificou dez abas, 975 células preenchidas e 12 cidades. Nenhuma fórmula está armazenada; os resultados existentes são valores fixos. A fonte original é preservada.

## Achados e decisões

| Achado | Evidência | Tratamento para a revisão |
|---|---|---|
| Coordenadas fora dos limites em graus decimais | 24 células de latitude/longitude na aba de estratégia | Reobter coordenadas com fonte e código municipal; não deslocar a vírgula por suposição |
| Unidade populacional ambígua | Cabeçalho em milhares e valores como 364331 | Confirmar unidade e período na fonte |
| Escala do PIB de Frutal pendente | Valor 2473117,87, diferente da ordem de grandeza das demais cidades | Confirmar se o valor está em reais ou milhares de reais; preservar original |
| Crescimento em cinco anos aplicado a cada ano | 120 projeções reproduzem `base * (1 + taxa) ** (ano - 2023)` | Confirmar definição da taxa e período; refazer cenários |
| PIB usado para projetar vendas | Aba de potencial reproduz a mesma regra das projeções de PIB | Documentar e validar hipótese de demanda, sem assumir equivalência |
| Razão potencial/custo apresentada como retorno | 12 razões coincidem com potencial dividido por custo de entrega | Compatibilizar períodos e custos comerciais antes de interpretar retorno |
| Rankings sem evidência específica | Percentuais e listas estão salvos como valores | Rastrear fonte ou manter como premissas não aprovadas |
| Percentuais históricos reutilizados | Aba de dados complementares contém parâmetros de consumo | Preservar referência histórica; não converter prevalência em quantidade comprada |
| Origem logística única não comprovada | Todos os municípios indicam Ribeirão Preto | Comparar São Carlos e os CDs de Ribeirão Preto, Campinas, Sorocaba e São Paulo |

As 156 comparações aritméticas coincidem com os resultados armazenados: 120 projeções, 24 diferenças e 12 razões. Isso constitui reconstrução de regras compatíveis com os valores, não recuperação das fórmulas nem validação metodológica.

As classes A–E apresentam desvios pequenos em relação à soma de 100% em algumas cidades. Registrar os desvios e conferir arredondamento, definições e fonte; não normalizar silenciosamente. O consumo reportado em uma semana mede pessoas que referiram consumo, não número de compras, pacotes ou unidades.

IBGE e Caravela são fontes informadas pelo usuário. O PIB foi atribuído ao IBGE pelo usuário, mas ainda exige tabela específica, ano, variável e unidade. Não há evidência suficiente para atribuir retrospectivamente cada indicador às instituições.

## Próximo bloco

Validar a base municipal com fonte e período explícitos, revisar unidades e localizar premissas de venda e logística. Refazer os cálculos em Python, preservando os resultados antigos apenas para comparação. Preços são por produto e apresentação; custos fabris não integram o escopo comercial do vendedor.
