# potencial-de-mercado-e-expansao-comercial — Modelo dimensional v1.0

Data: 03/10/2026. Etapa 18: definição e criação da estrutura; carga ainda não implementada.

## Objetivo e entrada

Aprofundar a análise comercial no SQL Server e disponibilizar uma base dimensional para Power BI/DAX. O nome do banco é exatamente `potencial-de-mercado-e-expansao-comercial`.

Modelo conferido contra os campos dos JSON Silver locais de teste e os dicionários das etapas 08/09. Isso não substitui validar os arquivos da execução real do usuário na carga. Referências: Silver municipal, Silver documental e restrições da síntese EDA.

## Granularidade e relacionamentos

| Fato | Uma linha representa | Dimensões relacionadas |
|---|---|---|
| fato_indicador_municipal | Observação município + indicador/classificação + período + fonte, dentro de uma carga | Município, indicador, período, fonte |
| fato_distancia_municipio_origem | Distância destino + ponto de origem + tipo, dentro de uma carga | Município e ponto de distribuição |
| fato_preco_referencia | Registro publicado de preço, dentro de uma carga | Produto/apresentação, período e fonte |
| fato_estudo_publicado | Célula de consumo/perfil publicada no estudo, dentro de uma carga | Estrato do estudo, período e fonte |

São sete dimensões, quatro fatos e cinco tabelas de auditoria/qualidade: 16 tabelas. Os cinco pontos de distribuição são a fábrica de São Carlos e CDs em Ribeirão Preto, Campinas, Sorocaba e São Paulo. A dimensão município comporta os 17 municípios conhecidos. Não confundir centroide do município com endereço da operação.

## Chaves e histórico

As PK são inteiros técnicos; o código IBGE é texto de sete dígitos. Cada dimensão também tem chave natural única. Chaves hash de fonte, produto e estrato serão calculadas a partir de JSON canônico na carga; a receita exata ficará documentada junto do carregador, sem concatenar campos ambíguos.

Cada carga aponta os dois run_id Silver e os hashes dos manifestos. As fatos são snapshots: a mesma observação pode aparecer em cargas diferentes, mas não pode duplicar dentro da mesma carga. Não somar várias cargas no Power BI. Views da carga aprovada selecionarão uma única execução conjunta; ainda serão implementadas com o carregador. Último período deve ser selecionado por município/indicador, respeitando anos distintos.

O modelo inicial tem dimensões do tipo 1: atributos cadastrais são atualizados mediante conferência. O JSON original nas fatos preserva a observação e seu contexto histórico. Não alegar histórico completo de atributos dimensionais; uma necessidade futura desse histórico exige SCD tipo 2 antes de alterar cadastros.

Fonte é identificada pela resposta/documento e contexto de edição. SHA de conteúdo sozinho não equivale a edição; edição não informada permanece explicitamente ausente. Não inventar data de publicação a partir da data de coleta.

## Regras analíticas

- Indicadores municipais: usar decimal(28,10), preservar marcadores não numéricos como NULL e conservar valor/unidade original. Reconciliação verificará precisão e limites antes da carga. Não converter mil reais novamente.
- Percentuais: armazenar de 0 a 100; dividir por 100 na medida percentual DAX. Taxas não são aditivas; não somar percentuais, renda mediana, PIB per capita ou distâncias.
- PIB: flag própria de revisão e restrição comercial. Preservar números publicados; a seleção analítica seguirá a decisão documentada da EDA. Candidato EDA não libera automaticamente análise comercial.
- Preços: decimal(18,4), estado e apresentação preservados. Não derivar SKU de descrição agrupada, nem custo fabril ou preço global. Vigência desconhecida usa período NAO_INFORMADO; orçamento atual exige confirmação.
- Estudos: 312 observações de consumo e 310 de universitários na base conhecida, sem vínculo artificial com cidades-alvo. Estratos contêm região, curso, grupo e frequência quando publicados. Não agregar percentuais de denominadores diferentes.
- Imagens: tabela de evidência ligada à observação PDF. Nunca acrescentar as 312 transcrições como novos casos. Divergências e inconsistências permanecem pendentes.
- Coeficientes, ajustes e testes: 72 registros auxiliares (20 + 5 + 47), preservados com JSON original; p-valores com limites/notas não viram probabilidade zero. Não são medidas comerciais municipais.

