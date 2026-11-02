"""Solicitação manual por arquivo: python -m experimentos.teste_acesso_imagem."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Testa o acesso facial por imagem, com autorização e auditoria no MySQL."
    )
    parser.add_argument("--imagem", required=True, help="Caminho da imagem; relativo ao diretório atual.")
    parser.add_argument("--area", required=True, type=int, help="ID da área solicitada.")
    argumentos = parser.parse_args(argv)

    from controle_acesso import solicitar_acesso
    from processamento_facial import ErroDeteccaoFacial
    from auditoria import registrar_falha_biometrica

    print("\nTESTE DE ACESSO POR IMAGEM")
    print(f"Imagem: {argumentos.imagem}")
    print(f"ID da área solicitada: {argumentos.area}")

    try:
        try:
            return solicitar_acesso(
                id_area=argumentos.area,
                caminho_imagem=argumentos.imagem
            )
        except ErroDeteccaoFacial as erro:
            registrar_falha_biometrica(
                id_area_solicitada=argumentos.area,
                motivo=str(erro)
            )
            print("\nACESSO NEGADO")
            print(f"Motivo: {erro}")
    except ValueError as erro:
        print("\nNão foi possível concluir a solicitação.")
        print(f"Motivo: {erro}")
    except Exception as erro:
        print("\nOcorreu um erro inesperado.")
        print(f"Detalhes: {erro}")

    return None

if __name__ == "__main__":
    main()
