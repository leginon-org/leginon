-- MySQL dump 10.13  Distrib 5.1.73, for redhat-linux-gnu (x86_64)
--
-- Host: localhost    Database: leginondb
-- ------------------------------------------------------
-- Server version	5.1.73-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `leginondb`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `leginondb` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `leginondb`;

--
-- Table structure for table `AcquisitionImageData`
--

DROP TABLE IF EXISTS `AcquisitionImageData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AcquisitionImageData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `MRC|image` text,
  `pixeltype` text,
  `pixels` int(20) DEFAULT NULL,
  `label` text,
  `filename` text,
  `REF|ImageListData|list` int(20) DEFAULT NULL,
  `REF|QueueData|queue` int(20) DEFAULT NULL,
  `REF|ScopeEMData|scope` int(20) DEFAULT NULL,
  `REF|CameraEMData|camera` int(20) DEFAULT NULL,
  `REF|CorrectorPlanData|corrector plan` int(20) DEFAULT NULL,
  `correction channel` int(20) DEFAULT NULL,
  `channel` int(20) DEFAULT NULL,
  `REF|DarkImageData|dark` int(20) DEFAULT NULL,
  `REF|BrightImageData|bright` int(20) DEFAULT NULL,
  `REF|NormImageData|norm` int(20) DEFAULT NULL,
  `REF|PresetData|preset` int(20) DEFAULT NULL,
  `REF|AcquisitionImageTargetData|target` int(20) DEFAULT NULL,
  `REF|EMTargetData|emtarget` int(20) DEFAULT NULL,
  `REF|GridData|grid` int(20) DEFAULT NULL,
  `REF|SpotWellMapData|spotmap` int(20) DEFAULT NULL,
  `REF|TiltSeriesData|tilt series` int(20) DEFAULT NULL,
  `version` int(20) DEFAULT NULL,
  `tiltnumber` int(20) DEFAULT NULL,
  `REF|MoverParamsData|mover` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|ImageListData|list` (`REF|ImageListData|list`),
  KEY `REF|QueueData|queue` (`REF|QueueData|queue`),
  KEY `REF|ScopeEMData|scope` (`REF|ScopeEMData|scope`),
  KEY `REF|CameraEMData|camera` (`REF|CameraEMData|camera`),
  KEY `REF|CorrectorPlanData|corrector plan` (`REF|CorrectorPlanData|corrector plan`),
  KEY `REF|DarkImageData|dark` (`REF|DarkImageData|dark`),
  KEY `REF|BrightImageData|bright` (`REF|BrightImageData|bright`),
  KEY `REF|NormImageData|norm` (`REF|NormImageData|norm`),
  KEY `REF|PresetData|preset` (`REF|PresetData|preset`),
  KEY `REF|AcquisitionImageTargetData|target` (`REF|AcquisitionImageTargetData|target`),
  KEY `REF|EMTargetData|emtarget` (`REF|EMTargetData|emtarget`),
  KEY `REF|GridData|grid` (`REF|GridData|grid`),
  KEY `REF|SpotWellMapData|spotmap` (`REF|SpotWellMapData|spotmap`),
  KEY `REF|TiltSeriesData|tilt series` (`REF|TiltSeriesData|tilt series`),
  KEY `REF|MoverParamsData|mover` (`REF|MoverParamsData|mover`)
) ENGINE=MyISAM AUTO_INCREMENT=9 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AcquisitionImageData`
--

LOCK TABLES `AcquisitionImageData` WRITE;
/*!40000 ALTER TABLE `AcquisitionImageData` DISABLE KEYS */;
INSERT INTO `AcquisitionImageData` VALUES (1,'2015-10-05 17:02:57',2,'06jul12a_00015gr_00028sq_00004hl_00002en.mrc',NULL,NULL,'UploadImage','06jul12a_00015gr_00028sq_00004hl_00002en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(2,'2015-10-05 17:02:58',2,'06jul12a_00015gr_00028sq_00023hl_00002en.mrc',NULL,NULL,'UploadImage','06jul12a_00015gr_00028sq_00023hl_00002en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(3,'2015-10-05 17:02:58',2,'06jul12a_00015gr_00028sq_00023hl_00004en.mrc',NULL,NULL,'UploadImage','06jul12a_00015gr_00028sq_00023hl_00004en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(4,'2015-10-05 17:02:58',2,'06jul12a_00022gr_00013sq_00002hl_00004en.mrc',NULL,NULL,'UploadImage','06jul12a_00022gr_00013sq_00002hl_00004en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(5,'2015-10-05 17:02:58',2,'06jul12a_00022gr_00013sq_00003hl_00005en.mrc',NULL,NULL,'UploadImage','06jul12a_00022gr_00013sq_00003hl_00005en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(6,'2015-10-05 17:02:59',2,'06jul12a_00022gr_00037sq_00025hl_00004en.mrc',NULL,NULL,'UploadImage','06jul12a_00022gr_00037sq_00025hl_00004en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(7,'2015-10-05 17:02:59',2,'06jul12a_00022gr_00037sq_00025hl_00005en.mrc',NULL,NULL,'UploadImage','06jul12a_00022gr_00037sq_00025hl_00005en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(8,'2015-10-05 17:02:59',2,'06jul12a_00035gr_00063sq_00012hl_00004en.mrc',NULL,NULL,'UploadImage','06jul12a_00035gr_00063sq_00012hl_00004en',NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `AcquisitionImageData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AcquisitionSettingsData`
--

DROP TABLE IF EXISTS `AcquisitionSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AcquisitionSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `correct image` tinyint(1) DEFAULT NULL,
  `SEQ|preset order` text,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `move type` text,
  `save image` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `display image` tinyint(1) DEFAULT NULL,
  `duplicate targets` tinyint(1) DEFAULT NULL,
  `wait for process` tinyint(1) DEFAULT NULL,
  `duplicate target type` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `wait time` double DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `adjust for drift` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `process target type` text,
  `save integer` int(20) DEFAULT NULL,
  `drift between` int(20) DEFAULT NULL,
  `final image shift` int(20) DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `wait for reference` int(20) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `adjust for transform` text,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `use parent mover` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `park after list` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=21 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AcquisitionSettingsData`
--

LOCK TABLES `AcquisitionSettingsData` WRITE;
/*!40000 ALTER TABLE `AcquisitionSettingsData` DISABLE KEYS */;
INSERT INTO `AcquisitionSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'[u\'gr\']',0,'stage position',1,1.5,1,NULL,0,NULL,1,'Grid',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(2,'2015-09-28 19:56:33',1,'[u\'sq\']',0,'stage position',1,1.5,1,NULL,1,NULL,1,'Square',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(3,'2015-09-28 19:56:33',1,'[u\'rsq\']',0,'stage position',1,1.5,1,NULL,1,NULL,1,'RCT Square',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(4,'2015-09-28 19:56:33',1,'[u\'hl\']',1,'stage position',1,1.5,1,NULL,1,NULL,1,'Hole',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(5,'2015-09-28 19:56:33',1,'[u\'hl\']',0,'stage position',1,2.5,1,NULL,0,NULL,1,'Preview',0,1,NULL,1,'presets manager',1e-06,'preview',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(6,'2015-09-28 19:56:33',1,'[u\'en\', u\'ef\']',1,'image shift',1,2.5,1,NULL,0,NULL,1,'Exposure',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,1,0,0,'Continue',65536,50,0,0,0,0,0,0,0),(7,'2015-09-28 19:56:33',1,'[u\'sq\']',0,'stage position',1,2.5,1,NULL,0,NULL,1,'Square Q',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(8,'2015-09-28 19:56:33',1,'[u\'hl\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'Hole Q',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(9,'2015-09-28 19:56:33',1,'[u\'preview\']',0,'stage position',1,2.5,1,NULL,0,NULL,1,'Tomography Preview',0,1,NULL,1,'presets manager',0,'preview',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(10,'2015-09-28 19:56:33',1,'[u\'hl\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'Final Section',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',1,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(11,'2015-09-28 19:56:33',1,'[u\'hl\']',1,'stage position',1,2.5,1,NULL,1,NULL,1,'Subsquare',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(12,'2015-09-28 19:56:33',1,'[u\'sq\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'Centered Square',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(13,'2015-09-28 19:56:33',1,'[u\'sq\']',0,'stage position',1,2.5,1,NULL,1,NULL,1,'Rough Tissue',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(14,'2015-09-28 19:56:33',1,'[u\'hl\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'Final Raster',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',1,1,NULL,0,1,'Continue',65536,50,0,0,0,0,NULL,0,0),(15,'2015-09-28 19:56:33',1,'[u\'gr\']',0,'stage position',1,2.5,1,NULL,1,NULL,1,'Grid Survey',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(16,'2015-09-28 19:56:33',1,'[u\'hl\']',0,'stage position',1,2.5,1,NULL,0,NULL,1,'Mid Mag Survey',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(17,'2015-09-28 19:56:33',1,'[u\'sq\']',0,'stage position',1,2.5,1,NULL,1,NULL,1,'Reacquisition',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(18,'2015-09-28 19:56:33',1,'[u\'en\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'High Mag Acquisition',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'one',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(19,'2015-09-28 19:56:33',1,'[u\'en\']',1,'stage position',1,2.5,1,NULL,0,NULL,1,'Exposure MultiMove',0,1,NULL,1,'navigator',1e-07,'acquisition',0,0,0,5e-07,1,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,0,0,0),(20,'2015-09-28 19:56:33',1,'[u\'hl\']',0,'stage position',1,2.5,1,NULL,0,NULL,1,'Align Parent Image',0,1,NULL,1,'presets manager',0,'acquisition',0,0,0,0.001,0,NULL,'no',0,0,NULL,0,0,'Continue',65536,50,0,0,0,0,0,0,0);
/*!40000 ALTER TABLE `AcquisitionSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `AlignmentManagerSettingsData`
--

DROP TABLE IF EXISTS `AlignmentManagerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AlignmentManagerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `bypass` tinyint(1) DEFAULT NULL,
  `reset a` tinyint(1) DEFAULT NULL,
  `reset z` tinyint(1) DEFAULT NULL,
  `reset xy` tinyint(1) DEFAULT NULL,
  `repeat time` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AlignmentManagerSettingsData`
--

LOCK TABLES `AlignmentManagerSettingsData` WRITE;
/*!40000 ALTER TABLE `AlignmentManagerSettingsData` DISABLE KEYS */;
INSERT INTO `AlignmentManagerSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Align Manager',1,0,0,0,0,3600);
/*!40000 ALTER TABLE `AlignmentManagerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApplicationData`
--

DROP TABLE IF EXISTS `ApplicationData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApplicationData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `version` int(20) DEFAULT NULL,
  `hide` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApplicationData`
--

LOCK TABLES `ApplicationData` WRITE;
/*!40000 ALTER TABLE `ApplicationData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApplicationData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BeamFixerSettingsData`
--

DROP TABLE IF EXISTS `BeamFixerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BeamFixerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` int(20) DEFAULT NULL,
  `move type` text,
  `pause time` double DEFAULT NULL,
  `interval time` double DEFAULT NULL,
  `override preset` int(20) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  `SUBD|stage position|x` double DEFAULT NULL,
  `SUBD|stage position|y` double DEFAULT NULL,
  `SUBD|stage position|z` double DEFAULT NULL,
  `SEQ|correction presets` text,
  `shift step` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BeamFixerSettingsData`
--

LOCK TABLES `BeamFixerSettingsData` WRITE;
/*!40000 ALTER TABLE `BeamFixerSettingsData` DISABLE KEYS */;
INSERT INTO `BeamFixerSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Fix Beam',1,'stage position',3,3600,0,3,'None','None',0,0,0,'[u\'fc\', u\'fa\', u\'en\', u\'ef\']',25);
/*!40000 ALTER TABLE `BeamFixerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BeamTiltCalibratorSettingsData`
--

DROP TABLE IF EXISTS `BeamTiltCalibratorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BeamTiltCalibratorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `correlation type` text,
  `defocus beam tilt` double DEFAULT NULL,
  `first defocus` double DEFAULT NULL,
  `second defocus` double DEFAULT NULL,
  `stig beam tilt` double DEFAULT NULL,
  `stig delta` double DEFAULT NULL,
  `measure beam tilt` double DEFAULT NULL,
  `correct tilt` tinyint(1) DEFAULT NULL,
  `settling time` double DEFAULT NULL,
  `comafree beam tilt` double DEFAULT NULL,
  `comafree misalign` double DEFAULT NULL,
  `imageshift coma tilt` double DEFAULT NULL,
  `imageshift coma step` double DEFAULT NULL,
  `imageshift coma number` int(20) DEFAULT NULL,
  `imageshift coma repeat` int(20) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BeamTiltCalibratorSettingsData`
--

LOCK TABLES `BeamTiltCalibratorSettingsData` WRITE;
/*!40000 ALTER TABLE `BeamTiltCalibratorSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `BeamTiltCalibratorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BeamTiltFixerSettingsData`
--

DROP TABLE IF EXISTS `BeamTiltFixerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BeamTiltFixerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `SEQ|preset order` text,
  `process target type` text,
  `park after list` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `move type` text,
  `correct image` tinyint(1) DEFAULT NULL,
  `display image` tinyint(1) DEFAULT NULL,
  `save image` tinyint(1) DEFAULT NULL,
  `wait for process` tinyint(1) DEFAULT NULL,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `wait for reference` tinyint(1) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `wait time` double DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `adjust for transform` text,
  `drift between` tinyint(1) DEFAULT NULL,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `final image shift` tinyint(1) DEFAULT NULL,
  `save integer` tinyint(1) DEFAULT NULL,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `beam tilt` double DEFAULT NULL,
  `min threshold` double DEFAULT NULL,
  `max threshold` double DEFAULT NULL,
  `correct` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BeamTiltFixerSettingsData`
--

LOCK TABLES `BeamTiltFixerSettingsData` WRITE;
/*!40000 ALTER TABLE `BeamTiltFixerSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `BeamTiltFixerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BeamTiltImagerSettingsData`
--

DROP TABLE IF EXISTS `BeamTiltImagerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BeamTiltImagerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `correct image` tinyint(1) DEFAULT NULL,
  `SEQ|preset order` text,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `move type` text,
  `save image` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `display image` tinyint(1) DEFAULT NULL,
  `duplicate targets` tinyint(1) DEFAULT NULL,
  `wait for process` tinyint(1) DEFAULT NULL,
  `duplicate target type` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `wait time` double DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `adjust for drift` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `process target type` text,
  `save integer` int(20) DEFAULT NULL,
  `drift between` int(20) DEFAULT NULL,
  `final image shift` int(20) DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `wait for reference` int(20) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `adjust for transform` text,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `park after list` tinyint(1) DEFAULT NULL,
  `beam tilt` double DEFAULT NULL,
  `beam tilt count` int(20) DEFAULT NULL,
  `sites` int(20) DEFAULT NULL,
  `startangle` double DEFAULT NULL,
  `tableau type` text,
  `tableau binning` int(20) DEFAULT NULL,
  `tableau split` int(20) DEFAULT NULL,
  `correlation type` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BeamTiltImagerSettingsData`
--

LOCK TABLES `BeamTiltImagerSettingsData` WRITE;
/*!40000 ALTER TABLE `BeamTiltImagerSettingsData` DISABLE KEYS */;
INSERT INTO `BeamTiltImagerSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'[u\'fc\']',0,'image shift',1,2.5,1,NULL,0,NULL,1,'Beam Tilt Image',0,1,NULL,1,'presets manager',0,'acquisition',0,0,NULL,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0,0.005,1,4,0,'beam tilt series-power',2,8,'phase');
/*!40000 ALTER TABLE `BeamTiltImagerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BindingSpecData`
--

DROP TABLE IF EXISTS `BindingSpecData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BindingSpecData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `event class string` text,
  `from node alias` text,
  `to node alias` text,
  `REF|ApplicationData|application` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApplicationData|application` (`REF|ApplicationData|application`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BindingSpecData`
--

LOCK TABLES `BindingSpecData` WRITE;
/*!40000 ALTER TABLE `BindingSpecData` DISABLE KEYS */;
/*!40000 ALTER TABLE `BindingSpecData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `BlobFinderSettingsData`
--

DROP TABLE IF EXISTS `BlobFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `BlobFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `on` tinyint(1) DEFAULT NULL,
  `max` int(20) DEFAULT NULL,
  `min size` int(20) DEFAULT NULL,
  `max size` int(20) DEFAULT NULL,
  `min mean` double DEFAULT NULL,
  `min stdev` double DEFAULT NULL,
  `border` int(20) DEFAULT NULL,
  `max mean` double DEFAULT NULL,
  `max stdev` double DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `BlobFinderSettingsData`
--

LOCK TABLES `BlobFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `BlobFinderSettingsData` DISABLE KEYS */;
INSERT INTO `BlobFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',NULL,100,10,10000,1000,10,0,20000,500,1,NULL,0);
/*!40000 ALTER TABLE `BlobFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CameraEMData`
--

DROP TABLE IF EXISTS `CameraEMData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CameraEMData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `system time` double DEFAULT NULL,
  `SUBD|dimension|x` int(20) DEFAULT NULL,
  `SUBD|dimension|y` int(20) DEFAULT NULL,
  `SUBD|binning|x` int(20) DEFAULT NULL,
  `SUBD|binning|y` int(20) DEFAULT NULL,
  `binned multiplier` double DEFAULT NULL,
  `exposure time` double DEFAULT NULL,
  `exposure type` text,
  `exposure timestamp` double DEFAULT NULL,
  `inserted` tinyint(1) DEFAULT '0',
  `dump` tinyint(1) DEFAULT '0',
  `energy filtered` tinyint(1) DEFAULT '0',
  `energy filter` tinyint(1) DEFAULT '0',
  `energy filter width` double DEFAULT NULL,
  `nframes` int(20) DEFAULT NULL,
  `save frames` tinyint(1) DEFAULT '0',
  `align frames` tinyint(1) DEFAULT '0',
  `align filter` text,
  `frames name` text,
  `frame time` double DEFAULT NULL,
  `frame flip` tinyint(1) DEFAULT '0',
  `frame rotate` int(20) DEFAULT NULL,
  `temperature` double DEFAULT NULL,
  `temperature status` text,
  `readout delay` int(20) DEFAULT NULL,
  `gain index` int(20) DEFAULT NULL,
  `system corrected` tinyint(1) DEFAULT '0',
  `REF|InstrumentData|ccdcamera` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|InstrumentData|ccdcamera` (`REF|InstrumentData|ccdcamera`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CameraEMData`
--

LOCK TABLES `CameraEMData` WRITE;
/*!40000 ALTER TABLE `CameraEMData` DISABLE KEYS */;
INSERT INTO `CameraEMData` VALUES (1,'2015-10-05 17:02:57',2,NULL,4096,4096,1,1,NULL,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,0,NULL,NULL,NULL,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,3);
/*!40000 ALTER TABLE `CameraEMData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CameraSettingsData`
--

DROP TABLE IF EXISTS `CameraSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CameraSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `exposure time` double DEFAULT NULL,
  `SUBD|dimension|x` int(20) DEFAULT NULL,
  `SUBD|dimension|y` int(20) DEFAULT NULL,
  `SUBD|offset|x` int(20) DEFAULT NULL,
  `SUBD|offset|y` int(20) DEFAULT NULL,
  `SUBD|binning|x` int(20) DEFAULT NULL,
  `SUBD|binning|y` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CameraSettingsData`
--

LOCK TABLES `CameraSettingsData` WRITE;
/*!40000 ALTER TABLE `CameraSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `CameraSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CenterTargetFilterSettingsData`
--

DROP TABLE IF EXISTS `CenterTargetFilterSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CenterTargetFilterSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `bypass` tinyint(1) DEFAULT NULL,
  `limit` int(20) DEFAULT NULL,
  `target type` text,
  `user check` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CenterTargetFilterSettingsData`
--

LOCK TABLES `CenterTargetFilterSettingsData` WRITE;
/*!40000 ALTER TABLE `CenterTargetFilterSettingsData` DISABLE KEYS */;
INSERT INTO `CenterTargetFilterSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Square Target Filtering',1,0,1,'acquisition',1);
/*!40000 ALTER TABLE `CenterTargetFilterSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ClickTargetFinderSettingsData`
--

DROP TABLE IF EXISTS `ClickTargetFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ClickTargetFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `wait for done` tinyint(1) DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `ignore images` tinyint(1) DEFAULT NULL,
  `no resubmit` tinyint(1) DEFAULT NULL,
  `name` text,
  `queue` tinyint(1) DEFAULT NULL,
  `user check` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `queue drift` tinyint(1) DEFAULT NULL,
  `sort target` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  `skip` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ClickTargetFinderSettingsData`
--

LOCK TABLES `ClickTargetFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `ClickTargetFinderSettingsData` DISABLE KEYS */;
INSERT INTO `ClickTargetFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',1,1,0,0,'Hole Targeting',1,1,1,1,0,0,0),(2,'2015-09-28 19:56:33',1,1,0,0,'Tomography Targeting',1,1,1,1,0,0,0);
/*!40000 ALTER TABLE `ClickTargetFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `CorrectorSettingsData`
--

DROP TABLE IF EXISTS `CorrectorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `CorrectorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `despike size` int(20) DEFAULT NULL,
  `despike threshold` double DEFAULT NULL,
  `despike` tinyint(1) DEFAULT NULL,
  `n average` int(20) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `combine` text,
  `clip min` double DEFAULT NULL,
  `clip max` double DEFAULT NULL,
  `channels` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `CorrectorSettingsData`
--

LOCK TABLES `CorrectorSettingsData` WRITE;
/*!40000 ALTER TABLE `CorrectorSettingsData` DISABLE KEYS */;
INSERT INTO `CorrectorSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Correction',11,3.5,0,3,2,'None','None',1,'average',0,65536,NULL);
/*!40000 ALTER TABLE `CorrectorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DTFinderSettingsData`
--

DROP TABLE IF EXISTS `DTFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DTFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` int(20) DEFAULT NULL,
  `wait for done` int(20) DEFAULT NULL,
  `ignore images` int(20) DEFAULT NULL,
  `queue` int(20) DEFAULT NULL,
  `user check` int(20) DEFAULT NULL,
  `queue drift` int(20) DEFAULT NULL,
  `sort target` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  `skip` int(20) DEFAULT NULL,
  `image filename` text,
  `REF|LowPassFilterSettingsData|edge lpf` int(20) DEFAULT NULL,
  `edge` int(20) DEFAULT NULL,
  `edge type` text,
  `edge log size` int(20) DEFAULT NULL,
  `edge log sigma` double DEFAULT NULL,
  `edge absolute` int(20) DEFAULT NULL,
  `edge threshold` double DEFAULT NULL,
  `template type` text,
  `REF|LowPassFilterSettingsData|template lpf` int(20) DEFAULT NULL,
  `threshold` double DEFAULT NULL,
  `threshold method` text,
  `blobs border` int(20) DEFAULT NULL,
  `blobs max` int(20) DEFAULT NULL,
  `blobs max size` int(20) DEFAULT NULL,
  `blobs min size` int(20) DEFAULT NULL,
  `lattice spacing` double DEFAULT NULL,
  `lattice tolerance` double DEFAULT NULL,
  `lattice hole radius` double DEFAULT NULL,
  `lattice zero thickness` double DEFAULT NULL,
  `ice min mean` double DEFAULT NULL,
  `ice max mean` double DEFAULT NULL,
  `ice max std` double DEFAULT NULL,
  `focus hole` text,
  `target template` int(20) DEFAULT NULL,
  `focus template thickness` int(20) DEFAULT NULL,
  `focus stats radius` int(20) DEFAULT NULL,
  `focus min mean thickness` double DEFAULT NULL,
  `focus max mean thickness` double DEFAULT NULL,
  `focus max stdev thickness` double DEFAULT NULL,
  `template diameter` int(20) DEFAULT NULL,
  `file diameter` int(20) DEFAULT NULL,
  `template filename` text,
  `template size` int(20) DEFAULT NULL,
  `correlation lpf` double DEFAULT NULL,
  `correlation type` text,
  `angle increment` double DEFAULT NULL,
  `rotate` int(20) DEFAULT NULL,
  `snr threshold` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|LowPassFilterSettingsData|edge lpf` (`REF|LowPassFilterSettingsData|edge lpf`),
  KEY `REF|LowPassFilterSettingsData|template lpf` (`REF|LowPassFilterSettingsData|template lpf`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DTFinderSettingsData`
--

LOCK TABLES `DTFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `DTFinderSettingsData` DISABLE KEYS */;
INSERT INTO `DTFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Tissue Centering',1,1,0,1,1,1,0,0,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,100,1.3,'phase',5,0,6);
/*!40000 ALTER TABLE `DTFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `DoseCalibratorSettingsData`
--

DROP TABLE IF EXISTS `DoseCalibratorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `DoseCalibratorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `correlation type` text,
  `beam diameter` double DEFAULT NULL,
  `scale factor` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `DoseCalibratorSettingsData`
--

LOCK TABLES `DoseCalibratorSettingsData` WRITE;
/*!40000 ALTER TABLE `DoseCalibratorSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `DoseCalibratorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ExposureFixerSettingsData`
--

DROP TABLE IF EXISTS `ExposureFixerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ExposureFixerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `SEQ|correction presets` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `move type` text,
  `pause time` double DEFAULT NULL,
  `interval time` double DEFAULT NULL,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `required dose` double DEFAULT NULL,
  `max exposure time` int(20) DEFAULT NULL,
  `SUBD|stage position|x` double DEFAULT NULL,
  `SUBD|stage position|y` double DEFAULT NULL,
  `SUBD|stage position|z` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `isdefault` (`isdefault`),
  KEY `override preset` (`override preset`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ExposureFixerSettingsData`
--

LOCK TABLES `ExposureFixerSettingsData` WRITE;
/*!40000 ALTER TABLE `ExposureFixerSettingsData` DISABLE KEYS */;
INSERT INTO `ExposureFixerSettingsData` VALUES (1,'2015-09-28 19:56:33','[u\'en\', u\'fa\']',1,'Fix Exposure Time',1,'stage position',3,3600,0,1,20,1000,0,0,0);
/*!40000 ALTER TABLE `ExposureFixerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FocusSequenceData`
--

DROP TABLE IF EXISTS `FocusSequenceData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FocusSequenceData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `node name` text,
  `SEQ|sequence` text,
  `isdefault` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FocusSequenceData`
--

LOCK TABLES `FocusSequenceData` WRITE;
/*!40000 ALTER TABLE `FocusSequenceData` DISABLE KEYS */;
INSERT INTO `FocusSequenceData` VALUES (1,'2015-09-28 19:56:33',1,'Focus','[\'Defocus1\', \'Defocus2\', \'Manual_after\']',1),(2,'2015-09-28 19:56:33',1,'Z Focus','[u\'Stage_Tilt_Rough\', u\'Stage_Tilt_Fine\', \'Manual_after\']',1),(3,'2015-09-28 19:56:33',1,'Tomo Focus','[u\'Stage_Tilt_Fine1\', \'Stage_Tilt_Fine2\', \'Beam_Tilt_Fine\', \'Manual_after\']',1),(4,'2015-09-28 19:56:33',1,'Tomo Z Focus','[u\'Stage_Tilt_Rough\', \'Stage_Tilt_Fine\', \'Beam_Tilt_Auto\', \'Manual_after\']',1),(5,'2015-09-28 19:56:33',1,'RCT Focus','[u\'Z_to_Eucentric\', u\'Def_to_Eucentric\']',1),(6,'2015-09-28 19:56:33',1,'Section Z Focus','[u\'Stage_Tilt_Fine\', u\'Stage_Tilt_High\']',1),(7,'2015-09-28 19:56:33',1,'Grid Focus','[u\'Stage_Wobble_Rough\']',1),(8,'2015-09-28 19:56:33',1,'Section Focus','[u\'Stage_Wobble_Rough\', u\'Stage_Wobble_Fine\']',1),(9,'2015-09-28 19:56:33',1,'Screen Z Focus','[u\'Rough\', u\'Medium\', u\'Fine\']',1),(10,'2015-09-28 19:56:33',1,'Align Focus','[u\'Stage Tilt Fine\', u\'Beam Tilt 1\', u\'Beam Tilt 2\', u\'Manual after\']',1);
/*!40000 ALTER TABLE `FocusSequenceData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FocusSettingData`
--

DROP TABLE IF EXISTS `FocusSettingData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FocusSettingData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `correlation type` text,
  `fit limit` double DEFAULT NULL,
  `focus method` text,
  `stig defocus min` double DEFAULT NULL,
  `drift threshold` double DEFAULT NULL,
  `stig correction` tinyint(1) DEFAULT NULL,
  `correction type` text,
  `check drift` tinyint(1) DEFAULT NULL,
  `preset name` text,
  `name` text,
  `stig defocus max` double DEFAULT NULL,
  `tilt` double DEFAULT NULL,
  `node name` text,
  `switch` tinyint(1) DEFAULT NULL,
  `delta min` double DEFAULT NULL,
  `delta max` double DEFAULT NULL,
  `reset defocus` tinyint(1) DEFAULT NULL,
  `isdefault` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=30 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FocusSettingData`
--

LOCK TABLES `FocusSettingData` WRITE;
/*!40000 ALTER TABLE `FocusSettingData` DISABLE KEYS */;
INSERT INTO `FocusSettingData` VALUES (1,'2015-09-28 19:56:33',1,'phase',1000,'Beam Tilt',2e-06,3e-10,0,'Stage Z',0,'fa','Z_to_Eucentric',4e-06,0.01,'Focus',0,0,2e-05,NULL,1),(2,'2015-09-28 19:56:33',1,'phase',5000,'Beam Tilt',2e-06,3e-10,0,'Defocus',1,'fa','Defocus1',4e-06,0.01,'Focus',1,0,2e-05,NULL,1),(3,'2015-09-28 19:56:33',1,'phase',5000,'Beam Tilt',2e-06,3e-10,0,'Defocus',0,'fa','Defocus2',4e-06,0.01,'Focus',0,0,2e-05,NULL,1),(4,'2015-09-28 19:56:33',1,'phase',5000,'Manual',2e-06,3e-10,0,'Defocus',0,'fc','Manual_after',4e-06,0.01,'Focus',1,0,0.001,NULL,1),(5,'2015-09-28 19:56:33',1,'phase',5000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'sq','Stage_Tilt_Rough',4e-06,0.0174532925199433,'Z Focus',0,0,0.0002,NULL,1),(6,'2015-09-28 19:56:33',1,'phase',5000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_Fine',4e-06,0.0174532925199433,'Z Focus',1,0,0.0002,NULL,1),(7,'2015-09-28 19:56:33',1,'phase',10000,'Manual',2e-06,3e-10,0,'Defocus',0,'fc','Manual_after',4e-06,0.01,'Z Focus',0,0,0.001,NULL,1),(8,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_Fine1',4e-06,0.0174532925199433,'Tomo Focus',1,0,0.0001,NULL,1),(9,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_Fine2',4e-06,0.0174532925199433,'Tomo Focus',1,0,5e-05,NULL,1),(10,'2015-09-28 19:56:33',1,'phase',5000,'Beam Tilt',2e-06,3e-10,0,'Defocus',1,'fa','Beam_Tilt_Fine',4e-06,0.01,'Tomo Focus',0,0,5e-05,NULL,1),(11,'2015-09-28 19:56:33',1,'phase',1000,'Manual',2e-06,3e-10,0,'Defocus',0,'fc','Manual_after',4e-06,0.01,'Tomo Focus',0,0,0.001,NULL,1),(12,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'sq','Stage_Tilt_Rough',4e-06,0.0174532925199433,'Tomo Z Focus',1,0,0.0002,NULL,1),(13,'2015-09-28 19:56:33',1,'phase',5000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_Fine',4e-06,0.0174532925199433,'Tomo Z Focus',1,0,0.0001,NULL,1),(14,'2015-09-28 19:56:33',1,'phase',5000,'Beam Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Beam_Tilt_Auto',4e-06,0.01,'Tomo Z Focus',0,0,5e-05,NULL,1),(15,'2015-09-28 19:56:33',1,'phase',1000,'Manual',2e-06,3e-10,0,'Defocus',0,'fc','Manual_after',4e-06,0.01,'Tomo Z Focus',0,0,0.001,NULL,1),(16,'2015-09-28 19:56:33',1,'phase',2000,'Beam Tilt',2e-06,3e-10,0,'Stage Z',0,'fa','Z_to_Eucentric',4e-06,0.01,'RCT Focus',1,0,2e-05,NULL,1),(17,'2015-09-28 19:56:33',1,'phase',2000,'Beam Tilt',2e-06,3e-10,0,'Defocus',0,'fa','Def_to_Eucentric',4e-06,0.01,'RCT Focus',1,0,2e-05,NULL,1),(18,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_Fine',4e-06,0.0174532925199433,'Section Z Focus',1,0,0.001,NULL,1),(19,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Tilt_High',4e-06,0.0349065850398866,'Section Z Focus',0,0,0.001,NULL,1),(20,'2015-09-28 19:56:33',1,'phase',1000,'Beam Tilt',2e-06,3e-10,0,'Defocus',0,'gr','Stage_Wobble_Rough',4e-06,0.01,'Grid Focus',1,0,0.001,NULL,1),(21,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'sq','Stage_Wobble_Rough',4e-06,0.0174532925199433,'Section Focus',1,0,0.001,NULL,1),(22,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage_Wobble_Fine',4e-06,0.0174532925199433,'Section Focus',1,0,0.0001,NULL,1),(23,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'sq','Rough',4e-06,0.0174532925199433,'Screen Z Focus',1,0,0.0002,NULL,1),(24,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Medium',4e-06,0.0174532925199433,'Screen Z Focus',0,0,0.0001,NULL,1),(25,'2015-09-28 19:56:33',1,'phase',2000,'Beam Tilt',2e-06,3e-10,0,'Stage Z',0,'fa','Fine',4e-06,0.01,'Screen Z Focus',1,0,2e-05,NULL,1),(26,'2015-09-28 19:56:33',1,'phase',1000,'Stage Tilt',2e-06,3e-10,0,'Stage Z',0,'hl','Stage Tilt Fine',4e-06,0.0174532925199433,'Align Focus',1,0,0.0001,NULL,1),(27,'2015-09-28 19:56:33',1,'phase',1000,'Beam Tilt',2e-06,3e-10,0,'Defocus',1,'fa','Beam Tilt 1',4e-06,0.01,'Align Focus',1,0,5e-05,NULL,1),(28,'2015-09-28 19:56:33',1,'phase',1000,'Beam Tilt',2e-06,3e-10,0,'Defocus',0,'fa','Beam Tilt 2',4e-06,0.01,'Align Focus',1,0,2e-05,NULL,1),(29,'2015-09-28 19:56:33',1,'phase',1000,'Manual',2e-06,3e-10,0,'Defocus',0,'fc','Manual after',4e-06,0.01,'Align Focus',1,0,0.001,NULL,1);
/*!40000 ALTER TABLE `FocusSettingData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FocuserSettingsData`
--

DROP TABLE IF EXISTS `FocuserSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FocuserSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `acquire final` tinyint(1) DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `SEQ|preset order` text,
  `save image` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `duplicate targets` tinyint(1) DEFAULT NULL,
  `melt time` double DEFAULT NULL,
  `name` text,
  `correct image` tinyint(1) DEFAULT NULL,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `display image` tinyint(1) DEFAULT NULL,
  `duplicate target type` text,
  `wait for process` tinyint(1) DEFAULT NULL,
  `move type` text,
  `adjust for drift` tinyint(1) DEFAULT NULL,
  `wait time` double DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `process target type` text,
  `melt preset` text,
  `manual focus preset` text,
  `save integer` int(20) DEFAULT NULL,
  `drift between` int(20) DEFAULT NULL,
  `final image shift` int(20) DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `wait for reference` tinyint(1) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `adjust for transform` text,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `park after list` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FocuserSettingsData`
--

LOCK TABLES `FocuserSettingsData` WRITE;
/*!40000 ALTER TABLE `FocuserSettingsData` DISABLE KEYS */;
INSERT INTO `FocuserSettingsData` VALUES (1,'2015-09-28 19:56:33',1,1,'[u\'fc\']',1,1.5,NULL,0,'Focus',1,0,1,NULL,0,'image shift',NULL,0,1,1,'presets manager',0,'focus','fc','fc',0,0,0,0.001,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(2,'2015-09-28 19:56:33',0,1,'[u\'hl\']',1,2.5,NULL,0,'Z Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','hl','fc',0,0,0,0.001,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(3,'2015-09-28 19:56:33',0,1,'[u\'fc\']',1,2.5,NULL,0,'Tomo Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','fc','fc',0,0,0,0.001,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(4,'2015-09-28 19:56:33',0,1,'[u\'hl\']',1,2.5,NULL,0,'Tomo Z Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','fc','fc',0,0,0,0,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(5,'2015-09-28 19:56:33',1,1,'[u\'fc\']',1,2.5,NULL,0,'RCT Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','fc','fc',0,0,0,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(6,'2015-09-28 19:56:33',0,1,'[u\'hl\']',1,2.5,NULL,0,'Section Z Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','hl','fc',0,0,0,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(7,'2015-09-28 19:56:33',0,1,'[u\'gr\']',1,2.5,NULL,0,'Grid Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','gr','gr',0,0,0,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(8,'2015-09-28 19:56:33',0,1,'[u\'hl\']',1,2.5,NULL,0,'Section Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','hl','fc',0,0,0,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(9,'2015-09-28 19:56:33',0,1,'[u\'fc\']',1,2.5,NULL,0,'Screen Z Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'focus','fc','fc',0,0,0,0.001,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0),(10,'2015-09-28 19:56:33',0,1,'[u\'fc\']',1,2.5,NULL,0,'Align Focus',1,0,1,NULL,0,'stage position',NULL,0,1,1,'presets manager',0,'acquisition','fc','fc',0,0,0,0.001,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,0,0,0);
/*!40000 ALTER TABLE `FocuserSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GonModelerSettingsData`
--

DROP TABLE IF EXISTS `GonModelerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GonModelerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `correlation type` text,
  `measure axis` text,
  `measure points` int(20) DEFAULT NULL,
  `measure interval` double DEFAULT NULL,
  `measure tolerance` double DEFAULT NULL,
  `model axis` text,
  `model magnification` int(20) DEFAULT NULL,
  `model terms` int(20) DEFAULT NULL,
  `model mag only` tinyint(1) DEFAULT NULL,
  `model tolerance` double DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GonModelerSettingsData`
--

LOCK TABLES `GonModelerSettingsData` WRITE;
/*!40000 ALTER TABLE `GonModelerSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `GonModelerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GridEntrySettingsData`
--

DROP TABLE IF EXISTS `GridEntrySettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GridEntrySettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `grid name` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GridEntrySettingsData`
--

LOCK TABLES `GridEntrySettingsData` WRITE;
/*!40000 ALTER TABLE `GridEntrySettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `GridEntrySettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `GroupData`
--

DROP TABLE IF EXISTS `GroupData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `GroupData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `name` text,
  `description` text,
  `REF|projectdata|privileges|privilege` int(11) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|projectdata|privileges|privilege` (`REF|projectdata|privileges|privilege`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `GroupData`
--

LOCK TABLES `GroupData` WRITE;
/*!40000 ALTER TABLE `GroupData` DISABLE KEYS */;
INSERT INTO `GroupData` VALUES (1,'2015-09-28 19:56:33','administrators','Administrator Group - Have all the power on project and user management.',1),(2,'2015-09-28 19:56:33','power users','Power User Group - view, edit, all the projects.',2),(3,'2015-09-28 19:56:33','users','Normal User Group - view, edit all owned and shared projects.',3),(4,'2015-09-28 19:56:33','guests','Guest Group - view own and share projects',4),(5,'2015-09-28 19:56:33','disabled','Disabled Group - locked users',5);
/*!40000 ALTER TABLE `GroupData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `HoleFinderSettingsData`
--

DROP TABLE IF EXISTS `HoleFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `HoleFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `lattice tolerance` double DEFAULT NULL,
  `blobs max` int(20) DEFAULT NULL,
  `lattice spacing` double DEFAULT NULL,
  `focus template thickness` tinyint(1) DEFAULT NULL,
  `skip` tinyint(1) DEFAULT NULL,
  `edge threshold` double DEFAULT NULL,
  `threshold` double DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `SEQ|focus template` text,
  `edge log sigma` double DEFAULT NULL,
  `target template` tinyint(1) DEFAULT NULL,
  `ignore images` tinyint(1) DEFAULT NULL,
  `REF|LowPassFilterSettingsData|template lpf` int(20) DEFAULT NULL,
  `edge absolute` tinyint(1) DEFAULT NULL,
  `ice min mean` double DEFAULT NULL,
  `edge log size` int(20) DEFAULT NULL,
  `wait for done` tinyint(1) DEFAULT NULL,
  `template type` text,
  `lattice hole radius` double DEFAULT NULL,
  `focus stats radius` int(20) DEFAULT NULL,
  `focus hole` text,
  `SEQ|acquisition template` text,
  `user check` tinyint(1) DEFAULT NULL,
  `edge type` text,
  `focus min mean thickness` double DEFAULT NULL,
  `blobs border` int(20) DEFAULT NULL,
  `SEQ|template rings` text,
  `ice max mean` double DEFAULT NULL,
  `REF|LowPassFilterSettingsData|edge lpf` int(20) DEFAULT NULL,
  `name` text,
  `focus max mean thickness` double DEFAULT NULL,
  `image filename` text,
  `ice max std` double DEFAULT NULL,
  `lattice zero thickness` double DEFAULT NULL,
  `blobs max size` int(20) DEFAULT NULL,
  `edge` tinyint(1) DEFAULT NULL,
  `focus max stdev thickness` double DEFAULT NULL,
  `queue` tinyint(1) DEFAULT NULL,
  `queue drift` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `threshold method` text,
  `sort target` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  `blobs min size` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|LowPassFilterSettingsData|template lpf` (`REF|LowPassFilterSettingsData|template lpf`),
  KEY `REF|LowPassFilterSettingsData|edge lpf` (`REF|LowPassFilterSettingsData|edge lpf`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `HoleFinderSettingsData`
--

LOCK TABLES `HoleFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `HoleFinderSettingsData` DISABLE KEYS */;
INSERT INTO `HoleFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',0.2,300,102,0,0,4000,240,1,'[(0, 0)]',1.4,0,0,4,0,0.28,9,1,'cross',15,10,'Good Hole','[(0, 0)]',1,'sobel',0.05,20,'[(35, 41)]',0.3,3,'Hole Targeting',0.5,NULL,0.2,52000,200,1,0.5,0,1,1,NULL,0,0,0),(2,'2015-09-28 19:56:33',0.1,1,150,1,0,6000,0.01,1,'[(220, 0), (150, 150), (0, 220), (-150, 150), (-220, 0), (-150, -150), (0, -220), (150, -150)]',1.4,1,0,NULL,0,0.01,9,1,'phase',15,100,'Off','[(0, 0)]',1,'sobel',0.05,20,'[(160, 170)]',0.2,NULL,'Exposure Targeting',0.5,NULL,0.2,26000,1000,1,0.5,0,1,1,NULL,0,0,0);
/*!40000 ALTER TABLE `HoleFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ImageCommentData`
--

DROP TABLE IF EXISTS `ImageCommentData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ImageCommentData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `REF|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `comment` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|AcquisitionImageData|image` (`REF|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ImageCommentData`
--

LOCK TABLES `ImageCommentData` WRITE;
/*!40000 ALTER TABLE `ImageCommentData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ImageCommentData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `InstrumentData`
--

DROP TABLE IF EXISTS `InstrumentData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `InstrumentData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `hostname` text,
  `type` text,
  `description` text,
  `scope` text,
  `camera` text,
  `camera size` int(11) DEFAULT NULL,
  `camera pixel size` double DEFAULT NULL,
  `cs` double DEFAULT NULL,
  `pixelmax` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `InstrumentData`
--

LOCK TABLES `InstrumentData` WRITE;
/*!40000 ALTER TABLE `InstrumentData` DISABLE KEYS */;
INSERT INTO `InstrumentData` VALUES (1,'2015-09-28 19:56:33','AppionTEM','appion','TEM',NULL,NULL,NULL,NULL,NULL,NULL,NULL),(2,'2015-10-05 17:02:57','AppionTEM','appion',NULL,NULL,NULL,NULL,NULL,NULL,0.002,NULL),(3,'2015-10-05 17:02:57','AppionCamera','appion',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `InstrumentData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `JAHCFinderSettingsData`
--

DROP TABLE IF EXISTS `JAHCFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `JAHCFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `lattice tolerance` double DEFAULT NULL,
  `blobs max` int(20) DEFAULT NULL,
  `blobs border` int(20) DEFAULT NULL,
  `lattice spacing` double DEFAULT NULL,
  `focus template thickness` tinyint(1) DEFAULT NULL,
  `skip` tinyint(1) DEFAULT NULL,
  `edge threshold` double DEFAULT NULL,
  `threshold` double DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `SEQ|focus template` text,
  `edge log sigma` double DEFAULT NULL,
  `target template` tinyint(1) DEFAULT NULL,
  `queue drift` tinyint(1) DEFAULT NULL,
  `ignore images` tinyint(1) DEFAULT NULL,
  `REF|LowPassFilterSettingsData|template lpf` int(20) DEFAULT NULL,
  `edge absolute` tinyint(1) DEFAULT NULL,
  `ice min mean` double DEFAULT NULL,
  `edge log size` int(20) DEFAULT NULL,
  `wait for done` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `template type` text,
  `lattice hole radius` double DEFAULT NULL,
  `focus stats radius` int(20) DEFAULT NULL,
  `focus hole` text,
  `SEQ|acquisition template` text,
  `template diameter` int(20) DEFAULT NULL,
  `user check` tinyint(1) DEFAULT NULL,
  `edge type` text,
  `focus min mean thickness` double DEFAULT NULL,
  `file diameter` int(20) DEFAULT NULL,
  `ice max mean` double DEFAULT NULL,
  `REF|LowPassFilterSettingsData|edge lpf` int(20) DEFAULT NULL,
  `name` text,
  `focus max mean thickness` double DEFAULT NULL,
  `image filename` text,
  `ice max std` double DEFAULT NULL,
  `lattice zero thickness` double DEFAULT NULL,
  `blobs max size` int(20) DEFAULT NULL,
  `queue` tinyint(1) DEFAULT NULL,
  `template filename` text,
  `edge` tinyint(1) DEFAULT NULL,
  `focus max stdev thickness` double DEFAULT NULL,
  `threshold method` text,
  `sort target` int(20) DEFAULT NULL,
  `blobs min size` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  `lattice extend` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|LowPassFilterSettingsData|template lpf` (`REF|LowPassFilterSettingsData|template lpf`),
  KEY `REF|LowPassFilterSettingsData|edge lpf` (`REF|LowPassFilterSettingsData|edge lpf`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `JAHCFinderSettingsData`
--

LOCK TABLES `JAHCFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `JAHCFinderSettingsData` DISABLE KEYS */;
INSERT INTO `JAHCFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',0.2,300,20,77,0,0,100,3,1,'[(0, 0)]',1.4,0,1,0,NULL,0,0.05,9,1,1,'cross',15,10,'Any Hole','[(0, 0)]',45,1,'sobel',0.05,168,0.16,5,'Hole Targeting',0.5,NULL,0.15,140,1000,0,NULL,1,0.5,'Threshold = mean + A * stdev',0,10,0,NULL),(2,'2015-09-28 19:56:33',0.1,1,20,150,1,0,100,0.0009,1,'[(-12, -144), (-144, 12), (12, 144), (144, -12)]',1.4,1,1,0,6,0,0.05,9,1,1,'phase',35,50,'Off','[(0, 35), (0, -35)]',115,1,'sobel',0.05,168,5,6,'Exposure Targeting Q',4,NULL,0.5,115,10000,1,NULL,1,0.1,'Threshold = A',0,10,0,'off'),(3,'2015-09-28 19:56:33',0.1,1,20,150,1,0,100,0.0009,1,'[(-12, -144), (-144, 12), (12, 144), (144, -12)]',1.4,1,1,0,6,0,0.05,9,1,1,'phase',35,50,'Off','[(0, 35), (0, -35)]',115,1,'sobel',0.05,168,5,6,'Exposure Targeting',4,NULL,0.5,115,10000,0,NULL,1,0.1,'Threshold = A',0,10,0,'off'),(4,'2015-09-28 19:56:33',0.1,1,20,150,1,1,100,1.5,1,'[(22, 128), (128, -22), (-22, -128), (-128, 22)]',1.4,1,1,0,4,0,0.05,9,1,1,'cross',30,100,'Off','[(0, -35), (0, 35)]',140,1,'sobel',0.1,168,0.2,4,'RCT Targeting',0.3,NULL,0.2,110,1000,1,NULL,1,0.1,'Threshold = mean + A * stdev',0,10,0,'off'),(5,'2015-09-28 19:56:33',0.1,300,20,110,0,0,100,2,1,'[]',1.4,0,1,0,4,0,0.15,9,1,1,'cross',30,10,'Off','[]',90,1,'sobel',0.05,168,0.35,4,'Square Targeting',0.5,NULL,0.3,200,1000,0,NULL,1,0.5,'Threshold = mean + A * stdev',0,10,0,'off');
/*!40000 ALTER TABLE `JAHCFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LaunchedApplicationData`
--

DROP TABLE IF EXISTS `LaunchedApplicationData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `LaunchedApplicationData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `REF|ApplicationData|application` int(20) DEFAULT NULL,
  `SEQ|launchers` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|ApplicationData|application` (`REF|ApplicationData|application`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LaunchedApplicationData`
--

LOCK TABLES `LaunchedApplicationData` WRITE;
/*!40000 ALTER TABLE `LaunchedApplicationData` DISABLE KEYS */;
/*!40000 ALTER TABLE `LaunchedApplicationData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `LowPassFilterSettingsData`
--

DROP TABLE IF EXISTS `LowPassFilterSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `LowPassFilterSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `on` tinyint(1) DEFAULT NULL,
  `sigma` double DEFAULT NULL,
  `size` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `LowPassFilterSettingsData`
--

LOCK TABLES `LowPassFilterSettingsData` WRITE;
/*!40000 ALTER TABLE `LowPassFilterSettingsData` DISABLE KEYS */;
INSERT INTO `LowPassFilterSettingsData` VALUES (1,'2015-09-28 19:56:33',0,1.4,5),(2,'2015-09-28 19:56:33',1,1.4,5),(3,'2015-09-28 19:56:33',NULL,1,NULL),(4,'2015-09-28 19:56:33',0,1,0),(5,'2015-09-28 19:56:33',1,1,5),(6,'2015-09-28 19:56:33',0,1,0);
/*!40000 ALTER TABLE `LowPassFilterSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MatrixCalibratorSettingsData`
--

DROP TABLE IF EXISTS `MatrixCalibratorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MatrixCalibratorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `correlation type` text,
  `image shift tolerance` double DEFAULT NULL,
  `image shift shift fraction` double DEFAULT NULL,
  `image shift n average` int(20) DEFAULT NULL,
  `image shift interval` double DEFAULT NULL,
  `image shift current as base` tinyint(1) DEFAULT NULL,
  `SUBD|image shift base|x` double DEFAULT NULL,
  `SUBD|image shift base|y` double DEFAULT NULL,
  `beam shift tolerance` double DEFAULT NULL,
  `beam shift shift fraction` double DEFAULT NULL,
  `beam shift n average` int(20) DEFAULT NULL,
  `beam shift interval` double DEFAULT NULL,
  `beam shift current as base` tinyint(1) DEFAULT NULL,
  `SUBD|beam shift base|x` double DEFAULT NULL,
  `SUBD|beam shift base|y` double DEFAULT NULL,
  `stage position tolerance` double DEFAULT NULL,
  `stage position shift fraction` double DEFAULT NULL,
  `stage position n average` int(20) DEFAULT NULL,
  `stage position interval` double DEFAULT NULL,
  `stage position current as base` tinyint(1) DEFAULT NULL,
  `SUBD|stage position base|x` double DEFAULT NULL,
  `SUBD|stage position base|y` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MatrixCalibratorSettingsData`
--

LOCK TABLES `MatrixCalibratorSettingsData` WRITE;
/*!40000 ALTER TABLE `MatrixCalibratorSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `MatrixCalibratorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MosaicClickTargetFinderSettingsData`
--

DROP TABLE IF EXISTS `MosaicClickTargetFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MosaicClickTargetFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `mosaic image on tile change` tinyint(1) DEFAULT NULL,
  `REF|BlobFinderSettingsData|blobs` int(20) DEFAULT NULL,
  `no resubmit` tinyint(1) DEFAULT NULL,
  `name` text,
  `scale image` tinyint(1) DEFAULT NULL,
  `wait for done` tinyint(1) DEFAULT NULL,
  `calibration parameter` text,
  `scale size` int(20) DEFAULT NULL,
  `threshold` double DEFAULT NULL,
  `REF|LowPassFilterSettingsData|lpf` int(20) DEFAULT NULL,
  `ignore images` tinyint(1) DEFAULT NULL,
  `queue` tinyint(1) DEFAULT NULL,
  `user check` tinyint(1) DEFAULT NULL,
  `queue drift` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `min region area` double DEFAULT NULL,
  `max region area` double DEFAULT NULL,
  `ve limit` double DEFAULT NULL,
  `raster spacing` double DEFAULT NULL,
  `raster angle` double DEFAULT NULL,
  `watchdone` tinyint(1) DEFAULT NULL,
  `targetpreset` text,
  `raster overlap` double DEFAULT NULL,
  `min threshold` double DEFAULT NULL,
  `max threshold` double DEFAULT NULL,
  `raster calibration` text,
  `black on white` tinyint(1) DEFAULT NULL,
  `axis ratio` double DEFAULT NULL,
  `limit region in sections` tinyint(1) DEFAULT NULL,
  `section area` double DEFAULT NULL,
  ` max sections` int(20) DEFAULT NULL,
  `section display` tinyint(1) DEFAULT NULL,
  `max sections` int(20) DEFAULT NULL,
  `section axis ratio` double DEFAULT NULL,
  `find section options` text,
  `adjust section area` double DEFAULT NULL,
  `region from centers` tinyint(1) DEFAULT NULL,
  `create when done` tinyint(1) DEFAULT NULL,
  `create on tile change` text,
  `autofinder` tinyint(1) DEFAULT NULL,
  `sort target` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  `skip` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|BlobFinderSettingsData|blobs` (`REF|BlobFinderSettingsData|blobs`),
  KEY `REF|LowPassFilterSettingsData|lpf` (`REF|LowPassFilterSettingsData|lpf`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MosaicClickTargetFinderSettingsData`
--

LOCK TABLES `MosaicClickTargetFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `MosaicClickTargetFinderSettingsData` DISABLE KEYS */;
INSERT INTO `MosaicClickTargetFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',1,NULL,1,0,'Square Targeting',1,0,'stage position',512,100,1,0,0,0,0,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'all',NULL,0,0,0),(2,'2015-09-28 19:56:33',1,NULL,NULL,0,'Raster Center Targeting',1,0,'stage position',512,100,NULL,0,0,0,1,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'all',NULL,0,0,0),(3,'2015-09-28 19:56:33',1,NULL,NULL,0,'Rough Tissue Targeting',1,0,'stage position',512,100,2,0,0,0,1,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'all',NULL,0,0,0),(4,'2015-09-28 19:56:33',1,NULL,1,0,'Atlas View',1,0,'stage position',512,100,1,0,0,0,1,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'all',NULL,0,0,0);
/*!40000 ALTER TABLE `MosaicClickTargetFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `MosaicTargetMakerSettingsData`
--

DROP TABLE IF EXISTS `MosaicTargetMakerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `MosaicTargetMakerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `max targets` int(20) DEFAULT NULL,
  `name` text,
  `max size` int(20) DEFAULT NULL,
  `overlap` double DEFAULT NULL,
  `label` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `radius` double DEFAULT NULL,
  `preset` text,
  `mosaic center` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `ignore request` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `MosaicTargetMakerSettingsData`
--

LOCK TABLES `MosaicTargetMakerSettingsData` WRITE;
/*!40000 ALTER TABLE `MosaicTargetMakerSettingsData` DISABLE KEYS */;
INSERT INTO `MosaicTargetMakerSettingsData` VALUES (1,'2015-09-28 19:56:33',128,'Grid Targeting',16384,1,NULL,1,0.0009,'gr','stage center',1,0),(2,'2015-09-28 19:56:33',128,'Grid Targeting Robot',16384,1,NULL,1,0.0005,'gr','stage center',1,0),(3,'2015-09-28 19:56:33',128,'Grid Survey Targeting',16384,1,NULL,1,0.0005,'gr','stage center',1,0);
/*!40000 ALTER TABLE `MosaicTargetMakerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `NavigatorSettingsData`
--

DROP TABLE IF EXISTS `NavigatorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `NavigatorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `move type` text,
  `check calibration` tinyint(1) DEFAULT NULL,
  `complete state` tinyint(1) DEFAULT NULL,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `precision` double DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `max error` double DEFAULT NULL,
  `cycle each` tinyint(1) DEFAULT NULL,
  `cycle after` tinyint(1) DEFAULT NULL,
  `final image shift` tinyint(1) DEFAULT NULL,
  `background readout` tinyint(1) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `NavigatorSettingsData`
--

LOCK TABLES `NavigatorSettingsData` WRITE;
/*!40000 ALTER TABLE `NavigatorSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `NavigatorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `NodeSpecData`
--

DROP TABLE IF EXISTS `NodeSpecData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `NodeSpecData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `class string` text,
  `alias` text,
  `launcher alias` text,
  `SEQ|dependencies` text,
  `REF|ApplicationData|application` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApplicationData|application` (`REF|ApplicationData|application`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `NodeSpecData`
--

LOCK TABLES `NodeSpecData` WRITE;
/*!40000 ALTER TABLE `NodeSpecData` DISABLE KEYS */;
/*!40000 ALTER TABLE `NodeSpecData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PixelSizeCalibrationData`
--

DROP TABLE IF EXISTS `PixelSizeCalibrationData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PixelSizeCalibrationData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `REF|InstrumentData|tem` int(20) DEFAULT NULL,
  `REF|InstrumentData|ccdcamera` int(20) DEFAULT NULL,
  `magnification` int(20) DEFAULT NULL,
  `high tension` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `comment` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|InstrumentData|tem` (`REF|InstrumentData|tem`),
  KEY `REF|InstrumentData|ccdcamera` (`REF|InstrumentData|ccdcamera`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PixelSizeCalibrationData`
--

LOCK TABLES `PixelSizeCalibrationData` WRITE;
/*!40000 ALTER TABLE `PixelSizeCalibrationData` DISABLE KEYS */;
INSERT INTO `PixelSizeCalibrationData` VALUES (1,'2015-10-05 17:02:57',2,2,3,100000,NULL,8.15e-11,'based on uploaded pixel size');
/*!40000 ALTER TABLE `PixelSizeCalibrationData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PixelSizeCalibratorSettingsData`
--

DROP TABLE IF EXISTS `PixelSizeCalibratorSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PixelSizeCalibratorSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `override preset` tinyint(1) DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `SUBD|instruments|ccdcamera` text,
  `SUBD|instruments|tem` text,
  `correlation type` text,
  `lattice a` double DEFAULT NULL,
  `lattice b` double DEFAULT NULL,
  `lattice gamma` double DEFAULT NULL,
  `h1` int(20) DEFAULT NULL,
  `k1` int(20) DEFAULT NULL,
  `h2` int(20) DEFAULT NULL,
  `k2` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PixelSizeCalibratorSettingsData`
--

LOCK TABLES `PixelSizeCalibratorSettingsData` WRITE;
/*!40000 ALTER TABLE `PixelSizeCalibratorSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `PixelSizeCalibratorSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PresetData`
--

DROP TABLE IF EXISTS `PresetData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PresetData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `number` int(20) DEFAULT NULL,
  `name` text,
  `magnification` int(20) DEFAULT NULL,
  `spot size` int(20) DEFAULT NULL,
  `intensity` double DEFAULT NULL,
  `defocus` double DEFAULT NULL,
  `defocus range min` double DEFAULT NULL,
  `defocus range max` double DEFAULT NULL,
  `exposure time` double DEFAULT NULL,
  `removed` tinyint(1) DEFAULT '0',
  `hasref` tinyint(1) DEFAULT '0',
  `dose` double DEFAULT NULL,
  `film` tinyint(1) DEFAULT '0',
  `REF|InstrumentData|tem` int(20) DEFAULT NULL,
  `REF|InstrumentData|ccdcamera` int(20) DEFAULT NULL,
  `tem energy filter` tinyint(1) DEFAULT '0',
  `tem energy filter width` double DEFAULT NULL,
  `energy filter` tinyint(1) DEFAULT '0',
  `energy filter width` double DEFAULT NULL,
  `pre exposure` double DEFAULT NULL,
  `skip` tinyint(1) DEFAULT '0',
  `alt channel` tinyint(1) DEFAULT '0',
  `save frames` tinyint(1) DEFAULT '0',
  `frame time` double DEFAULT NULL,
  `align frames` tinyint(1) DEFAULT '0',
  `align filter` text,
  `readout delay` int(20) DEFAULT NULL,
  `probe mode` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|InstrumentData|tem` (`REF|InstrumentData|tem`),
  KEY `REF|InstrumentData|ccdcamera` (`REF|InstrumentData|ccdcamera`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PresetData`
--

LOCK TABLES `PresetData` WRITE;
/*!40000 ALTER TABLE `PresetData` DISABLE KEYS */;
INSERT INTO `PresetData` VALUES (1,'2015-10-05 17:02:57',2,NULL,'upload',100000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,2,3,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `PresetData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `PresetsManagerSettingsData`
--

DROP TABLE IF EXISTS `PresetsManagerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `PresetsManagerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `xy only` tinyint(1) DEFAULT NULL,
  `stage always` tinyint(1) DEFAULT NULL,
  `cycle` tinyint(1) DEFAULT NULL,
  `optimize cycle` tinyint(1) DEFAULT NULL,
  `mag only` tinyint(1) DEFAULT NULL,
  `apply offset` tinyint(1) DEFAULT NULL,
  `blank` tinyint(1) DEFAULT NULL,
  `smallsize` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `PresetsManagerSettingsData`
--

LOCK TABLES `PresetsManagerSettingsData` WRITE;
/*!40000 ALTER TABLE `PresetsManagerSettingsData` DISABLE KEYS */;
INSERT INTO `PresetsManagerSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Presets Manager',1,1,1,1,1,1,0,0,0,1024);
/*!40000 ALTER TABLE `PresetsManagerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RCTAcquisitionSettingsData`
--

DROP TABLE IF EXISTS `RCTAcquisitionSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RCTAcquisitionSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `wait time` double DEFAULT NULL,
  `SEQ|preset order` text,
  `save image` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `adjust for drift` tinyint(1) DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `duplicate targets` tinyint(1) DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `name` text,
  `correct image` tinyint(1) DEFAULT NULL,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `tilt2` double DEFAULT NULL,
  `display image` tinyint(1) DEFAULT NULL,
  `tilt1` double DEFAULT NULL,
  `duplicate target type` text,
  `wait for process` tinyint(1) DEFAULT NULL,
  `move type` text,
  `minsize` double DEFAULT NULL,
  `sigma` double DEFAULT NULL,
  `maxsize` double DEFAULT NULL,
  `minstable` double DEFAULT NULL,
  `minperiod` double DEFAULT NULL,
  `stepsize` double DEFAULT NULL,
  `tilts` text,
  `process target type` text,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `blur` double DEFAULT NULL,
  `sharpen` double DEFAULT NULL,
  `drift threshold` double DEFAULT NULL,
  `drift preset` text,
  `save integer` int(20) DEFAULT NULL,
  `nsteps` int(20) DEFAULT NULL,
  `pause` double DEFAULT NULL,
  `medfilt` double DEFAULT NULL,
  `lowfilt` double DEFAULT NULL,
  `drift between` int(20) DEFAULT NULL,
  `final image shift` int(20) DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `wait for reference` tinyint(1) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `adjust for transform` text,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `park after list` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RCTAcquisitionSettingsData`
--

LOCK TABLES `RCTAcquisitionSettingsData` WRITE;
/*!40000 ALTER TABLE `RCTAcquisitionSettingsData` DISABLE KEYS */;
INSERT INTO `RCTAcquisitionSettingsData` VALUES (1,'2015-09-28 19:56:33',0,'[u\'en\']',1,2.5,NULL,1,NULL,1,1,'RCT',1,1,NULL,1,NULL,NULL,0,'stage position',50,NULL,0.8,NULL,NULL,15,'(-45, 0)','acquisition','navigator',6e-08,NULL,NULL,6e-10,'fa',0,NULL,1,2,1,0,0,5e-07,0,NULL,'no',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0);
/*!40000 ALTER TABLE `RCTAcquisitionSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RasterFinderSettingsData`
--

DROP TABLE IF EXISTS `RasterFinderSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RasterFinderSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `raster limit` int(20) DEFAULT NULL,
  `SEQ|acquisition constant template` text,
  `SEQ|focus constant template` text,
  `ice box size` double DEFAULT NULL,
  `user check` tinyint(1) DEFAULT NULL,
  `focus convolve` tinyint(1) DEFAULT NULL,
  `ice max mean` double DEFAULT NULL,
  `name` text,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `ignore images` tinyint(1) DEFAULT NULL,
  `acquisition convolve` tinyint(1) DEFAULT NULL,
  `image filename` text,
  `ice thickness` double DEFAULT NULL,
  `ice max std` double DEFAULT NULL,
  `SEQ|focus convolve template` text,
  `ice min mean` double DEFAULT NULL,
  `ice min std` double DEFAULT NULL,
  `wait for done` tinyint(1) DEFAULT NULL,
  `raster spacing` int(20) DEFAULT NULL,
  `SEQ|acquisition convolve template` text,
  `queue` tinyint(1) DEFAULT NULL,
  `queue drift` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `raster center on image` tinyint(1) DEFAULT NULL,
  `raster angle` double DEFAULT NULL,
  `raster center x` int(20) DEFAULT NULL,
  `raster center y` int(20) DEFAULT NULL,
  `select polygon` tinyint(1) DEFAULT NULL,
  `publish polygon` tinyint(1) DEFAULT NULL,
  `raster spacing asymm` int(20) DEFAULT NULL,
  `raster limit asymm` int(20) DEFAULT NULL,
  `raster symmetric` int(20) DEFAULT NULL,
  `sort target` int(20) DEFAULT NULL,
  `raster preset` text,
  `raster movetype` text,
  `raster overlap` double DEFAULT NULL,
  `skip` int(20) DEFAULT NULL,
  `allow append` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RasterFinderSettingsData`
--

LOCK TABLES `RasterFinderSettingsData` WRITE;
/*!40000 ALTER TABLE `RasterFinderSettingsData` DISABLE KEYS */;
INSERT INTO `RasterFinderSettingsData` VALUES (1,'2015-09-28 19:56:33',9,'[]','[(550, 512)]',15,1,0,0.3,'Subsquare Targeting',1,0,1,NULL,140,0.2,'[]',0.05,NULL,1,50,'[(0, 0)]',0,1,1,1,-103.37793736856,0,0,0,0,50,0,1,0,'hl','stage position',0,0,0),(2,'2015-09-28 19:56:33',5,'[]','[(256, 200)]',15,1,0,0.2,'Exposure Targeting',1,0,1,NULL,110,0.2,'[]',0.05,0,1,100,'[(0, 0)]',0,1,1,1,0,0,0,0,0,0,0,1,0,'gr','stage position',0,0,0),(3,'2015-09-28 19:56:33',1,'[]','[]',15,1,1,0.2,'Square Centering',1,0,1,NULL,1000,0.2,'[(0, 0)]',0.05,NULL,1,100,'[(0, 0)]',0,1,1,1,0,0,0,0,0,0,0,1,0,'en','stage position',0,1,0),(4,'2015-09-28 19:56:33',5,'[]','[(256, 240)]',15,1,0,0.2,'RCT Targeting',1,0,1,NULL,110,0.2,'[]',0.05,0,1,100,'[(0, 0)]',1,1,1,1,0,0,0,0,0,0,0,1,0,'en','stage position',0,0,0),(5,'2015-09-28 19:56:33',2,'[]','[]',15,1,0,0.5,'Mid Mag Survey Targeting',1,0,0,NULL,100,0.2,'[]',0.05,0,1,100,'[]',0,1,1,1,0,0,0,0,0,0,0,1,0,'hl','stage position',0,0,0),(6,'2015-09-28 19:56:33',3,'[]','[(256, 256)]',15,1,0,0.2,'High Mag Raster Targeting',1,0,0,NULL,1000,0.2,'[]',0.05,0,1,100,'[]',0,1,1,1,0,0,0,0,0,0,0,1,0,'gr','stage position',0,0,0);
/*!40000 ALTER TABLE `RasterFinderSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RasterTargetFilterSettingsData`
--

DROP TABLE IF EXISTS `RasterTargetFilterSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RasterTargetFilterSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `bypass` tinyint(1) DEFAULT NULL,
  `raster spacing` double DEFAULT NULL,
  `raster angle` double DEFAULT NULL,
  `raster preset` text,
  `raster movetype` text,
  `raster overlap` double DEFAULT NULL,
  `raster width` double DEFAULT NULL,
  `target type` text,
  `ellipse angle` double DEFAULT NULL,
  `ellipse a` double DEFAULT NULL,
  `ellipse b` double DEFAULT NULL,
  `user check` int(20) DEFAULT NULL,
  `raster offset` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RasterTargetFilterSettingsData`
--

LOCK TABLES `RasterTargetFilterSettingsData` WRITE;
/*!40000 ALTER TABLE `RasterTargetFilterSettingsData` DISABLE KEYS */;
INSERT INTO `RasterTargetFilterSettingsData` VALUES (1,'2015-09-28 19:56:33',1,'Raster Generation',1,0,20,0,'hl','stage position',0,NULL,'acquisition',0,2,2,1,0),(2,'2015-09-28 19:56:33',1,'Final Raster Targeting',1,0,50,0,'hl','stage position',0,NULL,'acquisition',0,2,2,1,0);
/*!40000 ALTER TABLE `RasterTargetFilterSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `RobotSettingsData`
--

DROP TABLE IF EXISTS `RobotSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `RobotSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `column pressure threshold` double DEFAULT NULL,
  `default Z position` double DEFAULT NULL,
  `simulate` tinyint(1) DEFAULT NULL,
  `turbo on` tinyint(1) DEFAULT NULL,
  `grid clear wait` tinyint(1) DEFAULT NULL,
  `pause` tinyint(1) DEFAULT NULL,
  `grid tray` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `RobotSettingsData`
--

LOCK TABLES `RobotSettingsData` WRITE;
/*!40000 ALTER TABLE `RobotSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `RobotSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScopeEMData`
--

DROP TABLE IF EXISTS `ScopeEMData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScopeEMData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `system time` double DEFAULT NULL,
  `magnification` int(20) DEFAULT NULL,
  `spot size` int(20) DEFAULT NULL,
  `intensity` double DEFAULT NULL,
  `defocus` double DEFAULT NULL,
  `focus` double DEFAULT NULL,
  `reset defocus` int(20) DEFAULT NULL,
  `screen current` double DEFAULT NULL,
  `beam blank` text,
  `corrected stage position` int(20) DEFAULT NULL,
  `SUBD|stage position|a` double DEFAULT NULL,
  `SUBD|stage position|x` double DEFAULT NULL,
  `SUBD|stage position|y` double DEFAULT NULL,
  `SUBD|stage position|z` double DEFAULT NULL,
  `holder type` text,
  `holder status` text,
  `stage status` text,
  `vacuum status` text,
  `column valves` text,
  `column pressure` double DEFAULT NULL,
  `turbo pump` text,
  `high tension` int(20) DEFAULT NULL,
  `main screen position` text,
  `main screen magnification` int(20) DEFAULT NULL,
  `small screen position` text,
  `low dose` text,
  `low dose mode` text,
  `film stock` int(20) DEFAULT NULL,
  `film exposure number` int(20) DEFAULT NULL,
  `pre film exposure` tinyint(1) DEFAULT '0',
  `post film exposure` tinyint(1) DEFAULT '0',
  `film exposure` tinyint(1) DEFAULT '0',
  `film exposure type` text,
  `film exposure time` double DEFAULT NULL,
  `film manual exposure time` double DEFAULT NULL,
  `film automatic exposure time` double DEFAULT NULL,
  `film text` text,
  `film user code` text,
  `film date type` text,
  `objective current` double DEFAULT NULL,
  `exp wait time` double DEFAULT NULL,
  `tem energy filtered` tinyint(1) DEFAULT '0',
  `tem energy filter` tinyint(1) DEFAULT '0',
  `tem energy filter width` double DEFAULT NULL,
  `probe mode` text,
  `REF|InstrumentData|tem` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|InstrumentData|tem` (`REF|InstrumentData|tem`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScopeEMData`
--

LOCK TABLES `ScopeEMData` WRITE;
/*!40000 ALTER TABLE `ScopeEMData` DISABLE KEYS */;
INSERT INTO `ScopeEMData` VALUES (1,'2015-10-05 17:02:57',2,NULL,100000,NULL,NULL,-1e-06,NULL,NULL,NULL,NULL,NULL,0,0,0,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,120000,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,2);
/*!40000 ALTER TABLE `ScopeEMData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SessionData`
--

DROP TABLE IF EXISTS `SessionData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SessionData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `REF|UserData|user` int(20) DEFAULT NULL,
  `image path` text,
  `comment` text,
  `hidden` tinyint(4) DEFAULT NULL,
  `REF|InstrumentData|instrument` int(20) DEFAULT NULL,
  `REF|GridHolderData|holder` int(20) DEFAULT NULL,
  `frame path` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|UserData|user` (`REF|UserData|user`),
  KEY `REF|GridHolderData|holder` (`REF|GridHolderData|holder`),
  FULLTEXT KEY `name` (`name`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SessionData`
--

LOCK TABLES `SessionData` WRITE;
/*!40000 ALTER TABLE `SessionData` DISABLE KEYS */;
INSERT INTO `SessionData` VALUES (1,'2015-09-28 19:56:33','importsettings20150928195633',1,NULL,'import default',1,NULL,NULL,NULL),(2,'2015-10-05 17:02:57','06jul12a',NULL,'/emg/data/leginon/06jul12a/rawdata','First test session with GroEL',NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `SessionData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `SetupWizardSettingsData`
--

DROP TABLE IF EXISTS `SetupWizardSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `SetupWizardSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `session type` text,
  `selected session` text,
  `limit` tinyint(1) DEFAULT NULL,
  `n limit` int(20) DEFAULT NULL,
  `connect` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `SetupWizardSettingsData`
--

LOCK TABLES `SetupWizardSettingsData` WRITE;
/*!40000 ALTER TABLE `SetupWizardSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `SetupWizardSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TiltRotateSettingsData`
--

DROP TABLE IF EXISTS `TiltRotateSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TiltRotateSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `bypass` tinyint(1) DEFAULT NULL,
  `tilts` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TiltRotateSettingsData`
--

LOCK TABLES `TiltRotateSettingsData` WRITE;
/*!40000 ALTER TABLE `TiltRotateSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `TiltRotateSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TomographySettingsData`
--

DROP TABLE IF EXISTS `TomographySettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TomographySettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `display image` tinyint(1) DEFAULT NULL,
  `SEQ|registration preset order` text,
  `wait time` double DEFAULT NULL,
  `SEQ|preset order` text,
  `tilt max` double DEFAULT NULL,
  `save image` tinyint(1) DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `adjust for drift` tinyint(1) DEFAULT NULL,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `duplicate targets` tinyint(1) DEFAULT NULL,
  `iterations` int(20) DEFAULT NULL,
  `cosine exposure` tinyint(1) DEFAULT NULL,
  `isdefault` tinyint(1) DEFAULT NULL,
  `tilt min` double DEFAULT NULL,
  `thickness value` double DEFAULT NULL,
  `run buffer cycle` tinyint(1) DEFAULT NULL,
  `correct image` tinyint(1) DEFAULT NULL,
  `move type` text,
  `wait for rejects` tinyint(1) DEFAULT NULL,
  `name` text,
  `align zero loss peak` tinyint(1) DEFAULT NULL,
  `xcf bin` int(20) DEFAULT NULL,
  `duplicate target type` text,
  `wait for process` tinyint(1) DEFAULT NULL,
  `tilt start` double DEFAULT NULL,
  `tilt step` double DEFAULT NULL,
  `dose` double DEFAULT NULL,
  `min exposure` double DEFAULT NULL,
  `max exposure` double DEFAULT NULL,
  `process target type` text,
  `mover` text,
  `move precision` double DEFAULT NULL,
  `equally sloped` tinyint(1) DEFAULT NULL,
  `equally sloped n` int(20) DEFAULT NULL,
  `measure dose` tinyint(1) DEFAULT NULL,
  `mean threshold` double DEFAULT NULL,
  `collection threshold` double DEFAULT NULL,
  `tilt pause time` double DEFAULT NULL,
  `measure defocus` tinyint(1) DEFAULT NULL,
  `integer` tinyint(1) DEFAULT NULL,
  `intscale` double DEFAULT NULL,
  `pausegroup` tinyint(1) DEFAULT NULL,
  `save integer` int(20) DEFAULT NULL,
  `model mag` text,
  `z0 error` double DEFAULT NULL,
  `phi` double DEFAULT NULL,
  `offset` double DEFAULT NULL,
  `fixed model` int(20) DEFAULT NULL,
  `offset2` double DEFAULT NULL,
  `phi2` double DEFAULT NULL,
  `use lpf` int(20) DEFAULT NULL,
  `drift between` int(20) DEFAULT NULL,
  `final image shift` int(20) DEFAULT NULL,
  `use wiener` int(20) DEFAULT NULL,
  `accept precision` double DEFAULT NULL,
  `wiener max tilt` double DEFAULT NULL,
  `use tilt` int(20) DEFAULT NULL,
  `fit data points` int(20) DEFAULT NULL,
  `taper size` int(20) DEFAULT NULL,
  `wait for reference` tinyint(1) DEFAULT NULL,
  `wait for transform` tinyint(1) DEFAULT NULL,
  `adjust for transform` text,
  `background` tinyint(1) DEFAULT NULL,
  `use parent tilt` tinyint(1) DEFAULT NULL,
  `adjust time by tilt` tinyint(1) DEFAULT NULL,
  `reset tilt` tinyint(1) DEFAULT NULL,
  `bad stats response` text,
  `high mean` double DEFAULT NULL,
  `low mean` double DEFAULT NULL,
  `emission off` tinyint(1) DEFAULT NULL,
  `target offset row` int(20) DEFAULT NULL,
  `target offset col` int(20) DEFAULT NULL,
  `correct image shift coma` tinyint(1) DEFAULT NULL,
  `pause between time` double DEFAULT NULL,
  `park after target` tinyint(1) DEFAULT NULL,
  `park after list` tinyint(1) DEFAULT NULL,
  `z0` double DEFAULT NULL,
  `use z0` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TomographySettingsData`
--

LOCK TABLES `TomographySettingsData` WRITE;
/*!40000 ALTER TABLE `TomographySettingsData` DISABLE KEYS */;
INSERT INTO `TomographySettingsData` VALUES (1,'2015-09-28 19:56:33',1,NULL,0,'[u\'tomo\']',60,1,2.5,NULL,1,NULL,1,NULL,1,-60,NULL,0,1,'stage position',1,'Tomography',0,1,NULL,0,0,1,200,0.025,2,'acquisition','navigator',6e-08,0,8,1,100,90,1,0,1,1,NULL,0,'custom values',2e-06,0,0,1,0,0,0,1,1,NULL,2e-07,NULL,1,4,10,0,NULL,'one',0,0,0,0,'Continue',65536,50,0,0,0,0,NULL,0,0,0,0);
/*!40000 ALTER TABLE `TomographySettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `TransformManagerSettingsData`
--

DROP TABLE IF EXISTS `TransformManagerSettingsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `TransformManagerSettingsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `isdefault` tinyint(1) DEFAULT NULL,
  `registration` text,
  `threshold` double DEFAULT NULL,
  `pause time` double DEFAULT NULL,
  `REF|CameraSettingsData|camera settings` int(20) DEFAULT NULL,
  `timeout` int(20) DEFAULT NULL,
  `min mag` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|CameraSettingsData|camera settings` (`REF|CameraSettingsData|camera settings`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `TransformManagerSettingsData`
--

LOCK TABLES `TransformManagerSettingsData` WRITE;
/*!40000 ALTER TABLE `TransformManagerSettingsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `TransformManagerSettingsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserData`
--

DROP TABLE IF EXISTS `UserData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `username` varchar(24) DEFAULT NULL,
  `firstname` varchar(24) DEFAULT NULL,
  `lastname` varchar(24) DEFAULT NULL,
  `password` char(32) DEFAULT NULL,
  `email` varchar(60) DEFAULT NULL,
  `REF|GroupData|group` int(20) DEFAULT NULL,
  `noleginon` tinyint(1) DEFAULT NULL,
  `advanced` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  UNIQUE KEY `username` (`username`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|GroupData|group` (`REF|GroupData|group`),
  KEY `email` (`email`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserData`
--

LOCK TABLES `UserData` WRITE;
/*!40000 ALTER TABLE `UserData` DISABLE KEYS */;
INSERT INTO `UserData` VALUES (1,'2015-09-28 19:56:33','administrator','Appion-Leginon','Administrator','80692cde4cd41c7aeaac4d86a4ad90c3','vossman77@yahoo.com',1,NULL,NULL),(2,'2015-09-28 19:56:33','anonymous','Public','User','294de3557d9d00b3d2d8a1e6aab028cf','vossman77@yahoo.com',4,NULL,NULL);
/*!40000 ALTER TABLE `UserData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ViewerImageStatus`
--

DROP TABLE IF EXISTS `ViewerImageStatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ViewerImageStatus` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|SessionData|session` int(11) DEFAULT NULL,
  `REF|AcquisitionImageData|image` int(11) DEFAULT NULL,
  `status` enum('hidden','visible','exemplar','trash') DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|SessionData|session` (`REF|SessionData|session`),
  KEY `REF|AcquisitionImageData|image` (`REF|AcquisitionImageData|image`),
  KEY `status` (`status`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ViewerImageStatus`
--

LOCK TABLES `ViewerImageStatus` WRITE;
/*!40000 ALTER TABLE `ViewerImageStatus` DISABLE KEYS */;
/*!40000 ALTER TABLE `ViewerImageStatus` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_cache`
--

DROP TABLE IF EXISTS `viewer_cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_cache` (
  `session` varchar(255) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_cache`
--

LOCK TABLES `viewer_cache` WRITE;
/*!40000 ALTER TABLE `viewer_cache` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_cache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_comment`
--

DROP TABLE IF EXISTS `viewer_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_comment` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `sessionId` int(11) DEFAULT NULL,
  `type` enum('rt','post') DEFAULT NULL,
  `imageId` int(11) DEFAULT NULL,
  `name` text,
  `comment` text,
  PRIMARY KEY (`id`),
  KEY `timestamp` (`timestamp`),
  KEY `sessionId` (`sessionId`),
  KEY `imageId` (`imageId`),
  KEY `type` (`type`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_comment`
--

LOCK TABLES `viewer_comment` WRITE;
/*!40000 ALTER TABLE `viewer_comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_del_image`
--

DROP TABLE IF EXISTS `viewer_del_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_del_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `username` varchar(50) DEFAULT NULL,
  `sessionId` int(11) DEFAULT NULL,
  `imageId` int(11) DEFAULT NULL,
  `status` enum('deleted','marked') DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `timestamp` (`timestamp`),
  KEY `username` (`username`),
  KEY `sessionId` (`sessionId`),
  KEY `imageId` (`imageId`),
  KEY `status` (`status`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_del_image`
--

LOCK TABLES `viewer_del_image` WRITE;
/*!40000 ALTER TABLE `viewer_del_image` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_del_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_login`
--

DROP TABLE IF EXISTS `viewer_login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_login` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) DEFAULT NULL,
  `password` varchar(50) DEFAULT NULL,
  `privilege` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `username` (`username`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_login`
--

LOCK TABLES `viewer_login` WRITE;
/*!40000 ALTER TABLE `viewer_login` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_login` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_pref_image`
--

DROP TABLE IF EXISTS `viewer_pref_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_pref_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `username` varchar(50) DEFAULT NULL,
  `sessionId` int(11) DEFAULT NULL,
  `imageId` int(11) DEFAULT NULL,
  `status` enum('hidden','visible','exemplar') DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `timestamp` (`timestamp`),
  KEY `username` (`username`),
  KEY `sessionId` (`sessionId`),
  KEY `imageId` (`imageId`),
  KEY `status` (`status`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_pref_image`
--

LOCK TABLES `viewer_pref_image` WRITE;
/*!40000 ALTER TABLE `viewer_pref_image` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_pref_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_update`
--

DROP TABLE IF EXISTS `viewer_update`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_update` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `status` enum('N','Y') DEFAULT NULL,
  `name` text,
  `update` text,
  PRIMARY KEY (`id`),
  KEY `timestamp` (`timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_update`
--

LOCK TABLES `viewer_update` WRITE;
/*!40000 ALTER TABLE `viewer_update` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_update` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `viewer_users`
--

DROP TABLE IF EXISTS `viewer_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `viewer_users` (
  `userId` int(11) NOT NULL AUTO_INCREMENT,
  `login` varchar(50) DEFAULT NULL,
  `firstname` text,
  `lastname` text,
  `title` text,
  `institution` text,
  `dept` text,
  `address` text,
  `city` text,
  `statecountry` text,
  `zip` text,
  `phone` text,
  `fax` text,
  `email` text,
  `url` text,
  PRIMARY KEY (`userId`),
  KEY `login` (`login`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `viewer_users`
--

LOCK TABLES `viewer_users` WRITE;
/*!40000 ALTER TABLE `viewer_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `viewer_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `projectdb`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `projectdb` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `projectdb`;

--
-- Table structure for table `boxtypes`
--

DROP TABLE IF EXISTS `boxtypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `boxtypes` (
  `boxtypeId` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `label` text NOT NULL,
  `image` varchar(100) NOT NULL DEFAULT '0',
  `image_tiny` varchar(100) NOT NULL,
  PRIMARY KEY (`boxtypeId`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `boxtypes`
--

LOCK TABLES `boxtypes` WRITE;
/*!40000 ALTER TABLE `boxtypes` DISABLE KEYS */;
INSERT INTO `boxtypes` VALUES (1,'2003-11-17 13:55:35','cryo grid box','grid_box_cryo.jpg','grid_box_cryo_tiny.jpg'),(2,'2003-11-17 13:55:47','grid box','grid_box.jpg','grid_box_tiny.jpg'),(3,'2003-11-17 13:55:56','tray','tray.png','tray_tiny.png');
/*!40000 ALTER TABLE `boxtypes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `confirmauth`
--

DROP TABLE IF EXISTS `confirmauth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `confirmauth` (
  `mdhash` longtext NOT NULL,
  `username` text NOT NULL,
  `password` text NOT NULL,
  `firstname` text NOT NULL,
  `lastname` text NOT NULL,
  `email` text NOT NULL,
  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `confirmauth`
--

LOCK TABLES `confirmauth` WRITE;
/*!40000 ALTER TABLE `confirmauth` DISABLE KEYS */;
/*!40000 ALTER TABLE `confirmauth` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `dataStatusReport`
--

DROP TABLE IF EXISTS `dataStatusReport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `dataStatusReport` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `appion_project` int(11) NOT NULL,
  `processed_session` int(11) NOT NULL,
  `processed_run` int(11) NOT NULL,
  `last_exp_runtime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `ace_run` int(11) NOT NULL,
  `ace2_run` int(11) NOT NULL,
  `ctfind_run` int(11) NOT NULL,
  `ace_processed_image` int(11) NOT NULL,
  `particle_selection` int(11) NOT NULL,
  `dog_picker` int(11) NOT NULL,
  `manual_picker` int(11) NOT NULL,
  `tilt_picker` int(11) NOT NULL,
  `template_picker` int(11) NOT NULL,
  `selected_particle` bigint(20) NOT NULL,
  `classification` int(11) NOT NULL,
  `classes` int(11) NOT NULL,
  `classified_particles` bigint(20) NOT NULL,
  `RCT_Models` int(11) NOT NULL,
  `tomogram` int(11) NOT NULL,
  `stack` int(11) NOT NULL,
  `stack_particle` bigint(20) NOT NULL,
  `3D_recon` int(11) NOT NULL,
  `recon_iteration` int(11) NOT NULL,
  `classified_particle` bigint(20) NOT NULL,
  `template` int(11) NOT NULL,
  `initial_model` int(11) NOT NULL,
  `first_exp_runtime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `dataStatusReport`
--

LOCK TABLES `dataStatusReport` WRITE;
/*!40000 ALTER TABLE `dataStatusReport` DISABLE KEYS */;
/*!40000 ALTER TABLE `dataStatusReport` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gridboxes`
--

DROP TABLE IF EXISTS `gridboxes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gridboxes` (
  `gridboxId` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `label` text,
  `boxtypeId` int(11) DEFAULT '0',
  `container` text,
  PRIMARY KEY (`gridboxId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gridboxes`
--

LOCK TABLES `gridboxes` WRITE;
/*!40000 ALTER TABLE `gridboxes` DISABLE KEYS */;
/*!40000 ALTER TABLE `gridboxes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `gridlocations`
--

DROP TABLE IF EXISTS `gridlocations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gridlocations` (
  `gridlocationId` int(11) NOT NULL AUTO_INCREMENT,
  `gridboxId` int(11) DEFAULT NULL,
  `gridId` int(11) DEFAULT NULL,
  `location` int(11) DEFAULT NULL,
  PRIMARY KEY (`gridlocationId`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `gridlocations`
--

LOCK TABLES `gridlocations` WRITE;
/*!40000 ALTER TABLE `gridlocations` DISABLE KEYS */;
/*!40000 ALTER TABLE `gridlocations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `grids`
--

DROP TABLE IF EXISTS `grids`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `grids` (
  `gridId` int(11) NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `label` varchar(255) DEFAULT NULL,
  `prepdate` timestamp NULL DEFAULT NULL,
  `specimenId` int(11) DEFAULT '0',
  `substrate` varchar(100) DEFAULT NULL,
  `preparation` varchar(100) DEFAULT NULL,
  `number` varchar(10) DEFAULT NULL,
  `concentration` double DEFAULT NULL,
  `fraction` text,
  `note` text,
  `sort` text,
  `boxId` int(11) DEFAULT NULL,
  `projectId` int(20) DEFAULT NULL,
  `specimen` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`gridId`),
  KEY `label` (`label`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grids`
--

LOCK TABLES `grids` WRITE;
/*!40000 ALTER TABLE `grids` DISABLE KEYS */;
/*!40000 ALTER TABLE `grids` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `install`
--

DROP TABLE IF EXISTS `install`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `install` (
  `key` varchar(100) NOT NULL,
  `value` varchar(100) NOT NULL,
  KEY `key` (`key`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `install`
--

LOCK TABLES `install` WRITE;
/*!40000 ALTER TABLE `install` DISABLE KEYS */;
INSERT INTO `install` VALUES ('settable','1'),('version','3.1.0'),('revision','18367');
/*!40000 ALTER TABLE `install` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `privileges`
--

DROP TABLE IF EXISTS `privileges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `privileges` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `description` text NOT NULL,
  `groups` tinyint(4) NOT NULL,
  `users` tinyint(4) NOT NULL,
  `projects` tinyint(4) NOT NULL,
  `projectowners` tinyint(4) NOT NULL,
  `shareexperiments` tinyint(4) NOT NULL,
  `data` tinyint(4) NOT NULL,
  `gridboxes` tinyint(4) NOT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=6 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `privileges`
--

LOCK TABLES `privileges` WRITE;
/*!40000 ALTER TABLE `privileges` DISABLE KEYS */;
INSERT INTO `privileges` VALUES (1,'2015-09-28 19:56:33','All at administration level',4,4,4,4,4,4,4),(2,'2015-09-28 19:56:33','View all but administrate owned',3,3,3,3,3,3,4),(3,'2015-09-28 19:56:33','Administrate/view only  owned projects and view shared experiments',1,2,2,2,2,2,1),(4,'2015-09-28 19:56:33','View owned projects and shared experiments',1,1,1,1,1,1,1),(5,'2015-09-28 19:56:33','No privilege for anything',0,0,0,0,0,0,0);
/*!40000 ALTER TABLE `privileges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `processingdb`
--

DROP TABLE IF EXISTS `processingdb`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `processingdb` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|projects|project` int(20) DEFAULT NULL,
  `appiondb` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|projects|project` (`REF|projects|project`),
  KEY `appiondb` (`appiondb`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `processingdb`
--

LOCK TABLES `processingdb` WRITE;
/*!40000 ALTER TABLE `processingdb` DISABLE KEYS */;
INSERT INTO `processingdb` VALUES (1,'2015-10-05 17:02:51',1,'ap1');
/*!40000 ALTER TABLE `processingdb` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projectexperiments`
--

DROP TABLE IF EXISTS `projectexperiments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projectexperiments` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|projects|project` int(11) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(11) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `project` (`REF|projects|project`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `session` (`REF|leginondata|SessionData|session`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projectexperiments`
--

LOCK TABLES `projectexperiments` WRITE;
/*!40000 ALTER TABLE `projectexperiments` DISABLE KEYS */;
INSERT INTO `projectexperiments` VALUES (1,'2015-10-05 17:02:57',1,2);
/*!40000 ALTER TABLE `projectexperiments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projectowners`
--

DROP TABLE IF EXISTS `projectowners`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projectowners` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|projects|project` int(16) NOT NULL,
  `REF|leginondata|UserData|user` int(16) NOT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|projects|project` (`REF|projects|project`),
  KEY `REF|leginondata|UserData|user` (`REF|leginondata|UserData|user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projectowners`
--

LOCK TABLES `projectowners` WRITE;
/*!40000 ALTER TABLE `projectowners` DISABLE KEYS */;
/*!40000 ALTER TABLE `projectowners` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projects` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` varchar(255) NOT NULL,
  `short_description` text NOT NULL,
  `long_description` text NOT NULL,
  `category` text NOT NULL,
  `funding` text NOT NULL,
  `leginondb` varchar(50) DEFAULT NULL,
  `hidden` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`DEF_id`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `projects`
--

LOCK TABLES `projects` WRITE;
/*!40000 ALTER TABLE `projects` DISABLE KEYS */;
INSERT INTO `projects` VALUES (1,'2015-10-05 17:02:16','GroEL','Docker Test #1 GroEL','','','',NULL,0);
/*!40000 ALTER TABLE `projects` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `shareexperiments`
--

DROP TABLE IF EXISTS `shareexperiments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `shareexperiments` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|experiment` int(11) NOT NULL DEFAULT '0',
  `REF|leginondata|UserData|user` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|experiment` (`REF|leginondata|SessionData|experiment`),
  KEY `REF|leginondata|UserData|user` (`REF|leginondata|UserData|user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `shareexperiments`
--

LOCK TABLES `shareexperiments` WRITE;
/*!40000 ALTER TABLE `shareexperiments` DISABLE KEYS */;
/*!40000 ALTER TABLE `shareexperiments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `userdetails`
--

DROP TABLE IF EXISTS `userdetails`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `userdetails` (
  `DEF_id` int(11) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|UserData|user` int(20) DEFAULT NULL,
  `title` text NOT NULL,
  `institution` text NOT NULL,
  `dept` text NOT NULL,
  `address` text NOT NULL,
  `city` text NOT NULL,
  `statecountry` text NOT NULL,
  `zip` text NOT NULL,
  `phone` text NOT NULL,
  `fax` text NOT NULL,
  `url` text NOT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|UserData|user` (`REF|leginondata|UserData|user`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `userdetails`
--

LOCK TABLES `userdetails` WRITE;
/*!40000 ALTER TABLE `userdetails` DISABLE KEYS */;
/*!40000 ALTER TABLE `userdetails` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `ap1`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `ap1` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `ap1`;

--
-- Table structure for table `Ap3dDensityData`
--

DROP TABLE IF EXISTS `Ap3dDensityData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Ap3dDensityData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `boxsize` int(20) DEFAULT NULL,
  `mask` int(20) DEFAULT NULL,
  `imask` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `lowpass` double DEFAULT NULL,
  `highpass` double DEFAULT NULL,
  `maxfilt` double DEFAULT NULL,
  `resolution` double DEFAULT NULL,
  `rmeasure` double DEFAULT NULL,
  `handflip` tinyint(1) DEFAULT NULL,
  `norm` tinyint(1) DEFAULT NULL,
  `invert` tinyint(1) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `md5sum` text,
  `pdbid` text,
  `emdbid` text,
  `eman` text,
  `description` text,
  `ampName` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApPathData|ampPath` int(20) DEFAULT NULL,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `REF|ApRefineIterData|refineIter` int(20) DEFAULT NULL,
  `REF|ApHipIterData|hipIter` int(20) DEFAULT NULL,
  `REF|ApRctRunData|rctrun` int(20) DEFAULT NULL,
  `REF|ApOtrRunData|otrrun` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `hard` int(20) DEFAULT NULL,
  `sigma` double DEFAULT NULL,
  `maxjump` double DEFAULT NULL,
  `mass` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `handflip` (`handflip`),
  KEY `norm` (`norm`),
  KEY `invert` (`invert`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApPathData|ampPath` (`REF|ApPathData|ampPath`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `REF|ApRefineIterData|refineIter` (`REF|ApRefineIterData|refineIter`),
  KEY `REF|ApHipIterData|hipIter` (`REF|ApHipIterData|hipIter`),
  KEY `REF|ApRctRunData|rctrun` (`REF|ApRctRunData|rctrun`),
  KEY `REF|ApOtrRunData|otrrun` (`REF|ApOtrRunData|otrrun`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Ap3dDensityData`
--

LOCK TABLES `Ap3dDensityData` WRITE;
/*!40000 ALTER TABLE `Ap3dDensityData` DISABLE KEYS */;
/*!40000 ALTER TABLE `Ap3dDensityData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAce2ParamsData`
--

DROP TABLE IF EXISTS `ApAce2ParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAce2ParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `bin` int(20) DEFAULT NULL,
  `reprocess` double DEFAULT NULL,
  `cs` double DEFAULT NULL,
  `stig` tinyint(1) DEFAULT NULL,
  `min_defocus` double DEFAULT NULL,
  `max_defocus` double DEFAULT NULL,
  `edge_thresh` double DEFAULT NULL,
  `edge_blur` double DEFAULT NULL,
  `rot_blur` double DEFAULT NULL,
  `refine2d` tinyint(1) DEFAULT NULL,
  `onepass` double DEFAULT NULL,
  `zeropass` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `stig` (`stig`),
  KEY `refine2d` (`refine2d`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAce2ParamsData`
--

LOCK TABLES `ApAce2ParamsData` WRITE;
/*!40000 ALTER TABLE `ApAce2ParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAce2ParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAceParamsData`
--

DROP TABLE IF EXISTS `ApAceParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAceParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `display` int(20) DEFAULT NULL,
  `stig` int(20) DEFAULT NULL,
  `medium` text,
  `df_override` double DEFAULT NULL,
  `edgethcarbon` double DEFAULT NULL,
  `edgethice` double DEFAULT NULL,
  `pfcarbon` double DEFAULT NULL,
  `pfice` double DEFAULT NULL,
  `overlap` int(20) DEFAULT NULL,
  `fieldsize` int(20) DEFAULT NULL,
  `resamplefr` double DEFAULT NULL,
  `drange` int(20) DEFAULT NULL,
  `reprocess` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAceParamsData`
--

LOCK TABLES `ApAceParamsData` WRITE;
/*!40000 ALTER TABLE `ApAceParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAceParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAceRunData`
--

DROP TABLE IF EXISTS `ApAceRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAceRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApAceParamsData|aceparams` int(20) DEFAULT NULL,
  `REF|ApCtfTiltParamsData|ctftilt_params` int(20) DEFAULT NULL,
  `REF|ApAce2ParamsData|ace2_params` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `name` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAceParamsData|aceparams` (`REF|ApAceParamsData|aceparams`),
  KEY `REF|ApCtfTiltParamsData|ctftilt_params` (`REF|ApCtfTiltParamsData|ctftilt_params`),
  KEY `REF|ApAce2ParamsData|ace2_params` (`REF|ApAce2ParamsData|ace2_params`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAceRunData`
--

LOCK TABLES `ApAceRunData` WRITE;
/*!40000 ALTER TABLE `ApAceRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAceRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAffinityPropagationClusterParamsData`
--

DROP TABLE IF EXISTS `ApAffinityPropagationClusterParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAffinityPropagationClusterParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mask_diam` double DEFAULT NULL,
  `preference_type` text,
  `run_seconds` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAffinityPropagationClusterParamsData`
--

LOCK TABLES `ApAffinityPropagationClusterParamsData` WRITE;
/*!40000 ALTER TABLE `ApAffinityPropagationClusterParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAffinityPropagationClusterParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAlignAnalysisRunData`
--

DROP TABLE IF EXISTS `ApAlignAnalysisRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAlignAnalysisRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApCoranRunData|coranrun` int(20) DEFAULT NULL,
  `REF|ApImagicAlignAnalysisData|imagicMSArun` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApCoranRunData|coranrun` (`REF|ApCoranRunData|coranrun`),
  KEY `REF|ApImagicAlignAnalysisData|imagicMSArun` (`REF|ApImagicAlignAnalysisData|imagicMSArun`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAlignAnalysisRunData`
--

LOCK TABLES `ApAlignAnalysisRunData` WRITE;
/*!40000 ALTER TABLE `ApAlignAnalysisRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAlignAnalysisRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAlignParticleData`
--

DROP TABLE IF EXISTS `ApAlignParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAlignParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `partnum` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `REF|ApStackParticleData|stackpart` int(20) DEFAULT NULL,
  `xshift` double DEFAULT NULL,
  `yshift` double DEFAULT NULL,
  `rotation` double DEFAULT NULL,
  `mirror` tinyint(1) DEFAULT NULL,
  `spread` double DEFAULT NULL,
  `correlation` double DEFAULT NULL,
  `score` double DEFAULT NULL,
  `REF|ApAlignReferenceData|ref` int(20) DEFAULT NULL,
  `bad` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `REF|ApStackParticleData|stackpart` (`REF|ApStackParticleData|stackpart`),
  KEY `mirror` (`mirror`),
  KEY `REF|ApAlignReferenceData|ref` (`REF|ApAlignReferenceData|ref`),
  KEY `bad` (`bad`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAlignParticleData`
--

LOCK TABLES `ApAlignParticleData` WRITE;
/*!40000 ALTER TABLE `ApAlignParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAlignParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAlignReferenceData`
--

DROP TABLE IF EXISTS `ApAlignReferenceData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAlignReferenceData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `refnum` int(20) DEFAULT NULL,
  `iteration` int(20) DEFAULT NULL,
  `mrcfile` text,
  `varmrcfile` text,
  `imagicfile` text,
  `ssnr_resolution` double DEFAULT NULL,
  `REF|ApAlignRunData|alignrun` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApTemplateImageData|template` int(20) DEFAULT NULL,
  `REF|ApTemplateStackData|templatestack` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAlignRunData|alignrun` (`REF|ApAlignRunData|alignrun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApTemplateImageData|template` (`REF|ApTemplateImageData|template`),
  KEY `REF|ApTemplateStackData|templatestack` (`REF|ApTemplateStackData|templatestack`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAlignReferenceData`
--

LOCK TABLES `ApAlignReferenceData` WRITE;
/*!40000 ALTER TABLE `ApAlignReferenceData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAlignReferenceData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAlignRunData`
--

DROP TABLE IF EXISTS `ApAlignRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAlignRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `bin` int(20) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `description` text,
  `REF|ApSpiderNoRefRunData|norefrun` int(20) DEFAULT NULL,
  `REF|ApRefBasedRunData|refbasedrun` int(20) DEFAULT NULL,
  `REF|ApMaxLikeRunData|maxlikerun` int(20) DEFAULT NULL,
  `REF|ApSparxISACRunData|isacrun` int(20) DEFAULT NULL,
  `REF|ApEMANRefine2dRunData|refine2drun` int(20) DEFAULT NULL,
  `REF|ApMultiRefAlignRunData|imagicMRA` int(20) DEFAULT NULL,
  `REF|ApEdIterRunData|editerrun` int(20) DEFAULT NULL,
  `REF|ApTopolRepRunData|topreprun` int(20) DEFAULT NULL,
  `REF|ApCL2DRunData|cl2drun` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSpiderNoRefRunData|norefrun` (`REF|ApSpiderNoRefRunData|norefrun`),
  KEY `REF|ApRefBasedRunData|refbasedrun` (`REF|ApRefBasedRunData|refbasedrun`),
  KEY `REF|ApMaxLikeRunData|maxlikerun` (`REF|ApMaxLikeRunData|maxlikerun`),
  KEY `REF|ApSparxISACRunData|isacrun` (`REF|ApSparxISACRunData|isacrun`),
  KEY `REF|ApEMANRefine2dRunData|refine2drun` (`REF|ApEMANRefine2dRunData|refine2drun`),
  KEY `REF|ApMultiRefAlignRunData|imagicMRA` (`REF|ApMultiRefAlignRunData|imagicMRA`),
  KEY `REF|ApEdIterRunData|editerrun` (`REF|ApEdIterRunData|editerrun`),
  KEY `REF|ApTopolRepRunData|topreprun` (`REF|ApTopolRepRunData|topreprun`),
  KEY `REF|ApCL2DRunData|cl2drun` (`REF|ApCL2DRunData|cl2drun`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAlignRunData`
--

LOCK TABLES `ApAlignRunData` WRITE;
/*!40000 ALTER TABLE `ApAlignRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAlignRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAlignStackData`
--

DROP TABLE IF EXISTS `ApAlignStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAlignStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `imagicfile` text,
  `avgmrcfile` text,
  `refstackfile` text,
  `iteration` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApAlignRunData|alignrun` int(20) DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `num_particles` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApAlignRunData|alignrun` (`REF|ApAlignRunData|alignrun`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAlignStackData`
--

LOCK TABLES `ApAlignStackData` WRITE;
/*!40000 ALTER TABLE `ApAlignStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAlignStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAppionJobData`
--

DROP TABLE IF EXISTS `ApAppionJobData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAppionJobData` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `name` text,
  `jobtype` text,
  `REF|ApPathData|dmfpath` int(20) DEFAULT NULL,
  `REF|ApPathData|clusterpath` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `cluster` text,
  `clusterjobid` int(20) DEFAULT NULL,
  `status` varchar(1) DEFAULT NULL,
  `user` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|clusterpath` (`REF|ApPathData|clusterpath`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|dmfpath` (`REF|ApPathData|dmfpath`),
  KEY `clusterjobid` (`clusterjobid`),
  KEY `status` (`status`),
  KEY `jobtype_10` (`jobtype`(10))
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAppionJobData`
--

LOCK TABLES `ApAppionJobData` WRITE;
/*!40000 ALTER TABLE `ApAppionJobData` DISABLE KEYS */;
INSERT INTO `ApAppionJobData` VALUES (1,'2015-10-05 17:02:59',1,'06jul12a.appionsub.job','uploadimages',NULL,1,NULL,'053ffadab348',NULL,'D','unknown');
/*!40000 ALTER TABLE `ApAppionJobData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAssessmentData`
--

DROP TABLE IF EXISTS `ApAssessmentData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAssessmentData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApAssessmentRunData|assessmentrun` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `selectionkeep` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAssessmentRunData|assessmentrun` (`REF|ApAssessmentRunData|assessmentrun`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAssessmentData`
--

LOCK TABLES `ApAssessmentData` WRITE;
/*!40000 ALTER TABLE `ApAssessmentData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAssessmentData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApAssessmentRunData`
--

DROP TABLE IF EXISTS `ApAssessmentRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApAssessmentRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApAssessmentRunData`
--

LOCK TABLES `ApAssessmentRunData` WRITE;
/*!40000 ALTER TABLE `ApAssessmentRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApAssessmentRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApBootstrappedAngularReconstitutionParamsData`
--

DROP TABLE IF EXISTS `ApBootstrappedAngularReconstitutionParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApBootstrappedAngularReconstitutionParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `num_averages` int(20) DEFAULT NULL,
  `num_volumes` int(20) DEFAULT NULL,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `num_alignment_refs` int(20) DEFAULT NULL,
  `angular_increment` int(20) DEFAULT NULL,
  `keep_ordered` int(20) DEFAULT NULL,
  `threed_lpfilt` int(20) DEFAULT NULL,
  `hamming_window` int(20) DEFAULT NULL,
  `non_weighted_sequence` tinyint(1) DEFAULT NULL,
  `PCA` tinyint(1) DEFAULT NULL,
  `numeigens` int(20) DEFAULT NULL,
  `preference_type` text,
  `prealign_avgs` tinyint(1) DEFAULT NULL,
  `scale` tinyint(1) DEFAULT NULL,
  `recalculate_volumes` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `non_weighted_sequence` (`non_weighted_sequence`),
  KEY `PCA` (`PCA`),
  KEY `prealign_avgs` (`prealign_avgs`),
  KEY `scale` (`scale`),
  KEY `recalculate_volumes` (`recalculate_volumes`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApBootstrappedAngularReconstitutionParamsData`
--

LOCK TABLES `ApBootstrappedAngularReconstitutionParamsData` WRITE;
/*!40000 ALTER TABLE `ApBootstrappedAngularReconstitutionParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApBootstrappedAngularReconstitutionParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApBootstrappedAngularReconstitutionRunData`
--

DROP TABLE IF EXISTS `ApBootstrappedAngularReconstitutionRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApBootstrappedAngularReconstitutionRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApBootstrappedAngularReconstitutionParamsData|aar_params` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `REF|ApTemplateStackData|templatestackid` int(20) DEFAULT NULL,
  `REF|ApClusteringStackData|clusterid` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApBootstrappedAngularReconstitutionParamsData|aar_params` (`REF|ApBootstrappedAngularReconstitutionParamsData|aar_params`),
  KEY `REF|ApTemplateStackData|templatestackid` (`REF|ApTemplateStackData|templatestackid`),
  KEY `REF|ApClusteringStackData|clusterid` (`REF|ApClusteringStackData|clusterid`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApBootstrappedAngularReconstitutionRunData`
--

LOCK TABLES `ApBootstrappedAngularReconstitutionRunData` WRITE;
/*!40000 ALTER TABLE `ApBootstrappedAngularReconstitutionRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApBootstrappedAngularReconstitutionRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApCL2DRunData`
--

DROP TABLE IF EXISTS `ApCL2DRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApCL2DRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `fast` text,
  `run_seconds` int(20) DEFAULT NULL,
  `timestamp` text,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `finished` tinyint(1) DEFAULT NULL,
  `max-iter` int(20) DEFAULT NULL,
  `num-ref` int(20) DEFAULT NULL,
  `correlation` tinyint(1) DEFAULT NULL,
  `correntropy` tinyint(1) DEFAULT NULL,
  `classical_multiref` tinyint(1) DEFAULT NULL,
  `intracluster_multiref` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `finished` (`finished`),
  KEY `correlation` (`correlation`),
  KEY `correntropy` (`correntropy`),
  KEY `classical_multiref` (`classical_multiref`),
  KEY `intracluster_multiref` (`intracluster_multiref`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApCL2DRunData`
--

LOCK TABLES `ApCL2DRunData` WRITE;
/*!40000 ALTER TABLE `ApCL2DRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApCL2DRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApClusteringParticleData`
--

DROP TABLE IF EXISTS `ApClusteringParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApClusteringParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `partnum` int(20) DEFAULT NULL,
  `refnum` int(20) DEFAULT NULL,
  `REF|ApClusteringReferenceData|clusterreference` int(20) DEFAULT NULL,
  `REF|ApClusteringStackData|clusterstack` int(20) DEFAULT NULL,
  `REF|ApAlignParticleData|alignparticle` int(20) DEFAULT NULL,
  `imagic_cls_quality` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApClusteringReferenceData|clusterreference` (`REF|ApClusteringReferenceData|clusterreference`),
  KEY `REF|ApClusteringStackData|clusterstack` (`REF|ApClusteringStackData|clusterstack`),
  KEY `REF|ApAlignParticleData|alignparticle` (`REF|ApAlignParticleData|alignparticle`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApClusteringParticleData`
--

LOCK TABLES `ApClusteringParticleData` WRITE;
/*!40000 ALTER TABLE `ApClusteringParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApClusteringParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApClusteringReferenceData`
--

DROP TABLE IF EXISTS `ApClusteringReferenceData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApClusteringReferenceData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `refnum` int(20) DEFAULT NULL,
  `avg_mrcfile` text,
  `var_mrcfile` text,
  `ssnr_resolution` double DEFAULT NULL,
  `num_particles` int(20) DEFAULT NULL,
  `REF|ApClusteringRunData|clusterrun` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApClusteringRunData|clusterrun` (`REF|ApClusteringRunData|clusterrun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApClusteringReferenceData`
--

LOCK TABLES `ApClusteringReferenceData` WRITE;
/*!40000 ALTER TABLE `ApClusteringReferenceData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApClusteringReferenceData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApClusteringRunData`
--

DROP TABLE IF EXISTS `ApClusteringRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApClusteringRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `description` text,
  `boxsize` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `num_particles` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `REF|ApAlignAnalysisRunData|analysisrun` int(20) DEFAULT NULL,
  `REF|ApSpiderClusteringParamsData|spiderparams` int(20) DEFAULT NULL,
  `REF|ApKerDenSOMParamsData|kerdenparams` int(20) DEFAULT NULL,
  `REF|ApRotKerDenSOMParamsData|rotkerdenparams` int(20) DEFAULT NULL,
  `REF|ApAffinityPropagationClusterParamsData|affpropparams` int(20) DEFAULT NULL,
  `REF|ApCL2DRunData|cl2dparams` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `REF|ApAlignAnalysisRunData|analysisrun` (`REF|ApAlignAnalysisRunData|analysisrun`),
  KEY `REF|ApSpiderClusteringParamsData|spiderparams` (`REF|ApSpiderClusteringParamsData|spiderparams`),
  KEY `REF|ApKerDenSOMParamsData|kerdenparams` (`REF|ApKerDenSOMParamsData|kerdenparams`),
  KEY `REF|ApRotKerDenSOMParamsData|rotkerdenparams` (`REF|ApRotKerDenSOMParamsData|rotkerdenparams`),
  KEY `REF|ApAffinityPropagationClusterParamsData|affpropparams` (`REF|ApAffinityPropagationClusterParamsData|affpropparams`),
  KEY `REF|ApCL2DRunData|cl2dparams` (`REF|ApCL2DRunData|cl2dparams`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApClusteringRunData`
--

LOCK TABLES `ApClusteringRunData` WRITE;
/*!40000 ALTER TABLE `ApClusteringRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApClusteringRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApClusteringStackData`
--

DROP TABLE IF EXISTS `ApClusteringStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApClusteringStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `num_classes` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `avg_imagicfile` text,
  `var_imagicfile` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApClusteringRunData|clusterrun` int(20) DEFAULT NULL,
  `ignore_images` int(20) DEFAULT NULL,
  `ignore_members` int(20) DEFAULT NULL,
  `num_factors` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApClusteringRunData|clusterrun` (`REF|ApClusteringRunData|clusterrun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApClusteringStackData`
--

LOCK TABLES `ApClusteringStackData` WRITE;
/*!40000 ALTER TABLE `ApClusteringStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApClusteringStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApContourData`
--

DROP TABLE IF EXISTS `ApContourData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApContourData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `x` double DEFAULT NULL,
  `y` double DEFAULT NULL,
  `version` int(20) DEFAULT NULL,
  `method` text,
  `particleType` text,
  `runname` text,
  `REF|ApSelectionRunData|selectionrun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`),
  KEY `REF|ApSelectionRunData|selectionrun` (`REF|ApSelectionRunData|selectionrun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApContourData`
--

LOCK TABLES `ApContourData` WRITE;
/*!40000 ALTER TABLE `ApContourData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApContourData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApContourPointData`
--

DROP TABLE IF EXISTS `ApContourPointData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApContourPointData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApContourData|contour` int(20) DEFAULT NULL,
  `x` double DEFAULT NULL,
  `y` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApContourData|contour` (`REF|ApContourData|contour`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApContourPointData`
--

LOCK TABLES `ApContourPointData` WRITE;
/*!40000 ALTER TABLE `ApContourPointData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApContourPointData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApCoranEigenImageData`
--

DROP TABLE IF EXISTS `ApCoranEigenImageData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApCoranEigenImageData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApCoranRunData|coranRun` int(20) DEFAULT NULL,
  `factor_num` int(20) DEFAULT NULL,
  `percent_contrib` double DEFAULT NULL,
  `image_name` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApCoranRunData|coranRun` (`REF|ApCoranRunData|coranRun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApCoranEigenImageData`
--

LOCK TABLES `ApCoranEigenImageData` WRITE;
/*!40000 ALTER TABLE `ApCoranEigenImageData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApCoranEigenImageData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApCoranRunData`
--

DROP TABLE IF EXISTS `ApCoranRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApCoranRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mask_diam` double DEFAULT NULL,
  `run_seconds` int(20) DEFAULT NULL,
  `num_factors` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApCoranRunData`
--

LOCK TABLES `ApCoranRunData` WRITE;
/*!40000 ALTER TABLE `ApCoranRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApCoranRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApCtfData`
--

DROP TABLE IF EXISTS `ApCtfData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApCtfData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApAceRunData|acerun` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `defocus1` double DEFAULT NULL,
  `defocus2` double DEFAULT NULL,
  `defocusinit` double DEFAULT NULL,
  `amplitude_contrast` double DEFAULT NULL,
  `angle_astigmatism` double DEFAULT NULL,
  `tilt_angle` double DEFAULT NULL,
  `tilt_axis_angle` double DEFAULT NULL,
  `snr` double DEFAULT NULL,
  `confidence` double DEFAULT NULL,
  `confidence_d` double DEFAULT NULL,
  `graph1` text,
  `graph2` text,
  `mat_file` text,
  `cross_correlation` double DEFAULT NULL,
  `ctfvalues_file` text,
  `cs` double DEFAULT NULL,
  `noise1` double DEFAULT NULL,
  `noise2` double DEFAULT NULL,
  `noise3` double DEFAULT NULL,
  `noise4` double DEFAULT NULL,
  `envelope1` double DEFAULT NULL,
  `envelope2` double DEFAULT NULL,
  `envelope3` double DEFAULT NULL,
  `envelope4` double DEFAULT NULL,
  `lowercutoff` double DEFAULT NULL,
  `uppercutoff` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApAceRunData|acerun` (`REF|ApAceRunData|acerun`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApCtfData`
--

LOCK TABLES `ApCtfData` WRITE;
/*!40000 ALTER TABLE `ApCtfData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApCtfData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApCtfTiltParamsData`
--

DROP TABLE IF EXISTS `ApCtfTiltParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApCtfTiltParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `medium` text,
  `ampcarbon` double DEFAULT NULL,
  `ampice` double DEFAULT NULL,
  `fieldsize` int(20) DEFAULT NULL,
  `cs` double DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `resmin` double DEFAULT NULL,
  `resmax` double DEFAULT NULL,
  `defstep` double DEFAULT NULL,
  `dast` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApCtfTiltParamsData`
--

LOCK TABLES `ApCtfTiltParamsData` WRITE;
/*!40000 ALTER TABLE `ApCtfTiltParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApCtfTiltParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApDDStackParamsData`
--

DROP TABLE IF EXISTS `ApDDStackParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApDDStackParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `preset` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApDDStackParamsData`
--

LOCK TABLES `ApDDStackParamsData` WRITE;
/*!40000 ALTER TABLE `ApDDStackParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApDDStackParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApDDStackRunData`
--

DROP TABLE IF EXISTS `ApDDStackRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApDDStackRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApDDStackParamsData|params` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApDDStackParamsData|params` (`REF|ApDDStackParamsData|params`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApDDStackRunData`
--

LOCK TABLES `ApDDStackRunData` WRITE;
/*!40000 ALTER TABLE `ApDDStackRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApDDStackRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApDogParamsData`
--

DROP TABLE IF EXISTS `ApDogParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApDogParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `diam` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `manual_thresh` double DEFAULT NULL,
  `max_threshold` double DEFAULT NULL,
  `invert` int(20) DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `max_peaks` int(20) DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `pixel_value_limit` double DEFAULT NULL,
  `maxsize` int(20) DEFAULT NULL,
  `kfactor` double DEFAULT NULL,
  `size_range` double DEFAULT NULL,
  `num_slices` int(20) DEFAULT NULL,
  `defocal_pairs` tinyint(1) DEFAULT NULL,
  `overlapmult` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `defocal_pairs` (`defocal_pairs`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApDogParamsData`
--

LOCK TABLES `ApDogParamsData` WRITE;
/*!40000 ALTER TABLE `ApDogParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApDogParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApEMANRefine2dRunData`
--

DROP TABLE IF EXISTS `ApEMANRefine2dRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApEMANRefine2dRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `num_iters` int(20) DEFAULT NULL,
  `num_classes` int(20) DEFAULT NULL,
  `run_seconds` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApEMANRefine2dRunData`
--

LOCK TABLES `ApEMANRefine2dRunData` WRITE;
/*!40000 ALTER TABLE `ApEMANRefine2dRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApEMANRefine2dRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApEdIterRunData`
--

DROP TABLE IF EXISTS `ApEdIterRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApEdIterRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `radius` int(20) DEFAULT NULL,
  `num_iter` int(20) DEFAULT NULL,
  `freealigns` int(20) DEFAULT NULL,
  `invert_templs` tinyint(1) DEFAULT NULL,
  `num_templs` int(20) DEFAULT NULL,
  `run_seconds` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `invert_templs` (`invert_templs`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApEdIterRunData`
--

LOCK TABLES `ApEdIterRunData` WRITE;
/*!40000 ALTER TABLE `ApEdIterRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApEdIterRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApEmanRefineIterData`
--

DROP TABLE IF EXISTS `ApEmanRefineIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApEmanRefineIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `package` text,
  `ang` double DEFAULT NULL,
  `lpfilter` int(20) DEFAULT NULL,
  `hpfilter` int(20) DEFAULT NULL,
  `mask` int(20) DEFAULT NULL,
  `imask` int(20) DEFAULT NULL,
  `pad` int(20) DEFAULT NULL,
  `EMAN_maxshift` int(20) DEFAULT NULL,
  `EMAN_hard` int(20) DEFAULT NULL,
  `EMAN_classkeep` double DEFAULT NULL,
  `EMAN_classiter` int(20) DEFAULT NULL,
  `EMAN_filt3d` int(20) DEFAULT NULL,
  `EMAN_shrink` int(20) DEFAULT NULL,
  `EMAN_euler2` int(20) DEFAULT NULL,
  `EMAN_xfiles` double DEFAULT NULL,
  `EMAN_amask1` double DEFAULT NULL,
  `EMAN_amask2` double DEFAULT NULL,
  `EMAN_amask3` double DEFAULT NULL,
  `EMAN_median` tinyint(1) DEFAULT NULL,
  `EMAN_phasecls` tinyint(1) DEFAULT NULL,
  `EMAN_fscls` tinyint(1) DEFAULT NULL,
  `EMAN_refine` tinyint(1) DEFAULT NULL,
  `EMAN_goodbad` tinyint(1) DEFAULT NULL,
  `EMAN_perturb` tinyint(1) DEFAULT NULL,
  `MsgP_cckeep` double DEFAULT NULL,
  `MsgP_minptls` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `EMAN_median` (`EMAN_median`),
  KEY `EMAN_phasecls` (`EMAN_phasecls`),
  KEY `EMAN_fscls` (`EMAN_fscls`),
  KEY `EMAN_refine` (`EMAN_refine`),
  KEY `EMAN_goodbad` (`EMAN_goodbad`),
  KEY `EMAN_perturb` (`EMAN_perturb`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApEmanRefineIterData`
--

LOCK TABLES `ApEmanRefineIterData` WRITE;
/*!40000 ALTER TABLE `ApEmanRefineIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApEmanRefineIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApEulerJumpData`
--

DROP TABLE IF EXISTS `ApEulerJumpData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApEulerJumpData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApStackParticleData|particle` int(20) DEFAULT NULL,
  `REF|ApRefineRunData|refineRun` int(20) DEFAULT NULL,
  `REF|ApMultiModelRefineRunData|multiModelRefineRun` int(20) DEFAULT NULL,
  `median` double DEFAULT NULL,
  `mean` double DEFAULT NULL,
  `stdev` double DEFAULT NULL,
  `min` double DEFAULT NULL,
  `max` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApStackParticleData|particle` (`REF|ApStackParticleData|particle`),
  KEY `REF|ApRefineRunData|refineRun` (`REF|ApRefineRunData|refineRun`),
  KEY `REF|ApMultiModelRefineRunData|multiModelRefineRun` (`REF|ApMultiModelRefineRunData|multiModelRefineRun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApEulerJumpData`
--

LOCK TABLES `ApEulerJumpData` WRITE;
/*!40000 ALTER TABLE `ApEulerJumpData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApEulerJumpData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApFSCData`
--

DROP TABLE IF EXISTS `ApFSCData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApFSCData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApRefineIterData|refineIter` int(20) DEFAULT NULL,
  `pix` int(20) DEFAULT NULL,
  `value` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApRefineIterData|refineIter` (`REF|ApRefineIterData|refineIter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApFSCData`
--

LOCK TABLES `ApFSCData` WRITE;
/*!40000 ALTER TABLE `ApFSCData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApFSCData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApFrealignIterData`
--

DROP TABLE IF EXISTS `ApFrealignIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApFrealignIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `iflag` int(20) DEFAULT NULL,
  `wgh` double DEFAULT NULL,
  `xstd` double DEFAULT NULL,
  `pbc` double DEFAULT NULL,
  `boff` double DEFAULT NULL,
  `itmax` int(20) DEFAULT NULL,
  `ipmax` int(20) DEFAULT NULL,
  `target` double DEFAULT NULL,
  `thresh` double DEFAULT NULL,
  `cs` double DEFAULT NULL,
  `rrec` double DEFAULT NULL,
  `highpass` double DEFAULT NULL,
  `lowpass` double DEFAULT NULL,
  `rbfact` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApFrealignIterData`
--

LOCK TABLES `ApFrealignIterData` WRITE;
/*!40000 ALTER TABLE `ApFrealignIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApFrealignIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApFrealignPrepareData`
--

DROP TABLE IF EXISTS `ApFrealignPrepareData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApFrealignPrepareData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `ppn` int(20) DEFAULT NULL,
  `rpn` int(20) DEFAULT NULL,
  `nodes` int(20) DEFAULT NULL,
  `memory` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `tarfile` text,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApStackData|reconstack` int(20) DEFAULT NULL,
  `REF|ApInitialModelData|model` int(20) DEFAULT NULL,
  `REF|ApAppionJobData|job` int(20) DEFAULT NULL,
  `REF|ApRefineIterData|refineIter` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApStackData|reconstack` (`REF|ApStackData|reconstack`),
  KEY `REF|ApInitialModelData|model` (`REF|ApInitialModelData|model`),
  KEY `REF|ApAppionJobData|job` (`REF|ApAppionJobData|job`),
  KEY `REF|ApRefineIterData|refineIter` (`REF|ApRefineIterData|refineIter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApFrealignPrepareData`
--

LOCK TABLES `ApFrealignPrepareData` WRITE;
/*!40000 ALTER TABLE `ApFrealignPrepareData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApFrealignPrepareData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApFullTomogramData`
--

DROP TABLE IF EXISTS `ApFullTomogramData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApFullTomogramData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|leginondata|TiltSeriesData|tiltseries` int(20) DEFAULT NULL,
  `REF|ApTomoAlignerParamsData|aligner` int(20) DEFAULT NULL,
  `REF|ApFullTomogramRunData|reconrun` int(20) DEFAULT NULL,
  `REF|ApTomoAlignmentRunData|alignrun` int(20) DEFAULT NULL,
  `thickness` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `name` text,
  `description` text,
  `REF|leginondata|AcquisitionImageData|zprojection` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApTomoReconParamsData|reconparam` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|leginondata|TiltSeriesData|tiltseries` (`REF|leginondata|TiltSeriesData|tiltseries`),
  KEY `REF|ApTomoAlignerParamsData|aligner` (`REF|ApTomoAlignerParamsData|aligner`),
  KEY `REF|ApFullTomogramRunData|reconrun` (`REF|ApFullTomogramRunData|reconrun`),
  KEY `REF|ApTomoAlignmentRunData|alignrun` (`REF|ApTomoAlignmentRunData|alignrun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|leginondata|AcquisitionImageData|zprojection` (`REF|leginondata|AcquisitionImageData|zprojection`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApTomoReconParamsData|reconparam` (`REF|ApTomoReconParamsData|reconparam`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApFullTomogramData`
--

LOCK TABLES `ApFullTomogramData` WRITE;
/*!40000 ALTER TABLE `ApFullTomogramData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApFullTomogramData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApFullTomogramRunData`
--

DROP TABLE IF EXISTS `ApFullTomogramRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApFullTomogramRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `runname` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `method` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApFullTomogramRunData`
--

LOCK TABLES `ApFullTomogramRunData` WRITE;
/*!40000 ALTER TABLE `ApFullTomogramRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApFullTomogramRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApHelicalCoordData`
--

DROP TABLE IF EXISTS `ApHelicalCoordData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApHelicalCoordData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `filno` double DEFAULT NULL,
  `xlngth` double DEFAULT NULL,
  `xcoord` double DEFAULT NULL,
  `ycoord` double DEFAULT NULL,
  `initialang` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApHelicalCoordData`
--

LOCK TABLES `ApHelicalCoordData` WRITE;
/*!40000 ALTER TABLE `ApHelicalCoordData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApHelicalCoordData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApHipIterData`
--

DROP TABLE IF EXISTS `ApHipIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApHipIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApHipRunData|hipRun` int(20) DEFAULT NULL,
  `iteration` int(20) DEFAULT NULL,
  `iterpath` text,
  `volumeDensity` text,
  `REF|ApResolutionData|resolution` int(20) DEFAULT NULL,
  `REF|ApRMeasureData|rMeasure` int(20) DEFAULT NULL,
  `cutfit1` text,
  `cutfit2` text,
  `cutfit3` text,
  `chop1` text,
  `chop2` text,
  `avglist_file` text,
  `final_numpart` int(20) DEFAULT NULL,
  `asymsu` int(20) DEFAULT NULL,
  `avg_file` text,
  `map_file` text,
  `mrc_file` text,
  `ll_file` text,
  `op_file` text,
  `output_file` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApHipRunData|hipRun` (`REF|ApHipRunData|hipRun`),
  KEY `REF|ApResolutionData|resolution` (`REF|ApResolutionData|resolution`),
  KEY `REF|ApRMeasureData|rMeasure` (`REF|ApRMeasureData|rMeasure`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApHipIterData`
--

LOCK TABLES `ApHipIterData` WRITE;
/*!40000 ALTER TABLE `ApHipIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApHipIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApHipParamsData`
--

DROP TABLE IF EXISTS `ApHipParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApHipParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApHipRunData|hipRun` int(20) DEFAULT NULL,
  `numpart` int(20) DEFAULT NULL,
  `replen` int(20) DEFAULT NULL,
  `diam` int(20) DEFAULT NULL,
  `diaminner` int(20) DEFAULT NULL,
  `subunits` int(20) DEFAULT NULL,
  `xlngth` int(20) DEFAULT NULL,
  `yht2` int(20) DEFAULT NULL,
  `padval` int(20) DEFAULT NULL,
  `rescut` int(20) DEFAULT NULL,
  `filval` int(20) DEFAULT NULL,
  `strong` text,
  `range` text,
  `llbo` text,
  `final_stack` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApHipRunData|hipRun` (`REF|ApHipRunData|hipRun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApHipParamsData`
--

LOCK TABLES `ApHipParamsData` WRITE;
/*!40000 ALTER TABLE `ApHipParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApHipParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApHipParticleData`
--

DROP TABLE IF EXISTS `ApHipParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApHipParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApHipRunData|hipRun` int(20) DEFAULT NULL,
  `particleNumber` int(20) DEFAULT NULL,
  `filename` text,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApStackRunData|stackRun` int(20) DEFAULT NULL,
  `tilt` double DEFAULT NULL,
  `shift` double DEFAULT NULL,
  `resid` double DEFAULT NULL,
  `far_phi` double DEFAULT NULL,
  `far_z` double DEFAULT NULL,
  `far_rscale` double DEFAULT NULL,
  `far_ampscale` double DEFAULT NULL,
  `ner_phi` double DEFAULT NULL,
  `ner_z` double DEFAULT NULL,
  `ner_rscale` double DEFAULT NULL,
  `ner_ampscale` double DEFAULT NULL,
  `mrc_file` text,
  `s_file` text,
  `dft_file` text,
  `colb_file` text,
  `ner_file` text,
  `far_file` text,
  `fft_file` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApHipRunData|hipRun` (`REF|ApHipRunData|hipRun`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApStackRunData|stackRun` (`REF|ApStackRunData|stackRun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApHipParticleData`
--

LOCK TABLES `ApHipParticleData` WRITE;
/*!40000 ALTER TABLE `ApHipParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApHipParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApHipRunData`
--

DROP TABLE IF EXISTS `ApHipRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApHipRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `description` text,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `apix` double DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApHipRunData`
--

LOCK TABLES `ApHipRunData` WRITE;
/*!40000 ALTER TABLE `ApHipRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApHipRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImageTiltTransformData`
--

DROP TABLE IF EXISTS `ApImageTiltTransformData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImageTiltTransformData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|AcquisitionImageData|image1` int(20) DEFAULT NULL,
  `image1_x` double DEFAULT NULL,
  `image1_y` double DEFAULT NULL,
  `image1_rotation` double DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image2` int(20) DEFAULT NULL,
  `image2_x` double DEFAULT NULL,
  `image2_y` double DEFAULT NULL,
  `image2_rotation` double DEFAULT NULL,
  `scale_factor` double DEFAULT NULL,
  `tilt_angle` double DEFAULT NULL,
  `rmsd` double DEFAULT NULL,
  `overlap` double DEFAULT NULL,
  `REF|ApSelectionRunData|tiltrun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|AcquisitionImageData|image1` (`REF|leginondata|AcquisitionImageData|image1`),
  KEY `REF|leginondata|AcquisitionImageData|image2` (`REF|leginondata|AcquisitionImageData|image2`),
  KEY `REF|ApSelectionRunData|tiltrun` (`REF|ApSelectionRunData|tiltrun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImageTiltTransformData`
--

LOCK TABLES `ApImageTiltTransformData` WRITE;
/*!40000 ALTER TABLE `ApImageTiltTransformData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImageTiltTransformData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImageTransformationData`
--

DROP TABLE IF EXISTS `ApImageTransformationData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImageTransformationData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|AcquisitionImageData|image1` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image2` int(20) DEFAULT NULL,
  `shiftx` double DEFAULT NULL,
  `shifty` double DEFAULT NULL,
  `correlation` double DEFAULT NULL,
  `scale` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|AcquisitionImageData|image1` (`REF|leginondata|AcquisitionImageData|image1`),
  KEY `REF|leginondata|AcquisitionImageData|image2` (`REF|leginondata|AcquisitionImageData|image2`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImageTransformationData`
--

LOCK TABLES `ApImageTransformationData` WRITE;
/*!40000 ALTER TABLE `ApImageTransformationData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImageTransformationData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImagic3dRefineIterationData`
--

DROP TABLE IF EXISTS `ApImagic3dRefineIterationData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImagic3dRefineIterationData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApImagic3dRefineRunData|refinement_run` int(20) DEFAULT NULL,
  `iteration` int(20) DEFAULT NULL,
  `name` text,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `filt_stack` tinyint(1) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `auto_filt_stack` tinyint(1) DEFAULT NULL,
  `auto_lp_filt_fraction` double DEFAULT NULL,
  `mask_val` int(20) DEFAULT NULL,
  `mirror_refs` tinyint(1) DEFAULT NULL,
  `cent_stack` tinyint(1) DEFAULT NULL,
  `max_shift_orig` double DEFAULT NULL,
  `max_shift_this` double DEFAULT NULL,
  `sampling_parameter` int(20) DEFAULT NULL,
  `minrad` int(20) DEFAULT NULL,
  `maxrad` int(20) DEFAULT NULL,
  `spider_align` tinyint(1) DEFAULT NULL,
  `xy_search` int(20) DEFAULT NULL,
  `xy_step` int(20) DEFAULT NULL,
  `minrad_spi` int(20) DEFAULT NULL,
  `maxrad_spi` int(20) DEFAULT NULL,
  `angle_change` int(20) DEFAULT NULL,
  `ignore_images` int(20) DEFAULT NULL,
  `num_classums` int(20) DEFAULT NULL,
  `num_factors` int(20) DEFAULT NULL,
  `ignore_members` int(20) DEFAULT NULL,
  `keep_classes` int(20) DEFAULT NULL,
  `euler_ang_inc` int(20) DEFAULT NULL,
  `keep_ordered` int(20) DEFAULT NULL,
  `ham_win` double DEFAULT NULL,
  `obj_size` double DEFAULT NULL,
  `3d_lpfilt` int(20) DEFAULT NULL,
  `amask_dim` double DEFAULT NULL,
  `amask_lp` double DEFAULT NULL,
  `amask_sharp` double DEFAULT NULL,
  `amask_thresh` double DEFAULT NULL,
  `mra_ang_inc` int(20) DEFAULT NULL,
  `forw_ang_inc` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApImagic3dRefineRunData|refinement_run` (`REF|ApImagic3dRefineRunData|refinement_run`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `filt_stack` (`filt_stack`),
  KEY `auto_filt_stack` (`auto_filt_stack`),
  KEY `mirror_refs` (`mirror_refs`),
  KEY `cent_stack` (`cent_stack`),
  KEY `spider_align` (`spider_align`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImagic3dRefineIterationData`
--

LOCK TABLES `ApImagic3dRefineIterationData` WRITE;
/*!40000 ALTER TABLE `ApImagic3dRefineIterationData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImagic3dRefineIterationData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImagic3dRefineRunData`
--

DROP TABLE IF EXISTS `ApImagic3dRefineRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImagic3dRefineRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApInitialModelData|initialModel` int(20) DEFAULT NULL,
  `REF|ApStackData|stackrun` int(20) DEFAULT NULL,
  `radius` int(20) DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `description` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApInitialModelData|initialModel` (`REF|ApInitialModelData|initialModel`),
  KEY `REF|ApStackData|stackrun` (`REF|ApStackData|stackrun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImagic3dRefineRunData`
--

LOCK TABLES `ApImagic3dRefineRunData` WRITE;
/*!40000 ALTER TABLE `ApImagic3dRefineRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImagic3dRefineRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImagicAlignAnalysisData`
--

DROP TABLE IF EXISTS `ApImagicAlignAnalysisData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImagicAlignAnalysisData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `run_seconds` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `highpass` int(20) DEFAULT NULL,
  `lowpass` int(20) DEFAULT NULL,
  `mask_radius` double DEFAULT NULL,
  `mask_dropoff` double DEFAULT NULL,
  `numiters` int(20) DEFAULT NULL,
  `overcorrection` double DEFAULT NULL,
  `MSAdistance` text,
  `eigenimages` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImagicAlignAnalysisData`
--

LOCK TABLES `ApImagicAlignAnalysisData` WRITE;
/*!40000 ALTER TABLE `ApImagicAlignAnalysisData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImagicAlignAnalysisData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApImodXcorrParamsData`
--

DROP TABLE IF EXISTS `ApImodXcorrParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApImodXcorrParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `RotationAngle` double DEFAULT NULL,
  `FilterSigma1` double DEFAULT NULL,
  `FilterRadius2` double DEFAULT NULL,
  `FilterSigma2` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApImodXcorrParamsData`
--

LOCK TABLES `ApImodXcorrParamsData` WRITE;
/*!40000 ALTER TABLE `ApImodXcorrParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApImodXcorrParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApInitialModelData`
--

DROP TABLE IF EXISTS `ApInitialModelData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApInitialModelData` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPathData|path` bigint(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `name` text,
  `resolution` double DEFAULT NULL,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT '0',
  `md5sum` varchar(32) DEFAULT NULL,
  `REF|Ap3dDensityData|original_density` int(20) DEFAULT NULL,
  `REF|ApInitialModelData|original_model` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `md5sum` (`md5sum`),
  KEY `REF|projectdata|projects|project` (`REF|projectdata|projects|project`),
  KEY `hidden` (`hidden`),
  KEY `REF|Ap3dDensityData|original_density` (`REF|Ap3dDensityData|original_density`),
  KEY `REF|ApInitialModelData|original_model` (`REF|ApInitialModelData|original_model`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApInitialModelData`
--

LOCK TABLES `ApInitialModelData` WRITE;
/*!40000 ALTER TABLE `ApInitialModelData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApInitialModelData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApKerDenSOMParamsData`
--

DROP TABLE IF EXISTS `ApKerDenSOMParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApKerDenSOMParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mask_diam` double DEFAULT NULL,
  `x_dimension` int(20) DEFAULT NULL,
  `y_dimension` int(20) DEFAULT NULL,
  `convergence` text,
  `run_seconds` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApKerDenSOMParamsData`
--

LOCK TABLES `ApKerDenSOMParamsData` WRITE;
/*!40000 ALTER TABLE `ApKerDenSOMParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApKerDenSOMParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApManualParamsData`
--

DROP TABLE IF EXISTS `ApManualParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApManualParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `diam` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `invert` int(20) DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `pixel_value_limit` double DEFAULT NULL,
  `REF|ApSelectionRunData|oldselectionrun` int(20) DEFAULT NULL,
  `trace` tinyint(1) DEFAULT NULL,
  `helicalstep` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSelectionRunData|oldselectionrun` (`REF|ApSelectionRunData|oldselectionrun`),
  KEY `trace` (`trace`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApManualParamsData`
--

LOCK TABLES `ApManualParamsData` WRITE;
/*!40000 ALTER TABLE `ApManualParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApManualParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaskAssessmentData`
--

DROP TABLE IF EXISTS `ApMaskAssessmentData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaskAssessmentData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApMaskAssessmentRunData|run` int(20) DEFAULT NULL,
  `REF|ApMaskRegionData|region` int(20) DEFAULT NULL,
  `keep` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApMaskAssessmentRunData|run` (`REF|ApMaskAssessmentRunData|run`),
  KEY `REF|ApMaskRegionData|region` (`REF|ApMaskRegionData|region`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaskAssessmentData`
--

LOCK TABLES `ApMaskAssessmentData` WRITE;
/*!40000 ALTER TABLE `ApMaskAssessmentData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaskAssessmentData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaskAssessmentRunData`
--

DROP TABLE IF EXISTS `ApMaskAssessmentRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaskAssessmentRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `REF|ApMaskMakerRunData|maskrun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApMaskMakerRunData|maskrun` (`REF|ApMaskMakerRunData|maskrun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaskAssessmentRunData`
--

LOCK TABLES `ApMaskAssessmentRunData` WRITE;
/*!40000 ALTER TABLE `ApMaskAssessmentRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaskAssessmentRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaskMakerParamsData`
--

DROP TABLE IF EXISTS `ApMaskMakerParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaskMakerParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `bin` int(20) DEFAULT NULL,
  `mask_type` text,
  `pdiam` int(20) DEFAULT NULL,
  `region_diameter` int(20) DEFAULT NULL,
  `edge_blur` double DEFAULT NULL,
  `edge_low` double DEFAULT NULL,
  `edge_high` double DEFAULT NULL,
  `region_std` double DEFAULT NULL,
  `convolve` double DEFAULT NULL,
  `convex_hull` tinyint(1) DEFAULT NULL,
  `libcv` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `convex_hull` (`convex_hull`),
  KEY `libcv` (`libcv`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaskMakerParamsData`
--

LOCK TABLES `ApMaskMakerParamsData` WRITE;
/*!40000 ALTER TABLE `ApMaskMakerParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaskMakerParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaskMakerRunData`
--

DROP TABLE IF EXISTS `ApMaskMakerRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaskMakerRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApMaskMakerParamsData|params` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApMaskMakerParamsData|params` (`REF|ApMaskMakerParamsData|params`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaskMakerRunData`
--

LOCK TABLES `ApMaskMakerRunData` WRITE;
/*!40000 ALTER TABLE `ApMaskMakerRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaskMakerRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaskRegionData`
--

DROP TABLE IF EXISTS `ApMaskRegionData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaskRegionData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApMaskMakerRunData|maskrun` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `x` int(20) DEFAULT NULL,
  `y` int(20) DEFAULT NULL,
  `area` int(20) DEFAULT NULL,
  `perimeter` int(20) DEFAULT NULL,
  `mean` double DEFAULT NULL,
  `stdev` double DEFAULT NULL,
  `label` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApMaskMakerRunData|maskrun` (`REF|ApMaskMakerRunData|maskrun`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaskRegionData`
--

LOCK TABLES `ApMaskRegionData` WRITE;
/*!40000 ALTER TABLE `ApMaskRegionData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaskRegionData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaxLikeJobData`
--

DROP TABLE IF EXISTS `ApMaxLikeJobData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaxLikeJobData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `timestamp` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `finished` tinyint(1) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `finished` (`finished`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaxLikeJobData`
--

LOCK TABLES `ApMaxLikeJobData` WRITE;
/*!40000 ALTER TABLE `ApMaxLikeJobData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaxLikeJobData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMaxLikeRunData`
--

DROP TABLE IF EXISTS `ApMaxLikeRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMaxLikeRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `mirror` tinyint(1) DEFAULT NULL,
  `student` tinyint(1) DEFAULT NULL,
  `mask_diam` int(20) DEFAULT NULL,
  `init_method` text,
  `fast` tinyint(1) DEFAULT NULL,
  `fastmode` text,
  `run_seconds` int(20) DEFAULT NULL,
  `REF|ApMaxLikeJobData|job` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `mirror` (`mirror`),
  KEY `student` (`student`),
  KEY `fast` (`fast`),
  KEY `REF|ApMaxLikeJobData|job` (`REF|ApMaxLikeJobData|job`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMaxLikeRunData`
--

LOCK TABLES `ApMaxLikeRunData` WRITE;
/*!40000 ALTER TABLE `ApMaxLikeRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMaxLikeRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMiscData`
--

DROP TABLE IF EXISTS `ApMiscData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMiscData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `REF|ApRefineRunData|refineRun` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApFullTomogramData|fulltomogram` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `name` text,
  `description` text,
  `md5sum` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApRefineRunData|refineRun` (`REF|ApRefineRunData|refineRun`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApFullTomogramData|fulltomogram` (`REF|ApFullTomogramData|fulltomogram`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMiscData`
--

LOCK TABLES `ApMiscData` WRITE;
/*!40000 ALTER TABLE `ApMiscData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMiscData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMultiModelRefineRunData`
--

DROP TABLE IF EXISTS `ApMultiModelRefineRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMultiModelRefineRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `num_refinements` int(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMultiModelRefineRunData`
--

LOCK TABLES `ApMultiModelRefineRunData` WRITE;
/*!40000 ALTER TABLE `ApMultiModelRefineRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMultiModelRefineRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApMultiRefAlignRunData`
--

DROP TABLE IF EXISTS `ApMultiRefAlignRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApMultiRefAlignRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `lowpass_refs` int(20) DEFAULT NULL,
  `thresh_refs` int(20) DEFAULT NULL,
  `maskrad_refs` double DEFAULT NULL,
  `mirror` tinyint(1) DEFAULT NULL,
  `center` tinyint(1) DEFAULT NULL,
  `alignment_type` text,
  `first_alignment` text,
  `num_orientations` int(20) DEFAULT NULL,
  `max_shift_orig` double DEFAULT NULL,
  `max_shift_this` double DEFAULT NULL,
  `samp_param` double DEFAULT NULL,
  `min_radius` double DEFAULT NULL,
  `max_radius` double DEFAULT NULL,
  `numiter` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `mirror` (`mirror`),
  KEY `center` (`center`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApMultiRefAlignRunData`
--

LOCK TABLES `ApMultiRefAlignRunData` WRITE;
/*!40000 ALTER TABLE `ApMultiRefAlignRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApMultiRefAlignRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApOtrRunData`
--

DROP TABLE IF EXISTS `ApOtrRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApOtrRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `classnums` text,
  `numiter` int(20) DEFAULT NULL,
  `euleriter` int(20) DEFAULT NULL,
  `maskrad` int(20) DEFAULT NULL,
  `lowpassvol` double DEFAULT NULL,
  `highpasspart` double DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `description` text,
  `numpart` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApResolutionData|fsc_resolution` int(20) DEFAULT NULL,
  `REF|ApResolutionData|rmeasure_resolution` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|tiltstack` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `REF|ApClusteringStackData|clusterstack` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApResolutionData|fsc_resolution` (`REF|ApResolutionData|fsc_resolution`),
  KEY `REF|ApResolutionData|rmeasure_resolution` (`REF|ApResolutionData|rmeasure_resolution`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|tiltstack` (`REF|ApStackData|tiltstack`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `REF|ApClusteringStackData|clusterstack` (`REF|ApClusteringStackData|clusterstack`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApOtrRunData`
--

LOCK TABLES `ApOtrRunData` WRITE;
/*!40000 ALTER TABLE `ApOtrRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApOtrRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApParticleData`
--

DROP TABLE IF EXISTS `ApParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApSelectionRunData|selectionrun` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `xcoord` int(20) DEFAULT NULL,
  `ycoord` int(20) DEFAULT NULL,
  `angle` double DEFAULT NULL,
  `correlation` double DEFAULT NULL,
  `REF|ApTemplateImageData|template` int(20) DEFAULT NULL,
  `peakmoment` double DEFAULT NULL,
  `peakstddev` double DEFAULT NULL,
  `peakarea` int(20) DEFAULT NULL,
  `diameter` double DEFAULT NULL,
  `label` text,
  `helixnum` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSelectionRunData|selectionrun` (`REF|ApSelectionRunData|selectionrun`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`),
  KEY `REF|ApTemplateImageData|template` (`REF|ApTemplateImageData|template`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApParticleData`
--

LOCK TABLES `ApParticleData` WRITE;
/*!40000 ALTER TABLE `ApParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApParticleExtractorData`
--

DROP TABLE IF EXISTS `ApParticleExtractorData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApParticleExtractorData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `boxSize` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `aceCutoff` double DEFAULT NULL,
  `correlationMin` double DEFAULT NULL,
  `correlationMax` double DEFAULT NULL,
  `checkMask` text,
  `checkImage` tinyint(1) DEFAULT NULL,
  `norejects` tinyint(1) DEFAULT NULL,
  `minDefocus` double DEFAULT NULL,
  `maxDefocus` double DEFAULT NULL,
  `defocpair` tinyint(1) DEFAULT NULL,
  `tiltangle` text,
  `rotate` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `checkImage` (`checkImage`),
  KEY `norejects` (`norejects`),
  KEY `defocpair` (`defocpair`),
  KEY `rotate` (`rotate`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApParticleExtractorData`
--

LOCK TABLES `ApParticleExtractorData` WRITE;
/*!40000 ALTER TABLE `ApParticleExtractorData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApParticleExtractorData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApParticleMovieData`
--

DROP TABLE IF EXISTS `ApParticleMovieData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApParticleMovieData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `movieNumber` int(20) DEFAULT NULL,
  `REF|ApParticleMovieRunData|movieRun` int(20) DEFAULT NULL,
  `REF|ApParticleData|particle` int(20) DEFAULT NULL,
  `format` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApParticleMovieRunData|movieRun` (`REF|ApParticleMovieRunData|movieRun`),
  KEY `REF|ApParticleData|particle` (`REF|ApParticleData|particle`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApParticleMovieData`
--

LOCK TABLES `ApParticleMovieData` WRITE;
/*!40000 ALTER TABLE `ApParticleMovieData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApParticleMovieData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApParticleMovieParamsData`
--

DROP TABLE IF EXISTS `ApParticleMovieParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApParticleMovieParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `boxSize` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `aceCutoff` double DEFAULT NULL,
  `correlationMin` double DEFAULT NULL,
  `correlationMax` double DEFAULT NULL,
  `checkMask` text,
  `checkImage` tinyint(1) DEFAULT NULL,
  `norejects` tinyint(1) DEFAULT NULL,
  `minDefocus` double DEFAULT NULL,
  `maxDefocus` double DEFAULT NULL,
  `defocpair` tinyint(1) DEFAULT NULL,
  `tiltangle` text,
  `rotate` tinyint(1) DEFAULT NULL,
  `frameavg` int(20) DEFAULT NULL,
  `framestep` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `checkImage` (`checkImage`),
  KEY `norejects` (`norejects`),
  KEY `defocpair` (`defocpair`),
  KEY `rotate` (`rotate`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApParticleMovieParamsData`
--

LOCK TABLES `ApParticleMovieParamsData` WRITE;
/*!40000 ALTER TABLE `ApParticleMovieParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApParticleMovieParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApParticleMovieRunData`
--

DROP TABLE IF EXISTS `ApParticleMovieRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApParticleMovieRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `movieRunName` text,
  `REF|ApParticleMovieParamsData|movieParams` int(20) DEFAULT NULL,
  `REF|ApSelectionRunData|selectionrun` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApParticleMovieParamsData|movieParams` (`REF|ApParticleMovieParamsData|movieParams`),
  KEY `REF|ApSelectionRunData|selectionrun` (`REF|ApSelectionRunData|selectionrun`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApParticleMovieRunData`
--

LOCK TABLES `ApParticleMovieRunData` WRITE;
/*!40000 ALTER TABLE `ApParticleMovieRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApParticleMovieRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApPathData`
--

DROP TABLE IF EXISTS `ApPathData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApPathData` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `path` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `path_index32` (`path`(32))
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApPathData`
--

LOCK TABLES `ApPathData` WRITE;
/*!40000 ALTER TABLE `ApPathData` DISABLE KEYS */;
INSERT INTO `ApPathData` VALUES (1,'2015-10-05 17:02:57','/emg/data/leginon/06jul12a/rawdata'),(2,'2015-10-05 17:02:57','/usr/lib64/python2.6/site-packages');
/*!40000 ALTER TABLE `ApPathData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApPrepRefineData`
--

DROP TABLE IF EXISTS `ApPrepRefineData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApPrepRefineData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApAppionJobData|job` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `method` text,
  `description` text,
  `REF|ApRefineIterData|paramiter` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApAppionJobData|job` (`REF|ApAppionJobData|job`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApRefineIterData|paramiter` (`REF|ApRefineIterData|paramiter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApPrepRefineData`
--

LOCK TABLES `ApPrepRefineData` WRITE;
/*!40000 ALTER TABLE `ApPrepRefineData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApPrepRefineData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApProtomoAlignerParamsData`
--

DROP TABLE IF EXISTS `ApProtomoAlignerParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApProtomoAlignerParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAlignmentRunData|alignrun` int(20) DEFAULT NULL,
  `REF|ApProtomoParamsData|protomo` int(20) DEFAULT NULL,
  `REF|ApProtomoRefinementParamsData|refine_cycle` int(20) DEFAULT NULL,
  `REF|ApProtomoRefinementParamsData|good_cycle` int(20) DEFAULT NULL,
  `good_start` int(20) DEFAULT NULL,
  `good_end` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAlignmentRunData|alignrun` (`REF|ApTomoAlignmentRunData|alignrun`),
  KEY `REF|ApProtomoParamsData|protomo` (`REF|ApProtomoParamsData|protomo`),
  KEY `REF|ApProtomoRefinementParamsData|refine_cycle` (`REF|ApProtomoRefinementParamsData|refine_cycle`),
  KEY `REF|ApProtomoRefinementParamsData|good_cycle` (`REF|ApProtomoRefinementParamsData|good_cycle`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApProtomoAlignerParamsData`
--

LOCK TABLES `ApProtomoAlignerParamsData` WRITE;
/*!40000 ALTER TABLE `ApProtomoAlignerParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApProtomoAlignerParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApProtomoAlignmentData`
--

DROP TABLE IF EXISTS `ApProtomoAlignmentData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApProtomoAlignmentData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAlignerParamsData|aligner` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `number` int(20) DEFAULT NULL,
  `rotation` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAlignerParamsData|aligner` (`REF|ApTomoAlignerParamsData|aligner`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApProtomoAlignmentData`
--

LOCK TABLES `ApProtomoAlignmentData` WRITE;
/*!40000 ALTER TABLE `ApProtomoAlignmentData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApProtomoAlignmentData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApProtomoModelData`
--

DROP TABLE IF EXISTS `ApProtomoModelData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApProtomoModelData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAlignerParamsData|aligner` int(20) DEFAULT NULL,
  `psi` double DEFAULT NULL,
  `theta` double DEFAULT NULL,
  `phi` double DEFAULT NULL,
  `azimuth` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAlignerParamsData|aligner` (`REF|ApTomoAlignerParamsData|aligner`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApProtomoModelData`
--

LOCK TABLES `ApProtomoModelData` WRITE;
/*!40000 ALTER TABLE `ApProtomoModelData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApProtomoModelData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApProtomoParamsData`
--

DROP TABLE IF EXISTS `ApProtomoParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApProtomoParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `series_name` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApProtomoParamsData`
--

LOCK TABLES `ApProtomoParamsData` WRITE;
/*!40000 ALTER TABLE `ApProtomoParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApProtomoParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApProtomoRefinementParamsData`
--

DROP TABLE IF EXISTS `ApProtomoRefinementParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApProtomoRefinementParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApProtomoParamsData|protomo` int(20) DEFAULT NULL,
  `cycle` int(20) DEFAULT NULL,
  `alismp` double DEFAULT NULL,
  `cormod` text,
  `imgref` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|reference` int(20) DEFAULT NULL,
  `SUBD|alibox|x` double DEFAULT NULL,
  `SUBD|alibox|y` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApProtomoParamsData|protomo` (`REF|ApProtomoParamsData|protomo`),
  KEY `REF|leginondata|AcquisitionImageData|reference` (`REF|leginondata|AcquisitionImageData|reference`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApProtomoRefinementParamsData`
--

LOCK TABLES `ApProtomoRefinementParamsData` WRITE;
/*!40000 ALTER TABLE `ApProtomoRefinementParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApProtomoRefinementParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRMeasureData`
--

DROP TABLE IF EXISTS `ApRMeasureData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRMeasureData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `volume` text,
  `rMeasure` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRMeasureData`
--

LOCK TABLES `ApRMeasureData` WRITE;
/*!40000 ALTER TABLE `ApRMeasureData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRMeasureData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRaptorParamsData`
--

DROP TABLE IF EXISTS `ApRaptorParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRaptorParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `markersize` int(20) DEFAULT NULL,
  `markernumber` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRaptorParamsData`
--

LOCK TABLES `ApRaptorParamsData` WRITE;
/*!40000 ALTER TABLE `ApRaptorParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRaptorParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRctRunData`
--

DROP TABLE IF EXISTS `ApRctRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRctRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `classnums` text,
  `numiter` int(20) DEFAULT NULL,
  `maskrad` int(20) DEFAULT NULL,
  `lowpassvol` double DEFAULT NULL,
  `highpasspart` double DEFAULT NULL,
  `lowpasspart` double DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `description` text,
  `numpart` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApResolutionData|fsc_resolution` int(20) DEFAULT NULL,
  `REF|ApResolutionData|rmeasure_resolution` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|tiltstack` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `REF|ApClusteringStackData|clusterstack` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApResolutionData|fsc_resolution` (`REF|ApResolutionData|fsc_resolution`),
  KEY `REF|ApResolutionData|rmeasure_resolution` (`REF|ApResolutionData|rmeasure_resolution`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|tiltstack` (`REF|ApStackData|tiltstack`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `REF|ApClusteringStackData|clusterstack` (`REF|ApClusteringStackData|clusterstack`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRctRunData`
--

LOCK TABLES `ApRctRunData` WRITE;
/*!40000 ALTER TABLE `ApRctRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRctRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefBasedRunData`
--

DROP TABLE IF EXISTS `ApRefBasedRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefBasedRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `mask_diam` int(20) DEFAULT NULL,
  `xysearch` int(20) DEFAULT NULL,
  `xystep` int(20) DEFAULT NULL,
  `first_ring` int(20) DEFAULT NULL,
  `last_ring` int(20) DEFAULT NULL,
  `num_iter` int(20) DEFAULT NULL,
  `invert_templs` tinyint(1) DEFAULT NULL,
  `num_templs` int(20) DEFAULT NULL,
  `csym` int(20) DEFAULT NULL,
  `run_seconds` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `invert_templs` (`invert_templs`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefBasedRunData`
--

LOCK TABLES `ApRefBasedRunData` WRITE;
/*!40000 ALTER TABLE `ApRefBasedRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefBasedRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineGoodBadParticleData`
--

DROP TABLE IF EXISTS `ApRefineGoodBadParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineGoodBadParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApRefineIterData|refine` int(20) DEFAULT NULL,
  `good_refine` int(20) DEFAULT NULL,
  `bad_refine` int(20) DEFAULT NULL,
  `good_postRefine` int(20) DEFAULT NULL,
  `bad_postRefine` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApRefineIterData|refine` (`REF|ApRefineIterData|refine`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineGoodBadParticleData`
--

LOCK TABLES `ApRefineGoodBadParticleData` WRITE;
/*!40000 ALTER TABLE `ApRefineGoodBadParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineGoodBadParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineInitModelData`
--

DROP TABLE IF EXISTS `ApRefineInitModelData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineInitModelData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPrepRefineData|preprefine` int(20) DEFAULT NULL,
  `REF|ApInitialModelData|refmodel` int(20) DEFAULT NULL,
  `filename` text,
  `format` text,
  `apix` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPrepRefineData|preprefine` (`REF|ApPrepRefineData|preprefine`),
  KEY `REF|ApInitialModelData|refmodel` (`REF|ApInitialModelData|refmodel`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineInitModelData`
--

LOCK TABLES `ApRefineInitModelData` WRITE;
/*!40000 ALTER TABLE `ApRefineInitModelData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineInitModelData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineIterData`
--

DROP TABLE IF EXISTS `ApRefineIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `iteration` int(20) DEFAULT NULL,
  `exemplar` tinyint(1) DEFAULT NULL,
  `angularSamplingRate` int(20) DEFAULT NULL,
  `mask` int(20) DEFAULT NULL,
  `imask` int(20) DEFAULT NULL,
  `alignmentInnerRadius` int(20) DEFAULT NULL,
  `alignmentOuterRadius` int(20) DEFAULT NULL,
  `volumeDensity` text,
  `refineClassAverages` text,
  `postRefineClassAverages` text,
  `classVariance` text,
  `REF|ApSymmetryData|symmetry` int(20) DEFAULT NULL,
  `REF|ApRefineRunData|refineRun` int(20) DEFAULT NULL,
  `REF|ApResolutionData|resolution` int(20) DEFAULT NULL,
  `REF|ApRMeasureData|rMeasure` int(20) DEFAULT NULL,
  `REF|ApEmanRefineIterData|emanParams` int(20) DEFAULT NULL,
  `REF|ApXmippRefineIterData|xmippParams` int(20) DEFAULT NULL,
  `REF|ApFrealignIterData|frealignParams` int(20) DEFAULT NULL,
  `REF|ApXmippML3DRefineIterData|xmippML3DParams` int(20) DEFAULT NULL,
  `REF|ApRelionIterData|relionParams` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `exemplar` (`exemplar`),
  KEY `REF|ApSymmetryData|symmetry` (`REF|ApSymmetryData|symmetry`),
  KEY `REF|ApRefineRunData|refineRun` (`REF|ApRefineRunData|refineRun`),
  KEY `REF|ApResolutionData|resolution` (`REF|ApResolutionData|resolution`),
  KEY `REF|ApRMeasureData|rMeasure` (`REF|ApRMeasureData|rMeasure`),
  KEY `REF|ApEmanRefineIterData|emanParams` (`REF|ApEmanRefineIterData|emanParams`),
  KEY `REF|ApXmippRefineIterData|xmippParams` (`REF|ApXmippRefineIterData|xmippParams`),
  KEY `REF|ApFrealignIterData|frealignParams` (`REF|ApFrealignIterData|frealignParams`),
  KEY `REF|ApXmippML3DRefineIterData|xmippML3DParams` (`REF|ApXmippML3DRefineIterData|xmippML3DParams`),
  KEY `REF|ApRelionIterData|relionParams` (`REF|ApRelionIterData|relionParams`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineIterData`
--

LOCK TABLES `ApRefineIterData` WRITE;
/*!40000 ALTER TABLE `ApRefineIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineMaskVolData`
--

DROP TABLE IF EXISTS `ApRefineMaskVolData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineMaskVolData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPrepRefineData|preprefine` int(20) DEFAULT NULL,
  `REF|ApInitialModelData|refmodel` int(20) DEFAULT NULL,
  `filename` text,
  `format` text,
  `apix` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPrepRefineData|preprefine` (`REF|ApPrepRefineData|preprefine`),
  KEY `REF|ApInitialModelData|refmodel` (`REF|ApInitialModelData|refmodel`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineMaskVolData`
--

LOCK TABLES `ApRefineMaskVolData` WRITE;
/*!40000 ALTER TABLE `ApRefineMaskVolData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineMaskVolData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineParticleData`
--

DROP TABLE IF EXISTS `ApRefineParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApRefineIterData|refineIter` int(20) DEFAULT NULL,
  `REF|ApMultiModelRefineRunData|multiModelRefineRun` int(20) DEFAULT NULL,
  `REF|ApRefineReferenceData|reference_number` int(20) DEFAULT NULL,
  `REF|ApStackParticleData|particle` int(20) DEFAULT NULL,
  `shiftx` double DEFAULT NULL,
  `shifty` double DEFAULT NULL,
  `euler1` double DEFAULT NULL,
  `euler2` double DEFAULT NULL,
  `euler3` double DEFAULT NULL,
  `quality_factor` double DEFAULT NULL,
  `phase_residual` double DEFAULT NULL,
  `mirror` tinyint(1) DEFAULT NULL,
  `3Dref_num` int(20) DEFAULT NULL,
  `2Dclass_num` int(20) DEFAULT NULL,
  `refine_keep` tinyint(1) DEFAULT NULL,
  `postRefine_keep` tinyint(1) DEFAULT NULL,
  `euler_convention` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApRefineIterData|refineIter` (`REF|ApRefineIterData|refineIter`),
  KEY `REF|ApMultiModelRefineRunData|multiModelRefineRun` (`REF|ApMultiModelRefineRunData|multiModelRefineRun`),
  KEY `REF|ApRefineReferenceData|reference_number` (`REF|ApRefineReferenceData|reference_number`),
  KEY `REF|ApStackParticleData|particle` (`REF|ApStackParticleData|particle`),
  KEY `mirror` (`mirror`),
  KEY `refine_keep` (`refine_keep`),
  KEY `postRefine_keep` (`postRefine_keep`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineParticleData`
--

LOCK TABLES `ApRefineParticleData` WRITE;
/*!40000 ALTER TABLE `ApRefineParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineReferenceData`
--

DROP TABLE IF EXISTS `ApRefineReferenceData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineReferenceData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `volumeDensityStart` text,
  `volumeDensityEnd` text,
  `reference_number` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApRefineIterData|iteration` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApRefineIterData|iteration` (`REF|ApRefineIterData|iteration`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineReferenceData`
--

LOCK TABLES `ApRefineReferenceData` WRITE;
/*!40000 ALTER TABLE `ApRefineReferenceData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineReferenceData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineRunData`
--

DROP TABLE IF EXISTS `ApRefineRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `package` text,
  `description` text,
  `num_iter` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `reference_number` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApInitialModelData|initialModel` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApAppionJobData|job` int(20) DEFAULT NULL,
  `REF|ApMultiModelRefineRunData|multiModelRefineRun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApInitialModelData|initialModel` (`REF|ApInitialModelData|initialModel`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApAppionJobData|job` (`REF|ApAppionJobData|job`),
  KEY `REF|ApMultiModelRefineRunData|multiModelRefineRun` (`REF|ApMultiModelRefineRunData|multiModelRefineRun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineRunData`
--

LOCK TABLES `ApRefineRunData` WRITE;
/*!40000 ALTER TABLE `ApRefineRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRefineStackData`
--

DROP TABLE IF EXISTS `ApRefineStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRefineStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPrepRefineData|preprefine` int(20) DEFAULT NULL,
  `REF|ApStackData|stackref` int(20) DEFAULT NULL,
  `filename` text,
  `bin` int(20) DEFAULT NULL,
  `lowpass` double DEFAULT NULL,
  `highpass` double DEFAULT NULL,
  `last_part` int(20) DEFAULT NULL,
  `format` text,
  `apix` double DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `cs` double DEFAULT NULL,
  `recon` tinyint(1) DEFAULT NULL,
  `phaseflipped` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPrepRefineData|preprefine` (`REF|ApPrepRefineData|preprefine`),
  KEY `REF|ApStackData|stackref` (`REF|ApStackData|stackref`),
  KEY `recon` (`recon`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRefineStackData`
--

LOCK TABLES `ApRefineStackData` WRITE;
/*!40000 ALTER TABLE `ApRefineStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRefineStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRelionIterData`
--

DROP TABLE IF EXISTS `ApRelionIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRelionIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `ini_high` int(20) DEFAULT NULL,
  `ctf` tinyint(1) DEFAULT NULL,
  `offset_step` int(20) DEFAULT NULL,
  `auto_local_healpix_order` int(20) DEFAULT NULL,
  `healpix_order` int(20) DEFAULT NULL,
  `offset_range` int(20) DEFAULT NULL,
  `ctf_intact_first_peak` tinyint(1) DEFAULT NULL,
  `ctf_corrected_ref` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRelionIterData`
--

LOCK TABLES `ApRelionIterData` WRITE;
/*!40000 ALTER TABLE `ApRelionIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRelionIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApResolutionData`
--

DROP TABLE IF EXISTS `ApResolutionData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApResolutionData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `fscfile` text,
  `half` double DEFAULT NULL,
  `type` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApResolutionData`
--

LOCK TABLES `ApResolutionData` WRITE;
/*!40000 ALTER TABLE `ApResolutionData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApResolutionData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRotKerDenSOMParamsData`
--

DROP TABLE IF EXISTS `ApRotKerDenSOMParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRotKerDenSOMParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `mask_diam` double DEFAULT NULL,
  `x_dimension` int(20) DEFAULT NULL,
  `y_dimension` int(20) DEFAULT NULL,
  `convergence` text,
  `run_seconds` int(20) DEFAULT NULL,
  `initregulfact` double DEFAULT NULL,
  `finalregulfact` double DEFAULT NULL,
  `incrementregulfact` int(20) DEFAULT NULL,
  `spectrainnerradius` int(20) DEFAULT NULL,
  `spectraouterradius` int(20) DEFAULT NULL,
  `spectralowharmonic` int(20) DEFAULT NULL,
  `spectrahighharmonic` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRotKerDenSOMParamsData`
--

LOCK TABLES `ApRotKerDenSOMParamsData` WRITE;
/*!40000 ALTER TABLE `ApRotKerDenSOMParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRotKerDenSOMParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApRunsInStackData`
--

DROP TABLE IF EXISTS `ApRunsInStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApRunsInStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApStackRunData|stackRun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApStackRunData|stackRun` (`REF|ApStackRunData|stackRun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApRunsInStackData`
--

LOCK TABLES `ApRunsInStackData` WRITE;
/*!40000 ALTER TABLE `ApRunsInStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApRunsInStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSelectionParamsData`
--

DROP TABLE IF EXISTS `ApSelectionParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSelectionParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `diam` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `manual_thresh` double DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `invert` int(20) DEFAULT NULL,
  `max_peaks` int(20) DEFAULT NULL,
  `max_threshold` double DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `pixel_value_limit` double DEFAULT NULL,
  `maxsize` int(20) DEFAULT NULL,
  `defocal_pairs` tinyint(1) DEFAULT NULL,
  `overlapmult` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `defocal_pairs` (`defocal_pairs`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSelectionParamsData`
--

LOCK TABLES `ApSelectionParamsData` WRITE;
/*!40000 ALTER TABLE `ApSelectionParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSelectionParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSelectionRunData`
--

DROP TABLE IF EXISTS `ApSelectionRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSelectionRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApSelectionParamsData|params` int(20) DEFAULT NULL,
  `REF|ApDogParamsData|dogparams` int(20) DEFAULT NULL,
  `REF|ApManualParamsData|manparams` int(20) DEFAULT NULL,
  `REF|ApTiltAlignParamsData|tiltparams` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApSelectionParamsData|params` (`REF|ApSelectionParamsData|params`),
  KEY `REF|ApDogParamsData|dogparams` (`REF|ApDogParamsData|dogparams`),
  KEY `REF|ApManualParamsData|manparams` (`REF|ApManualParamsData|manparams`),
  KEY `REF|ApTiltAlignParamsData|tiltparams` (`REF|ApTiltAlignParamsData|tiltparams`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSelectionRunData`
--

LOCK TABLES `ApSelectionRunData` WRITE;
/*!40000 ALTER TABLE `ApSelectionRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSelectionRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSizingRunData`
--

DROP TABLE IF EXISTS `ApSizingRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSizingRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `method` text,
  `REF|ApSelectionRunData|tracerun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApSelectionRunData|tracerun` (`REF|ApSelectionRunData|tracerun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSizingRunData`
--

LOCK TABLES `ApSizingRunData` WRITE;
/*!40000 ALTER TABLE `ApSizingRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSizingRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSparxISACJobData`
--

DROP TABLE IF EXISTS `ApSparxISACJobData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSparxISACJobData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `timestamp` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `finished` tinyint(1) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `finished` (`finished`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSparxISACJobData`
--

LOCK TABLES `ApSparxISACJobData` WRITE;
/*!40000 ALTER TABLE `ApSparxISACJobData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSparxISACJobData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSparxISACRunData`
--

DROP TABLE IF EXISTS `ApSparxISACRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSparxISACRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApSparxISACJobData|job` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstackid` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSparxISACJobData|job` (`REF|ApSparxISACJobData|job`),
  KEY `REF|ApAlignStackData|alignstackid` (`REF|ApAlignStackData|alignstackid`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSparxISACRunData`
--

LOCK TABLES `ApSparxISACRunData` WRITE;
/*!40000 ALTER TABLE `ApSparxISACRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSparxISACRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSpiderClusteringParamsData`
--

DROP TABLE IF EXISTS `ApSpiderClusteringParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSpiderClusteringParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `factor_list` text,
  `method` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSpiderClusteringParamsData`
--

LOCK TABLES `ApSpiderClusteringParamsData` WRITE;
/*!40000 ALTER TABLE `ApSpiderClusteringParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSpiderClusteringParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSpiderNoRefRunData`
--

DROP TABLE IF EXISTS `ApSpiderNoRefRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSpiderNoRefRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `particle_diam` double DEFAULT NULL,
  `first_ring` int(20) DEFAULT NULL,
  `last_ring` int(20) DEFAULT NULL,
  `run_seconds` int(20) DEFAULT NULL,
  `init_method` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSpiderNoRefRunData`
--

LOCK TABLES `ApSpiderNoRefRunData` WRITE;
/*!40000 ALTER TABLE `ApSpiderNoRefRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSpiderNoRefRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApStackData`
--

DROP TABLE IF EXISTS `ApStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `name` text,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApStackData|oldstack` int(20) DEFAULT NULL,
  `substackname` text,
  `pixelsize` double DEFAULT NULL,
  `centered` tinyint(1) DEFAULT NULL,
  `junksorted` tinyint(1) DEFAULT NULL,
  `beamtilt_corrected` tinyint(1) DEFAULT NULL,
  `mask` int(20) DEFAULT NULL,
  `maxshift` int(20) DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApStackData|oldstack` (`REF|ApStackData|oldstack`),
  KEY `centered` (`centered`),
  KEY `junksorted` (`junksorted`),
  KEY `beamtilt_corrected` (`beamtilt_corrected`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApStackData`
--

LOCK TABLES `ApStackData` WRITE;
/*!40000 ALTER TABLE `ApStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApStackFormatData`
--

DROP TABLE IF EXISTS `ApStackFormatData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApStackFormatData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApPathData|eman` int(20) DEFAULT NULL,
  `REF|ApPathData|spider` int(20) DEFAULT NULL,
  `REF|ApPathData|xmipp` int(20) DEFAULT NULL,
  `REF|ApPathData|frealign` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApPathData|eman` (`REF|ApPathData|eman`),
  KEY `REF|ApPathData|spider` (`REF|ApPathData|spider`),
  KEY `REF|ApPathData|xmipp` (`REF|ApPathData|xmipp`),
  KEY `REF|ApPathData|frealign` (`REF|ApPathData|frealign`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApStackFormatData`
--

LOCK TABLES `ApStackFormatData` WRITE;
/*!40000 ALTER TABLE `ApStackFormatData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApStackFormatData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApStackParamsData`
--

DROP TABLE IF EXISTS `ApStackParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApStackParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `boxSize` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `aceCutoff` double DEFAULT NULL,
  `correlationMin` double DEFAULT NULL,
  `correlationMax` double DEFAULT NULL,
  `checkMask` text,
  `checkImage` tinyint(1) DEFAULT NULL,
  `norejects` tinyint(1) DEFAULT NULL,
  `minDefocus` double DEFAULT NULL,
  `maxDefocus` double DEFAULT NULL,
  `defocpair` tinyint(1) DEFAULT NULL,
  `tiltangle` text,
  `rotate` tinyint(1) DEFAULT NULL,
  `phaseFlipped` tinyint(1) DEFAULT NULL,
  `fliptype` text,
  `fileType` text,
  `inverted` tinyint(1) DEFAULT NULL,
  `normalized` tinyint(1) DEFAULT NULL,
  `xmipp-norm` double DEFAULT NULL,
  `lowpass` double DEFAULT NULL,
  `highpass` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `checkImage` (`checkImage`),
  KEY `norejects` (`norejects`),
  KEY `defocpair` (`defocpair`),
  KEY `rotate` (`rotate`),
  KEY `phaseFlipped` (`phaseFlipped`),
  KEY `inverted` (`inverted`),
  KEY `normalized` (`normalized`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApStackParamsData`
--

LOCK TABLES `ApStackParamsData` WRITE;
/*!40000 ALTER TABLE `ApStackParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApStackParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApStackParticleData`
--

DROP TABLE IF EXISTS `ApStackParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApStackParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `particleNumber` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApStackRunData|stackRun` int(20) DEFAULT NULL,
  `REF|ApParticleData|particle` int(20) DEFAULT NULL,
  `mean` double DEFAULT NULL,
  `stdev` double DEFAULT NULL,
  `min` double DEFAULT NULL,
  `max` double DEFAULT NULL,
  `skew` double DEFAULT NULL,
  `kurtosis` double DEFAULT NULL,
  `edgemean` double DEFAULT NULL,
  `edgestdev` double DEFAULT NULL,
  `centermean` double DEFAULT NULL,
  `centerstdev` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApStackRunData|stackRun` (`REF|ApStackRunData|stackRun`),
  KEY `REF|ApParticleData|particle` (`REF|ApParticleData|particle`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApStackParticleData`
--

LOCK TABLES `ApStackParticleData` WRITE;
/*!40000 ALTER TABLE `ApStackParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApStackParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApStackRunData`
--

DROP TABLE IF EXISTS `ApStackRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApStackRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `stackRunName` text,
  `REF|ApStackParamsData|stackParams` int(20) DEFAULT NULL,
  `REF|ApSyntheticStackParamsData|syntheticStackParams` int(20) DEFAULT NULL,
  `REF|ApSelectionRunData|selectionrun` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApStackParamsData|stackParams` (`REF|ApStackParamsData|stackParams`),
  KEY `REF|ApSyntheticStackParamsData|syntheticStackParams` (`REF|ApSyntheticStackParamsData|syntheticStackParams`),
  KEY `REF|ApSelectionRunData|selectionrun` (`REF|ApSelectionRunData|selectionrun`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApStackRunData`
--

LOCK TABLES `ApStackRunData` WRITE;
/*!40000 ALTER TABLE `ApStackRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApStackRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSubTomogramRunData`
--

DROP TABLE IF EXISTS `ApSubTomogramRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSubTomogramRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|ApSelectionRunData|pick` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `runname` text,
  `invert` tinyint(1) DEFAULT NULL,
  `subbin` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApSelectionRunData|pick` (`REF|ApSelectionRunData|pick`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `invert` (`invert`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSubTomogramRunData`
--

LOCK TABLES `ApSubTomogramRunData` WRITE;
/*!40000 ALTER TABLE `ApSubTomogramRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSubTomogramRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSymmetryData`
--

DROP TABLE IF EXISTS `ApSymmetryData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSymmetryData` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `eman_name` varchar(8) DEFAULT NULL,
  `fold_symmetry` int(11) DEFAULT NULL,
  `symmetry` text,
  `description` text,
  PRIMARY KEY (`DEF_id`),
  UNIQUE KEY `symmetry` (`symmetry`(12)),
  KEY `eman_name` (`eman_name`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=34 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSymmetryData`
--

LOCK TABLES `ApSymmetryData` WRITE;
/*!40000 ALTER TABLE `ApSymmetryData` DISABLE KEYS */;
INSERT INTO `ApSymmetryData` VALUES (1,'2015-10-05 17:02:51','c1',1,'C1','Asymmetric'),(2,'2015-10-05 17:02:51','icos',60,'Icos (5 3 2) EMAN','EMAN icosahedral convention: 5-fold along the z axis, 2-fold along the x and y axes. Symmetries along the xz-plane are 2, 3, 5, 2, 5.'),(3,'2015-10-05 17:02:51','icos',60,'Icos (2 3 5) Viper/3DEM','Viper/3DEM icosahedral convention: 2-fold icosahedral symmetry along the x, y, and z axes, front-most 5-fold vertices in yz plane. Symmetries along the xz-plane are 5, 3, 2, 3, 5.'),(4,'2015-10-05 17:02:51','icos',60,'Icos (2 5 3) Crowther','Crowther icosahedral convention. 2-fold icosahedral symmetry along the x, y, and z axes, front-most 5-fold vertices in xz plane. Symmetries along the xz-plane are 2, 5, 3, 2, 3.'),(5,'2015-10-05 17:02:51','oct',8,'Oct','Octahedral symmetry. 4-fold octahedral symmetry along the x, y, and z axes.'),(6,'2015-10-05 17:02:51','c2',2,'C2 (z)','2-fold symmetry along the z axis'),(7,'2015-10-05 17:02:51','c3',3,'C3 (z)','3-fold symmetry along the z axis'),(8,'2015-10-05 17:02:51','c4',4,'C4 (z)','4-fold symmetry along the z axis'),(9,'2015-10-05 17:02:51','c5',5,'C5 (z)','5-fold symmetry along the z axis'),(10,'2015-10-05 17:02:51','c6',6,'C6 (z)','6-fold symmetry along the z axis'),(11,'2015-10-05 17:02:51','c7',7,'C7 (z)','7-fold symmetry along the z axis'),(12,'2015-10-05 17:02:51','c8',8,'C8 (z)','8-fold symmetry along the z axis'),(13,'2015-10-05 17:02:51','c9',9,'C9 (z)','9-fold symmetry along the z axis'),(14,'2015-10-05 17:02:51','c10',10,'C10 (z)','10-fold symmetry along the z axis'),(15,'2015-10-05 17:02:51','c11',11,'C11 (z)','11-fold symmetry along the z axis'),(16,'2015-10-05 17:02:51','c12',12,'C12 (z)','12-fold symmetry along the z axis'),(17,'2015-10-05 17:02:51','c13',13,'C13 (z)','13-fold symmetry along the z axis'),(18,'2015-10-05 17:02:51','c14',14,'C14 (z)','14-fold symmetry along the z axis'),(19,'2015-10-05 17:02:51','c15',15,'C15 (z)','15-fold symmetry along the z axis'),(20,'2015-10-05 17:02:51','d2',4,'D2 (z)','2-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(21,'2015-10-05 17:02:51','d3',6,'D3 (z)','3-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(22,'2015-10-05 17:02:51','d4',8,'D4 (z)','4-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(23,'2015-10-05 17:02:51','d5',10,'D5 (z)','5-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(24,'2015-10-05 17:02:51','d6',12,'D6 (z)','6-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(25,'2015-10-05 17:02:51','d7',14,'D7 (z)','7-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(26,'2015-10-05 17:02:51','d8',16,'D8 (z)','8-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(27,'2015-10-05 17:02:51','d9',18,'D9 (z)','9-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(28,'2015-10-05 17:02:51','d10',20,'D10 (z)','10-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(29,'2015-10-05 17:02:51','d11',22,'D11 (z)','11-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(30,'2015-10-05 17:02:51','d12',26,'D12 (z)','12-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(31,'2015-10-05 17:02:51','d13',26,'D13 (z)','13-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(32,'2015-10-05 17:02:51','d14',28,'D14 (z)','14-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z'),(33,'2015-10-05 17:02:51','d15',30,'D15 (z)','15-fold symmetry along the z axis, 2-fold rotational axis 90 degrees from z');
/*!40000 ALTER TABLE `ApSymmetryData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApSyntheticStackParamsData`
--

DROP TABLE IF EXISTS `ApSyntheticStackParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApSyntheticStackParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApInitialModelData|modelid` int(20) DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `apix` double DEFAULT NULL,
  `projcount` int(20) DEFAULT NULL,
  `projstdev` double DEFAULT NULL,
  `shiftrad` double DEFAULT NULL,
  `rotang` int(20) DEFAULT NULL,
  `flip` tinyint(1) DEFAULT NULL,
  `kilovolts` int(20) DEFAULT NULL,
  `spher_aber` double DEFAULT NULL,
  `defocus_x` double DEFAULT NULL,
  `defocus_y` double DEFAULT NULL,
  `randomdef` tinyint(1) DEFAULT NULL,
  `randomdef_std` double DEFAULT NULL,
  `astigmatism` double DEFAULT NULL,
  `snr1` double DEFAULT NULL,
  `snrtot` double DEFAULT NULL,
  `envelope` text,
  `ace2correct` tinyint(1) DEFAULT NULL,
  `ace2correct_rand` tinyint(1) DEFAULT NULL,
  `ace2correct_std` double DEFAULT NULL,
  `ace2estimate` tinyint(1) DEFAULT NULL,
  `lowpass` int(20) DEFAULT NULL,
  `highpass` int(20) DEFAULT NULL,
  `norm` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApInitialModelData|modelid` (`REF|ApInitialModelData|modelid`),
  KEY `flip` (`flip`),
  KEY `randomdef` (`randomdef`),
  KEY `ace2correct` (`ace2correct`),
  KEY `ace2correct_rand` (`ace2correct_rand`),
  KEY `ace2estimate` (`ace2estimate`),
  KEY `norm` (`norm`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApSyntheticStackParamsData`
--

LOCK TABLES `ApSyntheticStackParamsData` WRITE;
/*!40000 ALTER TABLE `ApSyntheticStackParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApSyntheticStackParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTemplateImageData`
--

DROP TABLE IF EXISTS `ApTemplateImageData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTemplateImageData` (
  `DEF_id` int(20) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApPathData|path` bigint(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `templatename` text,
  `apix` double DEFAULT NULL,
  `diam` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT '0',
  `md5sum` varchar(32) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `stack_image_number` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `REF|ApClusteringStackData|clusterstack` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|templatepath` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `hidden` (`hidden`),
  KEY `md5sum` (`md5sum`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `REF|ApClusteringStackData|clusterstack` (`REF|ApClusteringStackData|clusterstack`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTemplateImageData`
--

LOCK TABLES `ApTemplateImageData` WRITE;
/*!40000 ALTER TABLE `ApTemplateImageData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTemplateImageData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTemplateRunData`
--

DROP TABLE IF EXISTS `ApTemplateRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTemplateRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTemplateImageData|template` int(20) DEFAULT NULL,
  `REF|ApSelectionRunData|selectionrun` int(20) DEFAULT NULL,
  `range_start` int(20) DEFAULT NULL,
  `range_end` int(20) DEFAULT NULL,
  `range_incr` int(20) DEFAULT NULL,
  `mirror` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTemplateImageData|template` (`REF|ApTemplateImageData|template`),
  KEY `REF|ApSelectionRunData|selectionrun` (`REF|ApSelectionRunData|selectionrun`),
  KEY `mirror` (`mirror`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTemplateRunData`
--

LOCK TABLES `ApTemplateRunData` WRITE;
/*!40000 ALTER TABLE `ApTemplateRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTemplateRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTemplateStackData`
--

DROP TABLE IF EXISTS `ApTemplateStackData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTemplateStackData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApClusteringStackData|clusterstack` int(20) DEFAULT NULL,
  `REF|ApAlignStackData|alignstack` int(20) DEFAULT NULL,
  `templatename` text,
  `cls_avgs` tinyint(1) DEFAULT NULL,
  `forward_proj` tinyint(1) DEFAULT NULL,
  `origfile` text,
  `description` text,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `apix` double DEFAULT NULL,
  `boxsize` int(20) DEFAULT NULL,
  `numimages` int(20) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApClusteringStackData|clusterstack` (`REF|ApClusteringStackData|clusterstack`),
  KEY `REF|ApAlignStackData|alignstack` (`REF|ApAlignStackData|alignstack`),
  KEY `cls_avgs` (`cls_avgs`),
  KEY `forward_proj` (`forward_proj`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `hidden` (`hidden`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTemplateStackData`
--

LOCK TABLES `ApTemplateStackData` WRITE;
/*!40000 ALTER TABLE `ApTemplateStackData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTemplateStackData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTestParamsData`
--

DROP TABLE IF EXISTS `ApTestParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTestParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `bin` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTestParamsData`
--

LOCK TABLES `ApTestParamsData` WRITE;
/*!40000 ALTER TABLE `ApTestParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTestParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTestResultData`
--

DROP TABLE IF EXISTS `ApTestResultData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTestResultData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTestRunData|testrun` int(20) DEFAULT NULL,
  `REF|leginondata|AcquisitionImageData|image` int(20) DEFAULT NULL,
  `x` double DEFAULT NULL,
  `y` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTestRunData|testrun` (`REF|ApTestRunData|testrun`),
  KEY `REF|leginondata|AcquisitionImageData|image` (`REF|leginondata|AcquisitionImageData|image`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTestResultData`
--

LOCK TABLES `ApTestResultData` WRITE;
/*!40000 ALTER TABLE `ApTestResultData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTestResultData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTestRunData`
--

DROP TABLE IF EXISTS `ApTestRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTestRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTestParamsData|params` int(20) DEFAULT NULL,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `name` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `append_timestamp` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTestParamsData|params` (`REF|ApTestParamsData|params`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTestRunData`
--

LOCK TABLES `ApTestRunData` WRITE;
/*!40000 ALTER TABLE `ApTestRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTestRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTiltAlignParamsData`
--

DROP TABLE IF EXISTS `ApTiltAlignParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTiltAlignParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `diam` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `invert` int(20) DEFAULT NULL,
  `lp_filt` int(20) DEFAULT NULL,
  `hp_filt` int(20) DEFAULT NULL,
  `median` int(20) DEFAULT NULL,
  `pixel_value_limit` double DEFAULT NULL,
  `output_type` text,
  `REF|ApSelectionRunData|oldselectionrun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApSelectionRunData|oldselectionrun` (`REF|ApSelectionRunData|oldselectionrun`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTiltAlignParamsData`
--

LOCK TABLES `ApTiltAlignParamsData` WRITE;
/*!40000 ALTER TABLE `ApTiltAlignParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTiltAlignParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTiltParticlePairData`
--

DROP TABLE IF EXISTS `ApTiltParticlePairData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTiltParticlePairData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApParticleData|particle1` int(20) DEFAULT NULL,
  `REF|ApParticleData|particle2` int(20) DEFAULT NULL,
  `REF|ApImageTiltTransformData|transform` int(20) DEFAULT NULL,
  `error` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApParticleData|particle1` (`REF|ApParticleData|particle1`),
  KEY `REF|ApParticleData|particle2` (`REF|ApParticleData|particle2`),
  KEY `REF|ApImageTiltTransformData|transform` (`REF|ApImageTiltTransformData|transform`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTiltParticlePairData`
--

LOCK TABLES `ApTiltParticlePairData` WRITE;
/*!40000 ALTER TABLE `ApTiltParticlePairData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTiltParticlePairData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTiltsInAlignRunData`
--

DROP TABLE IF EXISTS `ApTiltsInAlignRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTiltsInAlignRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAlignmentRunData|alignrun` int(20) DEFAULT NULL,
  `REF|leginondata|TiltSeriesData|tiltseries` int(20) DEFAULT NULL,
  `REF|leginondata|TomographySettingsData|settings` int(20) DEFAULT NULL,
  `primary_tiltseries` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAlignmentRunData|alignrun` (`REF|ApTomoAlignmentRunData|alignrun`),
  KEY `REF|leginondata|TiltSeriesData|tiltseries` (`REF|leginondata|TiltSeriesData|tiltseries`),
  KEY `REF|leginondata|TomographySettingsData|settings` (`REF|leginondata|TomographySettingsData|settings`),
  KEY `primary_tiltseries` (`primary_tiltseries`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTiltsInAlignRunData`
--

LOCK TABLES `ApTiltsInAlignRunData` WRITE;
/*!40000 ALTER TABLE `ApTiltsInAlignRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTiltsInAlignRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomoAlignerParamsData`
--

DROP TABLE IF EXISTS `ApTomoAlignerParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomoAlignerParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAlignmentRunData|alignrun` int(20) DEFAULT NULL,
  `REF|ApProtomoParamsData|protomo` int(20) DEFAULT NULL,
  `REF|ApProtomoRefinementParamsData|refine_cycle` int(20) DEFAULT NULL,
  `REF|ApProtomoRefinementParamsData|good_cycle` int(20) DEFAULT NULL,
  `good_start` int(20) DEFAULT NULL,
  `good_end` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAlignmentRunData|alignrun` (`REF|ApTomoAlignmentRunData|alignrun`),
  KEY `REF|ApProtomoParamsData|protomo` (`REF|ApProtomoParamsData|protomo`),
  KEY `REF|ApProtomoRefinementParamsData|refine_cycle` (`REF|ApProtomoRefinementParamsData|refine_cycle`),
  KEY `REF|ApProtomoRefinementParamsData|good_cycle` (`REF|ApProtomoRefinementParamsData|good_cycle`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomoAlignerParamsData`
--

LOCK TABLES `ApTomoAlignerParamsData` WRITE;
/*!40000 ALTER TABLE `ApTomoAlignerParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomoAlignerParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomoAlignmentRunData`
--

DROP TABLE IF EXISTS `ApTomoAlignmentRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomoAlignmentRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|leginondata|TiltSeriesData|tiltseries` int(20) DEFAULT NULL,
  `REF|leginondata|TomographySettingsData|coarseLeginonParams` int(20) DEFAULT NULL,
  `REF|ApImodXcorrParamsData|coarseImodParams` int(20) DEFAULT NULL,
  `REF|ApProtomoParamsData|fineProtomoParams` int(20) DEFAULT NULL,
  `REF|ApRaptorParamsData|raptorParams` int(20) DEFAULT NULL,
  `bin` int(20) DEFAULT NULL,
  `name` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  `badAlign` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|leginondata|TiltSeriesData|tiltseries` (`REF|leginondata|TiltSeriesData|tiltseries`),
  KEY `REF|leginondata|TomographySettingsData|coarseLeginonParams` (`REF|leginondata|TomographySettingsData|coarseLeginonParams`),
  KEY `REF|ApImodXcorrParamsData|coarseImodParams` (`REF|ApImodXcorrParamsData|coarseImodParams`),
  KEY `REF|ApProtomoParamsData|fineProtomoParams` (`REF|ApProtomoParamsData|fineProtomoParams`),
  KEY `REF|ApRaptorParamsData|raptorParams` (`REF|ApRaptorParamsData|raptorParams`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `hidden` (`hidden`),
  KEY `badAlign` (`badAlign`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomoAlignmentRunData`
--

LOCK TABLES `ApTomoAlignmentRunData` WRITE;
/*!40000 ALTER TABLE `ApTomoAlignmentRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomoAlignmentRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomoAverageRunData`
--

DROP TABLE IF EXISTS `ApTomoAverageRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomoAverageRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApStackData|stack` int(20) DEFAULT NULL,
  `REF|ApSubTomogramRunData|subtomorun` int(20) DEFAULT NULL,
  `xyhalfwidth` int(20) DEFAULT NULL,
  `description` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApStackData|stack` (`REF|ApStackData|stack`),
  KEY `REF|ApSubTomogramRunData|subtomorun` (`REF|ApSubTomogramRunData|subtomorun`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomoAverageRunData`
--

LOCK TABLES `ApTomoAverageRunData` WRITE;
/*!40000 ALTER TABLE `ApTomoAverageRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomoAverageRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomoAvgParticleData`
--

DROP TABLE IF EXISTS `ApTomoAvgParticleData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomoAvgParticleData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|ApTomoAverageRunData|avgrun` int(20) DEFAULT NULL,
  `REF|ApTomogramData|subtomo` int(20) DEFAULT NULL,
  `REF|ApAlignParticleData|aligned_particle` int(20) DEFAULT NULL,
  `z_shift` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTomoAverageRunData|avgrun` (`REF|ApTomoAverageRunData|avgrun`),
  KEY `REF|ApTomogramData|subtomo` (`REF|ApTomogramData|subtomo`),
  KEY `REF|ApAlignParticleData|aligned_particle` (`REF|ApAlignParticleData|aligned_particle`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomoAvgParticleData`
--

LOCK TABLES `ApTomoAvgParticleData` WRITE;
/*!40000 ALTER TABLE `ApTomoAvgParticleData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomoAvgParticleData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomoReconParamsData`
--

DROP TABLE IF EXISTS `ApTomoReconParamsData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomoReconParamsData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `tilt_angle_offset` double DEFAULT NULL,
  `z_shift` double DEFAULT NULL,
  `tilt_axis_tilt_out_xyplane` double DEFAULT NULL,
  `tilt_axis_rotation_in_xyplane` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomoReconParamsData`
--

LOCK TABLES `ApTomoReconParamsData` WRITE;
/*!40000 ALTER TABLE `ApTomoReconParamsData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomoReconParamsData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTomogramData`
--

DROP TABLE IF EXISTS `ApTomogramData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTomogramData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `REF|leginondata|SessionData|session` int(20) DEFAULT NULL,
  `REF|leginondata|TiltSeriesData|tiltseries` int(20) DEFAULT NULL,
  `REF|ApFullTomogramData|fulltomogram` int(20) DEFAULT NULL,
  `REF|ApSubTomogramRunData|subtomorun` int(20) DEFAULT NULL,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|ApParticleData|center` int(20) DEFAULT NULL,
  `offsetz` int(20) DEFAULT NULL,
  `name` text,
  `number` int(20) DEFAULT NULL,
  `pixelsize` double DEFAULT NULL,
  `description` text,
  `md5sum` text,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|leginondata|SessionData|session` (`REF|leginondata|SessionData|session`),
  KEY `REF|leginondata|TiltSeriesData|tiltseries` (`REF|leginondata|TiltSeriesData|tiltseries`),
  KEY `REF|ApFullTomogramData|fulltomogram` (`REF|ApFullTomogramData|fulltomogram`),
  KEY `REF|ApSubTomogramRunData|subtomorun` (`REF|ApSubTomogramRunData|subtomorun`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `REF|ApParticleData|center` (`REF|ApParticleData|center`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTomogramData`
--

LOCK TABLES `ApTomogramData` WRITE;
/*!40000 ALTER TABLE `ApTomogramData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTomogramData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTopolRepJobData`
--

DROP TABLE IF EXISTS `ApTopolRepJobData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTopolRepJobData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `timestamp` text,
  `REF|ApPathData|path` int(20) DEFAULT NULL,
  `REF|projectdata|projects|project` int(20) DEFAULT NULL,
  `finished` tinyint(1) DEFAULT NULL,
  `hidden` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApPathData|path` (`REF|ApPathData|path`),
  KEY `finished` (`finished`),
  KEY `hidden` (`hidden`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTopolRepJobData`
--

LOCK TABLES `ApTopolRepJobData` WRITE;
/*!40000 ALTER TABLE `ApTopolRepJobData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTopolRepJobData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApTopolRepRunData`
--

DROP TABLE IF EXISTS `ApTopolRepRunData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApTopolRepRunData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `mask` int(20) DEFAULT NULL,
  `itermult` double DEFAULT NULL,
  `learn` double DEFAULT NULL,
  `ilearn` double DEFAULT NULL,
  `age` int(20) DEFAULT NULL,
  `mramethod` text,
  `REF|ApTopolRepJobData|job` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ApTopolRepJobData|job` (`REF|ApTopolRepJobData|job`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApTopolRepRunData`
--

LOCK TABLES `ApTopolRepRunData` WRITE;
/*!40000 ALTER TABLE `ApTopolRepRunData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApTopolRepRunData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApXmippML3DRefineIterData`
--

DROP TABLE IF EXISTS `ApXmippML3DRefineIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApXmippML3DRefineIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `InSelFile` text,
  `InitialReference` text,
  `WorkingDir` text,
  `DoDeleteWorkingDir` tinyint(1) DEFAULT NULL,
  `DoMlf` tinyint(1) DEFAULT NULL,
  `DoCorrectAmplitudes` tinyint(1) DEFAULT NULL,
  `InCtfDatFile` text,
  `HighResLimit` double DEFAULT NULL,
  `ImagesArePhaseFlipped` tinyint(1) DEFAULT NULL,
  `InitialMapIsAmplitudeCorrected` tinyint(1) DEFAULT NULL,
  `SeedsAreAmplitudeCorrected` tinyint(1) DEFAULT NULL,
  `DoCorrectGreyScale` tinyint(1) DEFAULT NULL,
  `ProjMatchSampling` int(20) DEFAULT NULL,
  `DoLowPassFilterReference` tinyint(1) DEFAULT NULL,
  `LowPassFilter` int(20) DEFAULT NULL,
  `PixelSize` double DEFAULT NULL,
  `DoGenerateSeeds` tinyint(1) DEFAULT NULL,
  `NumberOfReferences` int(20) DEFAULT NULL,
  `DoJustRefine` tinyint(1) DEFAULT NULL,
  `SeedsSelfile` text,
  `DoML3DClassification` tinyint(1) DEFAULT NULL,
  `AngularSampling` int(20) DEFAULT NULL,
  `NumberOfIterations` int(20) DEFAULT NULL,
  `Symmetry` text,
  `DoNorm` tinyint(1) DEFAULT NULL,
  `DoFourier` tinyint(1) DEFAULT NULL,
  `RestartIter` tinyint(1) DEFAULT NULL,
  `ExtraParamsMLrefine3D` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `DoDeleteWorkingDir` (`DoDeleteWorkingDir`),
  KEY `DoMlf` (`DoMlf`),
  KEY `DoCorrectAmplitudes` (`DoCorrectAmplitudes`),
  KEY `ImagesArePhaseFlipped` (`ImagesArePhaseFlipped`),
  KEY `InitialMapIsAmplitudeCorrected` (`InitialMapIsAmplitudeCorrected`),
  KEY `SeedsAreAmplitudeCorrected` (`SeedsAreAmplitudeCorrected`),
  KEY `DoCorrectGreyScale` (`DoCorrectGreyScale`),
  KEY `DoLowPassFilterReference` (`DoLowPassFilterReference`),
  KEY `DoGenerateSeeds` (`DoGenerateSeeds`),
  KEY `DoJustRefine` (`DoJustRefine`),
  KEY `DoML3DClassification` (`DoML3DClassification`),
  KEY `DoNorm` (`DoNorm`),
  KEY `DoFourier` (`DoFourier`),
  KEY `RestartIter` (`RestartIter`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApXmippML3DRefineIterData`
--

LOCK TABLES `ApXmippML3DRefineIterData` WRITE;
/*!40000 ALTER TABLE `ApXmippML3DRefineIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApXmippML3DRefineIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ApXmippRefineIterData`
--

DROP TABLE IF EXISTS `ApXmippRefineIterData`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ApXmippRefineIterData` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `NumberofIterations` int(20) DEFAULT NULL,
  `MaskFileName` text,
  `MaskRadius` int(20) DEFAULT NULL,
  `InnerRadius` int(20) DEFAULT NULL,
  `OuterRadius` int(20) DEFAULT NULL,
  `SymmetryGroup` text,
  `FourierMaxFrequencyOfInterest` double DEFAULT NULL,
  `SelFileName` text,
  `DocFileName` text,
  `ReferenceFileName` text,
  `WorkingDir` text,
  `CleanUpFiles` tinyint(1) DEFAULT NULL,
  `DoCtfCorrection` tinyint(1) DEFAULT NULL,
  `CTFDatName` text,
  `DoAutoCtfGroup` tinyint(1) DEFAULT NULL,
  `CtfGroupMaxDiff` double DEFAULT NULL,
  `CtfGroupMaxResol` double DEFAULT NULL,
  `PaddingFactor` double DEFAULT NULL,
  `WienerConstant` double DEFAULT NULL,
  `DataArePhaseFlipped` tinyint(1) DEFAULT NULL,
  `ReferenceIsCtfCorrected` tinyint(1) DEFAULT NULL,
  `DoMask` tinyint(1) DEFAULT NULL,
  `DoSphericalMask` tinyint(1) DEFAULT NULL,
  `AngSamplingRateDeg` double DEFAULT NULL,
  `MaxChangeInAngles` double DEFAULT NULL,
  `PerturbProjectionDirections` tinyint(1) DEFAULT NULL,
  `MaxChangeOffset` double DEFAULT NULL,
  `Search5DShift` int(20) DEFAULT NULL,
  `Search5DStep` int(20) DEFAULT NULL,
  `DoRetricSearchbyTiltAngle` tinyint(1) DEFAULT NULL,
  `Tilt0` double DEFAULT NULL,
  `TiltF` double DEFAULT NULL,
  `SymmetryGroupNeighbourhood` text,
  `OnlyWinner` tinyint(1) DEFAULT NULL,
  `MinimumCrossCorrelation` double DEFAULT NULL,
  `DiscardPercentage` double DEFAULT NULL,
  `ProjMatchingExtra` text,
  `DoAlign2D` tinyint(1) DEFAULT NULL,
  `Align2DIterNr` int(20) DEFAULT NULL,
  `Align2dMaxChangeOffset` double DEFAULT NULL,
  `Align2dMaxChangeRot` double DEFAULT NULL,
  `ReconstructionMethod` text,
  `ARTLambda` double DEFAULT NULL,
  `ARTReconstructionExtraCommand` text,
  `WBPReconstructionExtraCommand` text,
  `FourierReconstructionExtraCommand` text,
  `ResolSam` double DEFAULT NULL,
  `ConstantToAddToFiltration` double DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `CleanUpFiles` (`CleanUpFiles`),
  KEY `DoCtfCorrection` (`DoCtfCorrection`),
  KEY `DoAutoCtfGroup` (`DoAutoCtfGroup`),
  KEY `DataArePhaseFlipped` (`DataArePhaseFlipped`),
  KEY `ReferenceIsCtfCorrected` (`ReferenceIsCtfCorrected`),
  KEY `DoMask` (`DoMask`),
  KEY `DoSphericalMask` (`DoSphericalMask`),
  KEY `PerturbProjectionDirections` (`PerturbProjectionDirections`),
  KEY `DoRetricSearchbyTiltAngle` (`DoRetricSearchbyTiltAngle`),
  KEY `OnlyWinner` (`OnlyWinner`),
  KEY `DoAlign2D` (`DoAlign2D`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ApXmippRefineIterData`
--

LOCK TABLES `ApXmippRefineIterData` WRITE;
/*!40000 ALTER TABLE `ApXmippRefineIterData` DISABLE KEYS */;
/*!40000 ALTER TABLE `ApXmippRefineIterData` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptHostName`
--

DROP TABLE IF EXISTS `ScriptHostName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptHostName` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `ip` text,
  `system` text,
  `distro` text,
  `arch` text,
  `nproc` int(20) DEFAULT NULL,
  `memory` int(20) DEFAULT NULL,
  `cpu_vendor` text,
  `gpu_vendor` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptHostName`
--

LOCK TABLES `ScriptHostName` WRITE;
/*!40000 ALTER TABLE `ScriptHostName` DISABLE KEYS */;
INSERT INTO `ScriptHostName` VALUES (1,'2015-10-05 17:02:57','053ffadab348','172.17.0.77','linux','CentOS release 6.7 (Final)','x86_64',2,8168476,'Intel','InnoTek');
/*!40000 ALTER TABLE `ScriptHostName` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptParamName`
--

DROP TABLE IF EXISTS `ScriptParamName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptParamName` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `REF|ScriptProgramName|progname` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ScriptProgramName|progname` (`REF|ScriptProgramName|progname`)
) ENGINE=MyISAM AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptParamName`
--

LOCK TABLES `ScriptParamName` WRITE;
/*!40000 ALTER TABLE `ScriptParamName` DISABLE KEYS */;
INSERT INTO `ScriptParamName` VALUES (1,'2015-10-05 17:02:57','projectid',1),(2,'2015-10-05 17:02:57','mpix',1),(3,'2015-10-05 17:02:57','cs',1),(4,'2015-10-05 17:02:57','rundir',1),(5,'2015-10-05 17:02:57','defocus',1),(6,'2015-10-05 17:02:57','uploadtype',1),(7,'2015-10-05 17:02:57','magnification',1),(8,'2015-10-05 17:02:57','kv',1),(9,'2015-10-05 17:02:57','description',1),(10,'2015-10-05 17:02:57','seriessize',1),(11,'2015-10-05 17:02:57','leginondir',1),(12,'2015-10-05 17:02:57','imagedir',1),(13,'2015-10-05 17:02:57','runname',1),(14,'2015-10-05 17:02:57','commit',1);
/*!40000 ALTER TABLE `ScriptParamName` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptParamValue`
--

DROP TABLE IF EXISTS `ScriptParamValue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptParamValue` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `value` text,
  `usage` text,
  `REF|ScriptParamName|paramname` int(20) DEFAULT NULL,
  `REF|ScriptProgramRun|progrun` int(20) DEFAULT NULL,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ScriptParamName|paramname` (`REF|ScriptParamName|paramname`),
  KEY `REF|ScriptProgramRun|progrun` (`REF|ScriptProgramRun|progrun`)
) ENGINE=MyISAM AUTO_INCREMENT=15 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptParamValue`
--

LOCK TABLES `ScriptParamValue` WRITE;
/*!40000 ALTER TABLE `ScriptParamValue` DISABLE KEYS */;
INSERT INTO `ScriptParamValue` VALUES (1,'2015-10-05 17:02:57','1','--projectid=1',1,1),(2,'2015-10-05 17:02:57','8.15e-11','--pixel-size=8.15e-11',2,1),(3,'2015-10-05 17:02:57','2.0','--cs=2.0',3,1),(4,'2015-10-05 17:02:57','/emg/data/leginon/06jul12a/rawdata','--outdir=/emg/data/leginon/06jul12a/rawdata',4,1),(5,'2015-10-05 17:02:57','-1e-06','--defocus=-1e-06',5,1),(6,'2015-10-05 17:02:57','normal','--type=normal',6,1),(7,'2015-10-05 17:02:57','100000','--mag=100000',7,1),(8,'2015-10-05 17:02:57','120','--kv=120',8,1),(9,'2015-10-05 17:02:57','First test session with GroEL','--description=\'First test session with GroEL\'',9,1),(10,'2015-10-05 17:02:57','1','--images-per-series=1',10,1),(11,'2015-10-05 17:02:57','/emg/data/leginon','--leginon-output-dir=/emg/data/leginon',11,1),(12,'2015-10-05 17:02:57','/emg/data/leginon/06jul12a/rawdata/','--image-dir=/emg/data/leginon/06jul12a/rawdata/',12,1),(13,'2015-10-05 17:02:57','06jul12a','--runname=06jul12a',13,1),(14,'2015-10-05 17:02:57','True','--commit',14,1);
/*!40000 ALTER TABLE `ScriptParamValue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptProgramName`
--

DROP TABLE IF EXISTS `ScriptProgramName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptProgramName` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptProgramName`
--

LOCK TABLES `ScriptProgramName` WRITE;
/*!40000 ALTER TABLE `ScriptProgramName` DISABLE KEYS */;
INSERT INTO `ScriptProgramName` VALUES (1,'2015-10-05 17:02:57','uploadImages');
/*!40000 ALTER TABLE `ScriptProgramName` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptProgramRun`
--

DROP TABLE IF EXISTS `ScriptProgramRun`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptProgramRun` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `runname` text,
  `revision` text,
  `REF|ScriptProgramName|progname` int(20) DEFAULT NULL,
  `REF|ScriptUserName|username` int(20) DEFAULT NULL,
  `REF|ScriptHostName|hostname` int(20) DEFAULT NULL,
  `REF|ApPathData|rundir` int(20) DEFAULT NULL,
  `REF|ApAppionJobData|job` int(20) DEFAULT NULL,
  `REF|ApPathData|appion_path` int(20) DEFAULT NULL,
  `unixshell` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`),
  KEY `REF|ScriptProgramName|progname` (`REF|ScriptProgramName|progname`),
  KEY `REF|ScriptUserName|username` (`REF|ScriptUserName|username`),
  KEY `REF|ScriptHostName|hostname` (`REF|ScriptHostName|hostname`),
  KEY `REF|ApPathData|rundir` (`REF|ApPathData|rundir`),
  KEY `REF|ApAppionJobData|job` (`REF|ApAppionJobData|job`),
  KEY `REF|ApPathData|appion_path` (`REF|ApPathData|appion_path`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptProgramRun`
--

LOCK TABLES `ScriptProgramRun` WRITE;
/*!40000 ALTER TABLE `ScriptProgramRun` DISABLE KEYS */;
INSERT INTO `ScriptProgramRun` VALUES (1,'2015-10-05 17:02:57','06jul12a','trunk',1,1,1,1,1,2,NULL);
/*!40000 ALTER TABLE `ScriptProgramRun` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ScriptUserName`
--

DROP TABLE IF EXISTS `ScriptUserName`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ScriptUserName` (
  `DEF_id` int(16) NOT NULL AUTO_INCREMENT,
  `DEF_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `name` text,
  `uid` int(20) DEFAULT NULL,
  `gid` int(20) DEFAULT NULL,
  `fullname` text,
  PRIMARY KEY (`DEF_id`),
  KEY `DEF_timestamp` (`DEF_timestamp`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ScriptUserName`
--

LOCK TABLES `ScriptUserName` WRITE;
/*!40000 ALTER TABLE `ScriptUserName` DISABLE KEYS */;
INSERT INTO `ScriptUserName` VALUES (1,'2015-10-05 17:02:57','unknown',NULL,NULL,NULL);
/*!40000 ALTER TABLE `ScriptUserName` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-10-05 17:06:52

--
-- Neil additions
--

CREATE USER usr_object@'localhost' IDENTIFIED BY 'Phys-554';
GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON leginondb.* TO usr_object@'localhost';
GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON projectdb.* TO usr_object@'localhost';
GRANT ALTER, CREATE, INSERT, SELECT, UPDATE ON `ap%`.* to usr_object@localhost; 

flush privileges;
