from captura_webcam import capturar_rosto
from controle_acesso import solicitar_acesso
from processamento_facial import ErroDeteccaoFacial
from auditoria import registrar_falha_biometrica

def main():

    print("=" * 50)
    print("SISTEMA DE CONTROLE DE ACESSO FACIAL")
    print("=" * 50)

    try:
        id_area = int(
            input("\nDigite o ID da área desejada: ")
        )

        if id_area <= 0:
            print("O ID da área deve ser positivo.")
            return

        frame = capturar_rosto()

        if frame is None:
            print("\nOperação cancelada.")
            return

        solicitar_acesso(
            id_area=id_area,
            frame=frame
        )

    except ErroDeteccaoFacial as erro:

        registrar_falha_biometrica(
            id_area_solicitada=id_area,
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

if __name__ == "__main__":
    main()