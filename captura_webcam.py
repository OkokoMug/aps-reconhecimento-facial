import cv2

def capturar_rosto():

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError(
            "Não foi possível acessar a webcam."
        )

    print("\nCAPTURA FACIAL")
    print("ESPAÇO: capturar fotografia")
    print("ESC: cancelar")

    try:
        while True:

            sucesso, frame = camera.read()

            if not sucesso:
                raise RuntimeError(
                    "Falha ao capturar imagem da webcam."
                )

            cv2.imshow("APS - Captura Facial", frame)

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == 32:
                print("Fotografia capturada.")
                return frame.copy()

            if tecla == 27:
                print("Captura cancelada.")
                return None

    finally:
        camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":

    imagem = capturar_rosto()

    if imagem is not None:
        print("Dimensões da imagem:", imagem.shape)