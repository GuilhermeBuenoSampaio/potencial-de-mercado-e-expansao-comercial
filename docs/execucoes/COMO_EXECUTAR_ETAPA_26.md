# Executar etapa 26

Extraia o pacote na raiz do projeto. No terminal:

```powershell
python src/etapa_26_jornada_atendimento.py
```

Alternativa isolada, sem repetir inventário ou carga SQL:

```powershell
python src/run_pipeline.py --jornada-atendimento
```

Hipóteses editáveis: docs/26_jornada_atendimento/PARAMETROS_JORNADA.json.
A etapa lê a última conclusão da etapa 24 e sua matriz Bronze. Não exige nova coleta ou login Azure. Requer pyarrow já previsto.
Saída: datalake/03_gold/<run_id>/jornada_atendimento. Conclusão: quality/26_jornada_atendimento/<run_id>/conclusao_26.json.
Status esperado: SIMULACAO_JORNADA_COM_PENDENCIAS. INVIAVEL_NESTE_LIMITE em um cenário é resultado analítico, não erro de execução.
Envie conclusao_26.json, resumo_cenarios.json e viagens_isoladas.json.