As contagens de 1.524 indicadores, 60 distâncias e 67 preços são expectativas da base conhecida, não restrições fixas do banco. A carga confrontará as contagens reais da entrada validada.

## Dicionário físico

Os campos abaixo são a especificação inicial de cada tabela. A declaração SQL é a referência para tipos, nulabilidade, PK, FK, UNIQUE e CHECK. Colunas terminadas em `_id` relacionam as tabelas; `registro_origem_json` preserva todos os campos Silver, mesmo os não promovidos em colunas analíticas.

### audit.execucao_carga

```sql
execucao_id bigint IDENTITY(1,1) PRIMARY KEY,
    run_id varchar(80) NOT NULL UNIQUE,
    inicio_utc datetime2(6) NOT NULL DEFAULT SYSUTCDATETIME(),
    fim_utc datetime2(6) NULL,
    status varchar(40) NOT NULL,
    silver_municipal_run_id varchar(80) NOT NULL,
    silver_documental_run_id varchar(80) NOT NULL,
    manifesto_municipal_sha256 char(64) NOT NULL,
    manifesto_documental_sha256 char(64) NOT NULL,
    versao_modelo varchar(20) NOT NULL,
    detalhe nvarchar(max) NULL
```

### gold.dim_municipio

```sql
municipio_id int IDENTITY(1,1) PRIMARY KEY,
    codigo_ibge varchar(7) NOT NULL UNIQUE,
    municipio nvarchar(120) NOT NULL,
    uf char(2) NOT NULL,
    cidade_expansao bit NOT NULL,
    regiao_imediata nvarchar(150) NULL,
    regiao_intermediaria nvarchar(150) NULL,
    latitude_centroide decimal(10,7) NULL CHECK(latitude_centroide BETWEEN -90 AND 90),
    longitude_centroide decimal(10,7) NULL CHECK(longitude_centroide BETWEEN -180 AND 180),
    tipo_coordenada varchar(50) NOT NULL,
    fonte_url nvarchar(max) NULL,
    fonte_sha256 char(64) NULL,
    versao_malha nvarchar(150) NULL,
    CHECK(LEN(codigo_ibge)=7 AND codigo_ibge NOT LIKE '%[^0-9]%')
```

### gold.dim_periodo

```sql
periodo_id int IDENTITY(1,1) PRIMARY KEY,
    periodo_chave varchar(100) NOT NULL UNIQUE,
    rotulo_original nvarchar(100) NOT NULL,
    tipo_periodo varchar(30) NOT NULL CHECK(tipo_periodo IN ('ANUAL','INTERVALO_ANOS','NAO_INFORMADO')),
    ano_inicial smallint NULL,
    ano_final smallint NULL,
    CHECK((tipo_periodo='NAO_INFORMADO' AND ano_inicial IS NULL AND ano_final IS NULL)
       OR (tipo_periodo='ANUAL' AND ano_inicial IS NOT NULL AND ano_final=ano_inicial)
       OR (tipo_periodo='INTERVALO_ANOS' AND ano_inicial IS NOT NULL AND ano_final IS NOT NULL AND ano_final>=ano_inicial))
```

### gold.dim_indicador

```sql
indicador_id int IDENTITY(1,1) PRIMARY KEY,
    indicador_chave varchar(100) NOT NULL UNIQUE,
    nome_oficial nvarchar(500) NOT NULL,
    grupo nvarchar(100) NULL,
    tabela_origem varchar(50) NULL,
    variavel_origem varchar(50) NULL,
    classificacoes_json nvarchar(max) NULL,
    unidade nvarchar(100) NOT NULL,
    escala_percentual smallint NULL CHECK(escala_percentual=100),
    definicao nvarchar(max) NULL,
    limitacoes_uso_json nvarchar(max) NULL,
    url_metadados nvarchar(max) NULL
```

### gold.dim_fonte

```sql
fonte_id int IDENTITY(1,1) PRIMARY KEY,
    fonte_chave char(64) NOT NULL UNIQUE,
    fonte_sha256 char(64) NOT NULL,
    tipo varchar(30) NOT NULL,
    fonte_url nvarchar(max) NULL,
    arquivo_origem nvarchar(1000) NULL,
    edicao nvarchar(200) NULL,
    edicao_informada bit NOT NULL,
    coleta_utc datetime2(6) NULL,
    hash_fisico_verificado bit NOT NULL,
    observacao nvarchar(max) NULL
```

### gold.dim_ponto_distribuicao

