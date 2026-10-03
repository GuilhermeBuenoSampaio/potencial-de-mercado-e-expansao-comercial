# Etapa 10 — preparação da EDA

Projeto: `potencial-de-mercado-e-expansao-comercial`.

Esta etapa valida as relações das duas Silver e materializa bases para exploração comercial. Não calcula ranking, demanda, faturamento previsto ou custos de fabricação. A comparação com a análise original permanece reservada ao encerramento.

## Execução no Windows

Na raiz do projeto, usando o ambiente Python e as dependências de requirements.txt:

```powershell
python src/etapa_10_base_eda.py
```

Para executar pela pipeline, incluindo as etapas locais existentes:

```powershell
python src/run_pipeline.py --preparar-eda
```

Não há consulta nova à internet nessa opção. As duas Silver devem existir com manifestos e conclusões de qualidade correspondentes. A seleção usa a execução mais recente concluída de cada tipo; os run_ids ficam registrados. Uma tabela adulterada interrompe a execução, sem buscar silenciosamente outra versão.

Para escolher versões manualmente, use `--municipal CAMINHO` e `--documental CAMINHO` no script da etapa 10. Essa opção verifica diretamente os manifestos e as tabelas indicadas; não exige a conclusão externa de qualidade. Deve ser usada para versões previamente revisadas ou reprodução controlada.

## Saídas

`datalake/03_gold/<run_id>/base_eda/` recebe JSON e Parquet:

| Tabela | Finalidade |
|---|---|
| indicadores_ultimo_disponivel_eda | Último valor numérico disponível, enriquecido com nome oficial, categorias e regiões; mantém os anos originais |
| painel_periodo_comum | Todas as cidades no maior ano registrado na série de cada indicador, inclusive quando esse ano tem marcadores sem valor |
| controle_periodos | Ano escolhido, cobertura numérica e ausências por indicador |
| precos_referencia_eda | Preços de cada produto/pacote, com precisão decimal e vigência pendente preservadas |

O painel possui uma linha por cidade e indicador/classificação. O mesmo ano é usado entre cidades para cada indicador, mas indicadores diferentes podem ter anos distintos. Quando um município só possui dado numérico mais antigo, esse dado continua na tabela de últimos valores; o painel não o substitui no ano comum. Ausências ficam nulas. Percentuais usam a escala 0–100. Categorias oficiais e unidades permanecem explícitas.

Os estudos históricos continuam disponíveis na Silver documental, por suas chaves e fontes. Não há junção desses estudos com municípios nem conversão automática de prevalência histórica em unidades vendidas. JPEG é evidência complementar do PDF. Distâncias e crescimento continuam nas tabelas municipais de origem, referenciadas pelos manifestos de entrada.

`quality/10_base_eda/<run_id>/` recebe `conclusao_10_base_eda.json` e `execucao.log`. O manifesto da base registra as entradas, hashes, contagens, regras e limitações.

## Validação

São conferidos hashes físicos de todos os pares JSON/Parquet declarados nos manifestos, reconciliação de conteúdo, unicidade e chaves das tabelas municipais e documentais. A junção municipal deve preservar a quantidade de linhas. O painel deve cobrir todas as combinações de cidade e indicador. Os preços mantêm os impedimentos de uso em orçamento atual.

A validação foi reproduzida com os dados reais anteriormente recebidos e extraídos: 38 regras aprovadas, 646 últimos indicadores, 672 linhas no painel, 56 controles de período e 67 preços. Há 75 linhas do painel sem valor numérico; não são 75 fontes novas faltantes, mas combinações de cidade/indicador no período comum. A entrada municipal adulterada por hash e uma chave geográfica inexistente foram bloqueadas. As seis pendências documentais permanecem abertas.

## Próxima análise

Explorar distribuição, cobertura, valores extremos e relações entre população, renda domiciliar, atividade econômica e estabelecimentos de alimentação. Conferir períodos, categorias, diferenças metodológicas e pendências antes de comparações. PIB por habitante não representa renda mensal; empregos no local de trabalho não representam taxa de emprego dos moradores. Contagens CNAE são indícios de estrutura comercial, não uma lista de clientes confirmados.

Antes de uma recomendação logística, obter endereços efetivos da fábrica e dos CDs e distâncias rodoviárias. Antes de cenários de venda, confirmar preços e levantar informações comerciais de clientes, concorrência, pedidos mínimos e condições de entrega. O finalizador será criado no encerramento do projeto.
