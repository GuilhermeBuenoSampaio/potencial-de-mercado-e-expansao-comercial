# Escopo da análise exploratória de dados (EDA)

**Projeto:** `potencial-de-mercado-e-expansao-comercial`  
**Data de aprovação do escopo:** 30/09/2026  
**Status:** sete blocos implementados; síntese consolidada em `08_SINTESE_EDA.md`, com limitações e conferências de resultados do usuário ainda explicitadas.  
**Destino no projeto:** `docs/11_eda/ESCOPO_EDA.md`

## 1. Objetivo e pergunta central

Investigar, resumir e compreender a estrutura, as distribuições, os padrões, as anomalias e as relações dos dados, produzindo um diagnóstico que apoie o aprofundamento da análise de expansão comercial.

> Como as 12 cidades se diferenciam em dimensão de mercado, condições socioeconômicas, estrutura comercial e localização, e quais dessas diferenças merecem aprofundamento para orientar a expansão do vendedor?

A perspectiva é comercial e de vendas. O custo de fabricação pertence ao contexto do proprietário da fábrica e não constitui o eixo desta análise. Cada produto/pacote possui seu próprio preço, quantidade e características.

A EDA produzirá evidências descritivas e hipóteses para investigação. A recomendação de expansão será construída posteriormente, incorporando as informações comerciais e logísticas necessárias.

## 2. Abrangência territorial

As cidades de expansão são Franca (SP), Cristais Paulista (SP), Frutal (MG), Morro Agudo (SP), Sales Oliveira (SP), Orlândia (SP), Nuporanga (SP), Ipuã (SP), Guaíra (SP), Barretos (SP), Planura (MG) e Colômbia (SP).

A fábrica fica em São Carlos (SP). Os centros de distribuição ficam em Ribeirão Preto (SP), Campinas (SP), Sorocaba (SP) e São Paulo (SP).

A hipótese de que Ribeirão Preto seja a melhor origem será examinada. A proximidade entre centroides municipais não determina a melhor rota operacional.

## 3. Bases de entrada e rastreabilidade

Usaremos as Silver municipal e documental validadas e as bases preparadas na etapa 10:

| Base | Uso previsto |
|---|---|
| `indicadores_ultimo_disponivel_eda` | Perfil municipal com último valor numérico disponível e período explícito |
| `painel_periodo_comum` | Comparações entre cidades no mesmo ano por indicador/classificação |
| `controle_periodos` | Cobertura numérica, ausências e ano selecionado |
| `precos_referencia_eda` | Exploração dos preços por produto/pacote, preservando vigência pendente |
| Silver municipal: séries, municípios, crescimento e distâncias | Análises temporais e geográficas, definições e referências |
| Silver documental: estudos, evidências, fontes e pendências | Contexto histórico de consumo, exploração documental e conferência |

Cada execução deverá registrar run_id, data e hora, versões das entradas, hashes, parâmetros, resultados e limitações. Os scripts Python permanecerão em `src`; a automação será incorporada progressivamente a `src/run_pipeline.py`. Os resultados de execuções anteriores não serão sobrescritos.

A data de coleta não altera o período de referência: um dado do Censo de 2022 continua sendo de 2022 quando consultado em 2026.

## 4. Premissas e critérios analíticos

- Ausência, zero e marcadores oficiais são condições diferentes. Não converteremos ausência ou sigilo em zero.
- Investigaremos os motivos das ausências antes de discutir exclusão ou imputação. Os dados disponíveis não permitem presumir que o mecanismo seja MCAR, MAR ou MNAR; padrões observados, isoladamente, não identificam esse mecanismo.
- Média e desvio padrão são medidas válidas sem exigir simetria, mas podem representar mal uma cidade típica em distribuições assimétricas. Serão acompanhados por mediana, quartis e IQR.
- Valores extremos serão investigados; não serão excluídos apenas por ultrapassar um limite estatístico.
- Comparações respeitarão unidade, definição, população de referência, classificação, período e metodologia.
- O painel de período comum não retrocederá o ano de uma cidade para preencher um valor ausente. Valores antigos continuarão disponíveis na série e na base de últimos valores.
- Associação não será apresentada como causalidade. Serão examinadas diferenças entre grupos e efeitos da agregação, quando a quantidade de observações permitir.
- O universo principal contém apenas 12 cidades selecionadas para o projeto. Resultados não serão generalizados automaticamente a outros municípios; estimativas e associações podem ser sensíveis a uma única cidade.
- Não serão criados dados artificiais ou preenchimentos automáticos para completar análises.
- Os seis registros de pendências documentais continuarão explícitos até sua resolução. A elegibilidade de um indicador para EDA não encerra pendências de renda ou garante comparabilidade metodológica.

## 5. Roteiro de investigação

### 5.1. Estrutura, sanidade e qualidade

**Investigações:**