```sql
ponto_id int IDENTITY(1,1) PRIMARY KEY,
    ponto_chave varchar(80) NOT NULL UNIQUE,
    nome nvarchar(150) NOT NULL,
    tipo varchar(20) NOT NULL CHECK(tipo IN ('FABRICA','CD')),
    municipio_id int NOT NULL REFERENCES gold.dim_municipio(municipio_id),
    endereco_confirmado nvarchar(500) NULL,
    latitude_endereco decimal(10,7) NULL CHECK(latitude_endereco BETWEEN -90 AND 90),
    longitude_endereco decimal(10,7) NULL CHECK(longitude_endereco BETWEEN -180 AND 180)
```

### gold.dim_produto

```sql
produto_id int IDENTITY(1,1) PRIMARY KEY,
    produto_chave char(64) NOT NULL UNIQUE,
    categoria nvarchar(200) NOT NULL,
    descricao_original nvarchar(1500) NOT NULL,
    estado nvarchar(100) NOT NULL,
    peso_pacote_kg decimal(18,6) NULL CHECK(peso_pacote_kg>0),
    quantidade_pacote int NULL CHECK(quantidade_pacote>0),
    quantidade_aproximada nvarchar(200) NULL,
    sku_confirmado nvarchar(100) NULL
```

### gold.dim_estrato_estudo

```sql
estrato_id int IDENTITY(1,1) PRIMARY KEY,
    estrato_chave char(64) NOT NULL UNIQUE,
    estudo varchar(50) NOT NULL,
    tabela_original nvarchar(100) NOT NULL,
    abrangencia nvarchar(300) NULL,
    regiao nvarchar(150) NULL,
    dimensao nvarchar(250) NULL,
    estrato nvarchar(300) NULL,
    grupo_alimento nvarchar(250) NULL,
    curso nvarchar(200) NULL,
    grupo nvarchar(250) NULL,
    frequencia nvarchar(250) NULL,
    indicador_publicado nvarchar(500) NULL
```

### gold.fato_indicador_municipal

```sql
observacao_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    municipio_id int NOT NULL REFERENCES gold.dim_municipio(municipio_id),
    indicador_id int NOT NULL REFERENCES gold.dim_indicador(indicador_id),
    periodo_id int NOT NULL REFERENCES gold.dim_periodo(periodo_id),
    fonte_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    valor decimal(28,10) NULL,
    valor_original nvarchar(200) NULL,
    unidade_original nvarchar(100) NULL,
    multiplicador decimal(18,6) NOT NULL,
    status_valor varchar(50) NOT NULL,
    status_atualidade varchar(50) NOT NULL,
    defasagem_anos int NULL,
    ultimo_valor_numerico bit NOT NULL,
    candidato_eda bit NOT NULL,
    conferencia_renda_pendente bit NOT NULL,
    revisao_pib_pendente bit NOT NULL,
    liberado_analise_comercial bit NOT NULL,
    motivo_restricao nvarchar(max) NULL,
    limitacoes_uso_json nvarchar(max) NULL,
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,municipio_id,indicador_id,periodo_id,fonte_id)
```

### gold.fato_distancia_municipio_origem

```sql
distancia_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    municipio_id int NOT NULL REFERENCES gold.dim_municipio(municipio_id),
    ponto_id int NOT NULL REFERENCES gold.dim_ponto_distribuicao(ponto_id),
    metodo nvarchar(200) NOT NULL,
    tipo_distancia varchar(30) NOT NULL CHECK(tipo_distancia IN ('GEODESICA_CENTROIDES','RODOVIARIA_ENDERECOS')),
    distancia_km decimal(18,6) NOT NULL CHECK(distancia_km>=0),
    tempo_minutos decimal(18,6) NULL CHECK(tempo_minutos>=0),
    fontes_sha256_json nvarchar(max) NOT NULL,
    uso_proposto nvarchar(max) NOT NULL,
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,municipio_id,ponto_id,tipo_distancia)
```

### gold.fato_preco_referencia

