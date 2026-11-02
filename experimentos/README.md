# Experimentos manuais

Executar a partir da raiz do projeto:

```powershell
python -m experimentos.teste_arcface
python -m experimentos.avaliador_embeddings
```

O módulo `experimentos.teste_banco_embedding` preserva o experimento de inserção e leitura no MySQL. Sua execução exige os argumentos `--imagem` e `--usuario`:

```powershell
python -m experimentos.teste_banco_embedding --imagem "imagens/referencia.jpg" --usuario 1
```

Forneça uma imagem própria autorizada e o ID de um usuário existente. Esse comando executa uma inserção real no banco selecionado pelas variáveis de ambiente da configuração centralizada e faz commit. Repetir a execução pode gerar registros
biométricos adicionais, e o experimento não remove a referência ao terminar. Ele não faz parte da execução dos testes automatizados.

Importar os módulos apenas define funções e o caminho da pasta de imagens.
As bibliotecas externas e o modelo são carregados na execução de `main()`.
Os experimentos `teste_arcface` e `avaliador_embeddings` localizam `imagens/` na raiz do projeto por caminhos derivados de `__file__`, independentemente do diretório de execução. Já `teste_banco_embedding` e `teste_acesso_imagem` usam o
caminho fornecido em `--imagem`: caminhos relativos são interpretados a partir do diretório de execução, e caminhos absolutos também são aceitos. No exemplo acima, `imagens/referencia.jpg` é relativo à raiz porque o comando é executado
nela e o arquivo deve ser fornecido pelo usuário.
As funções locais `extrair_embedding` dos experimentos recebem o modelo explicitamente como segundo argumento, em vez de depender de uma variável global.
