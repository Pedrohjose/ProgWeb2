-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: estok
-- ------------------------------------------------------
-- Server version	8.0.46-0ubuntu0.24.04.4

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Itens`
--

DROP TABLE IF EXISTS `Itens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Itens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_itemTarefa` int DEFAULT NULL,
  `id_localizacao` int DEFAULT NULL,
  `codigoUnico` varchar(255) NOT NULL,
  `nome` varchar(255) NOT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `dataCadastro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigoUnico` (`codigoUnico`),
  KEY `id_itemTarefa` (`id_itemTarefa`),
  KEY `id_localizacao` (`id_localizacao`),
  CONSTRAINT `Itens_ibfk_1` FOREIGN KEY (`id_itemTarefa`) REFERENCES `ItensTarefa` (`id`) ON DELETE CASCADE,
  CONSTRAINT `Itens_ibfk_2` FOREIGN KEY (`id_localizacao`) REFERENCES `Localizacoes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Itens`
--

LOCK TABLES `Itens` WRITE;
/*!40000 ALTER TABLE `Itens` DISABLE KEYS */;
/*!40000 ALTER TABLE `Itens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ItensTarefa`
--

DROP TABLE IF EXISTS `ItensTarefa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ItensTarefa` (
  `id` int NOT NULL AUTO_INCREMENT,
  `statusItemTarefa` varchar(20) NOT NULL,
  `dataConferencia` date NOT NULL,
  `id_tarefa` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `id_tarefa` (`id_tarefa`),
  CONSTRAINT `ItensTarefa_ibfk_1` FOREIGN KEY (`id_tarefa`) REFERENCES `Tarefas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ItensTarefa`
--

LOCK TABLES `ItensTarefa` WRITE;
/*!40000 ALTER TABLE `ItensTarefa` DISABLE KEYS */;
/*!40000 ALTER TABLE `ItensTarefa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Localizacoes`
--

DROP TABLE IF EXISTS `Localizacoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Localizacoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `cep` varchar(8) NOT NULL,
  `logradouro` varchar(255) NOT NULL,
  `numero` varchar(20) NOT NULL,
  `complemento` varchar(100) DEFAULT NULL,
  `bairro` varchar(100) NOT NULL,
  `cidade` varchar(100) NOT NULL,
  `estado` varchar(2) NOT NULL,
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `tipo_endereco` varchar(20) DEFAULT NULL,
  `principal` tinyint(1) DEFAULT NULL,
  `dataCadastro` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Localizacoes`
--

LOCK TABLES `Localizacoes` WRITE;
/*!40000 ALTER TABLE `Localizacoes` DISABLE KEYS */;
/*!40000 ALTER TABLE `Localizacoes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Tarefas`
--

DROP TABLE IF EXISTS `Tarefas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Tarefas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tituto` varchar(255) NOT NULL,
  `descricao` varchar(255) DEFAULT NULL,
  `dataCadastro` datetime DEFAULT CURRENT_TIMESTAMP,
  `prazo` date NOT NULL,
  `statusTarefas` varchar(20) NOT NULL,
  `id_usuario` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tituto` (`tituto`),
  KEY `id_usuario` (`id_usuario`),
  CONSTRAINT `Tarefas_ibfk_1` FOREIGN KEY (`id_usuario`) REFERENCES `Usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Tarefas`
--

LOCK TABLES `Tarefas` WRITE;
/*!40000 ALTER TABLE `Tarefas` DISABLE KEYS */;
/*!40000 ALTER TABLE `Tarefas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Usuarios`
--

DROP TABLE IF EXISTS `Usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'usuario',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Usuarios`
--

LOCK TABLES `Usuarios` WRITE;
/*!40000 ALTER TABLE `Usuarios` DISABLE KEYS */;
INSERT INTO `Usuarios` VALUES (2,'Carlos','carlos@estok.com','senha123','Super Admin',1);
/*!40000 ALTER TABLE `Usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('8064eb31a8d1');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-27 23:05:15
