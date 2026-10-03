# potencial-de-mercado-e-expansao-comercial — Gold e SQL

## Instalar e gerar Gold

Mesclar src e docs do pacote na raiz do projeto. Substituir run_pipeline.py e requirements.txt pelas versões entregues. Manter os demais scripts e dados locais existentes. Não executar novamente o DDL da etapa 18.

No terminal da raiz, com o ambiente virtual ativado:

```powershell
python -m pip install -r requirements.txt
python src/etapa_19_gold_dimensional.py
```

Usa a base EDA aprovada mais recente e as duas Silver vinculadas nela. Para fixar uma base:

```powershell
python src/etapa_19_gold_dimensional.py --base "datalake/03_gold/ID_DA_EXECUCAO/base_eda"
```

Esperado: GOLD_DIMENSIONAL_VERIFICADA_COM_LIMITACOES e 14 tabelas. Conferir `quality/19_gold_dimensional/<run_id>/conclusao_19_gold_dimensional.json` antes da carga.

## Driver e servidor

Verificar os drivers instalados:

```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
```

O padrão é ODBC Driver 18 for SQL Server. Se instalado somente o 17, passar `--driver "ODBC Driver 17 for SQL Server"`. A biblioteca pyodbc não instala o driver Microsoft. Download oficial, caso necessário: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

Servidor é o nome exato exibido na conexão do SSMS (ex.: nome do computador ou COMPUTADOR\SQLEXPRESS). Os comandos abaixo contêm placeholders que devem ser substituídos. Autenticação Windows usa a mesma conta do terminal. Não passar senha nem publicar credenciais.

## Carga isolada

```powershell
python src/etapa_20_carga_sql.py --servidor "SUA_INSTANCIA_SQL"
```

Seleciona a Gold dimensional aprovada mais recente. Para fixar a exportação:

```powershell
python src/etapa_20_carga_sql.py --servidor "SUA_INSTANCIA_SQL" --gold "datalake/03_gold/ID_DA_EXECUCAO/dimensional"
```

Se a instância local usa certificado próprio já reconhecido por você no SSMS, acrescentar `--confiar-certificado`; isso mantém criptografia e aceita esse certificado. Não é o padrão. Para uma instância remota, utilizar certificado confiável.

Esperado: CARGA_SQL_RECONCILIADA e 14 regras aprovadas. Enviar conclusão da etapa 19 e, após carregar, da etapa 20. Não precisa fotografar listas grandes de registros.

## Pipeline

As novas etapas estão incluídas no run_pipeline.py:

```powershell
python src/run_pipeline.py --gerar-gold-dimensional
python src/run_pipeline.py --gerar-gold-dimensional --carregar-sql --sql-servidor "SUA_INSTANCIA_SQL"
```

A pipeline completa também executa as etapas locais 01–05, como já fazia. Para gerar/carregar sem repetir extrações, usar os scripts isolados acima. A carga SQL não consulta novamente o IBGE. Sem a flag --carregar-sql, não conecta ao SQL Server.

## Conferência no SSMS

Após a carga, executar sql/03_conferir_carga_dimensional.sql. Consultar a execução aprovada, 14 regras e contagens das quatro fatos. As views analíticas e medidas DAX serão criadas depois da reconciliação.
