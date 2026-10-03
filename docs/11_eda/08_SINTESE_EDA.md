# Síntese da EDA

**Projeto:** `potencial-de-mercado-e-expansao-comercial`  
**Data:** 02/10/2026 — horário de São Paulo.  
**Situação:** sete blocos implementados; síntese consolidada com limitações e conferências de resultados ainda explicitadas abaixo. Não constitui encerramento do projeto nem recomendação comercial definitiva.

## 1. Pergunta de negócio

Como as 12 cidades se diferenciam em tamanho de mercado, condições socioeconômicas, estrutura comercial e localização, e quais diferenças devem orientar a investigação para abertura de mercado pelo vendedor?

Cidades: Franca, Cristais Paulista, Frutal, Morro Agudo, Sales Oliveira, Orlândia, Nuporanga, Ipuã, Guaíra, Barretos, Planura e Colômbia. Fábrica: São Carlos. CDs: Ribeirão Preto, Campinas, Sorocaba e São Paulo.

O foco é comercial e de vendas. Os preços são específicos por produto e pacote; custos de fabricação não foram estimados.

## 2. Qualidade e cobertura

A exploração trabalha com fontes e resultados rastreáveis, preservando unidade, período, classificação e indicador. A data de coleta não torna um dado antigo atual.

| Constatação da estrutura | Implicação |
|---|---|
| 56 indicadores/classificações; 43 com cobertura completa e 13 sem cobertura completa | A cobertura deve acompanhar cada comparação |
| 75 valores ausentes no painel de período comum | Ausência não foi convertida em zero nem preenchida com outro ano |
| 49 registros históricos na base de últimos valores | Último valor disponível não significa referência contemporânea |
| Seis pendências documentais | Preços e estudos mantêm restrições de uso |

O mecanismo de ausência não foi identificado como MCAR, MAR ou MNAR. Não houve imputação automática. Valores extremos foram sinalizados para investigação, sem exclusão estatística automática.

## 3. Tamanho de mercado e distribuição dos indicadores

Franca, Barretos e Frutal se destacam por população: respectivamente 366.534, 127.276 e 61.588 habitantes na estimativa de 2026. Esse recorte contextual difere da população de 2024 usada nas taxas comerciais e no painel multivariado.

Em 2024, Franca apresenta 869 unidades de alimentação, Barretos 474 e Frutal 166. Franca e Barretos concentram aproximadamente 69,9% das 1.922 unidades registradas nas 12 cidades.

A concentração sugere maior universo de estabelecimentos para investigar nas cidades maiores. Não demonstra que esses estabelecimentos compram salgados congelados, estão disponíveis para prospecção ou não possuem fornecedores.

A univariada registrou 70 sinalizações de valores extremos em 41 variáveis. Franca e Barretos concentram 56 sinalizações. Elas não representam 56 erros independentes: vários indicadores refletem o mesmo porte municipal. Mediana e IQR complementam média e desvio padrão para descrever esse conjunto assimétrico.

## 4. Renda, urbanização e presença comercial

PIB por habitante e renda domiciliar possuem conceitos distintos. A análise não usa PIB per capita como salário ou poder de compra mensal.

No recorte de renda mediana de 2022, Nuporanga e Sales Oliveira apresentam R$ 1.333,33, Barretos R$ 1.328,00, Orlândia R$ 1.266,67 e Franca R$ 1.250,00. Esses valores descrevem o indicador selecionado e sua população de referência; não equivalem ao orçamento alimentar de cada comprador.

As associações abaixo foram calculadas com 12 cidades. Pearson avalia associação linear; Spearman compara posições. Valores da etapa 16 foram conferidos na execução local de validação, ainda sem leitura independente das tabelas finais do computador do usuário.

| Relação | Pearson | Spearman | Leitura |
|---|---:|---:|---|
| População 2024 × unidades de alimentação 2024 | 0,981 | 0,916 | Forte associação entre porte e quantidade de estabelecimentos |
| Renda mediana 2022 × alimentação por 10 mil habitantes 2024 | 0,680 | 0,654 | Maior renda acompanha maior presença relativa neste conjunto |
| Renda mediana 2022 × varejo alimentar por 10 mil habitantes 2024 | 0,690 | 0,671 | Padrão semelhante no varejo alimentar |
| Urbanização 2022 × renda mediana 2022 | 0,398 | 0,060 | Não há ordenação consistente entre urbanização e renda |
| Renda mediana 2022 × distância ao CD mais próximo | −0,545 | −0,608 | Cidades mais próximas tendem a apresentar maior renda neste conjunto |
| Varejo alimentar por 10 mil habitantes 2024 × distância ao CD | −0,617 | −0,678 | Maior presença relativa tende a ocorrer mais perto do CD |

