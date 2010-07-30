<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadParticles();
}

// Create the form page
else {
	createUploadParticlesForm();
}

function createUploadParticlesForm($extra=false, $title='uploadParticles.py Launcher', $heading='Upload particle selection') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// Set any existing parameters in form
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';

	$javafunctions="<script src='../js/viewer.js'></script>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","extract",$sessionpath);
	$sessionname=$sessioninfo['Name'];

	//query the database for parameters
	$particle = new particledata();

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name');
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manual'.($lastrunnumber+1);
	$particles = ($_POST['particles']) ? $_POST['particles'] : '';
	$scale = ($_POST['scale']) ? $_POST['scale'] : '';

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
	
	echo docpop('particlefiles', "Particle file(s) with path <i>(wild cards are acceptable)</i>:");
	echo " <br> \n";
	echo "<INPUT TYPE='text' NAME='particles' VALUE='$particles' SIZE='55'/>\n";
	echo "<br>\n";			

	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	echo "<br>\n";
	echo docpop("diameter", "Particle Diameter");
	echo "<INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "<br><br>\n";

	echo docpop("particlescaling","Particle selection scaling:");
	echo " <input type='text' name='scale' size='3' value='$scale'>\n";
	echo "<br/>\n";

	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'>";
	echo getSubmitForm("Upload Particles");
	echo "</td></tr></table></form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runUploadParticles() {
	/* *******************
	PART 1: Get variables
	******************** */
	$particles = $_POST['particles'];
	$diam=$_POST['diam'];
	$scale=$_POST['scale'];
	$sessionname = $_POST['sessionname'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	// make sure box files are entered
	if (!$particles)
		createUploadParticlesForm("<b>Error:</b> Specify particle files for uploading");
	//make sure a diam was provided
	if (!$diam)
		createUploadParticlesForm("<B>ERROR:</B> Enter the particle diameter");

	/* *******************
	PART 3: Create program command
	******************** */

	//putting together command
	$command = "uploadParticles.py ";
	$command.="--session=$sessionname ";
	$command.="--files=\"$particles\" ";
	$command.="--diam=$diam ";
	if ($scale)
		$command.="--bin=$scale ";
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
