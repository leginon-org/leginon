<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 * $Source: /ami/sw/cvsroot/dbem/config.php,v $
 * $Revision: 1.12 $
 * $Name: not supported by cvs2svn $
 * $Date: 2004-10-23 00:11:50 $
 * $Author: dfellman $
 * $State: Exp $
 * $Locker:  $
 *
 */

// --- Leginon Viewer Configuration --- //

// --- Set your leginon MySQL database server parameters

$DB_HOST	= "";
$DB_USER	= "";
$DB_PASS	= "";
$DB		= "";

// --- Project database URL

$PROJECT_URL;
$PROJECT_DB_HOST;
$PROJECT_DB_USER;
$PROJECT_DB_PASS;
$PROJECT_DB;

// --- Particle database

$PARTICLE_DB_HOST;
$PARTICLE_DB_USER;
$PARTICLE_DB_PASS;
$PARTICLE_DB;

// --- Set Default table definition

$DEF_TABLES_FILE = "defaulttables20041021.xml";

// --- Set External SQL server here (use for import/export application)
$SQL_HOSTS[$DB_HOST]['db_host'] = $DB_HOST;
$SQL_HOSTS[$DB_HOST]['db_user'] = $DB_USER;
$SQL_HOSTS[$DB_HOST]['db_pass'] = $DB_PASS;
$SQL_HOSTS[$DB_HOST]['db'] = $DB;

// --- Set method to read mrc 

//	use an external python script to read mrc files
// $IMG_METHOD = "pymrc"; 

//	use a php extension mrcmodule.so to read mrc files
//
//	edit /etc/php.ini the following
//
//	[extension section]
//	extension=mrcmodule.so
//
$IMG_METHOD = "mrcmod"; 