- Volume de tabelas, registros e colunas; tipos e consistência dos schemas.
- Granularidade, chaves, cardinalidade e relações entre tabelas.
- Indicadores, categorias, unidades e definições oficiais.
- Períodos de referência, defasagem e cobertura por cidade.
- Ausências, marcadores, duplicatas, limites lógicos e pendências.
- Compatibilidade temporal e metodológica das comparações.

**Perguntas:** quais indicadores cobrem todas as cidades no mesmo período? Onde ausências ou defasagem limitam a comparação? Quais dados representam atualização recente e quais descrevem um perfil estrutural histórico?

**Entregas:** perfil das tabelas, matriz de cobertura, quadro de períodos e registro das restrições de uso.

### 5.2. Análise univariada

Explorar população, renda domiciliar per capita média e mediana, PIB total e por habitante, empregos, salários, unidades locais, estabelecimentos de alimentação, varejo alimentar, fabricação de alimentos, densidade demográfica e urbanização.

**Métodos:**

- Quantidade de valores válidos e ausentes.
- Mínimo, máximo, amplitude, média, mediana, quartis, IQR, variância e desvio padrão.
- Assimetria e curtose como complementos, com cautela diante de 12 municípios e registro das convenções utilizadas.
- Frequências absolutas/relativas e cardinalidade para variáveis categóricas.
- Moda apenas quando repetição e significado da variável tornarem a medida útil.
- Sinalização de extremos pelos limites Q1 − 1,5 × IQR e Q3 + 1,5 × IQR, seguida de investigação.

**Visualizações:** barras ordenadas, pontos identificados por cidade e boxplots acompanhados dos valores individuais. A escolha considerará o pequeno número de municípios.

**Entregas:** estatísticas por indicador e interpretação das diferenças de escala e distribuição, sem transformar a ordenação de uma variável em ranking definitivo de expansão.

### 5.3. Análise bivariada

| Relação | Pergunta exploratória |
|---|---|
| População × estabelecimentos de alimentação | Cidades maiores também possuem mais possíveis canais de venda? |
| Renda domiciliar × estrutura de alimentação | Como a estrutura comercial varia com o perfil de renda? |
| Urbanização × estabelecimentos | A concentração urbana acompanha a presença desses canais? |
| População × PIB | O tamanho demográfico acompanha o tamanho econômico? |
| PIB por habitante × renda domiciliar | Os perfis são semelhantes ou apresentam diferenças relevantes? |
| Dimensão de mercado × distância | Quais cidades combinam maior dimensão e maior proximidade geográfica? |

**Métodos:** gráficos de dispersão antes dos coeficientes; Spearman para associações monotônicas; Pearson quando a forma linear e a influência dos extremos justificarem seu uso. Kendall poderá ser considerado se houver necessidade específica de avaliar ordenações ou empates.

Cada relação deverá informar número de pares válidos, anos, unidades, dados excluídos por ausência e limitações. Não imputaremos valores para completar a matriz de correlação. Relações selecionadas deverão possuir fundamento comercial; correlações exploratórias não constituirão evidência causal ou confirmação de hipóteses.

Poderemos calcular estabelecimentos por 10 mil habitantes quando numerador e denominador corresponderem ao mesmo período. Fórmula: `(estabelecimentos / população) × 10.000`. A origem dos componentes e o denominador serão registrados.

Comparações categórica × numérica e tabelas de contingência serão usadas quando forem interpretáveis. Grupos com poucas cidades serão tratados descritivamente; testes como qui-quadrado não serão aplicados automaticamente a contagens pequenas ou a combinações sem sentido analítico.

Baixa quantidade relativa de estabelecimentos pode indicar menor oferta, menor demanda ou diferenças cadastrais. Não será denominada oportunidade de mercado sem investigação adicional.

### 5.4. Análise temporal

**Investigações:** evolução populacional, evolução do PIB, variações absolutas/percentuais e mudanças na estrutura econômica e comercial quando houver séries adequadas.

**Métodos:** séries cronológicas, crescimento acumulado e taxa anualizada claramente separados. Para valores positivos e intervalo de n anos, a taxa anualizada será `[(valor final / valor inicial)^(1/n) − 1] × 100`; o intervalo exato deverá ser informado.

PIB em valores correntes será interpretado como nominal. Crescimento real exigirá uma estratégia de deflação previamente definida e documentada. Quebras metodológicas, incluindo as do CEMPRE, serão sinalizadas antes da comparação; não concatenaremos séries incompatíveis.

**Entregas:** gráficos temporais, cálculos rastreáveis e notas sobre comparabilidade e limitações.

### 5.5. Análise geográfica

**Investigações:** distribuição territorial das cidades; distância geodésica até a fábrica e cada CD; origem mais próxima por essa medida; combinação entre dimensão de mercado e proximidade; possíveis conjuntos de cidades para futura avaliação de atendimento.

