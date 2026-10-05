# Etapa 31 — Views de consumo para Power BI

Extraia na raiz do projeto potencial-de-mercado-e-expansao-comercial. Adicione o script e SQL; substitua src/run_pipeline.py. Preserve todas as etapas anteriores.

```powershell
python src/run_pipeline.py --views-power-bi --sql-servidor 'DESKTOP-MAMEBQ8\SQLEXPRESS' --sql-driver 'ODBC Driver 17 for SQL Server' --confiar-certificado
```

O script instala as views automaticamente, dentro de transacao, e verifica contagens, chaves, relacionamentos, soma dos estabelecimentos e receitas. Esperado: VIEWS_POWER_BI_VERIFICADAS. Envie quality/31_views_power_bi/<run_id>/conclusao_31.json.

| View | Linhas | Funcao |
|---|---:|---|
| gold.vw_bi_execucao_comercial | 1 | Rastreabilidade da versao selecionada |
| gold.vw_bi_circuito | 5 | Dimensao de agrupamentos sugeridos |
| gold.vw_bi_municipio_comercial | 12 | Perfil municipal e vinculo ao circuito |
| gold.vw_bi_cenario_comercial | 27 | Parametros hipoteticos e identificacao do cenario de referencia |
| gold.vw_bi_custo_viagem_simulado | 135 | Custos e receitas de equilibrio simuladas |

Selecao: ultima carga comercial por carregado_utc, com desempate por run_29, vinculada a carga municipal SQL atualmente aprovada. Se nao houver carga compativel, as views ficam vazias, evitando exibir uma versao incompatível. A verificacao da etapa exige correspondencia com a ultima conclusao 30. Todas as chaves incluem a execucao.

## Relacionamentos no Power BI

Importe as quatro views de dados; a view de execucao e opcional para mostrar rastreabilidade. Use nomes de tabelas iguais aos nomes das views, sem prefixo gold.

| Lado 1 | Lado muitos | Coluna | Direcao |
|---|---|---|---|
| vw_bi_circuito | vw_bi_municipio_comercial | circuito_chave | Unica: circuito para municipio |
| vw_bi_circuito | vw_bi_custo_viagem_simulado | circuito_chave | Unica: circuito para fato |
| vw_bi_cenario_comercial | vw_bi_custo_viagem_simulado | cenario_chave | Unica: cenario para fato |

Nao criar relacionamento municipio–fato de custo: o custo pertence ao circuito inteiro. Selecionar um municipio nao deve transformar custo de circuito em custo municipal. Para comparar referencias financeiras, selecione circuito. Filtros municipais servem ao perfil municipal; o comportamento sera explicitado nas medidas e nos visuais.

Nao ativar filtros bidirecionais nem juntar fisicamente municipio com os 135 fatos, pois isso replica valores por cidade. No painel financeiro exigir exatamente um cenario selecionado, inicialmente cenario_referencia=true. Somar receita entre cenarios nao faz sentido. Somar circuitos de um mesmo cenario significa uma viagem sugerida de cada circuito, sem frequencia mensal definida. O cenario_referencia na dimensao de circuito e a receita fixa da etapa 29; use receita da fato para sensibilidade, e oculte receita_referencia_brl da dimensao nos visuais dinâmicos.

Populacao e contagem de estabelecimentos sao aditivas entre municipios; renda mediana municipal nao deve ser somada nem chamada de renda mediana regional. Varejo CNAE 47.2 exclui supermercados 47.1. Custos e parametros permanecem hipoteticos, pedagios OSM nao homologados, sequencias sao sugestoes comerciais. Gerente do CD define rotas e entregas.

Preparacao e compilacao verificadas localmente; instalacao das views e consultas de verificacao precisam rodar no servidor Windows. A etapa prepara o SQL, ainda nao cria o PBIX.
