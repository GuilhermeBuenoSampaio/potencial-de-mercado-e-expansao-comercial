-- Executado automaticamente pela etapa 30, dentro de transacao.

IF OBJECT_ID('gold.sim_execucao_comercial','U') IS NULL
CREATE TABLE gold.sim_execucao_comercial (
 run_29 varchar(80) NOT NULL PRIMARY KEY, run_28 varchar(80) NOT NULL,
 sql_execucao_id bigint NOT NULL, hash_conclusao_29 char(64) NOT NULL,
 carregado_utc datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
 status varchar(60) NOT NULL CHECK(status='REFERENCIAS_COMERCIAIS_COM_LIMITACOES'));
IF OBJECT_ID('gold.dim_circuito_sugerido','U') IS NULL
CREATE TABLE gold.dim_circuito_sugerido (
 run_29 varchar(80) NOT NULL, circuito_id varchar(100) NOT NULL,
 sequencia_sugerida nvarchar(1000) NOT NULL, km_sugeridos decimal(20,8) NOT NULL,
 varejo_especializado_2024 decimal(20,8) NOT NULL,
 participacao_varejo_percentual decimal(20,8) NOT NULL,
 receita_referencia_brl decimal(20,8) NULL,
 PRIMARY KEY(run_29,circuito_id),
 FOREIGN KEY(run_29) REFERENCES gold.sim_execucao_comercial(run_29));
IF OBJECT_ID('gold.ponte_circuito_municipio','U') IS NULL
CREATE TABLE gold.ponte_circuito_municipio (
 run_29 varchar(80) NOT NULL,circuito_id varchar(100) NOT NULL,
 codigo_ibge varchar(7) NOT NULL,municipio nvarchar(150) NOT NULL,
 populacao_2024 decimal(20,8) NOT NULL,renda_mediana_2022 decimal(20,8) NOT NULL,
 varejo_alimentar_2024 decimal(20,8) NOT NULL,
 PRIMARY KEY(run_29,codigo_ibge),
 FOREIGN KEY(run_29,circuito_id) REFERENCES gold.dim_circuito_sugerido(run_29,circuito_id));
IF OBJECT_ID('gold.dim_cenario_comercial','U') IS NULL
CREATE TABLE gold.dim_cenario_comercial (
 run_29 varchar(80) NOT NULL,cenario_id int NOT NULL,
 consumo_km_l decimal(20,8) NOT NULL,desgaste_brl_km decimal(20,8) NOT NULL,
 margem_contribuicao decimal(20,8) NOT NULL,
 PRIMARY KEY(run_29,cenario_id), UNIQUE(run_29,consumo_km_l,desgaste_brl_km,margem_contribuicao),
 FOREIGN KEY(run_29) REFERENCES gold.sim_execucao_comercial(run_29),
 CHECK(consumo_km_l>0 AND desgaste_brl_km>=0 AND margem_contribuicao>0 AND margem_contribuicao<=1));
IF OBJECT_ID('gold.fato_custo_viagem_simulado','U') IS NULL
CREATE TABLE gold.fato_custo_viagem_simulado (
 run_29 varchar(80) NOT NULL,circuito_id varchar(100) NOT NULL,cenario_id int NOT NULL,
 gasolina_brl decimal(20,8) NOT NULL,desgaste_brl decimal(20,8) NOT NULL,
 pedagio_estimado_osm_brl decimal(20,8) NULL,custo_estimado_brl decimal(20,8) NULL,
 receita_equilibrio_estimada_brl decimal(20,8) NULL,
 natureza varchar(80) NOT NULL CHECK(natureza='REFERENCIA_COMERCIAL_SIMULADA'),
 PRIMARY KEY(run_29,circuito_id,cenario_id),
 FOREIGN KEY(run_29,circuito_id) REFERENCES gold.dim_circuito_sugerido(run_29,circuito_id),
 FOREIGN KEY(run_29,cenario_id) REFERENCES gold.dim_cenario_comercial(run_29,cenario_id));
