# Executar etapa 25

Extraia na raiz do projeto, preservando src e docs. No terminal da raiz:

```powershell
python src/etapa_25_divisao_circuitos.py
```

Alternativa isolada pelo orquestrador:

```powershell
python src/run_pipeline.py --dividir-circuitos
```

Pode comparar outros limites hipotéticos:

```powershell
python src/etapa_25_divisao_circuitos.py --limites-h 5 6 7
```

A etapa usa a última conclusao_24.json em quality/24_coleta_logistica. Exige os arquivos originais locais da coleta (inclusive osrm_matriz.json e registro_coleta.json na Bronze), cujos hashes são verificados.
Não precisa de login Azure, conexão SQL nem nova consulta à internet. Requer pyarrow já listado em requirements.txt.
Resultados: datalake/03_gold/<novo_run_id>/divisao_circuitos. Conclusão: quality/25_divisao_circuitos/<novo_run_id>/conclusao_25.json.
Status esperado: DIVISAO_PRELIMINAR_COM_PENDENCIAS. Um cenário INVIAVEL_NESTE_LIMITE é resultado analítico, não falha da execução.
Envie conclusao_25.json, resumo_cenarios.json e circuitos_divididos.json para conferência.
