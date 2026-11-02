def buscar_usuario(cursor, id_usuario):
    cursor.execute(
        """
            SELECT id_usuario
            FROM usuario
            WHERE id_usuario = %s
            """,
        (id_usuario,)
    )
    return cursor.fetchone()

def inserir_biometria(cursor, id_usuario, embedding_bytes):
    cursor.execute(
        """
            INSERT INTO biometria_facial
                (id_usuario, embedding, modelo, dimensao)
            VALUES
                (%s, %s, %s, %s)
            """,
        (id_usuario, embedding_bytes, "buffalo_l", 512)
    )

def listar_biometrias_ativas(cursor):
    cursor.execute("""
            SELECT
                id_usuario,
                embedding,
                dimensao
            FROM biometria_facial
            WHERE ativo = 1
              AND modelo = %s
        """, ("buffalo_l",))
    return cursor.fetchall()
