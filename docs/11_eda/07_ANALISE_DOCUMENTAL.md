# EDA documental — preços e estudos publicados

Projeto: `potencial-de-mercado-e-expansao-comercial`.

## Objetivo

Investigar o catálogo comercial e os dados tabulares extraídos de PDF e JPEG, preservando a granularidade, os períodos, as fontes e as limitações. Esta etapa não estima demanda atual, não cria ranking e não compara a análise original.

## Entradas e rastreabilidade

O script seleciona a base EDA aprovada e usa exclusivamente a Silver documental registrada em sua linhagem. Recompõe o caminho com a raiz local, valida o hash do manifesto, a conclusão da etapa 09, os hashes, as contagens e a igualdade JSON–Parquet das nove tabelas. Uma Silver mais recente não substitui silenciosamente a entrada da base.

## Preços

Cada linha representa a apresentação publicada de um produto. Preservamos preço do pacote, categoria, estado, peso, quantidade e referências de origem. Não interpretamos preço de venda como custo fabril.

Os resumos usam categoria, estado e peso do pacote. Calculamos mínimo, mediana e máximo dos preços disponíveis com `Decimal`, sem média global nem ponderação por vendas. Produtos dentro do mesmo grupo ainda podem diferir em composição e processo.

Quando há peso positivo informado, calculamos preço por kg de referência como preço do pacote dividido pelo peso. Essa normalização não torna produtos equivalentes. O resultado decimal é exportado como texto para evitar conversão monetária para ponto flutuante. Não inferimos quantidade nem preço unitário a partir de descrições ambíguas.

Vigência e conferência comercial permanecem pendentes; os preços não são liberados para orçamento atual.

## Consumo histórico

Cada percentual é uma célula agregada publicada, não um consumidor individual. Mantemos fonte, tabela, período, indicador, dimensão, região, grupo alimentar, estrato e ID.

O resumo apresenta mínimo e máximo dos percentuais e a lista rastreável dos estratos dentro de cada recorte. Não somamos percentuais de grupos, não combinamos prevalências nem calculamos médias ponderadas sem os denominadores necessários. O intervalo descreve células da publicação, não um intervalo de confiança.

Os registros POF de 2002–2003 oferecem contexto histórico sobre alimentação fora do domicílio; não representam consumo atual nas cidades de expansão. As tabelas de universitários de instituição privada de Goiânia em 2011 permanecem separadas. Frequências e percentuais são preservados, incluindo inconsistências pendentes.

## Modelos e testes publicados

Coeficientes, ajustes e testes são reproduzidos com seus IDs, páginas e texto original. Não reestimamos os modelos, pois não dispomos dos microdados nesta base.

`LogRendaTot`, `D_urbana` e sua interação precisam ser interpretados conjuntamente, segundo a especificação original. Coeficientes de renda não medem elasticidade-preço. Valores publicados de p são preservados, inclusive desigualdades e arredondamentos. Os ajustes regionais não validam previsão municipal.

## JPEG e pendências

Cada evidência JPEG deve apontar para um registro PDF existente e preservar seu percentual. O script calcula a diferença entre percentual da imagem e do PDF e registra divergências; não as corrige automaticamente. Os registros JPEG não são incluídos como novas observações. Conferência percentual não certifica automaticamente intervalos de confiança e testes herdados do PDF.

As pendências da Silver são exportadas integralmente. Conclusão técnica com limitações não encerra a conferência científica ou comercial.

## Saídas

Em `datalake/03_gold/<run_id>/eda_documental/`, JSON e Parquet:

- `cobertura_documental`;
- `precos_referencia`;
- `resumo_precos_apresentacao`;
- `resumo_consumo_publicado`;
- `conferencia_imagens`;
- cópias rastreáveis de `consumo_historico`, `universitarios_historico`, `coeficientes_publicados`, `ajustes_publicados`, `testes_publicados`, `pendencias_documentais` e `fontes_documentais`.

Também são gerados `relatorio_documental.html` e `manifesto_eda_documental.json`. As cópias dos estudos conservam os tipos Parquet da Silver e não criam amostras independentes.

Em `quality/17_eda_documental/<run_id>/`: `conclusao_17_eda_documental.json` e `execucao.log`. Cada execução usa pasta nova, sem sobrescrever resultados.

## Execução

Na raiz do projeto:

```powershell
python src/etapa_17_eda_documental.py
```

Pela pipeline incremental, que também executa suas etapas locais iniciais:

```powershell
python src/run_pipeline.py --eda-documental
```

A flag utiliza a base existente e sua Silver vinculada; não exige nova coleta externa nem executa automaticamente outros blocos EDA.

## Continuidade

Após conferir a execução e os resultados, consolidaremos a síntese da EDA. A recomendação comercial aprofundada virá depois, incorporando as limitações de preços, estudos históricos, distância e PIB.
