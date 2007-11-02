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
	$javafunctions .= particleLoopJavaCommands();
	writeTop("DoG Picker Launcher","Automated Particle Selection with DoG Picker",$javafunctions);

	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

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
	<TR>
		<TD VALIGN='TOP'>";
	srand(time());
	if ((rand()%9) > 7) {
		echo"
	<CENTER><IMG SRC='img/dogpicker.jpg' WIDTH='300'></CENTER><BR/>\n";
	}
	createAppionLoopTable($sessiondata, $defrunid, "extract");
	$diam = ($_POST['diam']) ? $_POST['diam'] : "";
	echo"
		<TD CLASS='tablebg'>
		<B>Particle Diameter:</B><BR>
		<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>&nbsp;
		Particle diameter for filtering <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
		<BR><BR>";
	createParticleLoopTable(0.7, 1.5);
	$kfactor = ($_POST['kfactor']) ? $_POST['kfactor'] : "";
	$numslices = ($_POST['numslices']) ? $_POST['numslices'] : "";
	$sizerange = ($_POST['sizerange']) ? $_POST['sizerange'] : "";
	echo "
		<INPUT TYPE='text' NAME='kfactor' VALUE='$kfactor' SIZE='6'>&nbsp;
		<A HREF=\"javascript:particleinfopopup('kfactor')\">
		K-factor</A>&nbsp;<FONT SIZE=-2><I>(sloppiness)</I></FONT>
		<BR/><BR/>
		<B>Multi-scale dogpicker:</B><BR/>
		<INPUT TYPE='text' NAME='numslices' VALUE='$numslices' SIZE='3'>&nbsp;
		<A HREF=\"javascript:particleinfopopup('numslices')\">
		Number of Slices</A>&nbsp;<FONT SIZE=-2><I>(number of sizes)</I></FONT>
		<BR/>
		<INPUT TYPE='text' NAME='sizerange' VALUE='$sizerange' SIZE='3'>&nbsp;
		<A HREF=\"javascript:particleinfopopup('sizerange')\">
		Size Range</A>&nbsp;<FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
		<BR/>
		<HR>
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these settings on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>

		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		Host: <select name='host'>\n";

	$hosts=getHosts();
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run DogPicker'><BR>
		<FONT class='apcomment'>Submission will NOT run Dog Picker, only output a command that you can copy and paste into a unix shell</FONT>
		</TD>
	</TR>
	</TABLE>";
	writeBottom();
	?>

	</CENTER>
	</FORM>
	<?
}

function runDogPicker() {

	$command.="dogPicker.py ";
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

	if ($testimage && $_POST['process']=="Run DogPicker") {
		$host = $_POST['host'];
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) {
			createDogPickerForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}
		$prefix =  "source /ami/sw/ami.csh;";
		$prefix .= "source /ami/sw/share/python/usepython.csh cvs32;";
		$cmd = "$prefix webcaller.py '$command' dogPickerLog.txt";
		echo $cmd;
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	writeTop("Particle Selection Results","Particle Selection Results");

	if ($testimage) {
		$runid = $_POST[runid];
		$outdir = $_POST[outdir];
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		echo "<B>DogPicker Command:</B><BR>$command";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
		$cccimg=$outdir.$runid."/dogmaps/".$testjpg.".dogmap1.jpg";
		$ccclist[]=$cccimg;
		$images=writeTestResults($jpgimg,$ccclist);
		createDogPickerForm($images,'Particle Selection Test Results','');
		exit;
	}

	echo"
		<P>
		<TABLE WIDTH='600'>
		<TR><TD COLSPAN='2'>
		<B>Dog Picker Command:</B><BR>
		$command<HR>
		</TD></TR>";
	appionLoopSummaryTable();
	particleLoopSummaryTable();
	echo"</TABLE>\n";
	writeBottom();
}

function writeTestResults($jpg,$ccclist){
	echo"<CENTER>\n";
	echo"<A HREF='loadimg.php?filename=$jpg&scale=0.8'>\n";
	echo"<IMG SRC='loadimg.php?filename=$jpg&scale=0.35'></A>\n";
	if (count($ccclist)>1) echo "<BR>\n";
	foreach ($ccclist as $ccc){
		echo"<A HREF='loadimg.php?filename=$ccc&scale=0.8'>\n";
		echo"<IMG SRC='loadimg.php?filename=$ccc&scale=0.35'></A>\n";
	}
	echo"</CENTER>\n";
}

?>
