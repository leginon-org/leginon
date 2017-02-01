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
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";
require_once "inc/forms/ddstackForm.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runStackIntoPicks();
} else {
	createStackIntoPicksForm();
}

function createStackIntoPicksForm($extra=false, $title='Run Stack Into Picks', $heading='Run Stack Into Picks') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	//echo "Project ID: ".$projectId." <br/>\n";
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();
	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	// --- Get Stack Data --- //
	$particle = new particledata();
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/extract/';
	}
	//$stackids = $particle->getStackIdsForProject($projectId, False);
	$stackids = $particle->getStackIds($expId, False);
	$lastprtlruns = count($particle->getParticleRunIds($sessionId, True));
	while (file_exists($sessionpath.'stackrun'.($lastprtlruns+1)))
		$lastprtlruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'stackrun'.($lastprtlruns+1);
	$description = $_POST['description'];
	$stackparam = $particle->getStackParams($stackids[0]['stackid']);
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$ddstackform = new DDStackForm('','Apply to ddframe stack result images','ddstack.transfer2ddstack' );

	if ($stackids) {
		echo "<form name='stackform' method='post' action='$formAction'>\n";
		echo "<table border='1'>";
		echo "<tr><td colspan='4'><h2>New stack info:</h2>\n";
		echo docpop('runname','<b>Stack picking name:</b>');
		echo "<br/>\n";
		echo "<input type='text' name='runname' value='$runname'>\n";
		echo "<br/>\n";
		echo "<br/>\n";
		echo docpop('outdir','<b>Output Directory:</b>');
		echo "<br />\n";
		echo "<input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br />\n";
		echo "<br />\n";
		echo docpop('ddstack.transfer2ddstack','<b>Apply to dd frame stack result image:</b>');
		echo "<br />\n";
		echo $ddstackform->generateForm();
		echo "<br />\n";
		echo getSubmitForm("Run Stack Into Picks");
		echo "</td></tr>\n";
		echo "<tr><td colspan='4'><h2>Select stack to convert into picks:</h2>\n";
		foreach ($stackids as $stackdata) {
			$stackid = $stackdata['stackid'];
			echo "<tr><td>\n<input type='radio' name='stackid' value='$stackid'";
			if ($_POST['stack'.$stackid]) echo " checked";
			echo ">convert<br/>stack id $stackid\n</td><td>\n";
			echo ministacksummarytable($stackid);
			echo "</td></tr>\n";
		}
		echo "</table>";
		echo "</form>";
	} else {
		echo "<B>Project does not contain any stacks.</B>\n";
	}

	echo appionRef();

	processing_footer();
	exit;
}

function runStackIntoPicks() {
	$ddstackform = new DDStackForm('','Apply to ddframe stack result images','ddstack.transfer2ddstack' );
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackid=$_POST['stackid'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$stackid) 
		createStackIntoPicksForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="stackIntoPicks.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	$command.="--stackid=$stackid ";
	$command.="--commit ";
	$command .= $ddstackform->buildCommand( $_POST );	

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', $nproc);

	// if error display them
	if ($errors)
		createStackIntoPicksForm("<b>ERROR:</b> $errors");
	
}



?>
