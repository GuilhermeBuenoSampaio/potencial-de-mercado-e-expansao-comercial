# potencial-de-mercado-e-expansao-comercial

## Instalação e execução

Extraia o pacote na raiz do projeto, substituindo os scripts anteriores em `src/` e este documento em `docs/execucoes/`. Mantenha `requirements.txt` na raiz e preserve os arquivos originais em `datalake/00_landing/`.

No PowerShell, aberto na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python .\src\run_pipeline.py
```

A pipeline executa as etapas 01, 02, 03, 04 e 05. Cada execução recebe um identificador exclusivo; saídas anteriores são preservadas. Os perfis de extração dos PDFs são vinculados ao SHA-256 dos arquivos originais. Uma fonte diferente exige revisão do perfil.

## Etapas e saídas

| Etapa | Conteúdo | Local |
|---|---|---|
| 01 | Inventário, resumo, log e registro da execução | `quality/01_inventario/<run_id>/` |
| 02 | Preços por produto e apresentação, JSON e HTML para conferência | `datalake/01_bronze/<run_id>/precos_produtos/` |
| 03 | Texto por página, recortes e tabelas estruturadas, JSON e HTML | `datalake/01_bronze/<run_id>/estudos/<hash>/` |
| Qualidade 02 e 03 | Conclusões de cada etapa | `quality/02_precos/<run_id>/` e `quality/03_estudos/<run_id>/` |

Abra `conferencia_precos.html` e os arquivos `conferencia_estudo.html` no navegador. O registro da execução distingue processamento concluído de conferência pendente. As tabelas não são aprovadas automaticamente para análise comercial.

## Tabelas dos estudos

- Estudo nacional: 312 observações e 42 valores de testes publicados. Dimensões de região, renda, sexo, situação do domicílio e idade; percentuais e intervalos de confiança quando disponíveis. Referência: 2002–2003.
- Estudo dos universitários: 310 observações e cinco testes de grupos, além dos testes por linha quando publicados. Contagens, percentuais, cursos e frequências; referência: 2011, instituição privada de Goiânia.
- Estudo regional: 20 coeficientes e cinco registros de ajuste dos modelos. Significância e valores de p são preservados como publicados; `0,000` não é interpretado como probabilidade exatamente zero.

Cada observação inclui arquivo, SHA-256, página, tabela e texto de origem. Números tabulados são acompanhados de sua representação publicada quando aplicável. Os arquivos de recorte preservam as linhas extraídas; os JSON semânticos representam as observações em colunas.

Três divergências entre contagens e percentuais do estudo dos universitários são registradas em `alertas_fonte.json`: Enfermagem/Salgados/1–4 vezes por mês; Enfermagem/Doces/1–4 vezes por mês; Fisioterapia/Fast foods/Nunca. Os valores publicados são mantidos, sem correção silenciosa. O cálculo de comparação usa o denominador informado por curso na tabela.

## Uso comercial e pendências

Preços são específicos de produto, quantidade e apresentação. Não representam custos de fabricação. A vigência comercial ainda deve ser confirmada. Estudos históricos fornecem contexto; não representam automaticamente a demanda atual das cidades candidatas. Elasticidade de despesa em relação à renda não equivale a elasticidade de preço do produto.

Permanecem pendentes: conferência integral e aprovação das tabelas; revisão dos cálculos do XLSX; atualização socioeconômica; análise de distâncias e alternativas de atendimento; EDA e recomendação comercial. Esta versão não materializa XLSX ou Parquet. O finalizador será incorporado ao concluir o projeto.

## Evidência das fontes socioeconômicas

IBGE e Caravela foram informados como fontes da análise original. Para cada indicador, registrar instituição, produto/tabela, URL específica, município e código IBGE, variável, período, unidade, data de acesso, filtros, arquivo original e SHA-256. Preserve downloads em `datalake/00_landing/` e documente consultas manuais. O endereço inicial do site não comprova a origem de cada valor. Indicadores sem fonte específica permanecem com origem pendente. Os cálculos e projeções da planilha serão refeitos.

## Etapa 04 — imagens e equivalência de fonte

Os cinco JPEGs conhecidos reproduzem as tabelas 1–5 do estudo nacional. A etapa vincula seus hashes ao PDF da mesma execução; não executa OCR genérico. Transcrições visuais dos 312 percentuais ficam no perfil Python, verificadas pela comparação com o PDF. Os JSON por imagem preservam `percentual_imagem` e `percentual_pdf` separadamente. IC95 e testes são herdados exclusivamente do PDF, identificados como tal. O texto original continua sendo o texto do PDF.

Duas divergências são registradas: tabela 4, Salgados fritos e assados/Rural, 6,4% na imagem contra 7,0% no PDF; tabela 5, Refrigerantes/30–39, 14,5% contra 14,4%. Preservar ambas as fontes e não escolher automaticamente. Intervalos do PDF não devem ser associados ao percentual divergente da imagem.

Saídas: `datalake/01_bronze/<run_id>/imagens/<hash>/`, contendo imagem original copiada, indicadores, testes vinculados, alertas, metadados e HTML de conferência. Conclusão: `quality/04_imagens/<run_id>/conclusao_04_imagens.json`. O HTML usa a cópia `fonte.jpeg` na mesma pasta.

As imagens não acrescentam 312 novas observações ao conjunto analítico: são evidências alternativas do mesmo estudo. A decisão de fonte canônica será documentada na Silver. A execução falha para imagens novas, ausentes ou repetidas, evitando aplicar um perfil inadequado.

## Etapa 05 — revisão do XLSX original

O script `src/etapa_05_revisao_xlsx.py` lê o XLSX original sem modificá-lo. Seu perfil está vinculado ao hash do arquivo conhecido. Feche o Excel antes de executar a pipeline, para evitar bloqueio do arquivo no Windows.

Saída em `datalake/01_bronze/<run_id>/xlsx_original/`:

- `celulas_originais.json`: células preenchidas, valores, tipos e formatos com aba, coordenada e SHA-256.
- `abas_classificadas.json`: papel de cada aba e contagem de fórmulas armazenadas.
- `linhas_originais.json`: registros de todas as abas com cabeçalhos e coordenadas.
- `indicadores_socioeconomicos_originais.json`: 276 indicadores e premissas das 12 cidades. Períodos e unidades ficam pendentes, sem atribuição inventada.
- `reconciliacao_aritmetica_original.json`: 156 comparações dos resultados com regras inferidas. Não recupera fórmulas ausentes nem aprova a metodologia.
- `alertas_revisao.json` e `conferencia_xlsx.html`: pendências para revisão.

Conclusão em `quality/05_revisao_xlsx/<run_id>/conclusao_05_revisao_xlsx.json`. Status esperado: `REVISADO_COM_PENDENCIAS_METODOLOGICAS`, com zero erros de processamento. Os 41 alertas iniciais incluem ocorrências repetidas por cidade; não são 41 falhas de execução. Não há fórmulas armazenadas no arquivo original. A etapa não produz novas projeções nem modifica valores.

Antes do recálculo, confirmar fontes, períodos, unidades, coordenadas, distâncias e premissas comerciais. Para uma taxa acumulada em cinco anos, a anualização candidata é `(1 + crescimento_acumulado) ** (1/5) - 1`, desde que o período e a definição sejam confirmados. O vínculo entre PIB e vendas exige uma hipótese comercial documentada; a anualização sozinha não valida a projeção de demanda.

## Etapa 06 — coleta municipal oficial

Para coletar apenas os indicadores públicos do IBGE, na raiz do projeto:

```powershell
python src/etapa_06_coleta_municipal.py
```

Para acrescentar a coleta à pipeline completa:

```powershell
python src/run_pipeline.py --coletar-externos
```

Sem essa opção, a pipeline mantém as etapas locais 01–05. Cada coleta usa internet e cria um novo run_id. Conferir a conclusão em `quality/06_coleta_municipal` e a consulta HTML em `datalake/01_bronze/<run_id>/coleta_municipal`. Critérios e limitações: `docs/06_coleta_municipal/FONTES_ATUALIDADE_E_INDICADORES.md`.

## Etapa 07 — validação municipal

Executar somente a validação da última coleta local, sem consultar novamente a internet:

```powershell
python src/etapa_07_validacao_municipal.py
```

Conferir `conclusao_07_validacao_municipal.json` e `conferencia_validacao.html` em `quality/07_validacao_municipal/<run_id>`. Regras inconclusivas exigem conferência, sem preenchimento artificial. Documentação: `docs/07_validacao_municipal/VALIDACAO_E_USO.md`.

Atualização: a etapa 06 deixa a comparação com o original desativada por padrão, reservada ao encerramento do projeto. A pipeline com `--coletar-externos` acrescenta a validação da nova coleta.

## Etapa 08 — Silver municipal

Atualize as dependências e materialize a coleta validada:

```powershell
python -m pip install -r requirements.txt
python src/etapa_08_silver_municipal.py
```

Saída: `datalake/02_silver/<run_id>/municipal`, em JSON/Parquet, com dicionário e HTML. Conclusão e log: `quality/08_silver_municipal/<run_id>`. A rotina confere hashes da Bronze com a etapa 07 e bloqueia promoção se houver divergência. Documentação: `docs/08_silver_municipal/DICIONARIO_E_MATERIALIZACAO.md`.

## Etapa 09 — Silver dos PDFs e JPEGs

Executar a materialização da última extração documental conjunta:

```powershell
python src/etapa_09_silver_documental.py
```

Caso não exista uma extração conjunta com etapas 02–04 completas:

```powershell
python src/run_pipeline.py --gerar-silver-documental
```

Conferir a conclusão em `quality/09_silver_documental/<run_id>` e o HTML em `datalake/02_silver/<run_id>/documental`. Preços permanecem com vigência pendente; estudos preservam período e população; JPEGs são evidências vinculadas aos PDFs. Documentação: `docs/09_silver_documental/SILVER_PRECOS_ESTUDOS_IMAGENS.md`.

## Etapa 10 — base da EDA

Com as Silver municipal e documental concluídas:

```powershell
python src/etapa_10_base_eda.py
```

Ou, pela pipeline local:

```powershell
python src/run_pipeline.py --preparar-eda
```

Confira `quality/10_base_eda/<run_id>/conclusao_10_base_eda.json`. A saída esperada é `BASE_EDA_PREPARADA_COM_LIMITACOES`. As tabelas ficam em `datalake/03_gold/<run_id>/base_eda/`. Leia `docs/10_base_eda/BASE_EDA.md` antes das comparações.

## Etapa 11 — EDA: estrutura e cobertura

```powershell
python src/etapa_11_eda_estrutura.py
```

Ou `python src/run_pipeline.py --eda-estrutura`.

Confira `quality/11_eda_estrutura/<run_id>/conclusao_11_eda_estrutura.json` e abra `datalake/03_gold/<run_id>/eda_estrutura/relatorio_estrutura.html`. Leia `docs/11_eda/01_ESTRUTURA_COBERTURA.md`.

## Etapa 12 — EDA univariada municipal

Após a etapa 11 sobre a mesma base:

```powershell
python src/etapa_12_eda_univariada.py
```

Ou `python src/run_pipeline.py --eda-univariada`.

Confira `quality/12_eda_univariada/<run_id>/conclusao_12_eda_univariada.json` e abra `datalake/03_gold/<run_id>/eda_univariada/relatorio_univariado.html`. Métodos em `docs/11_eda/02_ANALISE_UNIVARIADA.md`.

## Etapa 13 — EDA bivariada municipal

```powershell
python src/etapa_13_eda_bivariada.py
```

Ou `python src/run_pipeline.py --eda-bivariada`. Exige etapa 12 concluída para a mesma base.

Confira `quality/13_eda_bivariada/<run_id>/conclusao_13_eda_bivariada.json`. Abra `datalake/03_gold/<run_id>/eda_bivariada/relatorio_bivariado.html`. Métodos em `docs/11_eda/03_ANALISE_BIVARIADA.md`.

## Etapa 14 — EDA temporal

```powershell
python src/etapa_14_eda_temporal.py
```

Ou `python src/run_pipeline.py --eda-temporal`. Exige etapa 13 concluída sobre a mesma base.

Confira `quality/14_eda_temporal/<run_id>/conclusao_14_eda_temporal.json` e abra `datalake/03_gold/<run_id>/eda_temporal/relatorio_temporal.html`. Métodos em `docs/11_eda/04_ANALISE_TEMPORAL.md`.


## Etapa 15 — EDA geográfica

```powershell
python src/etapa_15_eda_geografica.py
```

Ou `python src/run_pipeline.py --eda-geografica`. Exige etapa 14 concluída sobre a mesma base. Não coleta rotas: usa centroides e dados municipais existentes.

Confira `quality/15_eda_geografica/<run_id>/conclusao_15_eda_geografica.json` e `execucao.log`. Abra `datalake/03_gold/<run_id>/eda_geografica/relatorio_geografico.html`. Métodos e limitações em `docs/11_eda/05_ANALISE_GEOGRAFICA.md`.


## Etapa 16 — EDA multivariada

```powershell
python src/etapa_16_eda_multivariada.py
```

Ou `python src/run_pipeline.py --eda-multivariada`. Exige etapas 13 e 15 concluídas para a mesma base. Não coleta dados novos. Confira `quality/16_eda_multivariada/<run_id>/conclusao_16_eda_multivariada.json` e `execucao.log`. Abra `datalake/03_gold/<run_id>/eda_multivariada/relatorio_multivariado.html`. Métodos em `docs/11_eda/06_ANALISE_MULTIVARIADA.md`.

## Etapa 17 — EDA documental

Com a base EDA e sua Silver documental já disponíveis, na raiz:

```powershell
python src/etapa_17_eda_documental.py
```

Ou pela pipeline incremental:

```powershell
python src/run_pipeline.py --eda-documental
```

Consulte `docs/11_eda/07_ANALISE_DOCUMENTAL.md`. Resultados em `datalake/03_gold/<run_id>/eda_documental`; conclusão e log em `quality/17_eda_documental/<run_id>`. Nenhum preço fica automaticamente liberado para orçamento.
