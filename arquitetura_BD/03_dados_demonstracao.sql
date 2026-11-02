-- =====================================================
-- ARQUIVO: 03_dados_demonstracao.sql
--
-- Dados exclusivamente ficticios para demonstracao.
-- Nao contem fotografias, embeddings ou auditoria real.
--
-- Executar após:
--   01_estrutura.sql
--   02_procedures.sql
--
-- Destinado a um banco novo, com tabelas vazias.
-- =====================================================


-- =====================================================
-- 1. NIVEIS DE ACESSO
-- =====================================================

INSERT INTO nivel_acesso (id_nivel, nivel, descricao)
VALUES
(1, 1, 'Acesso básico às áreas de nível 1 da própria divisão'),
(2, 2, 'Acesso às áreas de níveis 1 e 2 da própria divisão'),
(3, 3, 'Acesso irrestrito a todas as divisões, incluindo o cofre');

-- =====================================================
-- 2. DIVISOES ORGANIZACIONAIS
-- =====================================================

INSERT INTO divisao (id_divisao, nome, descricao)
VALUES
(1, 'Administrativa','Responsável pela gestão administrativa e institucional'),

(2, 'Tecnologia da Informação','Responsável pela infraestrutura tecnológica, sistemas e suporte técnico'),

(3, 'Recursos Humanos','Responsável pela administração de pessoal e processos relacionados aos colaboradores');

-- =====================================================
-- 3. CARGOS
-- =====================================================

INSERT INTO cargo (id_cargo, nome, descricao)
VALUES
(1, 'Diretor Geral','Responsável pela administração geral e supervisão do cofre'),

(2, 'Gerente Administrativo','Responsável pela gestão da divisão Administrativa'),

(3, 'Assistente Administrativo','Responsável pelas atividades administrativas operacionais'),

(4, 'Analista de TI','Responsável pela infraestrutura e sistemas tecnológicos'),

(5, 'Técnico de Suporte','Responsável pelo suporte técnico e manutenção'),

(6, 'Analista de Recursos Humanos','Responsável pela gestão de pessoal');

-- =====================================================
-- 4. AREAS CONTROLADAS
-- =====================================================

INSERT INTO area
    (id_area, nome, descricao, id_divisao, id_nivel)
VALUES
(1, 'Recepção Administrativa','Área de atendimento administrativo', 1, 1),

(2, 'Diretoria Administrativa','Área destinada à gestão administrativa', 1, 2),

(3, 'Cofre Central','Área de segurança máxima destinada ao cofre institucional', 1, 3),

(4, 'Suporte Técnico','Área de suporte e manutenção de sistemas', 2, 1),

(5, 'Sala de Servidores','Área restrita à infraestrutura tecnológica', 2, 2),

(6, 'Atendimento de RH','Área de atendimento de Recursos Humanos', 3, 1),

(7, 'Arquivo Confidencial de RH','Área destinada ao armazenamento de documentos confidenciais', 3, 2);

-- =====================================================
-- 5. USUARIOS FICTICIOS
-- =====================================================

INSERT INTO usuario
    (id_usuario, nome, situacao, id_cargo, id_divisao, id_nivel)
VALUES
(1, 'João Carlos Almeida', 'ATIVO', 1, 1, 3),

(2, 'Fernanda Souza Lima', 'ATIVO', 2, 1, 2),

(3, 'Marcos Henrique Costa', 'ATIVO', 3, 1, 1),

(4, 'Lucas Andrade Silva', 'ATIVO', 4, 2, 2),

(5, 'Rafael Martins Oliveira', 'INATIVO', 5, 2, 1),

(6, 'Juliana Pereira Rocha', 'ATIVO', 6, 3, 2);