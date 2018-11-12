<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *		For Uploading of a Relion 3D Result
 *		Update: 2017-08-16
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadRefine3DRefine();
}

// Create the form page
else {
	createUploadRelion3DRefineForm();
}

function createUploadRelion3DRefineForm($extra=false, 
$title='uploadParticles.py Launcher', $heading='Upload particle selection') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// Set any existing parameters in form
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction' ENCTYPE='multipart/form-data'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$sessionpath=getBaseAppionPath($sessioninfo).'/extract/';
	$sessionname=$sessioninfo['Name'];

	//query the database for parameters
	$particle = new particledata();

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name');
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'relion3Drefine'.($lastrunnumber+1);
	$scale = ($_POST['scale']) ? $_POST['scale'] : '1';

	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";

	echo openRoundBorder();
	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' VALUE='$defrunname'><br>\n";
	echo "<br>\n";

	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' VALUE='$outdir' size='45'><br />\n";
	echo closeRoundBorder();
	echo "<br />\n";
	echo "<input type='hidden' name='projectId' value='$projectId'>\n";
	echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	
	/*
	**
	** START FILE TYPES
	**
	*/


	echo docpop('starfile', "Relion 3D auto-refine run_data.star with path");
	echo " <br> \n";
	echo "<INPUT TYPE='text' NAME='starfile' VALUE='$starfile' SIZE='55'>\n";
	echo "<br>\n";
	echo "<INPUT TYPE='checkbox' NAME='recenter' value='recenter'>\n";
	echo docpop('recenter', "Recenter particles based on shifts during Relion 3D auto-refine");
	echo "<br>\n";
	echo "<INPUT TYPE='checkbox' NAME='noinsert' value='noinsert'>\n";
	echo docpop('noinsert', "Do not insert final particle picks from Relion 3D auto-refine");

	/*
	**
	** END FILE TYPES
	**
	*/

	echo "</TD></tr><TR><TD VALIGN='TOP'>";
	
	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'>";
	echo getSubmitForm("Upload Particles");
	echo "</td></tr></table></form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runUploadRefine3DRefine() {
	/* *******************
	PART 1: Get variables
	******************** */
	$starfile = $_POST['starfile'];
	$sessionname = $_POST['sessionname'];
	$filetype = $_POST['filetype'];


	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	// make sure box files are entered
	//if (!$emanboxfiles && !$appionpartfile && !$_FILES['uploadpdb']['name'])
	//	createUploadParticlesForm("<b>Error:</b> Specify particle files for uploading");
	//make sure a diam was provided
	//if (!$diam)
	//	createUploadParticlesForm("<B>ERROR:</B> Enter the particle diameter");

	/* *******************
	PART 3: Create program command
	******************** */

	// get uploaded files
	if ($_FILES['uploadfile']['tmp_name']) {
		echo "UPLOAD NAME: '".$_FILES['uploadfile']['name']."'<br/>";
		echo "UPLOAD TEMP NAME: '".$_FILES['uploadfile']['tmp_name']."'<br/>";
		echo "UPLOAD SIZE: '".$_FILES['uploadfile']['size']."'<br/>";
		echo "UPLOAD ERRORS: '".$_FILES['uploadfile']['error']."'<br/>";

		$uploaddir = TEMP_IMAGES_DIR;
		if (substr($uploaddir,-1,1)!='/')
			$uploaddir.='/';
		$uploadfile = $uploaddir.basename($_FILES['uploadfile']['name']);
		echo "UPLOAD FILE: '".$uploadfile."'<br/>";
		if (!move_uploaded_file($_FILES['uploadfile']['tmp_name'], $uploadfile)) {
			print_r($_FILES['uploadfile']);
			createUploadParticlesForm("<B>ERROR:</B> Possible file upload attack! ".$_FILES['uploadfile']['tmp_name']);
			exit;
		}
	}

	//putting together command
	$command = "uploadRelion3DRefine.py ";
	$command.="--starfile=\"$starfile\" ";
	if ($_POST['recenter'] == 'recenter')
		$command.="--recenter ";
	if ($_POST['noinsert'] == 'noinsert')
		$command.="--noinsert ";
	$command.="--session=$sessionname ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadparticles', $nproc);

	// if error display them
	if ($errors)
		createAppionForm($errors);
	exit;
}

?>
