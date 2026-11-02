import argparse
from pathlib import Path

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / "imagens"

def main():
    parser = argparse.ArgumentParser(
        description="Insere e recupera um embedding no MySQL e a execução faz commit."
    )
    parser.add_argument("--imagem", required=True, help="Caminho da imagem, relativo ao diretório atual ou absoluto.")
    parser.add_argument("--usuario", required=True, type=int, help="ID do usuário que receberá a biometria.")
    argumentos = parser.parse_args()

    import cv2
    import numpy as np
    from banco import conectar_banco
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CPUExecutionProvider"]
    )

    app.prepare(ctx_id=-1, det_size=(640, 640))

    imagem = cv2.imread(argumentos.imagem)

    if imagem is None:
        raise ValueError("Não foi possível carregar a imagem.")

    faces = app.get(imagem)

    if len(faces) != 1:
        raise ValueError(
            f"Esperada 1 face, encontradas {len(faces)}."
        )

    embedding_original = faces[0].normed_embedding.astype(np.float32)

    print("Shape original:", embedding_original.shape)
    print("Tipo original:", embedding_original.dtype)

    #Serialização
    embedding_bytes = embedding_original.tobytes()

    print("Tamanho serializado:", len(embedding_bytes), "bytes")

    conexao = conectar_banco()

    cursor = conexao.cursor()

    sql = """
        INSERT INTO biometria_facial
            (id_usuario, embedding, modelo, dimensao)
        VALUES
            (%s, %s, %s, %s)
    """

    valores = (
        argumentos.usuario,
        embedding_bytes,
        "buffalo_l",
        512
    )

    cursor.execute(sql, valores)

    id_biometria = cursor.lastrowid

    conexao.commit()

    print("Biometria inserida. ID:", id_biometria)

    cursor.execute(
        """
        SELECT embedding
        FROM biometria_facial
        WHERE id_biometria = %s
        """,
        (id_biometria,)
    )

    resultado = cursor.fetchone()

    embedding_recuperado = np.frombuffer(
        resultado[0],
        dtype=np.float32
    )

    print("Shape recuperado:", embedding_recuperado.shape)

    iguais = np.array_equal(
        embedding_original,
        embedding_recuperado
    )

    print("Embeddings idênticos:", iguais)

    cursor.close()
    conexao.close()

if __name__ == "__main__":
    main()
