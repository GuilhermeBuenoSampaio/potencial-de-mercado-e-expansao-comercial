# potencial-de-mercado-e-expansao-comercial — Silver municipal

## Objetivo e escopo

Materializar os indicadores municipais coletados em tabelas tipadas, com dicionário e rastreabilidade. Esta etapa cobre apenas a fonte municipal externa. Preços e estudos extraídos de PDF/JPEG terão decisões de Silver próprias. Comparação com a análise antiga reservada ao encerramento.

## Executar

Na raiz do projeto, com o ambiente virtual ativado:

```powershell
python -m pip install -r requirements.txt
python src/etapa_08_silver_municipal.py
```

A rotina usa a conclusão mais recente da etapa 07, que aponta a coleta correspondente. Não escolhe outra Bronze independente da validação. É necessário manter as pastas quality e datalake já geradas no projeto.

Opcional: `--validacao "pasta da etapa 07"` e `--coleta "pasta coleta_municipal"`. Os hashes devem corresponder à validação escolhida. Na pipeline completa:

```powershell
python src/run_pipeline.py --gerar-silver-municipal
```

Esse comando também executa as etapas locais 01–05 e uma nova etapa 07. Para consultar novamente o IBGE antes da Silver, acrescentar `--coletar-externos`. Para executar somente a materialização, usar o comando isolado acima.

## Controles antes da promoção

Conclusão da etapa 07 deve estar tecnicamente aprovada, com zero regras reprovadas. Cinco regras de renda inconclusivas são aceitas com sinalização explícita. Contagens da conclusão e regras precisam coincidir. A validação deve pertencer ao ano corrente, para que a classificação de defasagem não fique desatualizada.

Os hashes físicos de cinco arquivos Bronze são confrontados com os hashes registrados na etapa 07. Isso verifica a identidade da entrada validada. Não equivale a reconciliar as respostas HTTP brutas com cada observação. Catálogo é confrontado com os últimos valores da série, por município e categoria.

Mudanças nas entradas bloqueiam a materialização até nova validação. Nenhuma imputação, arredondamento novo, interpolação de classes ou mistura de períodos é aplicada. Cada execução cria diretório próprio.

## Tabelas e chaves

| Tabela | Granularidade/chave | Conteúdo |
|---|---|---|
| municipios | codigo_ibge | 12 municípios de expansão e 5 municípios de origem; regionalização e centroides |
| dicionario_indicadores | indicador_id | Nome oficial, tabela, variável, classificação, unidade, escala e metadados |
| indicadores_serie | codigo_ibge + indicador_id + ano_referencia | Toda a série coletada, inclusive marcadores sem valor numérico |
| indicadores_ultimo_disponivel | codigo_ibge + indicador_id | Último valor numérico por categoria; anos podem diferir entre municípios |
| distancias_geodesicas | destino_codigo + origem_codigo | 60 distâncias entre centroides; sem interpretação de rota rodoviária |
| crescimento_pib | codigo_ibge + ano_inicial + ano_final | Crescimento nominal acumulado em cinco anos e taxa anualizada |

`indicador_id` combina tabela, variável e hash SHA-256 truncado da classificação canônica. Não combina categorias diferentes. Novas categorias geram identificadores próprios. Chave IBGE fica como texto de sete dígitos. Ano é inteiro, valor é numérico anulável e flags são booleanos. Classificações e listas são strings JSON nas tabelas planas, para posterior leitura explícita.

As unidades `%` e `Percentual` são padronizadas para `%`, mantendo valores na escala 0 a 100. O dicionário registra `escala_percentual=100`. Para uma medida percentual no Power BI, dividir por 100 antes da formatação percentual. Reais e salários mínimos permanecem distintos. Valores em mil reais já haviam sido normalizados na Bronze; a Silver preserva multiplicador e valor original, sem aplicar a conversão novamente.

## Campos de uso

`ultimo_valor_numerico` indica a observação mais recente com número para o município/indicador. `candidato_eda` marca somente últimos valores recentes ou censitários estruturais. Não confirma validade preditiva, demanda ou rentabilidade.

`conferencia_distribuicao_renda_pendente` sinaliza todas as observações da tabela 10296 nos cinco municípios cuja distribuição ficou inconclusiva. Os números individuais são preservados. Não tratar a distribuição como completa nem construir classes familiares A–E a partir dela.

`status_valor`, `valor_original`, `unidade_original`, `status_atualidade`, `defasagem_anos`, `fonte_url`, `fonte_sha256`, `coleta_utc`, `url_metadados` e `limitacoes_uso_json` mantêm a rastreabilidade. Registro sem valor numérico não entra automaticamente no último valor, mas continua na série.

## Saídas e qualidade

`datalake/02_silver/<run_id>/municipal` contém as seis tabelas em JSON e Parquet, manifesto e HTML para conferência. Arquivos Parquet são relidos e reconciliados com JSON, incluindo números, nulos, strings e flags. Chaves e contagens são verificadas.

`quality/08_silver_municipal/<run_id>` contém conclusão e log. O status `SILVER_GERADA_COM_LIMITACOES` confirma materialização e reconciliação, mantendo pendências metodológicas. Consultar o dicionário antes de comparar cidades, especialmente quando o último valor corresponde a anos diferentes.

## Resultado do teste com a coleta enviada

1.524 observações na série, 646 últimos valores, 17 municípios, 60 distâncias e 12 índices de crescimento. Os 143 registros sem valor numérico permanecem na série. Últimos valores: 195 candidatos recentes, 402 estruturais e 49 históricos.

As seis tabelas foram reconciliadas entre JSON e Parquet. Teste com entrada Bronze alterada bloqueia promoção. Não houve consulta nova à internet nem alteração da planilha original.
