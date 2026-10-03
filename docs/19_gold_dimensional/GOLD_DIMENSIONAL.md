# potencial-de-mercado-e-expansao-comercial — Etapa 19

Data: 03/10/2026. Objetivo: materializar o modelo dimensional aprovado na etapa 18, preservando os dados e limites da EDA.

## Entradas e contrato

A rotina usa a base EDA aprovada da etapa 10. Os dois run_id Silver são os registrados nessa base; não seleciona duas Silver recentes independentes. Confere manifesto/conclusão da base, hashes de suas exportações, manifesto e conclusão de cada Silver, hashes e conteúdo JSON × Parquet das tabelas Silver. Pode fixar a base com `--base`.

O arquivo `src/contrato_dimensional.py` registra tipos, nulabilidade, identidades e FKs do DDL v1.0. Inteiros, textos e decimais são verificados antes da exportação. Decimais que exigiriam arredondamento ou excederiam a precisão SQL bloqueiam a execução. Datas de coleta são convertidas para UTC e armazenadas em datetime2(6), sem fuso no SQL; UTC permanece no nome do campo.

## Saídas e grãos

`datalake/03_gold/<run_id>/dimensional` contém 14 tabelas, cada uma em JSON e Parquet, mais `manifesto_dimensional.json`. As sete dimensões e quatro fatos correspondem ao modelo 18. As três tabelas restantes preservam evidências, pendências e registros auxiliares. Audit.execucao_carga e quality.reconciliacao_carga são preenchidas pelo carregador SQL, não materializadas como dados fictícios.

Os nomes dos arquivos usam `gold__dim_municipio`, por exemplo; o manifesto registra o nome SQL com ponto. Chaves técnicas locais iniciam em 1 nesta exportação. A carga remapeia as chaves para as identidades reais SQL, sem IDENTITY_INSERT e sem pressupor que os mesmos números sejam livres no banco.

| Tabela | Linhas no teste local |
|---|---:|
| dim_municipio | 17 |
| dim_periodo | 19 |
| dim_indicador | 56 |
| dim_fonte | 29 |
| dim_ponto_distribuicao | 5 |
| dim_produto | 67 |
| dim_estrato_estudo | 622 |
| fato_indicador_municipal | 1.524 |
| fato_distancia_municipio_origem | 60 |
| fato_preco_referencia | 67 |
| fato_estudo_publicado | 622 |
| evidencia_imagem | 312 |
| pendencia | 6 |
| registro_documental_auxiliar | 72 |

As contagens descrevem a base local testada; a execução do usuário será confrontada com a entrada real. JSON guarda decimais como texto exato; Parquet usa decimal128. O arquivo original Silver não é modificado.

## Chaves naturais por hash

SHA-256 sobre JSON canônico UTF-8: chaves ordenadas, separadores vírgula/dois-pontos, caracteres Unicode preservados, nulos explícitos, sem NaN. Não concatenar campos manualmente.

- Fonte documental: hash físico do documento + caminho relativo + edição (NULL se desconhecida).
- Fonte API: hash da resposta + URL + coleta UTC + edição desconhecida. A rotina não relê o HTTP bruto nesta etapa; hash_fisico_verificado fica False para essas fontes.
- Produto: categoria, descrição original, estado, peso da embalagem, quantidade exata e quantidade aproximada. SKU não confirmado fica NULL; descrições agrupadas não são desmembradas.
- Estrato: hash da fonte, tabela Silver do estudo, tabela publicada, abrangência, região, dimensão, estrato, alimento, curso, grupo, frequência e indicador publicado.
- Pendência: registro documental completo.

## Restrições preservadas

Todos os indicadores PIB ficam fora do aprofundamento comercial inicial, conforme o bloco multivariado. Sales Oliveira, Guaíra e Nuporanga recebem também flag de revisão PIB entre edições; não eliminar seus valores publicados. O indicador municipal só fica liberado quando é candidato EDA, tem valor, não tem pendência de renda e não é PIB. Essa flag permite exploração descritiva, não prova demanda ou causalidade.

Vigência dos preços continua não confirmada; não liberar orçamento atual. Percentuais dos estudos mantêm escala 0–100. As imagens permanecem vinculadas ao PDF, sem novas observações. Registros auxiliares preservam coeficientes, ajustes e testes, inclusive p-valores textuais. Sem projeção de vendas, imputação, criação de SKUs ou comparação com a planilha original.

## Auditoria

Cada execução gera pasta nova em `quality/19_gold_dimensional/<run_id>` com log e conclusão. Status esperado: GOLD_DIMENSIONAL_VERIFICADA_COM_LIMITACOES. Falha não promove manifesto aprovado; uma saída parcial de execução falha não é selecionada pelo carregador.
