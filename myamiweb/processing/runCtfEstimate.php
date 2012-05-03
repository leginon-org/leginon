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

	// ctffind or ctftilt
	$ctftilt = $_GET['ctftilt'];
	if (!$ctftilt) $ctftilt = ($_POST['runctftilt']=='on') ? True : '';
	
	// parse params
	$ampcarbon=$_POST['ampcarbon'];
	$ampice=$_POST['ampice'];
	$fieldsize=$_POST['fieldsize'];
	$medium=$_POST['medium'];
	$binval=$_POST['binval'];
	$resmin=$_POST['resmin'];
	$resmax=$_POST['resmax'];
	$defstep=$_POST['defstep'];
	$dast=$_POST['dast'];
	//$nominal=$_POST['nominal'];
	//$reprocess=$_POST['reprocess'];
	
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
	if (!$defstep) createCtfEstimateForm("Enter a search step");
	if ($resmin<50) createCtfEstimateForm("Minimum resolution is too high");
	if (($resmax>50)||(!$resmax)) createCtfEstimateForm("Maximum resolution is too low");
	
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command = "ctfestimate.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createCtfEstimateForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$command.="--ampcarbon=$ampcarbon ";
	$command.="--ampice=$ampice ";
	$command.="--fieldsize=$fieldsize ";
	$command.="--medium=$medium ";
	$command.="--bin=$binval ";
	$command.="--resmin=$resmin ";
	$command.="--resmax=$resmax ";
	$command.="--defstep=$defstep ";
	$command.="--dast=$dast ";

	$progname = "CtfFind";
	if ($ctftilt) {
		$command.="--ctftilt ";
		$progname = "CtfTilt";
	}
	//if ($nominal) $command.=" nominal=$nominal";
	//if ($reprocess) $command.=" reprocess=$reprocess";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("Accurate determination of local defocus and specimen tilt in electron microscopy.", 2003, "Mindell, JA, Grigorieff N.", "J Struct Biol.", 142, 3, 12781660, false, false, "img/grigorieff_lab.png");
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'ctfestimate', $nproc);

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
	$progname = "CtfFind";
	$runbase = "ctffind";
	$ctftilt = $_GET['ctftilt'];
	if ($ctftilt) {
		$progname = "CtfTilt";
		$runbase = "ctftilt";
		$formAction .= "&ctftilt=True";
	}

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("$progname Launcher", "CTF Estimation by $progname", $javafunctions);

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	} elseif ($ctftilt) {
		echo "<font color='#bb8800' size='+1'>WARNING: CtfTilt is very slow and "
			."you cannot use the tilt angle or astigmatism results in makestack</font><br/><br/>\n";
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
	$form_fieldsz = ($_POST['fieldsize']) ? $_POST['fieldsize'] : 256;
	$form_bin = ($_POST['binval']) ? $_POST['binval'] : 2;
	$form_ampc = ($_POST['ampcarbon']) ? $_POST['ampcarbon'] : '0.15';
	$form_ampi = ($_POST['ampice']) ? $_POST['ampice'] : '0.07';
	$form_resmin = ($_POST['resmin']) ? $_POST['resmin'] : '400.0';
	$form_resmax = ($_POST['resmax']) ? $_POST['resmax'] : '8.0';
	$form_defstep = ($_POST['defstep']) ? $_POST['defstep'] : '5000.0';
	// check if ctftilt is set
	$ctftiltcheck = ($_POST['runctftilt']=='on') ? 'CHECKED' : '';
	$form_dast = ($_POST['dast']) ? $_POST['dast'] : '100';

	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg'>

	    <B>Medium:</B><br/>
	    <INPUT TYPE='radio' NAME='medium' VALUE='carbon'>&nbsp;carbon&nbsp;&nbsp;
	    <INPUT TYPE='radio' NAME='medium' VALUE='ice' checked>&nbsp;ice<br/>
	    <br/>\n";

	echo docpop('ampcontrast','<b>Amplitude Contrast:</b>');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='ampcarbon' VALUE='$form_ampc' SIZE='4'>\n";
	echo "Carbon<br />\n";
	echo "<INPUT TYPE='text' NAME='ampice' VALUE='$form_ampi' SIZE='4'>\n";
	echo "Ice\n";
	echo "<br/><br/>\n";

	echo "<INPUT TYPE='text' NAME='binval' VALUE='$form_bin' SIZE='4'>\n";
	echo docpop('binval','Binning');
	echo "<br/><br/>\n";

	echo "<b>$progname Values</b><br/>\n";
	echo "<INPUT TYPE='text' NAME='fieldsize' VALUE='$form_fieldsz' size='6'>\n";
	echo docpop('field','Field Size');
	echo "<br />\n";
	echo "<input type='text' name='resmin' value='$form_resmin' size='6'>\n";
	echo docpop('resmin','Minimum Resolution');
	echo "<br />\n";
	echo "<input type='text' name='resmax' value='$form_resmax' size='6'>\n";
	echo docpop('resmax','Maximum Resolution');
	echo "<br />\n";
	echo "<input type='text' name='defstep' value='$form_defstep' size='6'>\n";
	echo docpop('defstep','Search step (Ang)');
	echo "<br />\n";
	echo "<input type='text' name='dast' value='$form_dast' size='6'>\n";
	echo docpop('dast','Expected astigmatism (Ang)');
	echo "<br />\n";
	// give user option to run ctftilt (useful for film data)
	if (!$ctftilt) { 
		echo "<input type='checkbox' name='runctftilt' $ctftiltcheck>\n";
		echo docpop('ctftilt','Run CtfTilt');
		echo "<br>\n";
	}
	echo "<br />\n";
	//echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)'>\n";
	//echo "Reprocess Below Confidence Value<br />\n";
	//echo "Set Value:<INPUT TYPE='text' NAME='reprocess' DISABLED VALUE='0.8' SIZE='4'>\n";
	//echo "<FONT SIZE=-2><I>(between 0.0 - 1.0)</I></FONT><br />\n";
	//echo "<br />\n";
	//echo "<B>Nominal override:</B><br />\n";
	//echo "<INPUT TYPE='checkbox' NAME='nominalcheck' onclick='enabledf(this)'>\n";
	//echo "Override Nominal Defocus<br />\n";
	//echo "Set Defocus:<INPUT TYPE='text' NAME='nominal' DISABLED VALUE='db value' SIZE='8'>\n";
	//echo "<FONT SIZE=-2><I>(in meters, i.e. <B>-2.0e-6</B>)</I></FONT><br />";
	//if ($ctfruns > 0) {
	//	echo"
	//		<INPUT TYPE='checkbox' NAME='newnominal'>
	//    Use Previously ACE Estimated Defocus";
	//}
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

	echo referenceBox("Accurate determination of local defocus and specimen tilt in electron microscopy.", 2003, "Mindell, JA, Grigorieff N.", "J Struct Biol.", 142, 3, 12781660, false, false, "img/grigorieff_lab.png");

	processing_footer();
}

?>
