# Sincronizacao Azure — AZ01

Projeto e container: `potencial-de-mercado-e-expansao-comercial`. Conta: `stcustomeranalyticsgb01`.

## Escopo

O script em `src/sincronizar_datalake_azure.py` envia arquivos existentes em `datalake/01_bronze`, `datalake/02_silver`, `datalake/03_gold` e `quality`, preservando o caminho relativo completo e os run_ids. Inclui XLSX, XLS, XLSM, Parquet, JSON, HTML, LOG, TXT e SVG. JSON e logs acompanham os dados para manter rastreabilidade.

Nao cria XLSX nem converte tabelas. Uma camada que contenha somente Parquet/JSON sera enviada nesses formatos; a ausencia de XLSX nao e preenchida automaticamente. Landing e documentos fonte PDF/JPEG nao fazem parte desta sincronizacao. Copias de consulta que nao foram incorporadas ao projeto continuam fora do envio.

Todos os arquivos elegiveis dos prefixos sao enviados, inclusive execucoes antigas ou com pendencias. O envio preserva seus status; nao certifica qualidade analitica. Os registros AZ01 tambem ficam fora do Git pelo `.gitignore`.

## Autenticacao e execucao

No PowerShell, na raiz do projeto e usando seu ambiente Python:

```powershell
python -m pip install -r requirements.txt
az login
python src/sincronizar_datalake_azure.py
```

Sem `--aplicar`, gera somente inventario e plano local, sem acesso ao Azure. Revise a conclusao e a quantidade planejada.

Para enviar:

```powershell
python src/sincronizar_datalake_azure.py --aplicar
```

Usa `AzureCliCredential`, aproveitando o login do Azure CLI sem chaves no codigo. Se `az` nao for encontrado, instale ou habilite o Azure CLI no PATH e reabra o terminal. Para erro de autorizacao, confira a conta/tenant do login e a funcao **Storage Blob Data Contributor** no recurso adequado. Nao publique senhas, tokens ou chaves.

O script usa o endpoint Blob da conta, compativel com arquivos no armazenamento ADLS Gen2. O container e criado, se ausente e se a identidade tiver permissao. Nenhum acesso publico e solicitado.

## Integridade e repeticao

- Inventaria tamanho e SHA-256 locais.
- Cria blobs do tipo BlockBlob com `overwrite=False`.
- Para blobs existentes, verifica tamanho e baixa o conteudo para recalcular SHA-256; nao confia apenas em metadados.
- Condiciona a leitura ao ETag para detectar alteracao remota durante a verificacao.
- Arquivo identico e mantido; arquivo diferente no mesmo caminho interrompe a execucao.
- Nenhum blob e apagado ou sobrescrito. Uma repeticao verifica novamente os arquivos e retoma os que ainda faltam.
- Verifica se o arquivo local mudou entre inventario e transferencia. Nao execute a pipeline ou edite os dados durante o envio.

A verificacao por download gera leitura e transferencia adicionais no Azure. O script verifica correspondencia de bytes; nao repete as regras analiticas da Silver/Gold.

## Registros

Em `quality/AZ01_sincronizacao/<run_id>/`:

- `inventario_envio.json`;
- `conclusao_AZ01.json`;
- `execucao.log`.

O inventario e capturado antes desses registros para evitar autorreferencia. Apos envio bem-sucedido dos dados, os tres registros fechados sao enviados e verificados. Se essa ultima transferencia falhar, o programa retorna codigo 2 e informa que os dados foram verificados, mas os registros nao foram totalmente enviados. A conclusao local descreve a sincronizacao do inventario principal; nao declara que ela propria foi enviada. Codigo 1 indica falha no envio/verificacao principal e codigo 0 indica sucesso ou plano local concluido.

Esta sincronizacao e executada separadamente da pipeline analitica para nao reprocessar dados apenas para enviar ao Azure. Nao e o finalizador do projeto.

## Referencias oficiais

- https://learn.microsoft.com/python/api/azure-storage-blob/azure.storage.blob.blobclient
- https://learn.microsoft.com/azure/storage/blobs/storage-blob-upload-python
