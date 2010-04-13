<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once('inc/leginon.inc');
var_dump($leginondata->mysql->getDBInfo());
if(!$leginondata->mysql->checkDBConnection())
	echo "DB_LEGINON is not existError in database connection. Please check your config.php file";

if ($leginondata->mysql->checkDBConnection()) {
	$leginondata->importTables(DEF_TABLES_FILE);
	$leginondata->addDefaultGroupData();
}

//var_dump(gd_info());
?>