As associações não demonstram causalidade. Períodos de 2022 e 2024 permanecem distintos. Taxas comerciais compartilham o denominador populacional; seus vínculos não podem ser tratados como inteiramente independentes.

A hipótese de que cidades do interior expliquem a associação fraca entre urbanização e renda não foi comprovada por esta base.

## 5. Resultado multivariado e estabilidade

Foram integradas sete dimensões: população 2024, renda mediana 2022, urbanização 2022, unidades de alimentação 2024, alimentação e varejo alimentar por 10 mil habitantes em 2024 e distância ao CD.

Os perfis usam posição robusta em relação à mediana e ao IQR. `log1p` é aplicado apenas à população e à contagem de alimentação para visualização. As correlações utilizam os valores originais. Os perfis não foram somados e os sinais não representam desempenho bom ou ruim.

| Relação com controle linear | Original | Parcial | Intervalo ao retirar uma cidade por vez |
|---|---:|---:|---:|
| População × alimentação; controle: pessoal ocupado, 2024 | 0,981 | −0,101 | −0,449 a 0,692 |
| População × varejo alimentar; controle: pessoal ocupado, 2024 | 0,996 | 0,387 | −0,156 a 0,821 |
| Urbanização × renda mediana; controle: população, 2022 | 0,398 | 0,352 | −0,063 a 0,554 |

População e pessoal ocupado têm correlação de aproximadamente 0,997. Após o ajuste linear, resta apenas 0,52% da variância populacional para analisar. As mudanças de sinal nas exclusões individuais mostram sensibilidade; não sustentam efeitos econômicos negativos nem conclusões causais.

PCA e clustering não foram aplicados: nesta etapa, perfis por dimensão e análise de sensibilidade respondem à pergunta exploratória sem impor agrupamentos potencialmente instáveis em 12 cidades. As técnicas continuam condicionadas a uma pergunta comercial útil e validação posterior.

## 6. Evolução temporal e pendência de PIB

A população foi analisada em blocos separados de 2019–2021 e 2024–2026. A série CEMPRE foi restrita ao bloco comparável de 2022–2024. Não conectamos automaticamente períodos com diferenças metodológicas.

O PIB de 2018–2023 é nominal; crescimento monetário não equivale a crescimento real. A composição setorial disponível é histórica e não foi preenchida nos anos sem valores.

A auditoria de edições oficiais demonstrou mudança no valor de 2019 de Sales Oliveira: aproximadamente R$ 3,669 bilhões na edição de 2019 e R$ 364,293 milhões nas edições posteriores examinadas. Guaíra e Nuporanga também apresentaram diferenças entre edições para 2019.

A divergência entre edições foi evidenciada, mas a causa específica de sua magnitude não foi localizada. Portanto, a queda calculada de Sales Oliveira não pode ser apresentada como colapso econômico confirmado. Os registros afetados mantêm bloqueio interpretativo. PIB e composição setorial foram excluídos do bloco multivariado para todas as cidades.

## 7. Evidência geográfica

Entre a fábrica e os quatro CDs, Ribeirão Preto é a origem mais próxima das 12 cidades pela distância entre centroides calculada por Haversine. A conclusão confirma matematicamente o conhecimento prévio do negócio.

Na validação local, as distâncias ao CD vão de 42,318 km para Sales Oliveira a 179,255 km para Frutal. Orlândia–Sales Oliveira e Planura–Colômbia apresentam proximidade entre centroides de 15,781 km e 22,087 km, respectivamente, oferecendo hipóteses de atendimento conjunto.

A ordem de proximidade não é uma rota recomendada. Faltam endereços operacionais, trajetos rodoviários, tempo, frete, pedido mínimo e condições de atendimento. A etapa registra 17 pendências de referências logísticas: cinco instalações e 12 destinos.

## 8. Preços e estudos documentais

A etapa 17 descreveu 67 preços em 13 grupos de apresentação, 312 células de consumo histórico em 87 recortes e 312 evidências JPEG. Os quatro JSON enviados pelo usuário tiveram hashes e contagens conferidos com a conclusão da execução. Mínimos e máximos dos recortes foram recalculados a partir dos percentuais listados, e os 312 IDs permaneceram únicos.

| Apresentação | Mediana do preço do pacote |
|---|---:|
| Minis crus, 1 kg | R$ 22,57 |
| Minis fritos, 1 kg | R$ 23,83 |
| Empanados crus, peso não informado no campo estruturado | R$ 67,49 |
| Empanados fritos, peso não informado no campo estruturado | R$ 70,18 |

Os resumos não são custos fabris, ticket nem preços globais. A conferência independente das medianas contra os preços individuais foi feita na validação local; o usuário enviou o resumo, não a tabela individual de preços da etapa 17.

