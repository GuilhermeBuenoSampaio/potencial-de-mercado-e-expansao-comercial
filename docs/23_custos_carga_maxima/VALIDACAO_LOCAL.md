# Validação local da etapa 23

2026-10-03 — aprovada em ambiente local, sem conexão SQL necessária.

- Cinco circuitos reais da etapa 22 geram 15 cenários de sensibilidade.
- Parâmetros ausentes mantêm custos e equilíbrio nulos.
- Teste sintético separado: 100 km, R$ 6/l, 8 km/l, R$ 0,20/km e R$ 5 de pedágio resultam em custo R$ 100; margem 10% resulta em equilíbrio R$ 1.000.
- Sensibilidade: 12 km/l reduz o mesmo custo sintético a R$ 75.
- Capacidade e receita/kg verificam equilíbrio dentro ou fora da carga disponível.
- Consumo negativo, booleano e NaN são rejeitados.
- Exportação JSON/Parquet reconciliada integralmente; hashes registrados.
- Compilação dos scripts 23 e run_pipeline.py aprovada.

Dados sintéticos são exclusivamente testes e não integram as tabelas do projeto. Execução no computador do usuário e coleta dos parâmetros reais permanecem pendentes.
