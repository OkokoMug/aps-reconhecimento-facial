"""Interface por arquivo com python -m cli --help."""

import argparse

def main(argv=None):
    parser = argparse.ArgumentParser(description="Controle de acesso facial por imagem.")
    comandos = parser.add_subparsers(dest="comando", required=True)
    cadastrar = comandos.add_parser("cadastrar", help="Cadastra biometria; escreve no MySQL.")
    cadastrar.add_argument("--imagem", required=True, help="Caminho relativo ao diretório atual ou absoluto.")
    cadastrar.add_argument("--usuario", required=True, type=int, help="ID do usuário.")
    identificar = comandos.add_parser("identificar", help="Identifica sem autorizar ou registrar acesso.")
    identificar.add_argument("--imagem", required=True, help="Caminho relativo ao diretório atual ou absoluto.")
    acesso = comandos.add_parser("acesso", help="Solicita autorização; pode escrever auditoria no MySQL.")
    acesso.add_argument("--imagem", required=True, help="Caminho relativo ao diretório atual ou absoluto.")
    acesso.add_argument("--area", required=True, type=int, help="ID da área solicitada.")
    argumentos = parser.parse_args(argv)

    if argumentos.comando == "cadastrar":
        from cadastro_biometria import cadastrar_biometria

        return cadastrar_biometria(
            id_usuario=argumentos.usuario, caminho_imagem=argumentos.imagem
        )

    if argumentos.comando == "identificar":
        from identificacao_facial import identificar_usuario

        return identificar_usuario(caminho_imagem=argumentos.imagem)

    from experimentos.teste_acesso_imagem import main as acesso_por_imagem

    return acesso_por_imagem([
        "--imagem", argumentos.imagem, "--area", str(argumentos.area)
    ])

if __name__ == "__main__":
    main()
