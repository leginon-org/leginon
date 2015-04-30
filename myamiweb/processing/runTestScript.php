<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

//--------------------------------------------------------------------------------------
// This file should display a form for launching a "test_$sessionname.py" script
//
// Information on writing appion tests is available at:
// http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Testing
//--------------------------------------------------------------------------------------

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

// Cs should come straight out of the DB somehow, instead it is in config
$defaultcs=DEFAULTCS;

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTestSuite();
}
// CREATE FORM PAGE
else {
	createForm();
}


// CREATE FORM PAGE
function createForm($extra=false) {
	global $defaultcs;
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

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	processing_header("Test Suite Launcher", "Automated Software Testing");

	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"
	<FORM name='viewerform' method='POST' action='$phpself'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/testruns/';
	}
	
	// get the next run number for this type of run and set runname
	$jobtype = "test_".$sessioninfo["Name"];
	$particledata = new particledata();
	$lastrunnumber = $particledata->getMaxRunNumber( $jobtype, $sessionId );
	
	// sanity check - make certain we are not going to overwrite data
	while (file_exists($sessionpath.'testrun'.($lastrunnumber+1)))
		$lastrunnumber += 1;
		
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'testrun'.($lastrunnumber+1);

	// Create the GUI to set Appion parameters
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";

	// This creates the form for all the common parameters used for most programs.
	// The last parameter of this function sets the run directory.
	createAppionLoopTable($sessiondata, $defrunname, "testruns");


	echo"
	  </TD>
	</tr>
	<TR>
	  <TD COLSPAN='2' ALIGN='CENTER'>\n<hr />";
	echo getSubmitForm("Run Test Suite");
	echo "
	  </td>
	</tr>
	</table>
	</form>\n";
	processing_footer();
}


// --- parse data and process on submit
function runTestSuite() {
	
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];
	$binval=$_POST['binval'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	
	/* *******************
	* PART 3: Create program command
	*
	* Example usage:
	* testSuite.py --runname=testrun1 --projectid=5 --rundir=/ami/data08/appion/10may13l35/testruns/testrun1 
	* 			   --expid=7622 --jobtype=testsuite --show-cmd --session=10may13l35
	*
	******************** */
	$sessionname = $_POST['sessionname'];
	$command = "test_$sessionname.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$command.="--show-cmd ";
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	//$headinfo .= referenceBox("ACE: automated CTF estimation.", 2005, "Mallick SP, Carragher B, Potter CS, Kriegman DJ.", "Ultramicroscopy.", 104, 1, 15935913, false, false, false);
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'testsuite', $nproc);

	// if error display them
	if ($errors)
		createForm("<b>ERROR:</b> $errors");
}

?>
