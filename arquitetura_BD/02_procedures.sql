DELIMITER $$

-- =====================================================
-- 1. VERIFICACAO DE ACESSO
-- =====================================================

CREATE PROCEDURE `verificar_acesso`(
     IN p_id_usuario INT,
     IN p_id_area INT,
     IN p_confianca DECIMAL(5,4)
 )
 BEGIN

     DECLARE v_resultado VARCHAR(10);
     DECLARE v_motivo VARCHAR(255);

     -- 1. Usuário inexistente
     IF p_id_usuario IS NULL
        OR NOT EXISTS (
            SELECT 1
            FROM usuario
            WHERE id_usuario = p_id_usuario
        ) THEN

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
             CASE
                 WHEN EXISTS (
                     SELECT 1
                     FROM area
                     WHERE id_area = p_id_area
                 )
                 THEN p_id_area
                 ELSE NULL
             END,
             p_id_area,
             'NEGADO',
             p_confianca,
             'Usuário inexistente'
         );

         SELECT
             p_id_usuario AS id_usuario,
             NULL AS usuario,
             p_id_area AS id_area,
             NULL AS area,
             'NEGADO' AS resultado,
             'Usuário inexistente' AS motivo,
             p_confianca AS confianca;

     -- 2. Área inexistente
     ELSEIF p_id_area IS NULL
        OR NOT EXISTS (
            SELECT 1
            FROM area
            WHERE id_area = p_id_area
        ) THEN

         INSERT INTO registro_acesso (
             id_usuario,
             id_area,
             id_area_solicitada,
             resultado,
             confianca,
             motivo
         )
         VALUES (
             p_id_usuario,
             NULL,
             p_id_area,
             'NEGADO',
             p_confianca,
             'Área inexistente'
         );

         SELECT
             p_id_usuario AS id_usuario,
             NULL AS usuario,
             p_id_area AS id_area,
             NULL AS area,
             'NEGADO' AS resultado,
             'Área inexistente' AS motivo,
             p_confianca AS confianca;

     -- 3. Usuário e área existentes
     ELSE

         SELECT
             CASE
                 WHEN u.situacao <> 'ATIVO'
                     THEN 'NEGADO'

                 WHEN nu.nivel = 3
                     THEN 'PERMITIDO'

                 WHEN u.id_divisao = a.id_divisao
                      AND nu.nivel >= na.nivel
                     THEN 'PERMITIDO'

                 ELSE 'NEGADO'
             END,

             CASE
                 WHEN u.situacao <> 'ATIVO'
                     THEN 'Usuário inativo'

                 WHEN nu.nivel = 3
                     THEN 'Usuário possui nível máximo de acesso'

                 WHEN u.id_divisao <> a.id_divisao
                      OR u.id_divisao IS NULL
                     THEN 'Área pertence a outra divisão'

                 WHEN nu.nivel < na.nivel
                     THEN 'Nível de acesso insuficiente'

                 ELSE 'Acesso autorizado'
             END

         INTO v_resultado, v_motivo

         FROM usuario u

         JOIN nivel_acesso nu
             ON u.id_nivel = nu.id_nivel

         CROSS JOIN area a

         JOIN nivel_acesso na
             ON a.id_nivel = na.id_nivel

         WHERE u.id_usuario = p_id_usuario
           AND a.id_area = p_id_area;

         INSERT INTO registro_acesso (
             id_usuario,
             id_area,
             id_area_solicitada,
             resultado,
             confianca,
             motivo
         )
         VALUES (
             p_id_usuario,
             p_id_area,
             p_id_area,
             v_resultado,
             p_confianca,
             v_motivo
         );

         SELECT
             u.id_usuario,
             u.nome AS usuario,
             a.id_area,
             a.nome AS area,
             v_resultado AS resultado,
             v_motivo AS motivo,
             p_confianca AS confianca

         FROM usuario u

         CROSS JOIN area a

         WHERE u.id_usuario = p_id_usuario
           AND a.id_area = p_id_area;

     END IF;

 END$$

CREATE PROCEDURE `registrar_nao_identificado`(
     IN p_id_area INT,
     IN p_confianca DECIMAL(5,4)
 )
 BEGIN

     IF p_id_area IS NULL
        OR NOT EXISTS (
             SELECT 1
             FROM area
             WHERE id_area = p_id_area
        ) THEN

         SELECT
             'NEGADO' AS resultado,
             'Área inexistente' AS motivo;

     ELSE

         INSERT INTO registro_acesso (
             id_usuario,
             id_area,
             resultado,
             confianca,
             motivo
         )
         VALUES (
             NULL,
             p_id_area,
             'NEGADO',
             p_confianca,
             'Usuário não identificado'
         );

         SELECT
             p_id_area AS id_area,
             'NEGADO' AS resultado,
             'Usuário não identificado' AS motivo,
             p_confianca AS confianca;

     END IF;

 END$$

 DELIMITER ;