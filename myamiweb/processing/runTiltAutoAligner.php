<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
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
	runTiltAutoAligner();
}
// CREATE FORM PAGE
else {
	createTiltAutoAlignerForm();
}


function createTiltAutoAlignerForm($extra=false, $title='Tilt Auto Aligner Launcher', $heading='Tilt Auto Aligner') {

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

	// --- find hosts to run Tilt Aligner

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("Tilt Aligner Launcher","Tilt Aligner Particle Selection and Editing",$javafunctions);

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

	$sessiondata=getSessionList($projectId,$expId);

	// Set any existing parameters in form
	$particle=new particleData;
	$prtlrunIds = $particle->getParticleRunIds($sessionId, True);
	$prtlruns = count($prtlrunIds);
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name'); 
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'autotiltrun'.($lastrunnumber+1);
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$prtlrunval = ($_POST['pickrunid']) ? $_POST['pickrunid'] : '';
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>";

	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><img src='img/autotiltpicker.png' WIDTH='300'></center><br />\n";
	}

	createAppionLoopTable($sessiondata, $defrunname, "tiltalign");

	if (!$prtlrunIds) {
		echo"<FONT COLOR='RED'><B>No Particles for this Session</B></FONT>\n";
		echo"<INPUT TYPE='HIDDEN' NAME='pickrunid1' VALUE='None'>\n";
		echo"<INPUT TYPE='HIDDEN' NAME='pickrunid2' VALUE='None'>\n";
	}
	else {
		echo "<br>Edit Particle Picks:<br/>
		<SELECT NAME='pickrunid1'>\n";
		echo "<OPTION VALUE='None'>None</OPTION>";
		foreach ($prtlrunIds as $prtlrun){
			$prtlrunId=$prtlrun['DEF_id'];
			$runname=$prtlrun['name'];
			$prtlstats=$particle->getStats($prtlrunId);
			$totprtls=commafy($prtlstats['totparticles']);
			echo "<OPTION VALUE='$prtlrunId'";
			// select previously set prtl on resubmit
			if ($prtlrunval==$prtlrunId) echo " SELECTED";
			echo">$runname ($totprtls prtls)</OPTION>\n";
		}
		echo "</SELECT>\n";
		echo "<SELECT NAME='pickrunid2'>\n";
		echo "<OPTION VALUE='None'>None</OPTION>";
		foreach ($prtlrunIds as $prtlrun){
			$prtlrunId=$prtlrun['DEF_id'];
			$runname=$prtlrun['name'];
			$prtlstats=$particle->getStats($prtlrunId);
			$totprtls=commafy($prtlstats['totparticles']);
			echo "<OPTION VALUE='$prtlrunId'";
			// select previously set prtl on resubmit
			if ($prtlrunval==$prtlrunId) echo " SELECTED";
			echo">$runname ($totprtls prtls)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	$diam = ($_POST['diam']) ? $_POST['diam'] : "";
	echo"
		<TD CLASS='tablebg'>
		<B>Particle Diameter:</B><br />
		<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
	echo docpop('pdiam',' Particle diameter for result images');
	echo "<FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
		<br><br>";
	/*echo"
		<B>Picking Icon:</B><br>
		<SELECT NAME='shape'>\n";
	$shapes = array('plus', 'circle', 'cross', 'point', 'square', 'diamond', );
	foreach($shapes as $shape) {
		$s = ($_POST['shape']==$shape) ? 'SELECTED' : '';
		echo "<OPTION $s>$shape</OPTION>\n";
	}
	echo "</SELECT>\n&nbsp;Picking icon shape<br>";
	$shapesize = (int) $_POST['shapesize'];
	echo"
		<INPUT TYPE='text' NAME='shapesize' VALUE='$shapesize' SIZE='3'>&nbsp;
		Picking icon diameter <FONT SIZE=-2><I>(in pixels)</I></FONT>
		<br><br>";
	*/
	echo"
		<B>Output file type:</B><br>
		<SELECT NAME='ftype'>\n";
	$ftypes = array('spider', 'text', 'xml', 'pickle', );
	foreach($ftypes as $ftype) {
		$s = ($_POST['ftype']==$ftype) ? 'SELECTED' : '';
		echo "<OPTION $s>$ftype</OPTION>\n";
	}
	echo "</SELECT><br>";
	createParticleLoopTable(-1, -1);
	echo "
		</TD>
	</tr>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'><hr>";
	echo getSubmitForm("Run Tilt Auto Aligner");
	echo "
		</TD>
	</tr>
	</table>";

	echo referenceBox("DoG Picker and TiltPicker: software tools to facilitate particle selection in single particle electron microscopy.", 2009, "Voss NR, Yoshioka CK, Radermacher M, Potter CS, Carragher B.", "J Struct Biol.", 166, 2, 19374019, 2768396, false, false);

	processing_footer();
	?>

	</CENTER>
	</FORM>
	<?
}

function runTiltAutoAligner() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$command ="tiltAutoAligner.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createTiltAutoAlignerForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$partcommand = parseParticleLoopParams("manual", $_POST);
	if ($partcommand[0] == "<") {
		createTiltAutoAlignerForm($partcommand);
		exit;
	}
	$command .= $partcommand;

	$pickrunid1=$_POST['pickrunid1'];
	$pickrunid2=$_POST['pickrunid2'];
	if ($pickrunid1 != 'None' && $pickrunid2 != 'None') {
		$command .= " --pickrunids=$pickrunid1,$pickrunid2";
	} elseif ($pickrunid1 != 'None') {
		$command .= " --pickrunids=$pickrunid1";
	} elseif ($pickrunid2 != 'None') {
		$command .= " --pickrunids=$pickrunid2";
	} else {
		createTiltAutoAlignerForm("<b>ERROR:</b> Select a previous particle picking run");
		exit;
	}

	$ftype=$_POST['ftype'];
	$command .= " --outtype=$ftype";

	if ($_POST['process'] == "Run Tilt Auto Aligner") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			createTiltAutoAlignerForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'tiltalign',False,True);
		// if errors:
		if ($sub)
			createTiltAutoAlignerForm("<b>ERROR:</b> $sub");
		exit;

	} else {

		processing_header("Tilt Auto Aligner Command","Tilt Auto Aligner Command");

		echo referenceBox("DoG Picker and TiltPicker: software tools to facilitate particle selection in single particle electron microscopy.", 2009, "Voss NR, Yoshioka CK, Radermacher M, Potter CS, Carragher B.", "J Struct Biol.", 166, 2, 19374019, 2768396, false, false);

		echo"
			<TABLE WIDTH='600'>
			<TR><TD COLSPAN='2'>
			<B>Tilt Aligner Command:</B><br>
			$command<HR>
			</TD></tr>";

		appionLoopSummaryTable();
		particleLoopSummaryTable();
		echo"</table>\n";
		processing_footer();
	}
}

?>
