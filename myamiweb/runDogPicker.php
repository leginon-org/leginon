<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ssh.inc');
require ('inc/appionloop.inc');
  
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

	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId));
   writeTop("DoG Picker Launcher","Automated Particle Selection with DoG Picker",$javafunctions);
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","extract/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}


	// if session is changed, change the output directory
	$sessionpathval=(($_POST['sessionId']==$_POST['lastSessionId'] || $expId) && $_POST['lastSessionId']) ? $_POST['outdir'] : $sessionpath;
	// Set any existing parameters in form
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'dogrun'.($prtlruns+1);
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	echo"
        <script src='js/viewer.js'></script>
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
                 function enabledcont(val){
                         if (val==1) {
                                 document.viewerform.nocontinue.disabled=true;
                         }	
                         if (val==2) {
                                 document.viewerform.apcontinue.disabled=true;
                         }
                         else {
                                 document.viewerform.apcontinue.disabled=false;
                                 document.viewerform.nocontinue.disabled=false;
                         }	
                 }
                 function infopopup(infoname){
                         var newwindow=window.open('','name','height=150,width=300');
                         newwindow.document.write('<HTML><BODY>');
                         if (infoname=='runid'){
                                 newwindow.document.write('Specifies the name associated with the Template Correlator results unique to the specified session and parameters.        An attempt to use the same run name for a session using different Template Correlator parameters will result in an error.');
                         }
                         newwindow.document.write('</BODY></HTML>');
                         newwindow.document.close();
                 }
        </SCRIPT>\n";
	appionLoopJavaCommands();
   particleLoopJavaCommands();

	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>
		<A HREF=\"javascript:infopopup('runid')\"><B>Run Name:</B></A>
		<INPUT TYPE='text' NAME='runid' VALUE='$runidval'><BR>
		<BR>

		<B>Output Directory:</B><BR>
		<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='45'><BR>
		<BR>\n";
	if ($presets) {
		echo"<B>Preset</B>\n<SELECT NAME='preset'>\n";
		foreach ($presets as $preset) {
			echo "<OPTION VALUE='$preset' ";
			// make en selected by default
			if ($preset==$presetval) echo "SELECTED";
			echo ">$preset</OPTION>\n";
		}
		echo"</SELECT>";
	} else {
		echo"<FONT COLOR='RED'><B>No Presets for this Session</B></FONT>\n";
	}
	createAppionLoopTable();
	echo"
		<TD CLASS='tablebg'>
		<B>Particle Diameter:</B><BR>
		<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>&nbsp;
		Particle diameter for filtering <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
		<BR><BR>";
	createParticleLoopTable(0.7, 1.5);
	echo "
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these settings on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
		<HR>
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		Host: <select name='host'>\n";

	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>
	<BR>
	User: <INPUT TYPE='text' name='user' value=".$_POST['user'].">
	Password: <INPUT TYPE='password' name='password' value=".$_POST['password'].">\n";
	echo"
		</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run Correlator'><BR>
		<FONT COLOR='RED'>Submission will NOT run Dog Picker, only output a command that you can copy and paste into a unix shell</FONT>
		</TD>
	</TR>
	</TABLE>";
	echo "<INPUT TYPE='hidden' NAME='sessionname' VALUE='$sessionname'>\n";
	?>
		</TD>
	</TR></TABLE>

	</CENTER>
	</FORM>
	<?
	writeBottom();
}

function runDogPicker() {
	$host = $_POST['host'];
	$user = $_POST['user'];
	$password = $_POST['password'];
	if ($_POST['process']=="Run Correlator" && !($user && $password)) {
		createDogPickerForm("<B>ERROR:</B> Enter a user name and password");
	}
	//make sure a session was selected
	if (!$_POST[outdir]) {
		createDogPickerForm("<B>ERROR:</B> Select an experiment session");
		exit;
	}
	$outdir=$_POST[outdir];
	// make sure outdir ends with '/'
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$runid=$_POST[runid];
  
	$diam = $_POST[diam];
	if (!$diam) {
		createDogPickerForm("<B>ERROR:</B> Specify a particle diameter");
		exit;
	}

	$thresh = $_POST[thresh];
	if (!$thresh) {
		createDogPickerForm("<B>ERROR:</B> No thresholding value was entered");
		exit;
	}

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		else {
			createDogPickerForm("<B>ERROR:</B> Specify an mrc file to test these parameters");
			exit;
		}
	}
	elseif ($_POST['sessionname']) {
		if ($_POST['preset']) $dbimages=$_POST[sessionname].",".$_POST[preset];
		else {
			createDogPickerForm("<B>ERROR:</B> Select an image preset");
			exit;
		}
	}

	if ($testimage && $_POST['process']=="Run Correlator") {
		$command.="source /ami/sw/ami.csh;";
		$command.="source /ami/sw/share/python/usepython.csh cvs32;";
	}
	$command.="dogPicker.py ";
	if ($testimage) $command.="$testimage ";
	else $command.="dbimages=$dbimages ";
	$command.="runid=$runid ";
	$command.="outdir=$outdir ";
	$command.="diam=$diam ";
	$command .= parseAppionLoopParams($_POST);
	$command .= parseParticleLoopParams($_POST);

	$cmd = "$command > dogPickerLog.txt";
	echo $command;
	if ($testimage && $_POST['process']=="Run DoG Picker") {
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	writeTop("Particle Selection Results","Particle Selection Results");

	if ($testimage) {
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
   	$cccimg=$outdir.$runid."/dogmaps/".$testjpg.".dogmap.jpg";
		$ccclist[]=$cccimg;
		$images=writeTestResults($jpgimg,$ccclist);
		createDogPickerForm($images,'Particle Selection Results','');
		exit;
	}

	echo"
  <P>
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>Dog Picker Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>";
	echo"<TR><TD>runid</TD><TD>$runid</TD></TR>
  <TR><TD>testimage</TD><TD>$testimage</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  <TR><TD>diameter</TD><TD>$diam</TD></TR>";
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
