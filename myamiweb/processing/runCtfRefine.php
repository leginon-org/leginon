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
	runProgram();
}
// CREATE FORM PAGE
else {
	createForm();
}

/*
**
**
** FORM
**
**
*/

// CREATE FORM PAGE
function createForm($extra=false) {
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

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "
	<script type='text/javascript'>
		function enableconf(){
			 if (document.viewerform.confcheck.checked){
			    document.viewerform.reprocess.disabled=false;
			 } else {
			    document.viewerform.reprocess.disabled=true;
			 }
		}
	</script>";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("CTF Refinement", "CTF Refinement", $javafunctions);

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"
	<FORM name='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/ctf/';
	}
	$ctf = new particledata();
	$lastrunnumber = $ctf->getLastRunNumberForType($sessionId,'ApAceRunData','name'); 
	while (file_exists($sessionpath.'ctfRefine'.($lastrunnumber+1)))
		$lastrunnumber += 1;
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'ctfRefine'.($lastrunnumber+1);
	$binval = ($_POST['binval']) ? $_POST['binval'] : 2;
	$confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';
	$confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';

	// this query goes too slow for AMI database
	$pixelsize = 1.0; //$ctf->getMinimumPixelSizeForSession($expId)*1e10;
	$nyquistlimit = 2*$pixelsize;

	$reprocess = ($_POST['reprocess']) ? $_POST['reprocess'] : 10;
	$numRefineIter = ($_POST['numRefineIter']) ? $_POST['numRefineIter'] : 100;
	$maxAmpCon = ($_POST['maxAmpCon']) ? $_POST['maxAmpCon'] : 0.25;
	$minAmpCon = ($_POST['minAmpCon']) ? $_POST['minAmpCon'] : 0.01;

	$reslimit = ($_POST['reslimit']) ? $_POST['reslimit'] : ceil($nyquistlimit*1.5);
	if ($reslimit < $nyquistlimit) {
		$reslimit = ceil($nyquistlimit*1.5);
	}

	//$refine2d = ($_POST['refine2d']== 'on') ? 'CHECKED' : '';
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg' valign='top'>\n";

	echo "<br/>\n";
	echo "Resolution search cutoff: ";
	echo "<input type='text' name='reslimit' value='$reslimit' size='2'> &Aring;<br/>\n";
	//echo "<i>Nyquist limit: $nyquistlimit &Aring;</i>\n";
	echo "<br/><br/>\n";

	echo "Number of Refinement Iterations: ";
	echo "<input type='text' name='numRefineIter' value='$numRefineIter' size='4'><br/>\n";
	echo "<br/><br/>\n";

	echo "Allowed amplitude contrast range:<br/>";
	echo "<input type='text' name='minAmpCon' value='$minAmpCon' size='6'>\n";
	echo " -- ";
	echo "<input type='text' name='maxAmpCon' value='$maxAmpCon' size='6'>\n";

	echo "<br/><br/>\n";


	echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)' $confcheck >\n";
	echo "Reprocess Above Resolution Value<br />\n";
	echo "&nbsp;&nbsp;Set Value:&nbsp;<input type='text' name='reprocess' ";
	if ($confcheck != 'CHECKED')
		echo "disabled";
	echo " value=$reprocess size='2'> &Aring;\n";
	echo "<br/><br/>\n";

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run CTF");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";
	processing_footer();
}

/*
**
**
** ctfRefine COMMAND
**
**
*/


// --- parse data and process on submit
function runProgram() {
	
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$reslimit=trim($_POST['reslimit']);
	$numRefineIter=trim($_POST['numRefineIter']);
	$maxAmpCon=trim($_POST['maxAmpCon']);
	$minAmpCon=trim($_POST['minAmpCon']);
	
	$reprocess=trim($_POST['reprocess']);
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	$leginondata = new leginondata();
	if ($leginondata->getCsValueFromSession($expId) === false) {
		createForm("Cs value of the images in this session is not unique or known, can't process");
		exit;
	}

	// check the tilt situation
	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($_GET['expId']);
	if ($maxang > 5) {
		$tiltangle = $_POST['tiltangle'];
		if ($tiltangle!='notilt' && $tiltangle!='lowtilt') {
			createForm("ctfRefine CTF does not work on tilted images");
			exit;
		}
	}

	if (!$reslimit || !is_numeric($reslimit)) {
		createForm("Please provide a valid res limit type ".$reslimit);
		exit;
	}

	if (!$numRefineIter || !is_numeric($numRefineIter)) {
		createForm("Please provide a valid number of iterations ".$numRefineIter);
		exit;
	}

	if ($maxAmpCon && !is_numeric($maxAmpCon)) {
		createForm("Please provide a valid amplitude contrast value".$maxAmpCon);
		exit;
	}

	if ($minAmpCon && !is_numeric($minAmpCon)) {
		createForm("Please provide a valid amplitude contrast value".$minAmpCon);
		exit;
	}

	if (is_numeric($maxAmpCon) && is_numeric($minAmpCon) && $minAmpCon > $maxAmpCon) {
		createForm("Please provide a valid amplitude contrast value, "
			."minimum value must be less than maximum value");
		exit;
	}

	if (is_numeric($maxAmpCon) && is_numeric($minAmpCon) && $minAmpCon == $maxAmpCon) {
		// values are too close give it some range
		$minAmpCon -= 0.001;
		$maxAmpCon += 0.001;
	}
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command.= "ctfRefine.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	$command .= "--reslimit=$reslimit ";
	$command .= "--refineIter=$numRefineIter ";
	if (is_numeric($maxAmpCon))
		$command .= "--maxAmpCon=$maxAmpCon ";	
	if (is_numeric($minAmpCon))
		$command .= "--minAmpCon=$minAmpCon ";	
	if (is_numeric($reprocess))
		$command .= "--reprocess=".$reprocess." ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$nproc = 1;
	$errors = showOrSubmitCommand($command, $headinfo, 'ctfestimate', $nproc);

	// if error display them
	if ($errors)
		createForm("<b>ERROR:</b> $errors");
}

?>
