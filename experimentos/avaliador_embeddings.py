from pathlib import Path

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / "imagens"

def extrair_embedding(caminho, app):
    import cv2

    imagem = cv2.imread(str(caminho))

    if imagem is None:
        raise ValueError(
            f"Não foi possível carregar a imagem: {caminho}"
        )

    faces = app.get(imagem)

    if len(faces) == 0:
        raise ValueError(
            f"Nenhuma face encontrada em: {caminho}"
        )

    if len(faces) > 1:
        raise ValueError(
            f"Mais de uma face encontrada em: {caminho}"
        )

    return faces[0].normed_embedding

def main():
    import numpy as np
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(ctx_id=-1, det_size=(640, 640))

    pasta = PASTA_IMAGENS

    extensoes = {".jpg", ".jpeg", ".png"}

    arquivos = sorted(
        arquivo
        for arquivo in pasta.iterdir()
        if arquivo.suffix.lower() in extensoes
    )

    if not arquivos:
        raise ValueError("Nenhuma imagem encontrada.")

    embeddings = {}

    print("\nExtraindo embeddings...\n")

    for arquivo in arquivos:
        embedding = extrair_embedding(arquivo, app)
        embeddings[arquivo.stem] = embedding

        print(f"{arquivo.name}: OK")

    nomes = list(embeddings.keys())

    matriz = np.zeros((len(nomes), len(nomes)))

    for i, nome1 in enumerate(nomes):
        for j, nome2 in enumerate(nomes):

            matriz[i, j] = np.dot(
                embeddings[nome1],
                embeddings[nome2]
            )

    print("\nMATRIZ DE SIMILARIDADE\n")

    print(f"{'':16}", end="")

    for nome in nomes:
        print(f"{nome:16}", end="")

    print()

    for i, nome1 in enumerate(nomes):

        print(f"{nome1:16}", end="")

        for j in range(len(nomes)):
            print(f"{matriz[i, j]:<16.4f}", end="")

        print()

if __name__ == "__main__":
    main()
