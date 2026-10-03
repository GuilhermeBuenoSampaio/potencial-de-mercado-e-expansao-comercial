# EDA — bloco 1: estrutura, cobertura e períodos

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo

Descrever as bases preparadas na etapa 10 e identificar as condições para comparações entre as 12 cidades. Esta etapa inicia a EDA; os blocos univariado, bivariado, temporal, geográfico e multivariado ainda serão executados.

## Executar

Na raiz do projeto, com as dependências instaladas:

```powershell
python src/etapa_11_eda_estrutura.py
```

Pela pipeline (também executa as etapas locais 01 a 05):

```powershell
python src/run_pipeline.py --eda-estrutura
```

Para preparar uma nova base e executar o bloco em seguida:

```powershell
python src/run_pipeline.py --preparar-eda --eda-estrutura
```

Não é feita nova coleta externa nessas opções. A seleção padrão exige manifesto da base e conclusão da etapa 10 com status e run_id correspondentes. Usa a versão mais recente concluída e verifica os hashes e o conteúdo JSON × Parquet. Falhas na versão escolhida interrompem o processamento. `--base CAMINHO` no script da etapa 11 permite seleção manual e valida diretamente manifesto e tabelas, sem exigir o relatório externo da etapa 10.

## Análises e saídas

A saída fica em `datalake/03_gold/<run_id>/eda_estrutura/`:

| Arquivo/tabela | Conteúdo |
|---|---|
| estrutura_tabelas | Linhas, colunas, schema e duplicação integral de registros |
| perfil_colunas | Tipos, nulos, percentual de nulos e cardinalidade não nula |
| cobertura_indicadores | Ano comum, cobertura por indicador/classificação e sinalizações de renda |
| cobertura_cidades | Cobertura numérica e sinalizações por cidade |
| ausencias_painel | Registros sem valor, preservando status, período, fonte e unidade |
| uso_ultimos_disponiveis | Quantidades por status de atualidade e uso proposto |
| relatorio_estrutura.html | Relatório para abrir no navegador |
| manifesto_eda_estrutura.json | Entradas, hashes, verificações, resultados e limites |

As seis tabelas são gravadas em JSON e Parquet. A cardinalidade de colunas é diagnóstica, não uma definição de chave. Duplicação integral significa igualdade de todos os campos; as chaves municipais são verificadas separadamente.

A qualidade fica em `quality/11_eda_estrutura/<run_id>/conclusao_11_eda_estrutura.json` e `execucao.log`. Status esperado: `EDA_ESTRUTURA_CONCLUIDA_COM_LIMITACOES`.

## Primeiros resultados reproduzidos

A execução de teste com os dados reais anteriormente recebidos e extraídos apresentou:

- 12 cidades e 56 combinações de indicador/classificação.
- 672 combinações no painel, sendo 597 com valor e 75 sem valor.
- Cobertura numérica de 88,84%.
- 43 combinações de indicador/classificação com valor em todas as cidades.
- 49 últimos valores numéricos disponíveis em anos anteriores ao período comum.
- Seis pendências documentais preservadas.
- 77 regras de validação aprovadas.

Esses resultados são da reprodução local; a execução no computador do usuário deverá ser conferida pelo seu próprio relatório.

## Interpretação

As 56 combinações incluem categorias do mesmo indicador; não são 56 dimensões independentes. As 75 ausências são combinações de cidade e indicador no período comum. Não são automaticamente erros de coleta e não serão convertidas em zero.

Os 49 últimos valores mais antigos continuam disponíveis para contexto, mas não substituem valores ausentes no painel de ano comum. O status de marcador é preservado; este bloco não identifica automaticamente o mecanismo de ausência nem atribui significado aos símbolos oficiais.

Cobertura numérica não garante comparabilidade ou elegibilidade comercial. É necessário examinar definições, períodos, metodologia e pendências de renda. A vigência dos preços continua pendente; estudos históricos não estimam demanda municipal e distâncias de centroides não representam rotas.

## Próximo bloco

Selecionar indicadores coerentes com a pergunta comercial e executar a análise univariada: distribuição entre cidades, estatísticas descritivas, diferenças de escala e investigação de extremos. A comparação com a análise original permanece reservada ao encerramento.
