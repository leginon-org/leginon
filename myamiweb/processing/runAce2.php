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
	runAce2();
}
// CREATE FORM PAGE
else {
	createAce2Form();
}



/*
**
**
** Ace 2 FORM
**
**
*/

// CREATE FORM PAGE
function createAce2Form($extra=false) {
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
	processing_header("Ace 2 Launcher", "CTF Estimation by Ace 2", $javafunctions);

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
	while (file_exists($sessionpath.'acetwo'.($lastrunnumber+1)))
		$lastrunnumber += 1;
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'acetwo'.($lastrunnumber+1);
  $binval = ($_POST['binval']) ? $_POST['binval'] : 2;
  $confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';
  $reprocess = ($_POST['reprocess']) ? $_POST['reprocess'] : 0.8;
  $hpzero = ($_POST['hpzero']) ? $_POST['hpzero'] : '';
  $hpone = ($_POST['hpone']) ? $_POST['hpone'] : '';
  $edge1 = ($_POST['edge1']) ? $_POST['edge1'] : 10;
  $edge2 = ($_POST['edge2']) ? $_POST['edge2'] : 0.001;
  //$refine2d = ($_POST['refine2d']== 'on') ? 'CHECKED' : '';
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";


	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg' valign='top'>\n";

	echo"<center><img alt='ace2' src='img/ace2.jpg' WIDTH='300'></center><br />\n";


	echo "<input type='text' name='binval' value=$binval size='4'>\n";
	echo docpop('ace2bin','Binning');
	echo "<br/><br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)' $confcheck >\n";
	echo "Reprocess Below Confidence Value<br />\n";
	if ($confcheck == 'CHECKED') {
		echo "Set Value:<input type='text' name='reprocess' value=$reprocess size='4'>\n";
	} else {
		echo "Set Value:<input type='text' name='reprocess' disabled value=$reprocess size='4'>\n";
	}
	echo "<font size='-2'><i>(between 0.0 - 1.0)</i></font>\n";
	echo "<br/><br/>\n";

	echo docpop('hpmask','High Pass Filter');
	echo "<br/>\n";
	echo "<input type='text' name='hpzero' value='$hpzero' size='4'>\n";
	echo docpop('hpzero','low frequency set point');
	echo "<font size='-2'>(in &Aring;ngstroms)</font><br/>\n";

	echo "<input type='text' name='hpone' value='$hpone' size='4'>\n";
	echo docpop('hpone','high frequency set point');
	echo "<font size='-2'>(in &Aring;ngstroms)</font><br/><br/>\n";

	echo "<input type='text' name='edge1' value='10' size='4'>\n";
	echo docpop('edge1','Canny, edge Blur Sigma');
	echo "<br/><br/>\n";

	echo "<input type='text' name='edge2' value='0.001' size='4'>\n";
	echo docpop('edge2','Canny, edge Treshold(0.0-1.0)');
	echo "<br/><br/>\n";

	echo "<input type='text' name='rotblur' value='0.0' size='4'>\n";
	echo docpop('rotblur','Rotational blur <font size="-2">(in degrees)</font>');
	echo "<br/><br/>\n";

	/*echo "<input type='checkbox' name='refine2d' $refine2d>\n";
	echo docpop('refine2d','Extra 2d Refine');
	echo "<br/><br/>\n";*/

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run Ace 2");
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
function runAce2() {
	
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];
	// parse params
	//$refine2d=$_POST['refine2d'];
	$binval=$_POST['binval'];

	$hpzero=trim($_POST['hpzero']);
	$hpone=trim($_POST['hpone']);
	$edge1=trim($_POST['edge1']);
	$edge2=trim($_POST['edge2']);
	$rotblur=trim($_POST['rotblur']);
	$reprocess=$_POST['reprocess'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	$leginondata = new leginondata();
	if ($leginondata->getCsValueFromSession($expId) === false) {
		createAce2Form("Cs value of the images in this session is not unique or known, can't process");
		exit;
	}
	// check the tilt situation
	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($_GET['expId']);
	if ($maxang > 5) {
		$tiltangle = $_POST['tiltangle'];
		if ($tiltangle!='notilt' && $tiltangle!='lowtilt') {
			createAce2Form("ACE 2 does not work on tilted images");
			exit;
		}
	}
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command.= "pyace2.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createAce2Form($apcommand);
		exit;
	}
	$command .= $apcommand;

	if (is_numeric($reprocess))
		$command.="--reprocess=$reprocess ";

	if (is_numeric($hpone) and is_numeric($hpzero) and ($hpzero >=$hpone))
		$command.="--zeropass=$hpzero --onepass=$hpone ";

	if (is_numeric($edge1))
		$command.="--edge1=$edge1 ";

	if (is_numeric($edge2))
		$command.="--edge2=$edge2 ";

	if (is_numeric($rotblur))
		$command.="--rotblur=$rotblur ";

	//if($refine2d) $command.="--refine2d ";
	$command.="--bin=$binval ";
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("ACE: automated CTF estimation.", 2005, "Mallick SP, Carragher B, Potter CS, Kriegman DJ.", "Ultramicroscopy.", 104, 1, 15935913, false, false, false);
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'pyace2', $nproc);

	// if error display them
	if ($errors)
		createAce2Form("<b>ERROR:</b> $errors");
}

?>
