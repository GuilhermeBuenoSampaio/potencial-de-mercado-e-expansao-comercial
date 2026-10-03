# potencial-de-mercado-e-expansao-comercial — Criar modelo SQL

1. Copiar a pasta sql para a raiz do projeto e mesclar a pasta docs deste pacote com a existente. Python continuará em src.
2. Abrir o SQL Server Management Studio e conectar à instância utilizada nos outros projetos.
3. Confirmar se o banco potencial-de-mercado-e-expansao-comercial existe. Se não existir, criar esse banco vazio com esse nome no SSMS, em Bancos de Dados → Novo Banco de Dados.
4. Abrir sql/01_criar_modelo_dimensional.sql e executar. O script seleciona explicitamente o banco correto. Se houver tabelas nos schemas gold, audit ou quality, interrompe para conferência; não apagar tabelas para contornar o bloqueio.
5. Executar sql/02_conferir_modelo_dimensional.sql. O primeiro resultado deve listar 16 tabelas: 7 dimensões, 4 fatos e 5 tabelas de suporte. O terceiro deve mostrar FKs habilitadas e confiáveis (is_disabled=0 e is_not_trusted=0).
6. Enviar o resultado da primeira consulta e qualquer mensagem de erro. Não executar carga ainda: as tabelas estarão vazias.

Este pacote não exige credenciais no código, instalação de dependências Python nem nova execução da EDA. A automação e os registros JSON da carga serão implementados na próxima etapa.