```sql
preco_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    produto_id int NOT NULL REFERENCES gold.dim_produto(produto_id),
    fonte_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    periodo_id int NOT NULL REFERENCES gold.dim_periodo(periodo_id),
    registro_id varchar(200) NOT NULL,
    pagina int NOT NULL CHECK(pagina>0),
    linha int NOT NULL CHECK(linha>0),
    preco_pacote_brl decimal(18,4) NOT NULL CHECK(preco_pacote_brl>=0),
    preco_unidade_brl decimal(18,4) NULL CHECK(preco_unidade_brl>=0),
    preco_pacote_original nvarchar(100) NULL,
    preco_unidade_original nvarchar(100) NULL,
    vigencia_original nvarchar(100) NOT NULL,
    vigencia_confirmada bit NOT NULL,
    liberado_orcamento_atual bit NOT NULL,
    validacao nvarchar(100) NOT NULL,
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,registro_id),
    CHECK(liberado_orcamento_atual=0 OR vigencia_confirmada=1)
```

### gold.fato_estudo_publicado

```sql
observacao_estudo_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    estrato_id int NOT NULL REFERENCES gold.dim_estrato_estudo(estrato_id),
    fonte_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    periodo_id int NOT NULL REFERENCES gold.dim_periodo(periodo_id),
    registro_id varchar(200) NOT NULL,
    tabela_silver varchar(80) NOT NULL CHECK(tabela_silver IN ('consumo_historico','universitarios_historico')),
    pagina int NOT NULL CHECK(pagina>0),
    percentual decimal(18,6) NULL CHECK(percentual BETWEEN 0 AND 100),
    percentual_original nvarchar(100) NULL,
    n_publicado int NULL CHECK(n_publicado>=0),
    denominador_publicado int NULL CHECK(denominador_publicado>=0),
    ic95_inferior decimal(18,6) NULL,
    ic95_superior decimal(18,6) NULL,
    p_valor_original nvarchar(100) NULL,
    pendencia_publicada bit NOT NULL,
    uso_previsao_vendas_atual bit NOT NULL CHECK(uso_previsao_vendas_atual=0),
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,registro_id)
```

### quality.evidencia_imagem

```sql
evidencia_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    observacao_estudo_id bigint NOT NULL REFERENCES gold.fato_estudo_publicado(observacao_estudo_id),
    fonte_imagem_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    registro_id varchar(200) NOT NULL,
    registro_pdf_id varchar(200) NOT NULL,
    incluir_como_nova_observacao bit NOT NULL CHECK(incluir_como_nova_observacao=0),
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,registro_id)
```

### quality.pendencia

```sql
pendencia_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    pendencia_chave char(64) NOT NULL,
    tipo nvarchar(150) NOT NULL,
    registro_id varchar(200) NULL,
    detalhe nvarchar(max) NOT NULL,
    resolvida bit NOT NULL DEFAULT 0,
    evidencia_resolucao nvarchar(max) NULL,
    UNIQUE(execucao_id,pendencia_chave)
```

### quality.registro_documental_auxiliar

```sql
registro_auxiliar_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    fonte_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    tabela_silver varchar(80) NOT NULL CHECK(tabela_silver IN ('coeficientes_publicados','ajustes_publicados','testes_publicados')),
    registro_id varchar(200) NOT NULL,
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,tabela_silver,registro_id)
```

### quality.reconciliacao_carga

```sql
reconciliacao_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    tabela_destino varchar(100) NOT NULL,
    regra varchar(100) NOT NULL,
    registros_esperados bigint NULL,
    registros_observados bigint NULL,
    aprovado bit NOT NULL,
    detalhe nvarchar(max) NULL,
    UNIQUE(execucao_id,tabela_destino,regra)
```

## Validação e próximos passos

DDL organizado por dependências, com PK/FK/UNIQUE/CHECK e transação com rollback. Não usa DROP, DELETE, TRUNCATE ou desativação de constraints. Reexecução em schemas com tabelas é bloqueada para evitar aceitar estruturas incompatíveis. Criação dos schemas vazios antecede a transação.

Verificação local: nomes/quantidade de tabelas, referências e chaves comparados à especificação; o DDL ainda precisa ser executado no SQL Server do usuário. Não houve carga ou teste em uma instância SQL Server neste ambiente.

Próxima entrega: materialização Gold dimensional a partir das Silver validadas, seleção explícita dos run_id, carga Python transacional, logs e reconciliação Parquet × SQL (linhas, chaves, nulos, decimais, flags e conteúdo). Python fica em src; SQL em sql; execução em docs/execucoes. Somente após aprovação da carga criaremos views comerciais e integração ao run_pipeline.py. Esta estrutura inicial não altera a pipeline existente.

Referência técnica: https://learn.microsoft.com/en-us/sql/t-sql/statements/create-table-transact-sql
