<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCtfEstimate();
}
// CREATE FORM PAGE
else {
	createCtfEstimateForm();
}

// --- parse data and process on submit
function runCtfEstimate() {

	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	
	// parse params
	$fieldsize=$_POST['fieldsize'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	$leginondata = new leginondata();
	if ($leginondata->getCsValueFromSession($expId) === false) {
		createCtfEstimateForm("Cs value of the images in this session is not unique or known, can't process");
		exit;
	}
	// Error checking:
	if (!$fieldsize) createCtfEstimateForm("Enter a fieldsize");
	
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command = "xmippCtf.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createCtfEstimateForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$command.="--fieldsize=$fieldsize ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("Fast, robust, and accurate determination of transmission electron microscopy contrast transfer function.", 2007, "Sorzano CO, Jonic S, Núñez-Ramírez R, Boisset N, Carazo JM.", "J Struct Biol.", 160, 2, 17911028, false, false, "img/xmipp_logo.png");
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'ctfestimate', 1);

	// if error display them
	if ($errors)
		createCtfEstimateForm("<b>ERROR:</b> $errors");
}


/*
**
**
** CtfEstimate FORM
**
**
*/

// CREATE FORM PAGE
function createCtfEstimateForm($extra=false) {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=getProjectId();

	// check if running ctffind or ctftilt
	$progname = "Xmipp CTF Estimator";
	$runbase = "xmippctf";

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("$progname Launcher", "$progname", $javafunctions);

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"
	<form name='viewerform' method='POST' action='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/ctf';
	}
	$ctf = new particledata();
	$lastrunnumber = $ctf->getLastRunNumberForType($sessionId,'ApAceRunData','name'); 
	while (file_exists($sessionpath.$runbase.'run'.($lastrunnumber+1)))
		$lastrunnumber += 1;
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : $runbase.'run'.($lastrunnumber+1);

	// set defaults and check posted values
	$form_fieldsz = ($_POST['fieldsize']) ? $_POST['fieldsize'] : 512;

	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg'>";

	echo "<b>$progname Values</b><br/>\n";
	echo "<INPUT TYPE='text' NAME='fieldsize' VALUE='$form_fieldsz' size='6'>\n";
	echo docpop('field','Field Size');
	echo "<br />\n";

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run $progname");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";

	echo referenceBox("Fast, robust, and accurate determination of transmission electron microscopy contrast transfer function.", 2007, "Sorzano CO, Jonic S, Núñez-Ramírez R, Boisset N, Carazo JM.", "J Struct Biol.", 160, 2, 17911028, false, false, "img/xmipp_logo.png");

	processing_footer();
}

?>
