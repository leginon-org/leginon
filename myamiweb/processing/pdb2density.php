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

function createForm($extra=false, $title='PDB to EM', $heading='PDB to EM Density') {
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
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("leginon","appion",$outdir);
		$outdir=ereg_replace("rawdata","models",$outdir);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
  
	// Set any existing parameters in form
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$res = ($_POST['res']) ? $_POST['res'] : '';
	$pdbid = ($_POST['pdbid']) ? $_POST['pdbid'] : '';
	$box = ($_POST['box']) ? $_POST['box'] : '';
	$bunitcheck = ($_POST['bunit'] == 'on') ? 'checked' : '';

	echo "<table BORDER=3 CLASS=tableborder><tr><td valign='top'>\n";
	echo docpop('pdbid', '<b>PDB ID:</b>');
	echo "<input type='text' name='pdbid' value='$pdbid' size='5'><br />\n";
	echo "<input type='checkbox' name='bunit' $bunitcheck>\n";
	echo "Use the ";
	echo docpop('biolunit', "biological unit");
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
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "modelFromPDB.py ";

	$session=$_POST['sessionname'];

	//make sure a pdb id was entered
	$pdbid=$_POST['pdbid'];
  	if (!$pdbid) createForm("<B>ERROR:</B> Enter a PDB ID");

	//make sure a apix was provided
	$apix=$_POST['apix'];
	if (!$apix) createForm("<B>ERROR:</B> Enter the pixel size");

	//make sure a resolution was provided
	$res=$_POST['res'];
	if (!$res) createForm("<B>ERROR:</B> Enter the model resolution");

	//make sure a boxsize was provided
	$box=$_POST['box'];
	if (!$box) createForm("<B>ERROR:</B> Enter a box size");

	// check if downloading the biological unit

	if (!is_float($res)) $res = $res.".0";
	$filename = $pdbid.'-'.$apix.'-'.$res.'-'.$box;
	// filename will be the runid if running on cluster
	$runid = $filename.'.upload';

	$command.="-p $pdbid ";
	$command.="-s $session ";
	$command.="-a $apix ";
	$command.="-r $res ";
	$command.="-b $box ";
	if ($_POST['bunit']=='on') $command.="-u" ;
	
	// submit job to cluster
	if ($_POST['process']=="Create Model") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'uploadmodel',True);
		// if errors:
		if ($sub) createForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runid.'/'.$runid.'.appionsub.log';
		$status = "Model was created from PDB";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
	}

	processing_header("PDB to EM Density", "PDB to EM Density");
	// rest of the page
	echo"<table class='tableborder' width='600' border='1'>\n";
	echo "<tr><td>\n";
	if ($status) echo "$status<hr />\n";
	echo "<b>UploadModel Command:</b><br />\n";
	echo "$command\n";
	echo "<p>\n";
	if (!file_exists($outdir.'/'.$filename.'.mrc')) {
		echo "EM Density file to be created:<br />\n";
		echo "<b><a href='densitysummary.php?expId=$expId'>$outdir/$filename.mrc</a></b><br />\n";
	}
	else {
		echo "EM Density file created:<br />\n";
		echo "<b><a href='densitysummary.php?expId=$expId'>$outdir/$filename.mrc</a></b><br />\n";
		echo "<hr />\n";
		$formAction="uploadmodel.php?expId=$expId";
		$formAction.="&pdbmod=$outdir/$filename.mrc";
		echo "<form name='uploadmodel' method='POST' ACTION='$formAction'>\n";
		echo "<center><input type='submit' name='goUploadModel' value='Upload This Model'></center><br />\n";
		echo "<input type='hidden' name='description' value='density created from PDB id: $pdbid'>\n";
		echo "<input type='hidden' name='res' value='$res'>\n";
		echo "<input type='hidden' name='apix' value='$apix'>\n";
		echo "<font class='apcomment'>Remember that PDB may not be oriented relative to any axis</font>\n";
		echo "</form>\n";
	}
	echo "</td></tr>\n";
	echo "</table>\n";
	processing_footer();
}
?>
