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
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadStack();
}

// Create the form page
else {
	createUploadStackForm();
}

function createUploadStackForm($extra=false, $title='Upload Stack Launcher', $heading='Upload a stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	//query the database for parameters
	$particle = new particledata();

	// get path for submission
	$sessiondata=getSessionList($projectId, $expId);
	$sessioninfo=$sessiondata['info'];
	$defoutdir = $sessioninfo['Image path'];
	$defoutdir = ereg_replace("leginon", "appion",$defoutdir);
	$defoutdir = ereg_replace("rawdata", "stacks",$defoutdir);
	$sessionname = $sessioninfo['Name'];

	// Set default runname
	$stackruninfos = $particle->getStackIds($expId, True);
	$stackruns = ($stackruninfos) ? count($stackruninfos) : 0;
	//echo "Stack Runs: $stackruns";
	while (glob($defoutdir.'/stack'.($stackruns+1)."*"))
		$stackruns += 1;
	$defrunname = 'stack'.($stackruns+1);

	// Set any existing parameters in form
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $defoutdir;
	$description = $_POST['description'];

	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$stackfile = ($_POST['stackfile']) ? $_POST['stackfile'] : '';

	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	$ctfcorrectcheck = ($_POST['ctfcorrect']=='on') ? 'checked' : '';
	$normalizecheck = ($_POST['normalize']=='on' || !$_POST['process']) ? 'checked' : '';

	$javascript = writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";


	echo docpop('session','<b>Session name:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='dissessionname' value='$sessionname' size='10' disabled/>\n";
	echo "<input type='hidden' name='sessionname' value='$sessionname'/>\n";

	echo "<br/><br/>\n";

	echo docpop('outdir','<b>Output directory:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='disoutdir' value='$outdir' size='40' disabled/>\n";
	echo "<input type='hidden' name='outdir' value='$outdir'/>\n";

	echo "<br/><br/>\n";
	
	echo docpop('runname','<b>Runname:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='runname' value='$runname' size='20'/>\n";

	echo "<br/><br/>\n";

	echo "<b>Stack filename with path:</b><br/>\n";
	echo "<input type='text' name='stackfile' value='$stackfile' size='55'/>\n";

	echo "<br/><br/>\n";

	echo docpop('description','<b>Stack description:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='description' value='$description' size='55'/>\n";

	echo "<br/><br/>\n";

	echo "</td></tr><tr><td valign='top' class='tablebg'>";

	echo "<br/>\n";

	echo docpop('pdiam','<b>Particle diameter:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='diam' value='$diam' size='5'/>\n";
	echo "&nbsp;<font size='-2'>(in &Aring;ngstroms)</font>\n";

	echo "<br/><br/>\n";

	echo docpop('apix','<b>Pixel size:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='apix' value='$apix' size='5'/>\n";
	echo "&nbsp;<font size='-2'>(in &Aring;ngstroms)</font>\n";

	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='ctfcorrect' $ctfcorrectcheck>\n";
	echo '<b>Particle are CTF corrected</b>';

	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='normalize' $normalizecheck>\n";
	echo docpop('stacknorm','<b>Normalize particles</b>');

	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit to Database</b>');

	echo "<br/><br/>\n";

	echo "</td></tr></table></td></tr><tr><td align='center'><hr/>";

	echo getSubmitForm("Upload Stack");
	echo "</td></tr></table></form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runUploadStack() {
	/* *******************
	PART 1: Get variables
	******************** */
	$diam=$_POST['diam'];
	$session=$_POST['sessionname'];
	$description=$_POST['description'];
	$apix=$_POST['apix'];
	$stackfile=$_POST['stackfile'];
	$commit=$_POST['commit'];
	$normalize=$_POST['normalize'];
	$ctfcorrect=$_POST['ctfcorrect'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a description is provided
	if (!$description)
		createUploadStackForm("<B>ERROR:</B> Enter a brief description of the stack");

	//make sure a session was selected
	if (!$session)
		createUploadStackForm("<B>ERROR:</B> Select an experiment session");

	//make sure a diam was provided
	if (!$diam)
		createUploadStackForm("<B>ERROR:</B> Enter the particle diameter");

	//make sure a apix was provided
	if (!$apix)
		createUploadStackForm("<B>ERROR:</B> Enter the pixel size");

	//check if the stack is an existing file (wild type is not searched)
	if (!$stackfile)
		createUploadStackForm("<B>ERROR:</B> Enter a the root name of the stack");
	if (!file_exists($stackfile))
		createUploadStackForm("<B>ERROR:</B> File ".$stackfile." does not exist");

	/* *******************
	PART 3: Create program command
	******************** */

	//putting together command
	$command = "uploadstack.py ";
	$command.="--session=$session ";
	$command.="--file=$stackfile ";
	$command.="--apix=$apix ";
	$command.="--diam=$diam ";
	$command.="--description=\"$description\" ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	if ($normalize) $command.="--normalize ";
	else $command.="--no-normalize ";
	if ($ctfcorrect) $command.="--ctf-corrected ";
	else $command.="--not-ctf-corrected ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadstack', 1);

	// if error display them
	if ($errors)
		createUploadStackForm($errors);
	exit;
}

?>
