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

require_once('template.inc');
require_once("../config.php");
require_once("../inc/leginon.inc");
require_once("../project/inc/project.inc.php");

$uploadsample = $_GET['uploadsample'];
if ($uploadsample) {
	require_once("inc/ssh.inc");
}

/*
$template = new template;
$template->wizardHeader("", SETUP_CONFIG);
?>
<center>
<br /><br /><br /><br />
<img src="../img/wait.gif" alt="Angry face" />
<br /><br /><br /><br />
<h3>System updating...</h3></center>
<?php 
$template->wizardFooter();
*/

/*
 * make sure the xml files are in the myami download location.
 */

$dir = ($_GET['myamidir']) ? $_GET['myamidir']:'/tmp/myami/';
$dir .= 'leginon/applications/';

if(is_dir($dir)){
	
	// make sure it is an directory
	if($dh = opendir($dir)){
		
		// loop through the file in this folder
		while (($filename = readdir($dh)) !== false){
			
			//not xml file, skip
			if(!preg_match("/.xml/", $filename))
				continue;

			//don't import 'Advanced', 'Robot' or 'SimuTomography'
			if(preg_match("/Advanced/", $filename) || preg_match("/Robot/", $filename) || preg_match("/SimuTomography/", $filename))
				continue;
			else
				// import application to database.
				$leginondata->importApplication($dir.$filename);
		}
	}
}

/*
* create projects
*/
$project = new project();

/*
* Now we need to create a new project for Demo.
*/
if ($uploadsample) {

	$project->addProject('GroEL Demo', 'GroEL Demo Project', 'GroEL Demo Project: Created by auto installation script.', 'None', 'This is a free project.');

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

	/* basic appion tables and symmetry record
	*/
	$filename = "../project/defaultprocessingtables.xml";
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
	* Upload an sample session from downloaded images
	* the images location from centoautoinstallation script 
	* is in /tmp/images
	* TODO: need to change the username and password for the release.
	* Ask user instead of hard code
	*/
	$command = 'imageloader.py --projectid=1 --session=sample --dir=/tmp/images --filetype=mrc --apix=0.82 --binx=1 --biny=1 --df=-1.5 --mag=100000 --kv=120 --description="Sample Session" --jobtype=uploadimage';
	exec_over_ssh("localhost", "root", $_GET['password'], $command, TRUE);

	// wait 5 seconds for uploadimage to run
	sleep(5);
}

/*
* Now we need to create a new project for Testing.
*/
$project->addProject('Tests', 'Testing Project', 'Leginon Testing Project: Created by auto installation script.', 'None', 'This is a free project.');

/*
 * Redirect to the myamiweb homepage.
 */
// Using the HTTP_HOST is not always working for autoinstaller.
// Try localhost.
$host  = $_SERVER['HTTP_HOST'];
$uri = '/myamiweb';
header("Location: http://localhost$uri");
exit;
?>
