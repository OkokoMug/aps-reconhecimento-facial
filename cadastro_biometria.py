from banco import conectar_banco
from repositorio_biometrias import buscar_usuario, inserir_biometria

from processamento_facial import (
    app,
    ErroDeteccaoFacial,
    extrair_embedding,
    extrair_embedding_frame,
)

def cadastrar_biometria(id_usuario, caminho_imagem):

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        if buscar_usuario(cursor, id_usuario) is None:
            raise ValueError(
                f"Usuário {id_usuario} não encontrado."
            )

        embedding = extrair_embedding(caminho_imagem)

        embedding_bytes = embedding.tobytes()

        inserir_biometria(cursor, id_usuario, embedding_bytes)

        conexao.commit()

        print(
            f"Biometria cadastrada com sucesso. "
            f"ID: {cursor.lastrowid}"
        )

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()
