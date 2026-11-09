# Interface do terminal

Executar a partir da raiz do projeto, com o ambiente virtual e as dependências existentes. Caminhos de imagens podem ser absolutos ou relativos ao diretório
atual. Usar aspas para caminhos com espaços.

```powershell
python -m cli --help
python -m cli cadastrar --help
python -m cli identificar --help
python -m cli acesso --help
```

Importar `cli` ou consultar qualquer ajuda não carrega o modelo nem abre conexão.
Os exemplos seguintes são comandos operacionais, não simulações:

```powershell
python -m cli cadastrar --imagem "imagens/referencia.jpg" --usuario 3
python -m cli identificar --imagem "imagens/consulta.jpg"
python -m cli acesso --imagem "imagens/consulta.jpg" --area 2
```

| Comando       | Delegação               | Efeito no banco                                                                                                        |
|      ---      |           ---           |                                                 ---                                                                |
| `cadastrar`   | `cadastrar_biometria()` | Insere uma referência biométrica e faz commit em caso de sucesso. Repetições podem inserir novas referências.          |
| `identificar` | `identificar_usuario()` | Consulta referências; não solicita autorização nem registra acesso.                                                    |
| `acesso`      | `experimentos.teste_acesso_imagem.main()` | Executa autorização e auditoria conforme o fluxo existente, inclusive falhas biométricas e áreas     inexistentes.                                                                                                                                                      |

Os IDs são convertidos para inteiros sem consultas ou restrições adicionais pela CLI.

Para validar sem MySQL, webcam ou inferência real:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test_*.py' -v
```
