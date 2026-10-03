# potencial-de-mercado-e-expansao-comercial — Silver documental

## Objetivo

Materializar os preços, estudos PDF e evidências JPEG já tabulados na Bronze. A aprovação técnica da exportação não autoriza automaticamente uso comercial, inferência causal ou projeções de vendas. A análise original será comparada apenas no encerramento.

## Execução

No terminal aberto na raiz do projeto, com o ambiente virtual ativado:

```powershell
python -m pip install -r requirements.txt
python src/etapa_09_silver_documental.py
```

A rotina seleciona a última execução que contenha preços, estudos e imagens, junto das conclusões das etapas 02, 03 e 04. Não mistura automaticamente registros de execuções diferentes. Para selecionar uma execução: `--bronze-run-id "identificador da execucao"`.

Se não existir uma execução conjunta das etapas 02–04, usar a pipeline completa:

```powershell
python src/run_pipeline.py --gerar-silver-documental
```

A pipeline executa as etapas locais 01–05 e materializa a Silver documental da mesma execução. Não consulta novamente o IBGE. A Silver municipal permanece em sua pasta própria.

## Tabelas

| Tabela | Registros esperados na base atual | Uso |
|---|---:|---|
| precos_produtos | 67 | Produto/apresentação/estado publicado; vigência e conferência comercial pendentes |
| consumo_historico | 312 | Observações canônicas do PDF sobre consumo referido em uma semana, POF 2002–2003 |
| universitarios_historico | 310 | Perfil/consumo da população estudada, referência 2011; três inconsistências sinalizadas |
| coeficientes_publicados | 20 | Coeficientes do modelo publicado, sem tratá-los como parâmetros municipais atuais |
| ajustes_publicados | 5 | Estatísticas de ajuste do modelo publicado |
| testes_publicados | 47 | Testes dos dois PDFs; valores e notas originais preservados |
| evidencias_imagens | 312 | Transcrições visuais das cinco imagens, cada uma vinculada à observação PDF correspondente |
| fontes_documentais | 9 | Quatro PDFs e cinco JPEGs, com hash físico conferido na landing |
| pendencias_documentais | 6 | Uma pendência global de vigência de preços, duas divergências PDF/JPEG e três inconsistências universitárias |
| dicionario_documental | Gerado conforme campos | Tipos, nulabilidade e unidades básicas das tabelas |

As contagens são controles da base atual, não números a impor a qualquer nova fonte. O script confere as extrações com os relatórios das etapas 02–04. Novos documentos/layouts devem ser tratados nas etapas de extração antes desta materialização.

## Preservação e controles

Os arquivos originais são conferidos por SHA-256 físico. As tabelas Bronze lidas também têm seus hashes registrados. Esses controles identificam a origem e a execução, mas não provam sozinhos que cada célula foi transcrita corretamente. Conferência comercial e das divergências permanece explícita.

Preços usam Decimal(18,4) no Parquet. No JSON ficam como strings decimais para preservar precisão; as versões são reconciliadas após normalização. Preço original também permanece em campo próprio. Não calcular preço unitário com quantidade aproximada, não criar preço global e não interpretar preço publicado como custo fabril. Descrições que agrupam tamanhos permanecem como publicadas, sem inventar SKUs.

P-valores permanecem como texto, incluindo limites `<`, notas e arredondamento. Um valor publicado `0,000` não será interpretado como probabilidade exatamente zero. Coeficientes de renda não serão tratados como elasticidade-preço. Resultados nacionais/regionais ou de estudantes não são medições municipais atuais.

As imagens não acrescentam observações analíticas ao PDF equivalente. Os 312 registros das imagens ficam em tabela de evidência, com `incluir_como_nova_observacao=False` e `registro_pdf_id`. Intervalos e testes herdados do PDF não são tratados como novas medições das imagens.

## Divergências preservadas

- Salgados fritos e assados, rural: PDF 7,0%; imagem 6,4%.
- Refrigerantes, idade 30–39: PDF 14,4%; imagem 14,5%.

Ambos os valores ficam preservados. O registro do PDF recebe flag de pendência; não há correção nem escolha definitiva automática. As três inconsistências de n/percentual do estudo universitário ficam sinalizadas individualmente, sem recalcular e substituir o percentual publicado.

## Saídas

`datalake/02_silver/<run_id>/documental`: tabelas em JSON/Parquet, dicionário, manifesto e HTML de conferência. As tabelas são relidas e reconciliadas após exportação, incluindo nulos, números, decimais, strings e flags.

`quality/09_silver_documental/<run_id>`: conclusão e log. Status esperado: `SILVER_DOCUMENTAL_GERADA_COM_PENDENCIAS`. Consultar contagens e pendências antes de usar resultados na EDA.

Esta etapa não altera os dados municipais, não envia arquivos ao Azure/SQL e não produz ranking de cidades. O finalizador geral será preparado no encerramento.

## Inventário e fontes externas

O inventário passa a aceitar JSON e validar sua sintaxe, registrando tipo e tamanho da raiz. Assim, as respostas da coleta IBGE em `00_landing/fontes_externas` não interrompem a pipeline por formato não suportado. Arquivos JSON inválidos continuam reprovando a leitura. Essa validação não aprova o conteúdo analítico.
