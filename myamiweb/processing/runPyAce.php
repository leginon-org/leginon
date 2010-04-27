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

// Cs should come straight out of the DB somehow, instead it is in config
$defaultcs=$DEFAULTCS;

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runPyAce();
}
// CREATE FORM PAGE
else {
	createPyAceForm();
}

/*
$expId = $_GET[expId];
$phpself=$_SERVER['PHP_SELF'];

// --- Set sessionId
if ($expId){$sessionId=$expId;}
else {$sessionId=$_POST[sessionId];}

$projectId =getProjectId();

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if($projectdb)
	$projects = $projectdata->getProjects('all');

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);

$sessioninfo = $leginondata->getSessionInfo($sessionId);
$presets = $leginondata->getTruePresets($sessionId);

if (!empty($sessioninfo)) {
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","pyAce/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
}

*/

// --- parse data and process on submit
function runPyAce() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$command.= "pyace.py ";

	// parse params
	$edgethcarbon=$_POST[edgethcarbon];
	$edgethice=$_POST[edgethice];
	$pfcarbon=$_POST[pfcarbon];
	$pfice=$_POST[pfice];
	$overlap=$_POST[overlap];
	$fieldsize=$_POST[fieldsize];
	$resamplefr=$_POST[resamplefr];
	$medium=$_POST[medium];
	$cs=$_POST[cs];
	$nominal=$_POST[nominal];
	$reprocess=$_POST[reprocess];
	$display = ($_POST[display]=="on") ? "1" : '0';
	$newnominal = ($_POST[newnominal]=="on") ? "1" : '0';
	$drange = ($_POST[drange]=="on") ? "1" : '0';
	$stig = ($_POST[stig]=="on") ? "1" : '0';
	$continue = ($_POST[cont]=="on") ? "1" : '0';
	$commit = ($_POST[commit]=="on") ? "1" : '0';
	$proc = $_POST[processor];

	$command.="--edgethcarbon=$edgethcarbon ";
	$command.="--edgethice=$edgethice ";
	$command.="--pfcarbon=$pfcarbon ";
	$command.="--pfice=$pfice ";
	$command.="--overlap=$overlap ";
	$command.="--fieldsize=$fieldsize ";
	$command.="--resamplefr=$resamplefr ";
	$command.="--medium=$medium ";
	$command.="--cs=$cs ";
	$command.="--drange=$drange ";
	$command.="--display=$display ";
	$command.="--stig=$stig";
	if ($nominal) $command.=" --nominal=$nominal";
	if ($reprocess) $command.=" --reprocess=$reprocess";
	if ($newnominal) $command.=" --newnominal";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createPyAceForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	// check the tilt situation
	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($_GET['expId']);
	if ($maxang > 5) {
		$tiltangle = $_POST['tiltangle'];
		if ($tiltangle!='notilt') {
			createPyAceForm("ACE 1 does not work on tilted images");
			exit;
		}
	}

	// submit job to cluster
	if ($_POST['process']=="Run ACE") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createPyAceForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'ace',False,True);
		// if errors:
		if ($sub) createPyAceForm("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("PyACE Results","PyACE Results");

	echo"
	<TABLE WIDTH='600'>
	<TR><TD COLSPAN='2'>
	<B>ACE Command:</B><br/>
	$command<HR>
	</TD></tr>";
	appionLoopSummaryTable();
	echo"
	<TR><td>edgethcarbon</TD><td>$edgethcarbon</TD></tr>
	<TR><td>edgethice</TD><td>$edgethice</TD></tr>
	<TR><td>pfcarbon</TD><td>$pfcarbon</TD></tr>
	<TR><td>pfice</TD><td>$pfice</TD></tr>
	<TR><td>overlap</TD><td>$overlap</TD></tr>
	<TR><td>fieldsize</TD><td>$fieldsize</TD></tr>
	<TR><td>resamplefr</TD><td>$resamplefr</TD></tr>
	<TR><td>medium</TD><td>$medium</TD></tr>
	<TR><td>cs</TD><td>$cs</TD></tr>
	<TR><td>drange</TD><td>$drange</TD></tr>
	<TR><td>display</TD><td>$display</TD></tr>
	<TR><td>stig</TD><td>$stig</TD></tr>\n";

	if ($nominal=="db value" OR $nominal=="") echo "<TR><td>nominal</TD><td><I>NULL</I></TD></tr>\n";
	else echo "<TR><td>nominal</TD><td>$nominal</TD></tr>\n";
	if ($reprocess) echo "<TR><td>reprocess</TD><td>$reprocess</TD></tr>\n";
	else echo "<TR><td>reprocess</TD><td><I>NULL</I></TD></tr>\n";
	echo "<TR><td>newnominal</TD><td>$newnominal</TD></tr>\n";
	echo "</table>\n";
	processing_footer(True, True);
}

