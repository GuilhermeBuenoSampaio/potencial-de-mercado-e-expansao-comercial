# Primeira publicacao no GitHub

Projeto: `potencial-de-mercado-e-expansao-comercial`.

Repositorio publico: https://github.com/GuilhermeBuenoSampaio/potencial-de-mercado-e-expansao-comercial

## Preparacao

Copie `README.md` e `.gitignore` para a raiz do projeto e este guia para `docs/execucoes/`. Os scripts devem estar em `src` e as documentacoes em `docs`. O guia nao envia dados ao Azure.

O `.gitignore` exclui ambientes, credenciais, `datalake`, `quality`, planilhas, Parquet e ZIP. As evidencias binarias da auditoria podem permanecer locais/Azure, com sua descricao metodologica versionada. Conclusoes de `quality` ficam fora do Git por padrao; resumos revisados podem ser documentados em `docs`.

Verifique referencias documentais a arquivos nao publicados e nao inclua documentos com dados pessoais de clientes ou segredos. O README nao declara Azure, SQL Server ou Power BI concluidos antes da verificacao.

## Comandos no PowerShell

```powershell
Set-Location 'C:\Users\Dell\OneDrive\Desktop\30 - PORTFÓLIO NOVO\potencial-de-mercado-e-expansao-comercial'
git status
```

Se aparecer que a pasta nao e um repositorio Git, inicialize:

```powershell
git init -b main
```

Se ela ja for um repositorio, mantenha seu historico e confira a branch com `git branch --show-current` antes de seguir. Nao reinicialize para apagar historico.

Confira o remoto:

```powershell
git remote -v
```

Se nao houver `origin`, adicione:

```powershell
git remote add origin https://github.com/GuilhermeBuenoSampaio/potencial-de-mercado-e-expansao-comercial.git
```

Se ja houver, confirme que ele aponta para este projeto; nao substitua silenciosamente o remoto de outro projeto.

Prepare somente os caminhos desejados:

```powershell
git add README.md .gitignore requirements.txt src docs
git diff --cached --stat
git diff --cached --name-only
git diff --cached --check
```

Revise a lista antes do commit. Ela nao deve incluir `datalake`, credenciais, XLSX, Parquet ou ZIP. Arquivos ja rastreados nao sao removidos pelo `.gitignore`; caso aparecam itens indesejados, interrompa e ajuste a selecao.

Depois da revisao:

```powershell
git commit -m "Documenta pipeline e analise exploratoria de expansao comercial"
git push -u origin main
git status
```

O envio pressupoe branch local `main` e autenticacao GitHub configurada. Se houver erro de identidade, configure seu nome e o e-mail associado ao GitHub localmente. Se o remoto ganhar commits antes do envio, nao use `--force`; concilie o historico.

A conclusao exige conferir os arquivos no GitHub e o commit publicado. Estes comandos sao instrucoes para execucao no computador do usuario; sua entrega nao significa que o envio ja ocorreu.
