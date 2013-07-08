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
	processing_header("Interactive CTF Estimation", "Interactive CTF Estimation", $javafunctions);

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
	while (file_exists($sessionpath.'interact'.($lastrunnumber+1)))
		$lastrunnumber += 1;
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'interact'.($lastrunnumber+1);
  $binval = ($_POST['binval']) ? $_POST['binval'] : 2;
  $confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';
  $reprocess = ($_POST['reprocess']) ? $_POST['reprocess'] : 0.8;
  $reslimit = ($_POST['reslimit']) ? $_POST['reslimit'] : 6;
  $maxdef = ($_POST['maxdef']) ? $_POST['maxdef'] : 7;
  $mindef = ($_POST['mindef']) ? $_POST['mindef'] : 0.5;
  //$refine2d = ($_POST['refine2d']== 'on') ? 'CHECKED' : '';
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";


	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg' valign='top'>\n";

	echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)' $confcheck >\n";
	echo "Reprocess Below Confidence Value<br />\n";
	if ($confcheck == 'CHECKED') {
		echo "Set Value:<input type='text' name='reprocess' value=$reprocess size='4'>\n";
	} else {
		echo "Set Value:<input type='text' name='reprocess' disabled value=$reprocess size='4'>\n";
	}
	echo "<font size='-2'><i>(between 0.0 - 1.0)</i></font>\n";
	echo "<br/><br/>\n";

	echo "Viewer cutoff: <input type='text' name='reslimit' value=$reslimit size='4'> &Aring;ngstroms<br/>\n";
	echo "Max defocus: <input type='text' name='maxdef' value=$maxdef size='4'> microns<br/>\n";
	echo "Min defocus: <input type='text' name='mindef' value=$mindef size='4'> microns<br/>\n";

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run CTF", true, true);
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
** Ace 2 COMMAND
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
	// parse params
	//$refine2d=$_POST['refine2d'];
	$binval=$_POST['binval'];

	$reslimit=trim($_POST['reslimit']);
	$maxdef=trim($_POST['maxdef']);
	$mindef=trim($_POST['mindef']);
	$reprocess=$_POST['reprocess'];
	
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
			createForm("ACE 2 does not work on tilted images");
			exit;
		}
	}
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command.= "interactiveCtf.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	if ($reslimit)
		$command .= "--reslimit=$reslimit ";	
	if ($maxdef)
		$command .= "--maxdef=".($maxdef*1e-6)." ";
	if ($mindef)
		$command .= "--mindef=".($mindef*1e-6)." ";	
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'ctfestimate', 1);

	// if error display them
	if ($errors)
		createForm("<b>ERROR:</b> $errors");
}

?>
