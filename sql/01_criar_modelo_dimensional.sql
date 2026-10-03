-- potencial-de-mercado-e-expansao-comercial | modelo dimensional v1.0
-- Executar no SSMS. Banco deve existir. Nao cria nem apaga banco/dados.
USE [potencial-de-mercado-e-expansao-comercial];
GO
SET NOCOUNT ON;
SET XACT_ABORT ON;
IF DB_NAME() <> N'potencial-de-mercado-e-expansao-comercial'
    THROW 51000, 'Banco incorreto. Execucao bloqueada.', 1;
GO
IF SCHEMA_ID(N'gold') IS NULL EXEC(N'CREATE SCHEMA gold AUTHORIZATION dbo');
GO
IF SCHEMA_ID(N'audit') IS NULL EXEC(N'CREATE SCHEMA audit AUTHORIZATION dbo');
GO
IF SCHEMA_ID(N'quality') IS NULL EXEC(N'CREATE SCHEMA quality AUTHORIZATION dbo');
GO
BEGIN TRANSACTION;
BEGIN TRY
IF DB_NAME() <> N'potencial-de-mercado-e-expansao-comercial'
    THROW 51000, 'Banco incorreto. Execucao bloqueada.', 1;
-- Repetir sobre modelo existente bloqueia; nao aceita esquema desconhecido silenciosamente.
IF EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id
           WHERE s.name IN ('gold','audit','quality'))
    THROW 51001, 'Ja existem tabelas nos schemas do modelo. Conferir estrutura; nao repetir criacao.', 1;
CREATE TABLE audit.execucao_carga (
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
);

CREATE TABLE gold.dim_municipio (
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
);

CREATE TABLE gold.dim_periodo (
    periodo_id int IDENTITY(1,1) PRIMARY KEY,
    periodo_chave varchar(100) NOT NULL UNIQUE,
    rotulo_original nvarchar(100) NOT NULL,
    tipo_periodo varchar(30) NOT NULL CHECK(tipo_periodo IN ('ANUAL','INTERVALO_ANOS','NAO_INFORMADO')),
    ano_inicial smallint NULL,
    ano_final smallint NULL,
    CHECK((tipo_periodo='NAO_INFORMADO' AND ano_inicial IS NULL AND ano_final IS NULL)
       OR (tipo_periodo='ANUAL' AND ano_inicial IS NOT NULL AND ano_final=ano_inicial)
       OR (tipo_periodo='INTERVALO_ANOS' AND ano_inicial IS NOT NULL AND ano_final IS NOT NULL AND ano_final>=ano_inicial))
);

CREATE TABLE gold.dim_indicador (
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
);

CREATE TABLE gold.dim_fonte (
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
);

CREATE TABLE gold.dim_ponto_distribuicao (
    ponto_id int IDENTITY(1,1) PRIMARY KEY,
    ponto_chave varchar(80) NOT NULL UNIQUE,
    nome nvarchar(150) NOT NULL,
    tipo varchar(20) NOT NULL CHECK(tipo IN ('FABRICA','CD')),
    municipio_id int NOT NULL REFERENCES gold.dim_municipio(municipio_id),
    endereco_confirmado nvarchar(500) NULL,
    latitude_endereco decimal(10,7) NULL CHECK(latitude_endereco BETWEEN -90 AND 90),
    longitude_endereco decimal(10,7) NULL CHECK(longitude_endereco BETWEEN -180 AND 180)
);

CREATE TABLE gold.dim_produto (
    produto_id int IDENTITY(1,1) PRIMARY KEY,
    produto_chave char(64) NOT NULL UNIQUE,
    categoria nvarchar(200) NOT NULL,
    descricao_original nvarchar(1500) NOT NULL,
    estado nvarchar(100) NOT NULL,
    peso_pacote_kg decimal(18,6) NULL CHECK(peso_pacote_kg>0),
    quantidade_pacote int NULL CHECK(quantidade_pacote>0),
    quantidade_aproximada nvarchar(200) NULL,
    sku_confirmado nvarchar(100) NULL
);

CREATE TABLE gold.dim_estrato_estudo (
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
);

CREATE TABLE gold.fato_indicador_municipal (
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
);

CREATE TABLE gold.fato_distancia_municipio_origem (
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
);

CREATE TABLE gold.fato_preco_referencia (
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
);

CREATE TABLE gold.fato_estudo_publicado (
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
);

CREATE TABLE quality.evidencia_imagem (
    evidencia_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    observacao_estudo_id bigint NOT NULL REFERENCES gold.fato_estudo_publicado(observacao_estudo_id),
    fonte_imagem_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    registro_id varchar(200) NOT NULL,
    registro_pdf_id varchar(200) NOT NULL,
    incluir_como_nova_observacao bit NOT NULL CHECK(incluir_como_nova_observacao=0),
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,registro_id)
);

CREATE TABLE quality.pendencia (
    pendencia_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    pendencia_chave char(64) NOT NULL,
    tipo nvarchar(150) NOT NULL,
    registro_id varchar(200) NULL,
    detalhe nvarchar(max) NOT NULL,
    resolvida bit NOT NULL DEFAULT 0,
    evidencia_resolucao nvarchar(max) NULL,
    UNIQUE(execucao_id,pendencia_chave)
);

CREATE TABLE quality.registro_documental_auxiliar (
    registro_auxiliar_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    fonte_id int NOT NULL REFERENCES gold.dim_fonte(fonte_id),
    tabela_silver varchar(80) NOT NULL CHECK(tabela_silver IN ('coeficientes_publicados','ajustes_publicados','testes_publicados')),
    registro_id varchar(200) NOT NULL,
    registro_origem_json nvarchar(max) NOT NULL,
    UNIQUE(execucao_id,tabela_silver,registro_id)
);

CREATE TABLE quality.reconciliacao_carga (
    reconciliacao_id bigint IDENTITY(1,1) PRIMARY KEY,
    execucao_id bigint NOT NULL REFERENCES audit.execucao_carga(execucao_id),
    tabela_destino varchar(100) NOT NULL,
    regra varchar(100) NOT NULL,
    registros_esperados bigint NULL,
    registros_observados bigint NULL,
    aprovado bit NOT NULL,
    detalhe nvarchar(max) NULL,
    UNIQUE(execucao_id,tabela_destino,regra)
);

COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO
