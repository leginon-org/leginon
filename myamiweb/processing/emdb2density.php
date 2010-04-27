<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadModel();
}

// Create the form page
else {
	createForm();
}

function createForm($extra=false, $title='EMDB to EM', $heading='EMDB to EM Density') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$particle = new particledata();

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  
	$javafunctions = writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","models",$outdir);
		$outdir=$outdir."/emdb";
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";

	}
  
	// Set any existing parameters in form
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '';
	$emdbid = ($_POST['emdbid']) ? $_POST['emdbid'] : '';
	$symm = ($_POST['symm']) ? $_POST['symm'] : '';
	$runtime = ($_POST['runtime']) ? $_POST['runtime'] : getTimestring();

	echo "<table class=tablebubble cellspacing='8'>";

	echo "<tr><td valign='top'>\n";

	echo docpop('emdbid', '<b>EMDB ID:</b>');
	echo "<input type='text' name='emdbid' value='$emdbid' size='5'><br />\n";
	echo "<input type='hidden' name='runtime' value='$runtime'>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top'>\n";

	echo docpop('outdir', 'Output directory')."<br/>\n";
	echo "<input type='text' name='outdir' value='$outdir' size='40'>\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo "<input type='text' name='lowpass' value='$lowpass' size='5'>\n";
	echo "&nbsp;Low pass filter\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	$syms = $particle->getSymmetries();
   echo "<select name='symm'>\n";
   echo "<option value=''>select one...</option>\n";
	foreach ($syms as $sym) {
		echo "<option value='$sym[DEF_id]'";
		if ($sym['DEF_id']==$_POST['sym']) echo " selected";
		echo ">$sym[symmetry]";
		if ($sym['symmetry']=='C1') echo " (no symmetry)";
		echo "</option>\n";
	}
	echo "</select>\n";
	echo "&nbsp;Symmetry group <i>e.g.</i> c1\n";

	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";

	echo "<input type='checkbox' name='viper2eman' $viper2eman>\n";
	echo docpop('viper2eman', "convert VIPER to EMAN orientation");

	echo "</td></tr>\n";
	echo "<tr><td align='center'>\n";

	echo "<hr>";
	echo getSubmitForm("Create Model");

	echo "</td></tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	processing_footer();
	exit;
}

function runUploadModel() {
	$particle = new particledata();
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$session=$_POST['sessionname'];
	$lowpass=$_POST['lowpass'];

	//make sure a emdb id was entered
	$emdbid=$_POST['emdbid'];
  	if (!$emdbid)
		createForm("<B>ERROR:</B> Enter a EMDB ID");

	//make sure a symmetry group was provided
	$symm=$_POST['symm'];
	if (!$symm)
		createForm("<B>ERROR:</B> Enter a symmetry group");

	if (!is_float($apix)) $apix = sprintf("%.2f", $apix);

	// emdb id will be the runname
	$runtime = $_POST['runtime'];
	$filename = "emdb".$emdbid."-".$runtime;
	$runname = $filename;
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	$command = "modelFromEMDB.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--runname=$runname ";
	$command.="--emdbid=$emdbid ";
	$command.="--session=$session ";
	if ($lowpass)
		$command.="--lowpass=$lowpass ";
	$command.="--symm=$symm ";
	if ($_POST['viper2eman']=='on')
		$command.="--viper2eman " ;

	// submit job to cluster
	if ($_POST['process']=="Create Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command, $outdir, $runname, $expId,'modelfromemdb', false);

		// if errors:
		if ($sub) createForm("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("EMDB to EM Density", "EMDB to EM Density");
	// rest of the page
	echo"<table class='tableborder' width='600' border='1'>\n";
	echo "<tr><td>\n";
	if ($status) echo "$status<hr />\n";
	echo "<b>DownloadModel Command:</b><br />\n";
	echo "$command\n";
	echo "<p>\n";
	echo "</td></tr>\n";
	echo "</table>\n";
	processing_footer();
}
?>
