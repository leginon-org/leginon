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
	processing_header("Phasor CTF Estimation", "Phasor CTF Estimation", $javafunctions);

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
	while (file_exists($sessionpath.'phasor'.($lastrunnumber+1)))
		$lastrunnumber += 1;
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'phasor'.($lastrunnumber+1);
	$binval = ($_POST['binval']) ? $_POST['binval'] : 2;
	$confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';
	$confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';

	// this line is too slow for the AMI database.
	$pixelsize = 1.0; //$ctf->getMinimumPixelSizeForSession($expId)*1e10;
	$nyquistlimit = 2*$pixelsize;

	$reprocess = ($_POST['reprocess']) ? $_POST['reprocess'] : 10;
	$numRefineIter = ($_POST['numRefineIter']) ? $_POST['numRefineIter'] : 0;
	$reslimit = ($_POST['reslimit']) ? $_POST['reslimit'] : ceil($nyquistlimit*1.5);
	if ($reslimit < $nyquistlimit) {
		$reslimit = ceil($nyquistlimit*1.5);
	}

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

	echo "<b>Sample type:</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='radio' NAME='sample' VALUE='stain' SIZE='3'>\n";
	echo "Carbon stain<br />\n";
	echo "<INPUT TYPE='radio' NAME='sample' VALUE='ice' SIZE='3'>\n";
	echo "Vitreous ice \n";
	echo "<br/><br/>\n";

	echo "<b>Defocus limits:</b>\n";
	echo "<br />\n";
	echo "Min defocus: <input type='text' name='mindef' value=$mindef size='3'> microns<br/>\n";
	echo "Max defocus: <input type='text' name='maxdef' value=$maxdef size='3'> microns<br/>\n";
	echo "<br/><br/>\n";

	echo "<b>Level of astigmatism</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='radio' NAME='astig' VALUE='false' "
		.(($_POST['astig']== 'true') ? '' : 'CHECKED')." SIZE='3'>\n";
	echo "Small \n";
	echo "&nbsp; \n";
	echo "<INPUT TYPE='radio' NAME='astig' VALUE='true' "
		.(($_POST['astig']== 'true') ? 'CHECKED' : '')." SIZE='3'>\n";
	echo "Large\n";
	echo "<br/><br/>\n";

	echo "<br/>\n";
	echo "Resolution search cutoff: ";
	echo "<input type='text' name='reslimit' value='$reslimit' size='2'> &Aring;<br/>\n";
	//echo "<i>Nyquist limit: $nyquistlimit &Aring;</i>\n";
	echo "<br/><br/>\n";

	echo "Number of Post-Search Refinement Iterations: ";
	echo "<input type='text' name='numRefineIter' value='$numRefineIter' size='4'><br/>\n";
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
** Phasor COMMAND
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

	$sample=$_POST['sample'];
	$astig=$_POST['astig'];
	$reslimit=trim($_POST['reslimit']);
	$numRefineIter=trim($_POST['numRefineIter']);
	$maxdef=trim($_POST['maxdef']);
	$mindef=trim($_POST['mindef']);
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
			createForm("Phasor CTF does not work on tilted images");
			exit;
		}
	}

	if (!$sample) {
		createForm("Please select a sample type");
		exit;
	}

	if (!$reslimit || !is_numeric($reslimit)) {
		createForm("Please provide a valid res limit type ".$reslimit);
		exit;
	}

	if (!$maxdef || !is_numeric($maxdef)) {
		createForm("Please provide a valid maximum defocus ".$maxdef);
		exit;
	}

	if (!$mindef || !is_numeric($mindef)) {
		createForm("Please provide a valid minimum defocus ".$mindef);
		exit;
	}


	if (!is_numeric($numRefineIter)) {
		createForm("Please provide a valid number of iterations ".$numRefineIter);
		exit;
	}

	/* *******************
	PART 3: Create program command
	******************** */
	$command.= "phasorCtf.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	$command .= "--sample=$sample ";	
	if ($asitg == 'ON')
		$command .= "--astig ";	
	else
		$command .= "--no-astig ";	
	$command .= "--reslimit=$reslimit ";	
	$command .= "--maxdef=".($maxdef*1e-6)." ";
	$command .= "--mindef=".($mindef*1e-6)." ";
	$command .= "--refineIter=$numRefineIter ";	

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
