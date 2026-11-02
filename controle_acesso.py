from identificacao_facial import identificar_usuario
from banco import conectar_banco
from auditoria import registrar_falha_biometrica

def _executar_verificar_acesso(cursor, id_usuario, id_area, similaridade):
    """Executa a procedure; o chamador gerencia a transação e os recursos."""
    cursor.callproc(
        "verificar_acesso",
        (
            id_usuario,
            id_area,
            round(similaridade, 4)
        )
    )

    resultados = cursor.stored_results()

    resposta = None

    for resultado in resultados:
        resposta = resultado.fetchone()

    return resposta

def solicitar_acesso(id_area, caminho_imagem=None, frame=None):

    print("\nINICIANDO VERIFICAÇÃO DE ACESSO\n")

    identificacao = identificar_usuario(
        caminho_imagem=caminho_imagem,
        frame=frame
    )

    if identificacao is None:
        registrar_falha_biometrica(
            id_area_solicitada=id_area,
            motivo="Identidade não reconhecida"
        )

        print("\nACESSO NEGADO")
        print("Motivo: Identidade não reconhecida")

        return None

    id_usuario, similaridade = identificacao

    conexao = conectar_banco()
    cursor = conexao.cursor(dictionary=True)

    try:
        resposta = _executar_verificar_acesso(
            cursor, id_usuario, id_area, similaridade
        )

        conexao.commit()

        if resposta is None:
            raise RuntimeError(
                "A procedure não retornou um resultado."
            )

        print("\nRESULTADO DA AUTORIZAÇÃO")
        print(f"Usuário: {resposta['usuario']}")
        print(f"Área: {resposta['area']}")
        print(f"Resultado: {resposta['resultado']}")
        print(f"Motivo: {resposta['motivo']}")

        return resposta

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()
