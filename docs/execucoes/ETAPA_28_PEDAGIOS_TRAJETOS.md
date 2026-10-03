# Executar etapa 28

Extrair o pacote na raiz de `potencial-de-mercado-e-expansao-comercial`, substituindo `src/run_pipeline.py`. Manter os scripts das etapas anteriores. Requer internet, `pyarrow` e os arquivos locais das etapas 24, 26 e 27 concluídas e vinculadas.

```powershell
python src/run_pipeline.py --pedagios-trajetos
```

Ou executar diretamente:

```powershell
python src/etapa_28_pedagios_trajetos.py
```

O modo é isolado: não repete inventário nem carga SQL. Usa somente serviços públicos, sem credenciais. Se OSRM ou Overpass falhar, não cria estimativa aprovada; consultar a conclusão. Falha na fonte oficial Ecovias é registrada separadamente; estimativas OSM continuam identificadas como provisórias.

Saídas:
- Bronze: `datalake/01_bronze/<run_id>/pedagios_trajetos/` — respostas originais e registro da coleta.
- Gold: `datalake/03_gold/<run_id>/pedagios_trajetos/` — trajetos, trechos, passagens candidatas, tarifas oficiais disponíveis, sensibilidade e relatório.
- Qualidade: `quality/28_pedagios_trajetos/<run_id>/conclusao_28.json`.

Enviar `conclusao_28.json`, `trajetos.json` e `passagens_candidatas.json` para conferir os custos e as passagens encontradas. O resultado permanece provisório: não altera os pedágios aprovados da etapa 27.
