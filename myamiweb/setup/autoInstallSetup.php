<?php
/*
 * This script is going to add applications to the database 
 * base on the leginon/applications xml files.
 * also, it will create a demo project and redirect
 * to myamiweb homepage.
 * 
 * THIS SCRIPT ONLY run with centosAutoInstallation.py
 * 
 */

require_once("../config.php");
require_once("../inc/leginon.inc");
require_once("../project/inc/project.inc.php");

/*
 * make sure the xml files are in the myami download location.
 */

$dir = '/tmp/myami/leginon/applications/';
if(is_dir($dir)){
	
	// make sure it is an directory
	if($dh = opendir($dir)){
		
		// loop through the file in this folder
		while (($filename = readdir($dh)) !== false){
			
			//not xml file, skip
			if(!preg_match("/.xml/", $filename))
				continue;

			//don't import 'Robot' or 'SimuTomography'
			if(preg_match("/Robot/", $filename) || preg_match("/SimuTomography/", $filename))
				continue;
			else
				// import application to database.
				$leginondata->importApplication($dir.$filename);
		}
	}
}

/*
 * Now we need to create a new project for Demo.
 */
$project = new project();

$project->addProject('Demo', 'Demo Project', 'Demo Project: Created by installation', 'None', 'This is a free project.');

/*
 * Now we need to create a processing database for this demo project
 */
$dbname = 'ap1';
$selectedprojectId = '1';
$q='create database `'.$dbname.'`';
$r=$project->mysql->SQLQuery($q);

// --- created default tables --- //
$filename = DEF_PROCESSING_TABLES_FILE;
$leginondata->mysql->setSQLHost( array('db'=>$dbname) );
$leginondata->importTables($filename);

/* appion_extra.xml is created by sinedon/maketables.py
 * based on a database without importing the existing appion_extra.xml 
 * Since sinedon/maketables.py does not create table definition if
 * the table exists in the designated database,
 * DEF_PROCESSING_TABLES_FILE set type
 * varchar is retained that makes it indexable and faster */
$filename = "../xml/appion_extra.xml";
$leginondata->mysql->setSQLHost( array('db'=>$dbname) );
$leginondata->importTables($filename);

$data=array();
$data['REF|projects|project']=$selectedprojectId;
$data['appiondb']=$dbname;
$project->mysql->SQLInsertIfNotExists('processingdb', $data);


/*
 * Redirect to the myamiweb homepage.
 */
$host  = $_SERVER['HTTP_HOST'];
$uri = '/myamiweb';
header("Location: http://$host$uri");
exit;
?>