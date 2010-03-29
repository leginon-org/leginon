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
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","ctf/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$ctf = new particledata();
	$lastrunnumber = $ctf->getLastRunNumberType($sessionId,'ApAceRunData','name'); 
	while (file_exists($sessionpath.'acetwo'.($lastrunnumber+1)))
		$lastrunnumber += 1;
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'acetwo'.($lastrunnumber+1);
  $binval = ($_POST['binval']) ? $_POST['binval'] : 2;
  $cs = ($_POST['cs']) ? $_POST['cs'] : $defaultcs;
  $confcheck = ($_POST['confcheck']== 'on') ? 'CHECKED' : '';
  $reprocess = ($_POST['reprocess']) ? $_POST['reprocess'] : 0.8;
  $hpzero = ($_POST['hpzero']) ? $_POST['hpzero'] : '';
  $hpone = ($_POST['hpone']) ? $_POST['hpone'] : '';
  $edge1 = ($_POST['edge1']) ? $_POST['edge1'] : 10;
  $edge2 = ($_POST['edge2']) ? $_POST['edge2'] : 0.001;
  $refine2d = ($_POST['refine2d']== 'on') ? 'CHECKED' : '';
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
	echo docpop('binval','Binning');
	echo "<br/><br/>\n";

	echo "<input type='text' name='cs' value='".$cs."' size='4'>\n";
	echo docpop('cs','Spherical Aberration');
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
	echo docpop('hpzero','0% pass resolution limit (Angstrum)');
	echo "<br/>\n";

	echo "<input type='text' name='hpone' value='$hpone' size='4'>\n";
	echo docpop('hpone','100% pass resolution limit (Angstrum)');
	echo "<br/><br/>\n";

	echo "<input type='text' name='edge1' value='10' size='4'>\n";
	echo docpop('edge1','Canny, edge Blur Sigma');
	echo "<br/><br/>\n";

	echo "<input type='text' name='edge2' value='0.001' size='4'>\n";
	echo docpop('edge2','Canny, edge Treshold(0.0-1.0)');
	echo "<br/><br/>\n";

	echo "<input type='text' name='rotblur' value='0.0' size='4'>\n";
	echo docpop('rotblur','Rotational blur <font size="-2">(in degrees)</font>');
	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='refine2d' $refine2d>\n";
	echo docpop('refine2d','Extra 2d Refine');
	echo "<br/><br/>\n";

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
	$hpzero=trim($_POST['hpzero']);
	$hpone=trim($_POST['hpone']);
	$edge1=trim($_POST['edge1']);
	$edge2=trim($_POST['edge2']);
	$rotblur=trim($_POST['rotblur']);
	$reprocess=$_POST['reprocess'];

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

	if($refine2d) $command.="--refine2d ";
	$command.="--cs=$cs ";
	$command.="--bin=$binval ";

	// submit job to cluster
	if ($_POST['process'] == "Run Ace 2") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createAce2Form("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'pyace2',False,False);
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
		</TD></tr>";
		appionLoopSummaryTable();
		echo"
		<TR><td>refine 2d</TD><td>$refine2d</TD></tr>
		<TR><td>bin</TD><td>$binval</TD></tr>
		<TR><td>cs</TD><td>$cs</TD></tr>
		<TR><td>rotblur</TD><td>$rotblur</TD></tr>\n";
		echo "</table>\n";
		processing_footer(True, True);
	}
}


?>
