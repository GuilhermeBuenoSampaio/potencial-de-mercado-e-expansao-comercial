# Conferência de versões do PIB municipal

Projeto: `potencial-de-mercado-e-expansao-comercial`.
Conferência em 30/09/2026, horário de São Paulo.

## Resultado

A diferença apontada pela reportagem é real entre edições oficiais. A edição de 2019 do IBGE apresenta Sales Oliveira em sétimo lugar no PIB per capita. A base de dados dessa edição registra R$ 308.567,36 para 2019. As bases posteriores de 2010–2021 e 2010–2023 registram R$ 30.638,65 para o mesmo município e ano.

| Município | Ano | PIB per capita: edição 2019 | PIB per capita: edição 2023 |
|---|---:|---:|---:|
| Sales Oliveira | 2019 | R$ 308.567,36 | R$ 30.638,65 |
| Guaíra | 2019 | R$ 83.612,04 | R$ 51.739,62 |
| Nuporanga | 2019 | R$ 54.664,34 | R$ 72.118,89 |

Em Sales Oliveira, o PIB total de 2019 passa de 3.668.865,874 mil reais na edição antiga para 364.293,493 mil reais nas posteriores. Essas duas cifras se referem ao mesmo ano: a diferença entre elas não representa crescimento ou queda entre anos.

O layout oficial da edição antiga informa: “Os dados de 2019 estarão sujeitos a revisão na próxima publicação.” A mudança entre edições está demonstrada. Não foi localizada, nesta conferência, uma explicação específica para a dimensão das alterações nessas três cidades. Não atribuir a diferença a fechamento industrial, transferência de atividade ou erro estatístico sem evidência adicional.

## Verificações executadas

1. Arquivo bruto preservado da API de agregados: município `3544905`, tabela 5938, variável 37, unidade **Mil Reais**, 2019 = `364293`. A transformação para reais multiplicou corretamente por 1.000.
2. Consulta direta realizada novamente à API de agregados: confirmou `364293` em Mil Reais.
3. Consulta independente ao serviço SIDRA: confirmou município, indicador, unidade, ano e o mesmo valor.
4. Arquivo bruto da API de pesquisas, indicador 47001: 2019 = `30638.65`. O identificador retornado com seis dígitos corresponde à consulta específica de Sales Oliveira; não foi identificado erro de associação municipal.
5. Downloads completos de três edições oficiais: 2019, 2021 e 2023. Extração respeitou o layout de largura fixa de cada edição: PIB total na posição 934 na edição antiga e 935 na recente; PIB per capita nas posições 953 e 954, respectivamente. Valores de PIB total estão em mil reais, per capita em reais.
6. Comparação das 12 cidades para 2018 e 2019: 24 pares registrados em `evidencias_pib/comparacao_edicoes.json`. Alterações em 2019 com magnitude superior a 30% no PIB total ocorreram em Sales Oliveira (−90,07%), Guaíra (−38,12%) e Nuporanga (+31,93%). O limiar foi usado para priorizar a conferência; não demonstra erro.
7. Nota técnica 01/2026: trata do adiamento da divulgação de 2024 e da implantação da nova base. Não explica especificamente Sales Oliveira e não deve ser usada para atribuir uma causa à divergência.

A base completa conserva três casas decimais no PIB em mil reais; a API de agregados usada na coleta arredonda para inteiros. Essa diferença de precisão não explica a divergência de ordem de grandeza.

## Decisão na EDA e na pipeline

A etapa 14 conserva todos os valores, variações e taxas anualizadas para auditoria. Acrescenta `status_conferencia`, `pendencia_id` e `uso_interpretativo` às séries, variações, resumos por bloco e perfis setoriais. Para as três cidades acima, PIB nominal e contexto setorial recebem `CONFERENCIA_PENDENTE` e `BLOQUEADO`.

O campo `status=CALCULADO` informa somente que a conta foi possível. Não libera interpretação econômica. Qualquer análise posterior deve excluir registros com `uso_interpretativo=BLOQUEADO` dos escores, rankings e recomendações. Não existem ainda escores ou rankings no projeto; essa é uma regra para sua implementação futura.

As outras cidades recebem `SEM_DIVERGENCIA_REGISTRADA`, o que não constitui certificação de comparabilidade. Variações nominais anuais de PIB com magnitude igual ou superior a 30% geram uma tabela de alertas, sem exclusão automática.

Os indicadores de população, renda domiciliar e CEMPRE dessas cidades continuam disponíveis com suas limitações próprias. Não foram alteradas a Bronze, a Silver ou as execuções anteriores. A restrição está explicitada na nova saída temporal e não retroage automaticamente às análises anteriores.

Retirar a interpretação de que Sales Oliveira teve uma contração econômica comprovada de 85,69% entre 2018 e 2023. Esse percentual é uma conta sobre os valores coletados, cuja comparabilidade segue pendente. Pelo mesmo motivo, interpretar com cautela a trajetória de PIB de Guaíra e Nuporanga.

## Fontes e evidências

- [Base oficial da edição 2019](https://ftp.ibge.gov.br/Pib_Municipios/2019/base/base_de_dados_2010_2019_txt.zip).
- [Base oficial da edição 2021](https://ftp.ibge.gov.br/Pib_Municipios/2021/base/base_de_dados_2010_2021_txt.zip).
- [Base oficial da edição 2023](https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/base/base_de_dados_2010_2023_txt.zip).
- [Informativo original do IBGE de 2019](https://biblioteca.ibge.gov.br/visualizacao/livros/liv101896_informativo.pdf).
- [Nota técnica 01/2026](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102283.pdf).
- [SIDRA — consulta independente de 2019](https://apisidra.ibge.gov.br/values/t/5938/n6/3544905/v/37/p/2019).
- [API de pesquisas — PIB per capita](https://servicodados.ibge.gov.br/api/v1/pesquisas/38/indicadores/47001/resultados/3544905).

A pasta `evidencias_pib/` contém os três ZIPs oficiais, layouts, PDFs consultados, resposta SIDRA e linhas originais dos 24 pares de cada edição. `registro_fontes.json` registra URLs, hashes SHA-256 dos ZIPs e horário de registro desta conferência. A resposta SIDRA foi preservada; a nova tentativa de consultar a API de pesquisas expirou, portanto a confirmação de PIB per capita usa o arquivo bruto previamente coletado e as bases completas. Não se presume sucesso de consulta com falha.

## Encerramento da pendência

Para liberar o uso interpretativo, registrar uma explicação oficial ou evidência suficiente de comparabilidade da série vigente. Se necessário, solicitar esclarecimento ao IBGE ou ao órgão estadual parceiro, informando códigos, anos, versões e valores. Nenhuma mensagem externa foi enviada nesta etapa.

A notícia antiga não deve substituir automaticamente a série atual. Também não se deve combinar o valor antigo de 2019 com os valores recentes de outros anos. Uma explicação de revisão permite documentar a diferença histórica; a comparabilidade temporal exige avaliação própria.
