-- =====================================================
-- Criacao das tabelas do banco de dados
-- =====================================================

-- =====================================================
-- 1. NIVEL DE ACESSO
-- =====================================================

CREATE TABLE `nivel_acesso` (
   `id_nivel` int NOT NULL AUTO_INCREMENT,
   `nivel` tinyint NOT NULL,
   `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   PRIMARY KEY (`id_nivel`),
   UNIQUE KEY `uq_nivel` (`nivel`),
   CONSTRAINT `chk_nivel` CHECK ((`nivel` between 1 and 3))
 ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. DIVISOES ORGANIZACIONAIS
-- =====================================================

CREATE TABLE `divisao` (
   `id_divisao` int NOT NULL AUTO_INCREMENT,
   `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
   `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   PRIMARY KEY (`id_divisao`)
 ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. CARGOS
-- =====================================================

CREATE TABLE `cargo` (
   `id_cargo` int NOT NULL AUTO_INCREMENT,
   `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
   `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   PRIMARY KEY (`id_cargo`)
 ) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 4. AREAS CONTROLADAS
-- =====================================================

CREATE TABLE `area` (
   `id_area` int NOT NULL AUTO_INCREMENT,
   `nome` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
   `descricao` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   `id_divisao` int DEFAULT NULL,
   `id_nivel` int NOT NULL,
   PRIMARY KEY (`id_area`),
   KEY `idx_area_divisao` (`id_divisao`),
   KEY `idx_area_nivel` (`id_nivel`),
   CONSTRAINT `fk_area_divisao` FOREIGN KEY (`id_divisao`) REFERENCES `divisao` (`id_divisao`),
   CONSTRAINT `fk_area_nivel` FOREIGN KEY (`id_nivel`) REFERENCES `nivel_acesso` (`id_nivel`)
 ) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 5. USUARIOS
-- =====================================================

CREATE TABLE `usuario` (
   `id_usuario` int NOT NULL AUTO_INCREMENT,
   `nome` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
   `situacao` enum('ATIVO','INATIVO') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ATIVO',
   `id_cargo` int NOT NULL,
   `id_divisao` int DEFAULT NULL,
   `id_nivel` int NOT NULL,
   PRIMARY KEY (`id_usuario`),
   KEY `fk_usuario_cargo` (`id_cargo`),
   KEY `idx_usuario_divisao` (`id_divisao`),
   KEY `idx_usuario_nivel` (`id_nivel`),
   CONSTRAINT `fk_usuario_cargo` FOREIGN KEY (`id_cargo`) REFERENCES `cargo` (`id_cargo`),
   CONSTRAINT `fk_usuario_divisao` FOREIGN KEY (`id_divisao`) REFERENCES `divisao` (`id_divisao`),
   CONSTRAINT `fk_usuario_nivel` FOREIGN KEY (`id_nivel`) REFERENCES `nivel_acesso` (`id_nivel`)
 ) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 6. BIOMETRIAS FACIAIS
-- =====================================================

CREATE TABLE `biometria_facial` (
   `id_biometria` int NOT NULL AUTO_INCREMENT,
   `id_usuario` int NOT NULL,
   `embedding` blob NOT NULL,
   `modelo` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'buffalo_l',
   `dimensao` smallint unsigned NOT NULL DEFAULT '512',
   `data_cadastro` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `ativo` tinyint(1) NOT NULL DEFAULT '1',
   PRIMARY KEY (`id_biometria`),
   KEY `fk_biometria_usuario` (`id_usuario`),
   CONSTRAINT `fk_biometria_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`)
 ) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 7. REGISTROS DE ACESSO
-- =====================================================

CREATE TABLE `registro_acesso` (
   `id_registro` bigint NOT NULL AUTO_INCREMENT,
   `id_usuario` int DEFAULT NULL,
   `id_area` int DEFAULT NULL,
   `id_area_solicitada` int DEFAULT NULL,
   `data_hora` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
   `resultado` enum('PERMITIDO','NEGADO') COLLATE utf8mb4_unicode_ci NOT NULL,
   `confianca` decimal(5,4) DEFAULT NULL,
   `motivo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
   PRIMARY KEY (`id_registro`),
   KEY `idx_registro_usuario` (`id_usuario`),
   KEY `idx_registro_area` (`id_area`),
   KEY `idx_registro_data` (`data_hora`),
   CONSTRAINT `fk_registro_area` FOREIGN KEY (`id_area`) REFERENCES `area` (`id_area`),
   CONSTRAINT `fk_registro_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuario` (`id_usuario`),
   CONSTRAINT `chk_confianca` CHECK (((`confianca` is null) or (`confianca` between 0 and 1)))
 ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;