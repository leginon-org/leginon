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

// Include the class that contains the definition of the form that needs to be displayed.
// The form class file should begin with lower case while the actual class definition
// should begin with uppercase. The _GET array should have the uppercase version. 
if ( empty($_GET['form']) ) {
	echo "<FONT COLOR='RED'><B>Missing form type in URL. Unable to load.</B><br></FONT>";
}
$form = lcfirst($_GET['form']);
require_once "inc/forms/$form.inc";

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
	$formClass = $_GET['form'];
	$form = new $formClass( $expId, $extra );
	
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
	
	$form = new $formClass($expId, false);
	$errorMsg = $form->validate( $_POST );
	
	// reload the form with any validation error messages
	if ( !empty($errorMsg) ) {
		createForm( $errorMsg );
		//Do not continue to PART 2 if has error;
		return;
	}
	
	/* *******************
	 PART 2: Copy any needed files to the cluster
	******************** */
	$copyCommand = $form->copyFilesToCluster($_POST['processinghost'],$_POST['remoteoutdir']);
	
	/* *******************************
	PART 3: Create program command
	********************************* */
	$command .= $form->buildCommand( $_POST );

	/* *************************
	PART 4: Show or Run Command
	***************************** */
	$headinfo = $form->showReference(); 
	$headinfo.= $copyCommand;
	$headinfo.= "<br />";
	$jobType  = $form->getJobType();

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, $jobType, 1, $testimage);

	/* *********************************
	PART 5: Show Errors or Test results
	************************************ */
	// if error display them
	if ($errors) {
		createForm($errors);
	} else if ( $testimage ) {
		// display test command
		$html =  $form->getTestCommand($command );
		
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
