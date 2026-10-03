# Executar etapa 24 — coleta logística

Extraia o pacote na raiz do projeto. Todos os scripts ficam em src.
Execute no terminal da raiz:

```powershell
python src/etapa_24_coleta_logistica.py
```

Alternativa pelo orquestrador em modo isolado:

```powershell
python src/run_pipeline.py --coletar-logistica
```

Não exige nova carga SQL ou login Azure. Exige internet, openpyxl e pyarrow já previstos em requirements.txt, além dos arquivos locais da etapa 22.
O script seleciona a última pasta prioridades_circuitos e verifica os hashes. Para escolher uma execução específica:

```powershell
python src/etapa_24_coleta_logistica.py --etapa22 "datalake/03_gold/20261003T200058Z_a942753c/prioridades_circuitos"
```

Status esperado: COLETA_CONCLUIDA_COM_ROTAS_PRELIMINARES; falha de fonte produz COLETA_PARCIAL_COM_PENDENCIAS.
Os parâmetros finais de distância permanecem nulos para evitar tratar centroides como endereços de entrega.
Envie conclusao_24.json e circuitos_rodoviarios_preliminares.json; se houver falha, a conclusão registra a fonte que precisa de correção.
Não repetir a etapa 23 ainda: pedágios, desgaste e margens continuam pendentes.
