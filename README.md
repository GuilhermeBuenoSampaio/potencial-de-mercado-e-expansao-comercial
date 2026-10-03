# potencial-de-mercado-e-expansao-comercial

Projeto de análise de dados para apoiar a abertura de mercado por um vendedor de salgados congelados. Investiga como cidades se diferenciam em população, renda, estrutura comercial e localização, com coleta rastreável, tratamento de dados e análise exploratória.

## Status

Em desenvolvimento. Pipeline local implementada até a etapa 17 e síntese da EDA documentada. A priorização comercial aprofundada é o próximo bloco analítico. A publicação dos arquivos de dados no Azure, a carga SQL Server e os painéis Power BI devem ter sua conclusão registrada antes de serem apresentados como entregas realizadas.

A comparação com a análise original e o script Python finalizador serão produzidos no encerramento do projeto.

## Pergunta de negócio

Quais cidades merecem investigação prioritária para expansão, considerando tamanho do mercado prospectável, condições socioeconômicas, estrutura comercial e viabilidade de atendimento?

O foco é comercial e de vendas. Preços variam por produto e pacote. Custos de fabricação não são estimados neste trabalho.

## Abrangência

- Cidades de expansão: Franca, Cristais Paulista, Frutal, Morro Agudo, Sales Oliveira, Orlândia, Nuporanga, Ipuã, Guaíra, Barretos, Planura e Colômbia.
- Fábrica: São Carlos, SP.
- Centros de distribuição: Ribeirão Preto, Campinas, Sorocaba e São Paulo.

## Fontes e processamento

A análise utiliza arquivos XLSX, PDFs e JPEGs da análise original, além de indicadores municipais coletados de fontes oficiais do IBGE. A procedência histórica da planilha inclui IBGE e Caravela; isso não significa que todos os indicadores atuais sejam coletados de ambas as fontes.

Os PDFs são transformados em tabelas de preços e estudos publicados. Os JPEGs servem como evidência complementar aos PDFs, sem duplicação da amostra. As referências, períodos e limitações acompanham as tabelas e a documentação.

A arquitetura organiza os dados em Bronze, Silver e Gold. JSON registra metadados, conclusões e resultados; Parquet armazena tabelas; XLSX é utilizado quando disponível ou solicitado para leitura. Não são criados valores artificiais para completar indicadores.

## EDA implementada

| Bloco | Investigação |
|---|---|
| Estrutura e cobertura | Tipos, chaves, ausências, períodos e comparabilidade |
| Univariada | Distribuições, medidas descritivas e valores extremos |
| Bivariada | Pearson, Spearman e sensibilidade à retirada de cidades |
| Temporal | Séries em blocos comparáveis e auditoria de divergências de PIB |
| Geográfica | Distâncias por Haversine entre centroides e comparação de origens |
| Multivariada | Perfis por dimensão e associações com controle linear |
| Documental | Preços por apresentação, consumo histórico e conferência PDF–JPEG |

A síntese encontra-se em [docs/11_eda/08_SINTESE_EDA.md](docs/11_eda/08_SINTESE_EDA.md). Ela distingue resultados conferidos diretamente dos arquivos finais do usuário que ainda precisam de revisão independente.

## Achados e limites

- Porte populacional e quantidade de unidades de alimentação apresentam forte associação nas cidades analisadas.
- Ribeirão Preto é a origem mais próxima das 12 cidades pela distância entre centroides, confirmando o conhecimento prévio do negócio.
- Renda, presença comercial por habitante e distância oferecem informações complementares; não foi criado um escore ou ranking comercial nesta EDA.
- Uma contagem CNAE não identifica automaticamente clientes disponíveis, concorrentes ou demanda por salgados congelados.
- Os resultados são exploratórios, com 12 cidades selecionadas. Associação não demonstra causalidade.
- Renda e urbanização de 2022, dados comerciais de 2024 e outros períodos são identificados explicitamente. Não formam uma fotografia integral de um único ano.
- Distância entre centroides não representa estrada, tempo, frete ou endereço de entrega.
- Divergências entre edições oficiais do PIB, incluindo Sales Oliveira, permanecem com restrição interpretativa. A mudança entre edições foi evidenciada; sua causa específica ainda precisa de esclarecimento.
- Preços sem vigência confirmada não estão liberados para orçamento atual. Estudos históricos não estimam diretamente consumo atual municipal.

## Organização

| Caminho | Conteúdo |
|---|---|
| `src/` | Scripts das etapas e `run_pipeline.py` |
| `docs/` | Metodologia, decisões, evidências e guias de execução |
| `quality/` | Conclusões e logs por etapa e execução, mantidos localmente e fora do Git por padrão |
| `datalake/` | Arquivos de entrada e camadas de dados, fora do Git |
| `requirements.txt` | Dependências Python |

Os scripts permanecem juntos em `src`. Cada execução cria pastas com identificador próprio, sem sobrescrever resultados anteriores.

## Execução

Na raiz do projeto, com Python e ambiente virtual configurados:

```powershell
python -m pip install -r requirements.txt
python src/run_pipeline.py --help
```

A pipeline é incremental: as flags executam os blocos opcionais indicados e dependem das entradas já disponíveis. Rodar a pipeline sem flags não executa toda a EDA. Consulte [docs/execucoes/COMO_EXECUTAR.md](docs/execucoes/COMO_EXECUTAR.md) antes de iniciar ou repetir etapas.

## Infraestrutura prevista

- Azure Storage: `stcustomeranalyticsgb01`.
- Contêiner: `potencial-de-mercado-e-expansao-comercial`.
- SQL Server: banco com o mesmo nome do projeto.
- Power BI: camada de apresentação planejada.

Arquivos de dados são destinados ao Azure; scripts e documentação são versionados no GitHub. A presença desta configuração não comprova que a sincronização ou a carga foi concluída. Esses processos terão registros próprios.

## Continuidade

Qualificar estabelecimentos e canais, verificar condições reais de atendimento e confirmar a tabela comercial para construir recomendações de prospecção. Headroom, aderência produto–mercado, elasticidade-preço e previsão de vendas exigem evidências adicionais.
