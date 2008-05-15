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
	runDogPicker();
}
// CREATE FORM PAGE
else {
	createDogPickerForm();
}


function createDogPickerForm($extra=false, $title='DoG Picker Launcher', $heading='Automated Particle Selection with DoG Picker') {

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

	// --- find hosts to run Dog Picker
	$hosts=getHosts();

	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
	   function enabledtest(){
         if (document.viewerform.testimage.checked){
            document.viewerform.testfilename.disabled=false;
            document.viewerform.testfilename.value='';
         }	
         else {
	         document.viewerform.testfilename.disabled=true;
	         document.viewerform.testfilename.value='mrc file name';
         }
	   }
	</SCRIPT>\n";
	$javafunctions .= appionLoopJavaCommands();
	$javafunctions .= writeJavaPopupFunctions('eman');	
	$javafunctions .= particleLoopJavaCommands();

	writeTop("DoG Picker Launcher","Automated Particle Selection with DoG Picker",$javafunctions);

	if ($extra) {
		echo "<font COLOR='#DD0000' size=+2>$extra</font>\n<hr>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<input type='HIDDEN' NAME='lastSessionId' value='$sessionId'>\n";

	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

	// Set any existing parameters in form
	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId));
	$defrunid = ($_POST['runid']) ? $_POST['runid'] : 'dogrun'.($prtlruns+1);
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<tr>
		<td VALIGN='TOP'>";
	srand(time());
	if ((rand()%9) > 7) {
		echo"
	<center><IMG SRC='img/dogpicker.jpg' WIDTH='300'></center><br />\n";
	}
	createAppionLoopTable($sessiondata, $defrunid, "extract");
	$diam = ($_POST['diam']) ? $_POST['diam'] : "";
	echo "<td class='tablebg'>\n";
	echo "<b>Particle Diameter:</b><br />\n";
	echo "<input type='text' NAME='diam' value='$diam' size='4'>\n";
	echo docpop('pdiam','Particle diameter for filtering');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br /><br />\n";
	createParticleLoopTable(0.7, 1.5);
	$kfactor = ($_POST['kfactor']) ? $_POST['kfactor'] : "";
	$numslices = ($_POST['numslices']) ? $_POST['numslices'] : "";
	$sizerange = ($_POST['sizerange']) ? $_POST['sizerange'] : "";
	echo "<input type='text' name='kfactor' value='$kfactor' size='6'>\n";
	echo docpop('kfactor',' K-factor');
	echo " <font size=-2><i>(sloppiness)</i></font>\n";
	echo "<br /><br />\n";
	echo "<b>Multi-scale dogpicker:</b><br />\n";
	echo "<input type='text' name='numslices' value='$numslices' size='3'>\n";
	echo docpop('numslices',' Number of Slices');
	echo " <font size=-2><i>(number of sizes)</i></font>\n";
	echo "<br />\n";
	echo "<input type='text' name='sizerange' value='$sizerange' size='3'>\n";
	echo docpop('sizerange',' Size Range');
	echo " <font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br />\n";
	echo "</td>
	</tr>
	<tr>
		<td COLSPAN='2' ALIGN='center'>
		<hr>
		<input type='checkbox' name='testimage' onclick='enabledtest(this)' $testcheck>
		Test these settings on image:
		<input type='text' name='testfilename' $testdisabled value='$testvalue' size='45'>
		<hr />
	        <input type='submit' name='process' value='Just Show Command'>\n";
	if ($_SESSION['username']) echo "  <input type='submit' name='process' value='Run DogPicker'>\n";
	echo "  <br />
		</td>
	</tr>
	</form>
	</table>\n";
	writeBottom();
}

function runDogPicker() {
	$expId = $_GET['expId'];
	$runid = $_POST['runid'];
	$outdir = $_POST['outdir'];

	$command .="dogPicker.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createDogPickerForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$partcommand = parseParticleLoopParams($_POST);
	if ($partcommand[0] == "<") {
		createDogPickerForm($partcommand);
		exit;
	}
	$command .= $partcommand;

	$numslices = (int) $_POST[numslices];
	$sizerange = $_POST[sizerange];
	$kfactor = $_POST[kfactor];
	if ($numslices) {
		if($numslices < 2) {
			createDogPickerForm("<B>ERROR:</B> numslices must be more than 1");
			exit;
		}
		if(!$sizerange) {
			createDogPickerForm("<B>ERROR:</B> sizerange was not defined");
			exit;
		}
		if($sizerange < 2.0) {
			createDogPickerForm("<B>ERROR:</B> sizerange must be more than 2.0");
			exit;
		}
		$command .= " numslices=".$numslices;
		$command .= " sizerange=".$sizerange;
	} elseif($kfactor) {
		if ($kfactor < 1.00001 || $kfactor > 5.0) {
			createDogPickerForm("<B>ERROR:</B> K-factor must between 1.00001 and 5.0");
			exit;
		}
		$command .= " kfactor=".$kfactor;
	}

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	// submit job to cluster
	if ($_POST['process']=="Run DogPicker") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) {
			createDogPickerForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}

		submitAppionJob($command,$outdir,$runid,$expId,$testimage);
		if (!$testimage) exit;
	}

	writeTop("Particle Selection Results","Particle Selection Results");

	if ($testimage) {
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		echo "<B>DogPicker Command:</B><br />$command";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
		$cccimg=$outdir.$runid."/dogmaps/".$testjpg.".dogmap1.jpg";
		$ccclist[]=$cccimg;
		$images=writeTestResults($jpgimg,$ccclist,$_POST['bin']);
		createDogPickerForm($images,'Particle Selection Test Results','');
		exit;
	}

	echo"
		<P>
		<TABLE WIDTH='600'>
		<tr><td COLSPAN='2'>
		<B>Dog Picker Command:</B><br />
		$command<hr>
		</td></tr>";
	appionLoopSummaryTable();
	particleLoopSummaryTable();
	echo"</TABLE>\n";
	writeBottom(True, True);
}


?>
