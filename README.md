# APS — Controle de acesso por reconhecimento facial

Protótipo acadêmico de visão computacional para identificar pessoas e verificar permissões de acesso a áreas. O sistema recebe uma imagem de arquivo ou da webcam, compara características faciais com referências cadastradas e solicita a decisão de autorização ao MySQL.

Permite cadastrar múltiplas referências por usuário, rejeitar identidades desconhecidas, validar a quantidade de rostos e registrar decisões e falhas biométricas. Não controla fisicamente portas ou fechaduras.

## Tecnologias

Ambiente de referência: **CPython 3.11.9, Windows x64**, com execução facial em CPU.
As dependências diretas estão fixadas em [requirements.txt](requirements.txt):

| Biblioteca             | Versão   |
|           ---          |    ---   |
| InsightFace            | 2.1      |
| ONNX Runtime CPU       | 1.30.0   |
| OpenCV                 | 5.0.0.93 |
| NumPy                  | 2.4.6    |
| MySQL Connector/Python | 26.7.0   |

É necessário um servidor MySQL separado, com suporte ao esquema e às procedures fornecidos.

## Arquitetura

1. **Aquisição:** captura da webcam por OpenCV ou leitura de uma imagem.
2. **Detecção e extração:** `FaceAnalysis` do InsightFace, com modelo `buffalo_l`,
   `CPUExecutionProvider`, `ctx_id=-1` e `det_size=(640, 640)`. O projeto valida
   exatamente um rosto; o processamento interno do modelo é delegado à biblioteca.
3. **Representação:** uso de `normed_embedding`, convertido para 512 valores
   `float32`. A persistência utiliza `tobytes()`, totalizando 2.048 bytes.
4. **Identificação:** produto escalar dos vetores normalizados, equivalente à
   similaridade de cosseno. Considera a maior similaridade entre as referências
   de cada usuário e aceita o melhor candidato quando o valor é pelo menos `0.30`.
5. **Autorização:** a procedure `verificar_acesso` decide conforme situação do
   usuário, nível de acesso e divisão da área, incluindo os casos de inexistência.
6. **Auditoria:** a procedure registra suas decisões; o Python registra falhas
   biométricas previstas, sem duplicar os registros das decisões de autorização.

| Módulo                      | Responsabilidade                                              |
|              ---            |                            ---                                |
| `cli.py`                    | Interface por comandos para cadastro, identificação e acesso. |
| `sistema_acesso.py`         | Interface interativa de solicitação pela webcam.              |
| `captura_webcam.py`         | Captura, teclas de controle e liberação da câmera.            |
| `processamento_facial.py`   | Modelo, validação facial e extração de embeddings.            |
| `cadastro_biometria.py`     | Coordenação do cadastro e sua transação.                      |
| `identificacao_facial.py`   | Comparação de referências e seleção da identidade.            |
| `controle_acesso.py`        | Coordenação da identificação e chamada da autorização.        |
| `repositorio_biometrias.py` | Consultas e inserção de referências biométricas.              |
| `auditoria.py`              | Persistência de falhas biométricas.                           |
| `banco.py`                  | Conexão MySQL configurada por variáveis de ambiente.          |

Os experimentos manuais ficam em `experimentos/`, os testes automatizados em
`tests/` e os scripts do banco em `arquitetura_BD/`.

## Instalação e configuração

Na raiz do projeto, com Python 3.11 disponível, crie e ative o ambiente virtual.
Exemplo no PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Mantenha o OpenCV com interface gráfica para usar a webcam. Os pesos `buffalo_l` não são distribuídos nem instalados pelo `requirements.txt`: sua obtenção e disponibilidade devem ser preparadas para o InsightFace, observando suas condições
de uso. O módulo facial inicializa o modelo quando importado e a CLI adia esses imports até a execução de um comando, permitindo consultar `--help` sem carregá-lo.

Configure no ambiente do terminal ou IDE as quatro variáveis obrigatórias:

- `APS_DB_HOST`: endereço do servidor.
- `APS_DB_USER`: usuário MySQL.
- `APS_DB_PASSWORD`: senha da conexão.
- `APS_DB_NAME`: nome do banco selecionado.

Consulte [CONFIGURACAO.md](CONFIGURACAO.md) para configurar a sessão e fornecer a senha sem colocá-la nos comandos.
[.env.example](.env.example) contém apenas valores fictícios; arquivos `.env` **não são carregados automaticamente**.

## Preparação do banco demonstrativo

Os arquivos existentes estão em **`arquitetura_BD/`**.
Crie e selecione um banco novo para demonstração e execute, nessa ordem:

