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

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  
	$javafunctions = writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
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
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$res = ($_POST['res']) ? $_POST['res'] : '';
	$emdbid = ($_POST['emdbid']) ? $_POST['emdbid'] : '';
	$box = ($_POST['box']) ? $_POST['box'] : '';
	$runtime = ($_POST['runtime']) ? $_POST['runtime'] : getTimestring();

	echo "<table BORDER=3 CLASS=tableborder><tr><td valign='top'>\n";
	echo docpop('emdbid', '<b>EMDB ID:</b>');
	echo "<input type='text' name='emdbid' value='$emdbid' size='5'><br />\n";
	echo "<input type='hidden' name='runtime' value='$runtime'>\n";
	echo "</td></tr>\n";
	echo "<tr><td valign='top' class='tablebg'>\n";
	echo "<p>\n";
	echo "<input type='text' name='res' value='$res' size='5'> Model Resolution<br />\n";
	echo "<input type='text' name='apix' size='5' value='$apix'>\n";
	echo "Pixel Size <font size='-2'>(in &Aring;ngstroms per pixel)</font><br />\n";
	echo "<input type='text' name='box' size='5' value='$box'>\n";
	echo "Box Size <font size='-2'>(in pixels)</font>\n";
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

	$command = "modelFromEMDB.py ";

	$session=$_POST['sessionname'];

	//make sure a emdb id was entered
	$emdbid=$_POST['emdbid'];
  	if (!$emdbid) createForm("<B>ERROR:</B> Enter a EMDB ID");

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createForm("<B>ERROR:</B> Enter the pixel size");

	//make sure a resolution was provided
	$res=$_POST['res'];
	if (!$res) createForm("<B>ERROR:</B> Enter the model resolution");

	//make sure a boxsize was provided
	$box=$_POST['box'];
	if (!$box) createForm("<B>ERROR:</B> Enter a box size");


	if (!is_float($apix)) $apix = sprintf("%.1f", $apix);
	if (!is_float($res)) $res = sprintf("%.1f", $res);
	$filename = $emdbid.'-'.$apix.'-'.$res.'-'.$box;
	// emdb id will be the runname
	$runname = $_POST['runtime'];
	$runname = $emdbid."_".$runname;
	$rundir = $outdir."/".$runname;

	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--runname=".$runname." ";
	$command.="-e $emdbid ";
	$command.="-s $session ";
	$command.="-a $apix ";
	$command.="-r $res ";
	$command.="-b $box ";
	
	// submit job to cluster
	if ($_POST['process']=="Create Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'downloadmodel',False);

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
	if (!file_exists($rundir.'/'.$filename.'.mrc')) {
		echo "EM Density file to be created:<br />\n";
		echo "$rundir/$filename.mrc</b><br />\n";
	}
	else {
		echo "EM Density file created:<br />\n";
		$densityid = $particle -> getDensityIdFromFile($rundir,$filename.".mrc");
		echo "<b><a href='densityreport.php?expId=$expId&densityId=$densityid'>$rundir/$filename.mrc</a></b><br />\n";
		echo "<hr />\n";
		$formAction="uploadmodel.php?expId=$expId";
		$formAction.="&densityId=$densityid";
		echo "<form name='uploadmodel' method='POST' ACTION='$formAction'>\n";
		echo "<center><input type='submit' name='goUploadModel' value='Upload This Model'></center><br />\n";
		echo "<font class='apcomment'>Remember that EMDB may not be oriented relative to any axis</font>\n";
		echo "</form>\n";
	}
	echo "</td></tr>\n";
	echo "</table>\n";
	processing_footer();
}
?>
