from banco import conectar_banco

def registrar_falha_biometrica(id_area_solicitada, motivo):

    conexao = conectar_banco()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            SELECT id_area
            FROM area
            WHERE id_area = %s
            """,
            (id_area_solicitada,)
        )

        registro_area = cursor.fetchone()

        id_area = (
            registro_area[0]
            if registro_area is not None
            else None
        )

        cursor.execute(
            """
            INSERT INTO registro_acesso (
                id_usuario,
                id_area,
                id_area_solicitada,
                resultado,
                confianca,
                motivo
            )
            VALUES (
                NULL,
                %s,
                %s,
                'NEGADO',
                NULL,
                %s
            )
            """,
            (
                id_area,
                id_area_solicitada,
                motivo
            )
        )

        conexao.commit()

        print("\nTentativa registrada na auditoria.")

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()