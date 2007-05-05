<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 * $Source: /ami/sw/cvsroot/dbem/config.php,v $
 * $Revision: 1.24 $
 * $Name: not supported by cvs2svn $
 * $Date: 2007-05-05 03:06:06 $
 * $Author: sstagg $
 * $State: Exp $
 * $Locker:  $
 *
 */

// --- Leginon Viewer Configuration --- //

// --- Set your leginon MySQL database server parameters

$DB_HOST	= "cronus4";
$DB_USER	= "usr_object";
$DB_PASS	= "";
$DB		= "dbemdata";

// --- Project database URL

$PROJECT_URL = "http://cronus3.scripps.edu/projectdb/";
$PROJECT_DB_HOST = "cronus4";
$PROJECT_DB_USER = "usr_object";
$PROJECT_DB_PASS = "";
$PROJECT_DB = "project";

// --- Particle database

$PARTICLE_DB_HOST = "cronus4";
$PARTICLE_DB_USER = "usr_object";
$PARTICLE_DB_PASS = "";
$PARTICLE_DB = "dbappiondata";

// --- CTF database
$PROCESSING_DB_HOST = "cronus4";
$PROCESSING_DB_USER = "usr_object";
$PROCESSING_DB_PASS = "";
$PROCESSING_DB = "dbappiondata";

// --- Reconstruction Database
$RECON_DB_HOST = "cronus4";
$RECON_DB_USER = "usr_object";
$RECON_DB_PASS = "";
$RECON_DB = "dbappiondata";

// --- Set Default table definition

$DEF_TABLES_FILE = "defaulttables20060120.xml";

// --- Set External SQL server here (use for import/export application)
// --- You can add as many as you want, just copy and paste the block
// --- to a new one and update the connection parameters

$SQL_HOSTS[$DB_HOST]['db_host'] = $DB_HOST;
$SQL_HOSTS[$DB_HOST]['db_user'] = $DB_USER;
$SQL_HOSTS[$DB_HOST]['db_pass'] = $DB_PASS;
$SQL_HOSTS[$DB_HOST]['db'] = $DB;

/*
$SQL_HOSTS['name1']['db_host'] = 'name1';
$SQL_HOSTS['name1']['db_user'] = 'usr_object';
$SQL_HOSTS['name1']['db_pass'] = '';
$SQL_HOSTS['name1']['db'] = 'dbemdata';
*/
?>
