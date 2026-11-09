# Configuração da conexão

`conectar_banco()` mantém sua assinatura sem argumentos. Ela lê `APS_DB_HOST`, `APS_DB_USER`, `APS_DB_PASSWORD` e `APS_DB_NAME` a cada chamada. As quatro variáveis
são obrigatórias e não podem estar vazias. Na ausência delas, lança `ValueError` com os nomes ausentes.

Configurar explicitamente o banco de teste antes de executá-lo, seus argumentos válidos ainda permitem inserção e commit.

`.env.example` contém somente valores fictícios.

```powershell
$env:APS_DB_HOST = 'servidor-exemplo.invalid'
$env:APS_DB_USER = 'usuario_ficticio'
$env:APS_DB_NAME = 'banco_ficticio'
```

Substitua os valores pelo ambiente desejado e forneça `APS_DB_PASSWORD` pela configuração privada do terminal/IDE ou por entrada oculta, evitando gravar a senha
em scripts e no histórico. Exemplo de entrada oculta em PowerShell:

```powershell
$credencialAps = Get-Credential -UserName $env:APS_DB_USER -Message 'Credencial MySQL'
$env:APS_DB_PASSWORD = $credencialAps.GetNetworkCredential().Password
Remove-Variable credencialAps
```

Use uma conta com as permissões necessárias ao projeto. As variáveis são herdadas pelos processos filhos. Encerre a sessão ou remova a variável após o uso:

```powershell
Remove-Item Env:APS_DB_PASSWORD
```

O `.gitignore` exclui imagens, dados biométricos locais, ambientes privados, caches, logs e backups. Ele não apaga arquivos nem remove conteúdo já rastreado
ou presente no histórico. Dumps com nomes arbitrários também exigem revisão e scripts SQL públicos revisados não são bloqueados globalmente.