1. [01_estrutura.sql](arquitetura_BD/01_estrutura.sql): cria sete tabelas.
2. [02_procedures.sql](arquitetura_BD/02_procedures.sql): cria `verificar_acesso`
   e `registrar_nao_identificado`.
3. [03_dados_demonstracao.sql](arquitetura_BD/03_dados_demonstracao.sql): insere
   níveis, divisões, cargos, áreas e seis usuários fictícios.

Execute-os no MySQL Workbench com o schema de destino selecionado ou, no cliente `mysql` aberto na raiz do projeto:

```sql
USE aps_demonstracao;
SOURCE arquitetura_BD/01_estrutura.sql;
SOURCE arquitetura_BD/02_procedures.sql;
SOURCE arquitetura_BD/03_dados_demonstracao.sql;
```

`aps_demonstracao` é apenas um nome de exemplo para um banco previamente criado. O cliente precisa interpretar `DELIMITER`. Os scripts destinam-se a uma instalação nova, não a migrações ou reexecuções sobre dados existentes. Aponte `APS_DB_NAME` para o banco preparado e use uma conta com as permissões necessárias.

**`biometria_facial` e `registro_acesso` ficam inicialmente vazias.** Antes de reconhecer pessoas, cadastre referências autorizadas para os usuários desejados. O fluxo Python usa `verificar_acesso`; as falhas biométricas são registradas por `auditoria.py`, sem chamada à procedure `registrar_nao_identificado`.

## Utilização

Execute a partir da raiz, no ambiente configurado. Os nomes de imagem abaixo são exemplos: forneça arquivos próprios, obtidos com autorização. Caminhos relativos são interpretados a partir do diretório atual.

```powershell
python -m cli --help
python -m cli cadastrar --imagem "imagens/referencia.jpg" --usuario 3
python -m cli identificar --imagem "imagens/consulta.jpg"
python -m cli acesso --imagem "imagens/consulta.jpg" --area 2
```

| Operação      | Efeito no banco                                                                         |
|       ---     |                                        ---                                              |
| `cadastrar`   | Insere uma referência e confirma a transação; repetir pode adicionar novas referências. |
| `identificar` | Consulta referências; não solicita autorização nem registra acesso.                     |
| `acesso`      | Executa autorização e pode gravar auditoria, inclusive de falhas biométricas.           |

O cadastro exige usuário existente e exatamente um rosto. A identificação exibe candidato e similaridade; o acesso apresenta também a decisão e o motivo. A área é encaminhada ao fluxo existente sem validação adicional de existência pela CLI.
Consulte [CLI.md](CLI.md) para detalhes.

Para iniciar a interface interativa:

```powershell
python sistema_acesso.py
```

Informe o ID positivo da área. A câmera de índice `0` abre uma prévia:
**ESPAÇO captura** e **ESC cancela**. A solicitação capturada pode gerar auditoria real; cancelar não solicita autorização.
É necessária uma sessão com interface gráfica e câmera disponível.

## Testes e experimentos

Execute a suíte automatizada com descoberta restrita a `tests/`:

```powershell
python -B -m unittest discover -s tests -p "test_*.py" -v
```

A suíte contém 49 testes e usa mocks nas fronteiras externas, sem MySQL real, webcam ou inferência. Verifica contratos como threshold, múltiplas referências, serialização, auditoria, procedures, configuração, CLI e execução direta. A verificação da presença de imagens pode ser ignorada quando os arquivos privados não estiverem disponíveis.

Esses testes não substituem a validação integrada do modelo, câmera, permissões do banco e implementação das procedures. Consulte [tests/README.md](tests/README.md) e [experimentos/README.md](experimentos/README.md). Experimentos manuais podem
realizar operações reais: o teste de persistência exige `--imagem` e `--usuario` e insere uma biometria com commit quando executado.

## Limitações e privacidade

- Trata-se de um protótipo acadêmico, sem garantia de adequação a controle de
  acesso de produção e sem métricas publicadas de precisão ou desempenho.
- Não há detecção de vivacidade: o sistema não distingue necessariamente uma
  pessoa presente de uma fotografia apresentada à câmera.
- O threshold **`0.30` é experimental**; não representa uma garantia estatística
  e depende das condições e da amostra de validação.
- A aplicação exige exatamente um rosto por imagem. Iluminação, pose e qualidade
  de aquisição podem afetar os resultados.
- Fotografias e embeddings reais não fazem parte da distribuição pública.
  Cada instalação deve cadastrar suas próprias referências biométricas
  autorizadas; os usuários fictícios do SQL não incluem biometrias.
- A auditoria persiste informações das tentativas. Use um banco de demonstração
  e não publique imagens, embeddings, credenciais ou registros operacionais reais.

Os padrões de exclusão estão em [.gitignore](.gitignore); eles não removem dados
já versionados ou presentes no histórico.
