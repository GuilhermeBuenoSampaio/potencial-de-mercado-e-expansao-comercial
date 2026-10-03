# Executar etapa 23

Extraia o pacote na raiz de potencial-de-mercado-e-expansao-comercial, preservando as pastas src e docs.
No terminal da raiz, execute:

```powershell
python src/etapa_23_custos_carga_maxima.py
```

Alternativa pelo orquestrador, em modo isolado (não repete inventário ou carga SQL):

```powershell
python src/run_pipeline.py --custos-carga-maxima
```

A etapa 22 deve ter gerado circuitos.json em datalake/03_gold/<run_id>/prioridades_circuitos.
Os parâmetros ficam em docs/23_custos_carga_maxima/PARAMETROS_CARGA_MAXIMA.json.
A configuração inicial produz CENARIOS_COM_PENDENCIAS; isso é esperado e não significa custos aprovados.
Não preencher dados ausentes com zero. Margens usam fração (0.10 corresponde a 10%).
Resultados: datalake/03_gold/<novo_run_id>/custos_carga_maxima.
Conclusão: quality/23_custos_carga_maxima/<novo_run_id>/conclusao_23.json.
Envie a conclusão para conferirmos a execução. O script não pesquisa fontes automaticamente; a coleta rodoviária, pedágios e aprovação do combustível ainda estão pendentes.