**Visualizações:** mapas com identificação dos centroides e painéis de distâncias por cidade e origem.

**Limite de interpretação:** distâncias entre centroides não representam trajetos rodoviários, fretes, tempo de viagem ou endereços de entrega. Uma recomendação operacional dependerá dos endereços efetivos, rotas, disponibilidade de produtos e condições de atendimento.

**Entregas:** diagnóstico geográfico preliminar e requisitos para aprofundamento logístico.

### 5.6. Análise multivariada

Construir um painel integrado de população, renda domiciliar, estrutura comercial, urbanização e proximidade geográfica. Identificar semelhanças de perfil e destaques em diferentes dimensões.

Padronizações e transformações poderão apoiar a visualização, com registro do método e preservação dos valores originais. PCA e clustering ficam como possibilidades posteriores, condicionadas a uma pergunta útil, seleção coerente de variáveis e avaliação de estabilidade com apenas 12 cidades.

**Entregas:** comparação integrada e hipóteses sobre perfis municipais. Pesos e índice único de potencial não serão definidos nesta EDA.

### 5.7. Exploração documental: PDFs, JPEGs e preços

| Fonte | Investigação e cuidado |
|---|---|
| Preços | Comparação por categoria, produto, estado e pacote; preço unitário somente quando a quantidade for conhecida com precisão |
| Estudos de consumo | Padrões publicados por região, perfil e categoria alimentar, mantendo período, universo e população estudada |
| JPEGs | Evidência complementar, conferência dos vínculos e divergências com os PDFs; sem duplicação da amostra |
| Pendências | Natureza, evidências, impacto no uso analítico e situação de resolução |

Não calcularemos um preço unitário exato a partir de uma quantidade aproximada. Os preços históricos exigem confirmação antes de orçamento atual.

Estudos poderão gerar hipóteses, mas sua prevalência histórica de consumo não será convertida diretamente em unidades vendidas nas cidades atuais. Coeficientes de renda não serão interpretados como elasticidade de preço. Resultados de amostras universitárias ou nacionais manterão suas próprias limitações de representatividade.

## 6. Síntese orientada ao negócio

Ao finalizar, consolidaremos:

1. Perfil comparável das 12 cidades, com períodos e fontes explícitos.
2. Principais padrões, diferenças e valores extremos investigados.
3. Relações exploratórias com interpretação comercial e limites de evidência.
4. Cobertura, ausências, defasagens e pendências que afetam a decisão.
5. Hipóteses que merecem aprofundamento e quais dados serão necessários para avaliá-las.

Cada achado deverá informar a evidência, sua interpretação, a limitação e a próxima ação analítica ou de coleta.

Headroom, aderência produto–mercado, sensibilidade a preço e previsão de vendas dependerão de informações adicionais sobre consumo, clientes, concorrência e operação comercial. Contagens CNAE representam indícios de estrutura comercial, não clientes ou concorrentes confirmados. PIB por habitante não representa renda mensal; empregos no local de trabalho não equivalem à taxa de emprego dos moradores.

## 7. Entregas e organização

- Scripts reproduzíveis em `src`, com integração incremental à pipeline.
- Tabelas analíticas e resultados das execuções em `datalake/03_gold/<run_id>/`, com formato e subpasta documentados na implementação.
- Controles, conclusões e logs em `quality/<etapa>/<run_id>/`.
- Documentação metodológica e técnica da EDA em `docs/11_eda/`.
- Resumo executivo com perguntas, evidências, implicações e limitações.
- Gráficos com título, unidade, período e referência da base utilizada.

XLSX poderá ser disponibilizado para leitura humana quando solicitado; cópias destinadas somente à consulta não serão incorporadas ao projeto sem definição explícita. Os formatos técnicos e os registros de rastreabilidade continuarão preservados.

## 8. Critérios de conclusão

A EDA estará concluída quando:

- Os blocos previstos forem executados ou tiverem uma justificativa documentada para sua não aplicação.
- As contagens, chaves e cálculos utilizados forem reconciliados com as entradas da execução.
- Comparações explicitem período, unidade, definição, categorias e quantidade de valores válidos.
- Ausências e pendências relevantes estiverem identificadas, sem correção ou imputação silenciosa.
- Os achados puderem ser reproduzidos pelos scripts e relacionados às suas fontes.
- A documentação técnica e o resumo executivo estiverem consistentes com os resultados.
- As hipóteses para aprofundamento comercial estiverem relacionadas às evidências e às necessidades de dados.

## 9. Continuidade após a EDA

Aprofundar a análise comercial a partir dos achados, incorporar os dados operacionais necessários e construir a recomendação de expansão com critérios explícitos. A comparação com a planilha e os resultados da análise original acontecerá somente no encerramento do projeto atual. O script Python finalizador também será desenvolvido no encerramento.
