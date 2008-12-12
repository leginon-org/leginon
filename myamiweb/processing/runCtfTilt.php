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
	runCtfTilt();
}
// CREATE FORM PAGE
else {
	createCtfTiltForm();
}

// --- parse data and process on submit
function runCtfTilt() {
	$expId = $_GET['expId'];
	$runid = $_POST['runid'];
	$outdir=$_POST['outdir'];

	$command.= "ctftilt.py ";

	// parse params
	$ampcarbon=$_POST['ampcarbon'];
	$ampice=$_POST['ampice'];
	$fieldsize=$_POST['fieldsize'];
	$medium=$_POST['medium'];
	$binval=$_POST['binval'];
	$cs=$_POST['cs'];
	//$nominal=$_POST['nominal'];
	//$reprocess=$_POST['reprocess'];
	$proc = $_POST['processor'];

	$command.="ampcarbon=$ampcarbon ";
	$command.="ampice=$ampice ";
	$command.="fieldsize=$fieldsize ";
	$command.="medium=$medium ";
	$command.="cs=$cs ";
	$command.="bin=$binval ";
	//if ($nominal) $command.=" nominal=$nominal";
	//if ($reprocess) $command.=" reprocess=$reprocess";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createCtfTiltForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	// submit job to cluster
	if ($_POST['process'] == "Run CtfTilt") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createCtfTiltForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'ctftilt',False,True);
		// if errors:
		if ($sub) createCtfTiltForm("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("CtfTilt Results","CtfTilt Results");

	echo"
	<TABLE WIDTH='600'>
	<TR><TD COLSPAN='2'>
	<B>ACE Command:</B><br/>
	$command<HR>
	</TD></TR>";
	appionLoopSummaryTable();
	echo"
	<TR><TD>ampcarbon</TD><TD>$ampcarbon</TD></TR>
	<TR><TD>ampice</TD><TD>$ampice</TD></TR>
	<TR><TD>fieldsize</TD><TD>$fieldsize</TD></TR>
	<TR><TD>medium</TD><TD>$medium</TD></TR>
	<TR><TD>cs</TD><TD>$cs</TD></TR>\n";
	//if ($nominal=="db value" OR $nominal=="") echo "<TR><TD>nominal</TD><TD><I>NULL</I></TD></TR>\n";
	//else echo "<TR><TD>nominal</TD><TD>$nominal</TD></TR>\n";
	//if ($reprocess) echo "<TR><TD>reprocess</TD><TD>$reprocess</TD></TR>\n";
	//else echo "<TR><TD>reprocess</TD><TD><I>NULL</I></TD></TR>\n";
	echo "</TABLE>\n";
	processing_footer(True, True);
}

/*
**
**
** CtfTilt FORM
**
**
*/

// CREATE FORM PAGE
function createCtfTiltForm($extra=false) {
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
	$projectId=$_POST['projectId'];

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions = "";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("CtfTilt Launcher", "CTF Estimation by CtfTilt", $javafunctions);

	if ($extra) {
		echo "<font color='#dd0000'>$extra</FONT><br />\n";
	} else {
		echo "<font color='#bb8800' size='+1'>WARNING: CtfTilt is very slow and "
			."you cannot use the tilt angle or astigmatism results in makestack</font><br/><br/>\n";
	}

	echo"
	<FORM NAME='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","ctf",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$ctf = new particledata();
	$ctfruns = count($ctf->getCtfRunIds($sessionId));
	$defrunid = 'ctftiltrun'.($ctfruns+1);
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	createAppionLoopTable($sessiondata, $defrunid, "ctf");
	echo"
	  </TD>
	  <TD CLASS='tablebg'>

	    <B>Medium:</B><br/>
	    <INPUT TYPE='radio' NAME='medium' VALUE='carbon'>&nbsp;carbon&nbsp;&nbsp;
	    <INPUT TYPE='radio' NAME='medium' VALUE='ice' checked>&nbsp;ice<br/>
	    <br/>

	  <TABLE CELLSPACING=0 CELLPADDING=2><TR>

	    <TD VALIGN='TOP'>\n";
	echo docpop('binval','<b>Binning</b>');
	echo " (Pixel Average): ";
	echo "<INPUT TYPE='text' NAME='binval' VALUE='1' SIZE='4'>\n";
	echo "<br/><br/>\n";

	echo docpop('ampcontrast','<b>Amplitude Contrast:</b>');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='ampcarbon' VALUE='0.15' SIZE='4'>\n";
	echo "Carbon<br />\n";
	echo "<INPUT TYPE='text' NAME='ampice' VALUE='0.07' SIZE='4'>\n";
	echo "Ice\n";
	echo "</TD>\n";

	echo "</TR></TABLE><br /><br />\n";

	echo "<INPUT TYPE='text' NAME='fieldsize' VALUE='512' size='4'>\n";
	echo docpop('field','Field Size');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='cs' VALUE='".$defaultcs."' SIZE='4'>\n";
	echo docpop('cs','Spherical Aberration');
	echo "<br />\n";
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
	</TR>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run CtfTilt");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";
	processing_footer();
}

?>
