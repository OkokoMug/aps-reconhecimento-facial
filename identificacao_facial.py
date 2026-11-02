import numpy as np

from banco import conectar_banco
from repositorio_biometrias import listar_biometrias_ativas
from processamento_facial import (
    extrair_embedding,
    extrair_embedding_frame
)

THRESHOLD = 0.30

def identificar_usuario(caminho_imagem=None, frame=None):

    if (caminho_imagem is None) == (frame is None):
        raise ValueError(
            "Forneça uma imagem ou um frame, mas não ambos."
        )

    if frame is not None:
        embedding_consulta = extrair_embedding_frame(frame)
    else:
        embedding_consulta = extrair_embedding(caminho_imagem)

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        registros = listar_biometrias_ativas(cursor)

    finally:
        cursor.close()
        conexao.close()

    if not registros:
        print("Nenhuma biometria ativa encontrada.")
        return None

    similaridades_usuarios = {}

    for id_usuario, embedding_bytes, dimensao in registros:

        if dimensao != 512 or len(embedding_bytes) != 2048:
            print(
                f"Biometria inválida para usuário {id_usuario}."
            )
            continue

        embedding_banco = np.frombuffer(
            embedding_bytes,
            dtype=np.float32
        )

        similaridade = float(
            np.dot(embedding_consulta, embedding_banco)
        )

        if id_usuario not in similaridades_usuarios:
            similaridades_usuarios[id_usuario] = similaridade

        else:
            similaridades_usuarios[id_usuario] = max(
                similaridades_usuarios[id_usuario],
                similaridade
            )

    if not similaridades_usuarios:
        print("Nenhuma biometria válida encontrada.")
        return None

    print("\nSIMILARIDADES POR USUÁRIO\n")

    for id_usuario, similaridade in sorted(
        similaridades_usuarios.items(),
        key=lambda item: item[1],
        reverse=True
    ):
        print(
            f"Usuário {id_usuario}: {similaridade:.4f}"
        )

    melhor_usuario = max(
        similaridades_usuarios,
        key=similaridades_usuarios.get
    )

    melhor_similaridade = similaridades_usuarios[melhor_usuario]

    print("\nMELHOR CANDIDATO")
    print(f"Usuário: {melhor_usuario}")
    print(f"Similaridade: {melhor_similaridade:.4f}")

    if melhor_similaridade < THRESHOLD:
        print("\nRESULTADO: Pessoa desconhecida.")
        return None

    print("\nRESULTADO: Usuário identificado.")
    return melhor_usuario, melhor_similaridade

if __name__ == "__main__":
    identificar_usuario(
        "imagens/pessoa_A_teste.jpg"
    )
