# Como executar a etapa 29

Extraia o pacote na raiz do projeto, adicionando o novo script em src e substituindo src/run_pipeline.py. Preserve os scripts anteriores, inclusive as etapas 27 e 28. Não exige nova coleta nem alteração no SQL.

No terminal PowerShell da raiz:

```powershell
python src/run_pipeline.py --priorizacao-comercial --sql-servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --sql-driver 'ODBC Driver 17 for SQL Server' --confiar-certificado
```

Alternativa direta:

```powershell
python src/etapa_29_priorizacao_comercial.py --servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --confiar-certificado
```

Dependências já usadas pelo projeto: pyodbc e pyarrow. A etapa precisa da última conclusão 28 válida e dos arquivos originais trajetos.json e sensibilidade_provisoria.json no caminho registrado pela execução. Não use os arquivos de teste entregues em outra máquina.

Resultado esperado: status REFERENCIAS_COMERCIAIS_COM_LIMITACOES, municipios 12, circuitos 5. Saídas em datalake/03_gold/<run_id>/priorizacao_comercial; conclusão em quality/29_priorizacao_comercial/<run_id>/conclusao_29.json.

Para conferência, envie conclusao_29.json e circuitos_comerciais.json. A validação local testou fórmulas, cobertura e rejeição de duplicatas; a conexão ao servidor Windows precisa ser executada no seu computador. Se a view tiver um nome de coluna diferente, o script interrompe e identifica o campo necessário; não substitui ausências por zero.
