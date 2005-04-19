<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 * $Source: /ami/sw/cvsroot/dbem/config.php,v $
 * $Revision: 1.16 $
 * $Name: not supported by cvs2svn $
 * $Date: 2005-04-19 21:25:53 $
 * $Author: dfellman $
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

$PROJECT_URL = "http://cronus1.scripps.edu/leginon/project/";
$PROJECT_DB_HOST = "cronus1";
$PROJECT_DB_USER = "usr_object";
$PROJECT_DB_PASS = "";
$PROJECT_DB = "project";

// --- Particle database

$PARTICLE_DB_HOST = "cronus1";
$PARTICLE_DB_USER = "usr_object";
$PARTICLE_DB_PASS = "";
$PARTICLE_DB = "particledb";

$PROCESSING_DB_HOST = "cronus1";
$PROCESSING_DB_USER = "usr_object";
$PROCESSING_DB_PASS = "";
$PROCESSING_DB = "processing";

// --- Set Default table definition

$DEF_TABLES_FILE = "defaulttables20041021.xml";

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
