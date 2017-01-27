<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

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
	$resmin=$_POST['resmin'];
	$resmax=$_POST['resmax'];

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
	if (!$resmin) createCtfFindForm("Enter a minimum resolution");
	//minimum resolution for 4k image with 1.5 Apix is: 1.5*4096 = 6144, go with 5000
	if ($resmin>5000) createCtfFindForm("Minimum resolution is too high, maximum of 5000&Aring;");
	if ($resmin<20) createCtfFindForm("Minimum resolution is too low, minimum of 20&Aring;");
	if (!$resmax) createCtfFindForm("Enter a maxmimum resolution");
	if ($resmax>15) createCtfFindForm("Maximum resolution is too high, maximum of 15&Aring;");
	if ($resmax<3) createCtfFindForm("Maximum resolution is too low, minimum of 3&Aring;");
	
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
	$command.="--resmin=$resmin ";
	$command.="--resmax=$resmax ";

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
		$sessionpath=getBaseAppionPath($sessioninfo).'/ctf/';
	}
	$ctf = new particledata();
	$lastrunnumber = $ctf->getLastRunNumberForType($sessionId,'ApAceRunData','name'); 
	while (file_exists($sessionpath.$runbase.'run'.($lastrunnumber+1)))
		$lastrunnumber += 1;
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : $runbase.'run'.($lastrunnumber+1);

	// set defaults and check posted values
	$form_fieldsz = ($_POST['fieldsize']) ? $_POST['fieldsize'] : 512;
	$form_resmin = ($_POST['resmin']) ? $_POST['resmin'] : '100';
	$form_resmax = ($_POST['resmax']) ? $_POST['resmax'] : '10';

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
	echo "<input type='text' name='resmin' value='$form_resmin' size='6'>\n";
	echo docpop('resmin','Minimum Resolution');
	echo " (&Aring;ngstroms)<br />\n";
	echo "<input type='text' name='resmax' value='$form_resmax' size='6'>\n";
	echo docpop('resmax','Maximum Resolution');
	echo " (&Aring;ngstroms)<br />\n";
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
