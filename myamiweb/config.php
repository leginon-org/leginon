<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

// --- Leginon Viewer Configuration --- //

// --- Set your leginon MySQL database server parameters

$HOSTNAME = "cronus1";
$DBUSER = "usr_object";
$DBPASSWORD = "";
$DATABASE = "dbemdata";

// --- Project database URL

$PROJECT_URL = "http://cronus1.scripps.edu/leginon/project/";
$PROJECT_HOSTNAME = "cronus1";
$PROJECT_DBUSER = "usr_object";
$PROJECT_DBPASSWORD = "";
$PROJECT_DATABASE = "project";

// --- Particle database

$PARTICLE_HOSTNAME = "cronus1";
$PARTICLE_DBUSER = "usr_object";
$PARTICLE_DBPASSWORD = "";
$PARTICLE_DATABASE = "particledb";


$PROJECT_URL = "http://cronus1.scripps.edu/leginon/project/";
$PROJECT_HOSTNAME = "cronus1";

// --- Set External SQL server here (use for import/export application)
$SQL_HOSTS[] = "cronus1";
$SQL_HOSTS[] = "cronus2";
$SQL_HOSTS[] = "stratocaster";

// --- Set method to read mrc 

//	use an external python script to read mrc files
// $method = "pymrc"; 

//	use a php extension mrcmodule.so to read mrc files
//
//	edit /etc/php.ini the following
//
//	[extension section]
//	extension=mrcmodule.so
//
$method = "mrcmod"; 


// ------------------------------------------------- //
define("READ_MRC", $method);
