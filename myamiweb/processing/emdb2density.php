<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

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
		$outdir=getBaseAppionPath($sessioninfo).'/models';
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
		if ($sym['DEF_id']==$symm) echo " selected";
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

	echo initModelRef();

	processing_footer();
	exit;
}

function runUploadModel() {
	/* *******************
	PART 1: Get variables
	******************** */
	$session=$_POST['sessionname'];
	$lowpass=$_POST['lowpass'];
	$emdbid=$_POST['emdbid'];
	$symm=$_POST['symm'];
	// emdb id will be the runname
	$runtime = $_POST['runtime'];
	$filename = "emdb".$emdbid."-".$runtime;
	$_POST['runname'] = $filename;

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a emdb id was entered
  	if (!$emdbid)
		createForm("<B>ERROR:</B> Enter a EMDB ID");
  	if (!is_numeric($emdbid) && strlen($emdbid) == 4)
		createForm("<B>ERROR:</B> Enter a valid EMDB id, not a PDB id");
  	if (!is_numeric($emdbid))
		createForm("<B>ERROR:</B> Enter a valid EMDB ID, which is an integer");

	//make sure a symmetry group was provided
	if (!$symm)
		createForm("<B>ERROR:</B> Enter a symmetry group");
	if (!is_float($apix))
		$apix = sprintf("%.2f", $apix);

	/* *******************
	PART 3: Create program command
	******************** */
	$command = "modelFromEMDB.py ";
	$command.="--emdbid=$emdbid ";
	$command.="--session=$session ";
	if ($lowpass)
		$command.="--lowpass=$lowpass ";
	$command.="--symm=$symm ";
	if ($_POST['viper2eman']=='on')
		$command.="--viper2eman " ;

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'modelfromemdb', 1);
	// if error display them
	if ($errors)
		createForm($errors);
	exit;
}
?>
