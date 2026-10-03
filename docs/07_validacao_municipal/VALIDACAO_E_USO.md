# potencial-de-mercado-e-expansao-comercial — etapa 07

## Objetivo

Validar a coleta municipal e registrar uso proposto dos indicadores antes da EDA. A comparação com a análise original será avaliada no encerramento. A etapa 06 agora deixa a comparação desativada por padrão; os registros de comparação já produzidos permanecem preservados.

## Execução isolada

No terminal aberto na raiz do projeto:

```powershell
python src/etapa_07_validacao_municipal.py
```

A rotina seleciona a última pasta por run_id em `datalake/01_bronze/*/coleta_municipal`. Para escolher outra, passar `--coleta "caminho completo da pasta coleta_municipal"`.

Na pipeline completa, `--coletar-externos` também executa a validação da nova coleta. A opção `--validar-municipais` valida a última coleta já existente e executa as etapas locais 01–05, sem consultar novamente o IBGE. Para executar somente a etapa 07, usar o comando isolado acima.

## Regras

- Município, chave única por classificação e ano, números finitos, percentuais e multiplicadores monetários.
- Reconciliação do último valor numérico com a série completa.
- Atualidade recalculada segundo a política do projeto na data da validação.
- Presença de URLs, metadados, hashes declarados e data de consulta. A etapa não verifica fisicamente as respostas brutas, que não estavam no pacote enviado.
- Soma das faixas de renda por município: 11 faixas exclusivas, incluindo sem rendimento; tolerância 0,06 p.p., compatível com soma de percentuais arredondados a duas casas. Distribuição incompleta por marcadores fica INCONCLUSIVA, sem imputação.
- Reconciliação de crescimento nominal acumulado e taxa anualizada do PIB, par exato de cinco anos.
- Coordenadas válidas, 60 pares distintos e reconciliação de Haversine. Não valida rotas rodoviárias.

## Resultado no pacote enviado

48 verificações aprovadas, 5 inconclusivas, nenhuma reprovada. As inconclusivas são faixas de renda com marcadores em Planura, Colômbia, Ipuã, Morro Agudo e Sales Oliveira. Não converter os símbolos em zero sem confirmar o significado nas notas oficiais.

Os 646 últimos valores disponíveis são classificados como 195 dentro do limite, 402 estruturais e 49 defasados. Indicadores recentes são candidatos à EDA; dados censitários descrevem perfil estrutural; dados defasados ficam como contexto histórico. Essa seleção não equivale a medir demanda ou vendas.

PIB por habitante não é renda domiciliar. Postos locais não são a proporção de residentes empregados. Faixas de renda per capita não são classes familiares A–E. Estabelecimentos por CNAE não são clientes ou concorrentes confirmados. Distâncias entre centroides não são quilômetros percorridos.

## Saídas

Cada execução cria `quality/07_validacao_municipal/<run_id>` com conclusão JSON, regras, conferência de renda, catálogo de uso dos indicadores e HTML de conferência. Dados Bronze permanecem preservados. Esta etapa não promove automaticamente dados para Silver nem produz recomendação final de cidade.

## Continuidade

Após revisar as limitações, definir o dicionário de dados e a seleção de indicadores para Silver. Priorizar população, renda média e mediana, população urbana, estabelecimentos compatíveis com o portfólio e emprego. Manter PIB como contexto econômico. Rotas reais, versão do veículo e dados comerciais observados ainda serão necessários para avaliar esforço e retorno do vendedor.
