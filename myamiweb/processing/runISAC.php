<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
require_once "inc/publication.inc";


$formClass ="ISACForm";

require_once "inc/forms/$formClass.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runAppionLoop();
}
// CREATE FORM PAGE
else {
	createForm();
}

function createForm($extra=false) {
	// check if coming directly from a session
	$expId = $_GET['expId'];

	// The _GET array should include the actual class name of the form to be displayed
	global $formClass;
	$form = new $formClass( $expId);
	
	// Display the form
	echo $form->generateForm();
}

function runAppionLoop() {
	/* ********************************
	PART 1: Get variables and validate
	*********************************** */
	$expId = $_GET['expId'];
	$formClass = $_GET['form'];
	
	// We do need to know if the user selected to test an image
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename'])
			$testimage = $_POST['testfilename'];
	}	
	
	global $formClass;
	$form = new $formClass($expId);
	$errorMsg = $form->validate( $_POST );
	
	// reload the form with any validation error messages
	if ( !empty($errorMsg) ) createForm( $errorMsg );
	
	/* *******************************
	PART 2: Create program command
	********************************* */
	$command .= $form->buildCommand( $_POST );

	/* *************************
	PART 3: Show or Run Command
	***************************** */
	$headinfo = $form->showReference(); 
	$jobType  = $form->getJobType();

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, $jobType, 1, $testimage);

	/* *********************************
	PART 4: Show Errors or Test results
	************************************ */
	// if error display them
	if ($errors) {
		createForm($errors);
	} else if ( $testimage ) {
		// add the appion wrapper to the test command for display
		$wrappedcmd = addAppionWrapper($command);
		
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<B>Test Command:</B><br />$wrappedcmd";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		$html =  $results;
		
		$runname 	  = $_POST['runname'];		
		$outdir		  = $_POST['outdir'];
		$testfilename = $_POST['testfilename'];
		
		// make sure outdir ends with '/'
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		
		$html .= $form->getTestResults( $outdir, $runname, $testfilename );
		
		createForm( $html, 'Test Results', 'Test Results' );
	}		
	exit;
}

?>
