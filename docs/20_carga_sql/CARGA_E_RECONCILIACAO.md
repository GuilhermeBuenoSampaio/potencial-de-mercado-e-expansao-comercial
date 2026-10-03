# potencial-de-mercado-e-expansao-comercial — Etapa 20

Data: 03/10/2026. Carga SQL Server do contrato v1.0 aprovado na etapa 18.

## Controles

1. Conferir Gold com seu manifesto e conclusão, contrato, hashes, número de linhas e conteúdo Parquet × JSON.
2. Conectar com autenticação Windows à instância fornecida, criptografia habilitada e banco com o nome exato do projeto.
3. Comparar as 180 colunas do contrato com tipos, tamanhos, precisão, escala, nulabilidade e identidade no banco. Conferir as 24 FKs, seus campos e seu estado habilitado/confiável. O banco foi criado com PK/UNIQUE/CHECK na etapa 18; o carregador não recria nem migra o DDL.
4. Obter trava de aplicação para serializar os carregadores deste projeto.
5. Inserir auditoria, reutilizar dimensões idênticas por chave natural, inserir novas dimensões e fatos, remapeando todas as identidades e FKs.
6. Relê-las no SQL e comparar o conteúdo integral com o Parquet normalizado: PK/FK remapeadas, todos os campos, valores, nulos, flags e JSON original.
7. Registrar 14 regras aprovadas em quality.reconciliacao_carga, marcar audit.execucao_carga como APROVADA e confirmar uma única transação.

Uma falha antes do commit solicita rollback de dados, dimensões novas, auditoria e reconciliação. A evidência da falha fica no log e JSON locais, pois a auditoria SQL da tentativa foi revertida. Não afirmar que uma tentativa reprovada foi registrada permanentemente no banco.

Se o mesmo run_id Gold já estiver aprovado, o carregador confere seu hash e relê/reconcilia os registros existentes. Não cria outra carga nem duplica fatos. Uma Gold nova pode criar novo snapshot; filtros/views devem selecionar uma única carga aprovada antes da análise. Não somar snapshots.

## Dimensões e mudanças

Atributos idênticos reutilizam a dimensão. Se uma chave natural existente tiver atributos diferentes, a carga bloqueia antes do commit. Este carregador não faz atualização tipo 1 silenciosa: mudanças cadastrais exigem revisão e decisão explícita sobre atualização ou SCD tipo 2. Isso torna concreta a restrição de conferência prevista na etapa 18.

Reconciliar uma dimensão significa comparar o subconjunto referenciado por esta Gold, não exigir que o banco inteiro tenha apenas os municípios/fontes do snapshot atual. Fatos e tabelas de qualidade são conferidos pela execucao_id da carga.

## Saídas

`quality/20_carga_sql/<run_id>/conclusao_20_carga_sql.json` e `execucao.log`. Status esperado CARGA_SQL_RECONCILIADA. A conclusão registra Gold, hash, execucao_id_sql, 14 regras e se houve reuso sem nova carga. Audit.execucao_carga mantém mapas das identidades locais e SQL para repetir a conferência.

Os scripts não criam views comerciais ou medidas DAX nesta etapa. Não enviam automaticamente ao Azure ou GitHub. O sync Azure existente pode enviar a nova Gold e quality após a validação.

## Validação realizada

- Materialização real sobre a base local existente: 14 exportações JSON/Parquet reconciliadas e referências consistentes.
- Compilação dos scripts e opções de execução.
- Teste de integração do algoritmo de carga em SQLite com adaptador da interface de cursor: primeira carga e 14 reconciliações; repetição sem duplicação; novo snapshot com dimensões reutilizadas e fatos remapeados; rollback em conflito dimensional; alteração de preço SQL detectada.
- Decimal que exigiria arredondamento foi bloqueado.

O adaptador não exercita o catálogo, a autenticação, o driver ODBC ou a sintaxe de execução do SQL Server. Esses pontos precisam da execução na instância do usuário; nenhum teste local foi apresentado como carga real no SQL Server.

Referências técnicas:
https://github.com/mkleehammer/pyodbc
https://github.com/mkleehammer/pyodbc/wiki/Database-Transaction-Management
https://learn.microsoft.com/en-us/sql/database-engine/configure-windows/special-cases-for-encrypting-connections-sql-server
