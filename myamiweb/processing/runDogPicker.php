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
require_once "inc/path.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runDogPicker();
}
// CREATE FORM PAGE
else {
	createDogPickerForm();
}


function createDogPickerForm($extra=false, $title='DoG Picker Launcher', $heading='Automated Particle Selection with DoG Picker', $results=false) 
{
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

	$javafunctions="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
	   function enabledtest(){
         if (document.viewerform.testimage.checked){
		document.viewerform.testfilename.disabled=false;
		document.viewerform.testfilename.value='';
		document.viewerform.commit.disabled=true;
		document.viewerform.commit.checked=false;
         }	
         else {
		document.viewerform.testfilename.disabled=true;
		document.viewerform.testfilename.value='mrc file name';
		document.viewerform.commit.disabled=false;
		document.viewerform.commit.checked=true;
         }
	   }
	</SCRIPT>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');	

	processing_header($title, $heading, $headerstuff=$javafunctions, $pleaseWait=true, $showmenu=true, $printDiv=false, 
						$guideURL="http://emg.nysbc.org/redmine/projects/appion/wiki/Dog_Picking");
	
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	if ($results) echo "$results<hr>\n";
	
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<input type='HIDDEN' NAME='lastSessionId' value='$sessionId'>\n";

	$sessiondata=getSessionList($projectId,$sessionId,$expId);

	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId, True));
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name'); 
	// Set any existing parameters in form
	while (file_exists('dogrun'.($lastrunnumber+1))) {
		$lastrunnumber += 1;
	}
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'dogrun'.($lastrunnumber+1);
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
	$kfactor = ($_POST['kfactor']) ? $_POST['kfactor'] : "";
	$numslices = ($_POST['numslices']) ? $_POST['numslices'] : "";
	$sizerange = ($_POST['sizerange']) ? $_POST['sizerange'] : "";

	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<tr>
		<td VALIGN='TOP'>";
	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><img src='img/dogpicker.jpg' WIDTH='300'></center><br />\n";
	}
	createAppionLoopTable($sessiondata, $defrunname, "extract");
	$diam = ($_POST['diam']) ? $_POST['diam'] : "";
	echo "<td class='tablebg'>\n";
	echo "<b>Particle Diameter:</b><br />\n";
	echo "<input type='text' NAME='diam' value='$diam' size='4'>\n";
	echo docpop('pdiam','Particle diameter for filtering');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br /><br />\n";
	createParticleLoopTable(0.7, 1.5);

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
		<hr />";
	echo getSubmitForm("Run DogPicker");
	echo "
		</td>
	</tr>
	</form>
	</table>\n";

	echo referenceBox("DoG Picker and TiltPicker: software tools to facilitate particle selection in single particle electron microscopy.", 2009, "Voss NR, Yoshioka CK, Radermacher M, Potter CS, Carragher B.", "J Struct Biol.", 166, 2, 19374019, 2768396, false, false);

	processing_footer();
	exit;
}

function runDogPicker() {
	/* *******************
	PART 1: Get variables
	******************** */
	
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];
	$numslices = (int) $_POST[numslices];
	$sizerange = $_POST[sizerange];
	$kfactor = $_POST[kfactor];
	
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if ($numslices) {
		if($numslices < 2) createDogPickerForm("<B>ERROR:</B> numslices must be more than 1");
		if(!$sizerange) createDogPickerForm("<B>ERROR:</B> sizerange was not defined");
		if($sizerange < 2.0) createDogPickerForm("<B>ERROR:</B> sizerange must be more than 2.0");
	} elseif($kfactor) {
		if ($kfactor < 1.00001 || $kfactor > 5.0) createDogPickerForm("<B>ERROR:</B> K-factor must between 1.00001 and 5.0");
	}	

	/* *******************
	PART 3: Create program command
	******************** */
	
	$command ="dogPicker.py ";

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

	if ($numslices) {
		$command .= " --numslices=".$numslices;
		$command .= " --sizerange=".$sizerange;
	} elseif($kfactor) {
		$command .= " --kfactor=".$kfactor;
	}
		
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = preg_replace("% %","\ ",$testimage);
	}

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= referenceBox("DoG Picker and TiltPicker: software tools to facilitate particle selection in single particle electron microscopy.", 
	2009, "Voss NR, Yoshioka CK, Radermacher M, Potter CS, Carragher B.", "J Struct Biol.", 166, 2, 19374019, 2768396, false, false);	
	
	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'dogpicker', $nproc, $testimage);

	// if errors display them
	if ($errors) {
		createDogPickerForm($errors);
		
	} else if ($testimage) {
		// add the appion wrapper to the command for display
		$wrappedcmd = addAppionWrapper($command);
			
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<B>DogPicker Command:</B><br />$wrappedcmd";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		$testjpg = preg_replace("%.mrc%","",$_POST['testfilename']);
		$testResultFile = $testjpg.".prtl.jpg";
		$jpgimg = Path::join($outdir, $runname, "jpgs", $testResultFile);
		
		$pathToMaps = Path::join($outdir, $runname, "maps");
		
		if ($_POST['process'] != "Just Show Command") {
			$filePattern = $testjpg."*.jpg";
			$pathPattern = Path::join($pathToMaps, $filePattern);
			# write only the written files
			$dogmaplist = glob($pathPattern);
			$results .= writeTestResults($jpgimg, $dogmaplist, $_POST['bin']);
		} else {
			$mapFile = $testjpg.".dogmap1.jpg";
			$ccclist = array();
			$cccimg = Path::join($pathToMaps, $mapFile);
			# does not check if the result jpg is there because missing cccimg is not an error
			$ccclist[]=$cccimg;
			$results.= writeTestResults($jpgimg,$ccclist,$bin=$_POST['bin']);			
		}		
		
		createDogPickerForm(false, 'Particle Selection Test Results', 'Particle Selection Test Results', $results);
	}
	
	exit;
}


?>
