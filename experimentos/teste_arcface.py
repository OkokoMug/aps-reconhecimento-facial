from pathlib import Path

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / "imagens"

def extrair_embedding(caminho, app):
    import cv2

    imagem = cv2.imread(str(caminho))

    if imagem is None:
        raise FileNotFoundError(
            f"Não foi possível carregar: {caminho}"
        )

    faces = app.get(imagem)

    if len(faces) != 1:
        raise ValueError(
            f"{caminho}: esperado 1 rosto, encontrados {len(faces)}."
        )

    return faces[0].normed_embedding

def similaridade(embedding1, embedding2):
    import numpy as np

    return np.dot(embedding1, embedding2)

def main():
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(ctx_id=-1, det_size=(640, 640))

    embedding_a1 = extrair_embedding(PASTA_IMAGENS / "pessoa_A_01.jpg", app)
    embedding_a2 = extrair_embedding(PASTA_IMAGENS / "pessoa_A_02.jpg", app)
    embedding_b = extrair_embedding(PASTA_IMAGENS / "pessoa_B_01.jpg", app)

    sim_mesma_pessoa = similaridade(embedding_a1, embedding_a2)
    sim_pessoas_diferentes = similaridade(embedding_a1, embedding_b)

    print("A1 x A2:", sim_mesma_pessoa)
    print("A1 x B :", sim_pessoas_diferentes)

if __name__ == "__main__":
    main()