/*
**
**
** PyACE FORM
**
**
*/

// CREATE FORM PAGE
function createPyAceForm($extra=false) {
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
	$projectId=getProjectId();

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		function enabledf(){
			 if (document.viewerform.nominalcheck.checked){
			    document.viewerform.nominal.disabled=false;
			    document.viewerform.nominal.value='';
			 }
			 else {
			    document.viewerform.nominal.disabled=true;
			    document.viewerform.nominal.value='db value';
			 }
		}
		function enableconf(){
			 if (document.viewerform.confcheck.checked){
			    document.viewerform.reprocess.disabled=false;
			    document.viewerform.reprocess.value='';
			 }
			 else {
			    document.viewerform.reprocess.disabled=true;
			    document.viewerform.reprocess.value='0.8';
			 }
		}
		function infopopup(infoname){
			var newwindow=window.open('','name','height=250,width=400');
			newwindow.document.write('<HTML><BODY>');
			if (infoname=='edgethresh'){
				newwindow.document.write('The threshold set for edge detection. ACE searches a range of values to determine a good threshold, but this value should be increased if there are more edges in the power spectrum than in the ring.  Decrease if no edges are detected.');
			}
			if (infoname=='pfact'){
				newwindow.document.write('Location of the upper cutoff frequency.  If thon rings extend beyond the power spectrum cutoff frequency, increase this value.  In cases of low signal to noise ratio with few thon rings, decrease this value.')
			}
			if (infoname=='drange'){
				newwindow.document.write('Use in cases where the signal to noise ratio is so high that the edge detection is incorrect.');
			}
			if (infoname=='resamplefr'){
				newwindow.document.write('Sets the sampling size of the CTF.  At high defoci or at higher magnifications, the first thon rings may be so close to the origin that they are not processed by ACE. In these cases raise the resampling value (2.0 works well in these cases).<br/><br/><table><TR><TD COLSPAN=2>typical values for defocus/apix</TD></tr><TR><td>0.5</TD><td>1.2</TD></tr><TR><td>1.0</TD><td>1.5</TD></tr><TR><td>1.5</TD><td>1.6</TD></tr><TR><td>2.0</TD><td>1.8</TD></tr><TR><td>3.0</TD><td>2.2</TD></tr><TR><td>4.0</TD><td>2.7</TD></tr></table><br/>For example, with defocus = 2.0 (-2.0x10<SUP>-6</SUP> m) and apix (&Aring;/pixel) = 1.63<br/>then defocus/apix = 1.22 and you should use resamplefr=1.6<br/>(as long as its close it should work.)');
			}
			if (infoname=='overlap'){
				newwindow.document.write('During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio. This value (n) will result in successive images having an overlap of (1-n)*field size. Increase in cases of very low signal to noise ratio.');
			}
			if (infoname=='field'){
				newwindow.document.write('During processing, micrographs are cut into a series of smaller images and averaged together to increase the signal to noise ratio. This value refers to the width (in pixels) of the cropped images.');
			}
			newwindow.document.write('</BODY></HTML>');
			newwindow.document.close();
		}

	</SCRIPT>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header("PyACE Launcher","Automated CTF Estimation With PyACE",$javafunctions);

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	echo"
	<FORM NAME='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=getSessionList($projectId,$expId);
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
	$lastrunnumber = $ctf->getLastRunNumberForType($sessionId,'ApAceRunData','name'); 
	while (file_exists($sessionpath.'acerun'.($lastrunnumber+1)))
		$lastrunnumber += 1;
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'acerun'.($lastrunnumber+1);
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";


	createAppionLoopTable($sessiondata, $defrunname, "ctf");

	echo "<INPUT TYPE='checkbox' NAME='confcheck' onclick='enableconf(this)'>\n";
	echo "Reprocess Below Confidence Value<br />\n";
	echo "Set Value:<INPUT TYPE='text' NAME='reprocess' disabled value='0.8' size='4'>\n";
	echo "<FONT SIZE=-2><I>(between 0.0 - 1.0)</I></FONT><br />\n";
	echo "<br />\n";
	echo "<B>Nominal override:</B><br />\n";
	echo "<INPUT TYPE='checkbox' NAME='nominalcheck' onclick='enabledf(this)'>\n";
	echo "Override Nominal Defocus<br />\n";
	echo "Set Defocus:<INPUT TYPE='text' NAME='nominal' DISABLED VALUE='db value' SIZE='8'>\n";
	echo "<FONT SIZE=-2><I>(in meters, i.e. <B>-2.0e-6</B>)</I></FONT><br />";
	if ($ctfruns > 0) {
		echo"
			<INPUT TYPE='checkbox' NAME='newnominal'>
	    Use Previously ACE Estimated Defocus";
	}

	echo"
	  </TD>
	  <TD CLASS='tablebg'>";

	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><img src='img/ace1.jpg' WIDTH='300'></center><br />\n";
	}


	echo"
	    <INPUT TYPE='checkbox' NAME='display' CHECKED>
	    Write Result Images<br/>
	    <br/>
	    <B>Medium:</B><br/>
	    <INPUT TYPE='radio' NAME='medium' VALUE='carbon'>&nbsp;carbon&nbsp;&nbsp;
	    <INPUT TYPE='radio' NAME='medium' VALUE='ice' checked>&nbsp;ice<br/>
	    <br/>

	    <B>Astigmatism:</B><br/>
	    <INPUT TYPE='checkbox' NAME='stig'>
	    Estimate Astigmatism <FONT SIZE=-2><I>(experimental)</I></FONT><br/>
	    <br/>

	  <TABLE CELLSPACING=0 CELLPADDING=2><TR>

	    <TD VALIGN='TOP'>\n";
	echo docpop('edgethresh','<b>Edge Thresholds</b>');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='edgethcarbon' VALUE='0.8' SIZE='4'>\n";
	echo "Carbon<br />\n";
	echo "<INPUT TYPE='text' NAME='edgethice' VALUE='0.6' SIZE='4'>\n";
	echo "Ice\n";
	echo "</TD>\n";
	echo "<td>&nbsp;</td>\n";
	echo "<td>&nbsp;</td>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo docpop('pfact','<b>Power Factors:</b>');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='pfcarbon' VALUE='0.9' SIZE='4'>\n";
	echo "Carbon<br />\n";
	echo "<INPUT TYPE='text' NAME='pfice' VALUE='0.3' SIZE='4'>\n";
	echo "Ice\n";
	echo "</TD>\n";

	echo "</tr></table><br />\n";

	echo "<INPUT TYPE='text' NAME='resamplefr' VALUE='1.5' size='4'>\n";
	echo docpop('resamplefr','Resampling Frequency');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='overlap' VALUE='2' SIZE='4'>\n";
	echo docpop('overlap','Averaging Overlap');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='fieldsize' VALUE='512' size='4'>\n";
	echo docpop('field','Field Size');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='cs' VALUE='".$defaultcs."' SIZE='4'>\n";
	echo docpop('cs','Spherical Aberration');
	echo "<br />\n";
	echo "<INPUT TYPE='checkbox' NAME='drange'>\n";
	echo docpop('drange','Compress Dynamic Range');
	echo "<br />\n";

	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run ACE");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";
	processing_footer();
}

function getdata($str_field, $str_data) {
	$result=array();
	$f = explode(" ",$str_field);
	foreach($f as $k=>$v) {
		if ($v)
			$fields[]=$v;
	}
	foreach($fields as $k=>$f) {
		$positions[] = ($k) ? strpos($str_field, $f) : 0;
	}
	foreach ($positions as $k=>$v) {
		$l = ($k<count($positions)-1) ? $positions[$k+1]-$v : strlen($str_data);
		$f = $fields[$k];
		$result[$f]=trim(substr($str_data, $v, $l));
	}
	return $result;
}


?>
