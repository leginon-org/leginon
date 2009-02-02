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

$defaultcs="2.0";

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
	global $defaultcs;
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
	$projectId=$_SESSION['projectId'];

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("Ace 2 Launcher", "CTF Estimation by Ace 2", $javafunctions);

	if ($extra) {
		echo "<font color='#dd0000'>$extra</FONT><br />\n";
	}

	echo"
	<FORM NAME='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","ctf/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$ctf = new particledata();
	$ctfruns = count($ctf->getCtfRunIds($sessionId));
	$defrunname = 'acetwo'.($ctfruns+1);
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";


	createAppionLoopTable($sessiondata, $defrunname, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg' valign='top'>\n";

	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><IMG SRC='img/ace2.jpg' WIDTH='300'></center><br />\n";
	}


	echo "<INPUT TYPE='text' NAME='binval' VALUE='2' SIZE='4'>\n";
	echo docpop('binval','Binning');
	echo "<br/><br/>\n";

	echo "<INPUT TYPE='text' NAME='cs' VALUE='".$defaultcs."' SIZE='4'>\n";
	echo docpop('cs','Spherical Aberration');
	echo "<br/><br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='refine2d'>\n";
	echo docpop('refine2d','Extra 2d Refine');
	echo "<br/><br/>\n";

	echo"
	  </TD>
	</TR>
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
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$command.= "pyace2.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createAce2Form($apcommand);
		exit;
	}
	$command .= $apcommand;

	// parse params
	$refine2d=$_POST['refine2d'];
	$binval=$_POST['binval'];
	$cs=$_POST['cs'];

	if($refine2d) $command.="--refine2d ";
	$command.="--cs=$cs ";
	$command.="--bin=$binval ";

	// submit job to cluster
	if ($_POST['process'] == "Run Ace 2") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createAce2Form("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'ace2',False,False);
		// if errors:
		if ($sub) createAce2Form("<b>ERROR:</b> $sub");
		exit;
	} else {

		processing_header("Ace2 Results","Ace2 Results");

		echo"
		<TABLE WIDTH='600'>
		<TR><TD COLSPAN='2'>
		<B>ACE Command:</B><br/>
		$command<HR>
		</TD></TR>";
		appionLoopSummaryTable();
		echo"
		<TR><TD>refine 2d</TD><TD>$refine2d</TD></TR>
		<TR><TD>bin</TD><TD>$binval</TD></TR>
		<TR><TD>cs</TD><TD>$cs</TD></TR>\n";
		echo "</TABLE>\n";
		processing_footer(True, True);
	}
}


?>