Na publicação de 2002–2003, a prevalência semanal de consumo fora do domicílio de salgados fritos e assados foi 9,2% no Brasil e 10,6% no Sudeste. No recorte de renda per capita, variou de 5,8% até meio salário mínimo para 11,7% a partir de cinco salários mínimos. O padrão gera uma hipótese histórica sobre renda e consumo; não estima demanda atual dos municípios.

Os estudos universitários de Goiânia em 2011 permanecem separados. Coeficientes de renda publicados não medem elasticidade-preço. Nenhum modelo foi reestimado com microdados.

As seis pendências documentais são: uma de vigência de preços, duas divergências PDF–JPEG e três inconsistências entre frequência e percentual universitário. JPEG não duplica amostra. As divergências percentuais são −0,6 p.p. para salgados no estrato rural e +0,1 p.p. para refrigerantes na faixa de 30–39 anos, tomando imagem menos PDF.

## 9. Hipóteses para aprofundamento comercial

| Hipótese ou pergunta | Evidência disponível | Próxima informação necessária |
|---|---|---|
| Cidades maiores oferecem maior universo de prospecção | População e contagem CNAE fortemente associadas | Lista e qualificação dos estabelecimentos, canais, produtos e fornecedores |
| Renda e presença comercial ajudam a diferenciar perfis de oferta | Associações positivas com taxas comerciais | Compras reais, preço aceito, mix e perfil dos compradores |
| Proximidade pode facilitar atendimento e frequência de visitas | Ribeirão Preto é mais próximo por centroides | Endereços, rotas, custos de venda e entrega, pedidos mínimos |
| Cidades próximas podem integrar uma agenda comercial | Pares geográficos próximos | Sequência rodoviária, horários e capacidade de atendimento |
| Produtos e apresentações exigem propostas específicas | Catálogo com preços e características diferentes | Tabela vigente, disponibilidade e condições de negociação |

Ainda não podemos medir diretamente headroom, aderência produto–mercado, elasticidade-preço ou vendas previstas. Poucas unidades por habitante podem refletir oportunidade, menor demanda ou outro canal de consumo. Muitas unidades podem representar clientes potenciais, concorrentes ou ambas as situações. A classificação depende de qualificação comercial.

## 10. Situação de encerramento da EDA

| Bloco | Situação da conferência nesta colaboração |
|---|---|
| Estrutura, univariada e bivariada | Resultados revisados nas etapas anteriores |
| Temporal | Resultados e divergências entre edições revisados; causa de PIB permanece pendente |
| Geográfica | Conclusão e log do usuário revisados; tabela final de proximidade do usuário ainda não recebida |
| Multivariada | Conclusão e log do usuário revisados; números analisados na validação local; tabelas finais do usuário ainda não recebidas |
| Documental | Conclusão, log e quatro tabelas JSON do usuário revisados; restrições documentais preservadas |
| Síntese | Consolidada neste documento; sem ranking comercial |

Para completar a conferência independente dos resultados do usuário: `proximidade_por_cidade.json` da etapa 15 e `painel_integrado.json`, `associacoes_dimensoes.json`, `associacoes_parciais.json` e `sensibilidade_parcial.json` da etapa 16.

As pendências científicas podem permanecer formalmente abertas com restrição de uso. A aprovação técnica não certifica a representatividade das fontes nem substitui a conferência dos resultados. Esta síntese não atribui aprovação definitiva a arquivos ainda não recebidos.

## 11. Documentação e continuidade

Referências metodológicas locais: `01_ESTRUTURA_COBERTURA.md`, `02_ANALISE_UNIVARIADA.md`, `03_ANALISE_BIVARIADA.md`, `04_ANALISE_TEMPORAL.md`, `CONFERENCIA_PIB_SALES_OLIVEIRA.md`, `05_ANALISE_GEOGRAFICA.md`, `06_ANALISE_MULTIVARIADA.md` e `07_ANALISE_DOCUMENTAL.md`. As execuções permanecem em `quality` e as tabelas em `datalake/03_gold`, com seus respectivos run_ids.

Este arquivo é uma síntese editorial de resultados já calculados, não uma nova etapa numérica. Portanto, não foi criado um script ou flag de pipeline apenas para copiar o texto. As etapas analíticas 11–17 permanecem automatizadas. A geração automática de relatórios poderá ser incorporada quando seu conteúdo e critérios forem estabilizados.

O próximo trabalho é definir critérios explícitos para priorização comercial e os dados necessários para aplicá-los. A recomendação deve considerar tamanho do universo prospectável, perfil comercial, custo de venda e viabilidade de atendimento, com sensibilidade das decisões. A comparação com o projeto original e o script Python finalizador permanecem reservados ao encerramento do projeto atual.
