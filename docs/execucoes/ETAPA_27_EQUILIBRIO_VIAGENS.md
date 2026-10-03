# Executar a etapa 27

Extrair o pacote na raiz de `potencial-de-mercado-e-expansao-comercial`, substituindo `src/run_pipeline.py`. Manter os scripts anteriores, inclusive 24, 25 e 26.

No terminal da raiz:

```powershell
python src/run_pipeline.py --equilibrio-viagens
```

Alternativa direta, com o mesmo resultado:

```powershell
python src/etapa_27_equilibrio_viagens.py
```

O script usa a última conclusão válida das etapas 24 e 26, exige que ambas estejam vinculadas e verifica os hashes das tabelas de entrada. Se a última execução estiver reprovada, interrompe para análise. Não executa novamente inventário ou coleta online.

Configuração: `docs/27_equilibrio_viagens/PARAMETROS_EQUILIBRIO.json`. Os valores de consumo, desgaste e margem são hipóteses explícitas para sensibilidade. Não precisam de alteração para a primeira execução. Pedágio vazio significa pendente.

Saídas: `datalake/03_gold/<run_id>/equilibrio_viagens/` com JSON, Parquet e relatório Markdown; conclusão em `quality/27_equilibrio_viagens/<run_id>/conclusao_27.json`.

Enviar `conclusao_27.json` e `sensibilidade_equilibrio.json` para conferir. Receita parcial sem pedágio não é valor mínimo final autorizado para venda.
