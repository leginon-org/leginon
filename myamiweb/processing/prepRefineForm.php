<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Prepare a Frealign Job for submission to a cluster
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

require_once "inc/forms/stackPrepForm.inc";
require_once "inc/forms/runParametersForm.inc";

if ($_POST['process']) {
	createCommand(); // generate command
} else {
	jobForm(); // set parameters
}


/* ******************************************
 *********************************************
 MAIN FORM TO SET PARAMETERS
 *********************************************
 ****************************************** */

function jobForm($extra=false) {
	$expId 			= $_GET['expId'];
	$projectId 		= getProjectId();
	$reconMethod 	= $_POST['method'];
	
	// find any selected models
	// for single model, we expct the format $key="model, $value="model_#"
	// for multi model, we expect both the key and the value to be "model_#"
	foreach( $_POST as $key=>$value ) {
		if (strpos($value,"model_" ) !== False) {
			preg_match('/(\D+)_(\d+)/', $value, $matches);
			$id = $matches[2];
			
			$modelArray[] = array( 'name'=>$value, 'id'=>$id );
		}
	}
	
	if (!$modelArray)
		$error = "ERROR: no initial model selected";
	if (!$_POST['stackval'])
		$error = "ERROR: no stack selected";

	// get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = getBaseAppionPath($sessiondata).'/recon/';

	// ensure the cs value is set, or don't process
	if ($leginondata->getCsValueFromSession($expId) === false) {
		$error = "ERROR: Cs value of the images in this session is not unique or known, can't process.";
	}
	
	// set the runname
	// the default run name is the jobtype followed by an ever incrementing number
	$jobType = "preprefine".$reconMethod;
	$particle = new particledata();
	$reconruns = $particle->getMaxRunNumber( $jobType, $expId );
	
	// sanity check - make certain we are not going to overwrite data
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	
	// TODO: should '*recon' be repaced with $jobType??
	while (file_exists($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = $reconMethod."_recon".($reconruns+1);
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	
	// get stack data
	$stackinfo 	= explode('|--|',$_POST['stackval']);
	$stackid	= $stackinfo[0];
	$apix		= $stackinfo[1];
	$box		= $stackinfo[2];

	// preset information from stackid
	// TODO: make sure this is not needed and remove
//	$presetinfo = $particle->getPresetFromStackId($stackid);
//	$kv = $presetinfo['hightension']/1e3;

	
	// add javascript functions
	$javafunc .= writeJavaPopupFunctions('appion');
	
	// add the appion processing header
	processing_header("Appion: Recon Refinement","Prepare Recon Refinement",$javafunc);
	
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	} else if ($error) {
		echo "<font color='#cc3333' size='+2'>$error</font>\n<hr/>\n";
	}
	
	// create main form
	echo "<form name='prepRefine' method='post' action='$formaction'><br/>\n";
	
	// post hidden values
	foreach ( $modelArray as $model ) {
		echo "<input type='hidden' name='".$model['name']."' value='".$model['id']."'>\n";
	}
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";
	echo "<input type='hidden' name='method' value='".$_POST['method']."'>\n";
	echo "<input type='hidden' NAME='kv' value='$kv'>";
	echo "<input type='hidden' NAME='apix' value='$apix'>";
	if ($_POST['reconstackval'] && $stackid != $reconstackid) {
		echo "<input type='hidden' name='reconstackval' value='".$_POST['reconstackval']."'>\n";
	}
	
	// add Processing Run Parameter fields
	$runParametersForm = new RunParametersForm( $runname, $outdir );
	echo $runParametersForm->generateForm();
	
	// add stack preparation parameters
	$stackPrepForm = new StackPrepForm();
	echo $stackPrepForm->generateForm();
		
	// add submit button
	echo "<br/><br/>\n";
	echo getSubmitForm("Prepare Refinement");

	echo "</form>\n";
	echo "<br/><hr/>\n";

	// add stack and model summary
	//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
	echo "<br/>\n";
	echo "<table class='tablebubble'><tr><td>\n";
	echo stacksummarytable($stackid, true);
	echo "</td></tr>";
	foreach ( $modelArray as $model ) {
		echo "<tr><td>\n";
		echo modelsummarytable( $model['id'], true );
		echo "</td></tr>";
	}
	echo "</table>\n";

	// add reference for selected refinement method
	echo showReference($_POST['method']);

	// add appion processing footer
	processing_footer();
	exit;
}

/* ******************************************
 *********************************************
 GENERATE COMMAND
 *********************************************
 ****************************************** */

function createCommand ($extra=False) 
{
	/* ***********************************
	 PART 1: Get variables from POST array and validate
	 ************************************* */
	// validate processing run parameters
	$runParametersForm = new RunParametersForm();
	$errorMsg = $runParametersForm->validate( $_POST );
	
	// validate stack preparation parameters
	$stackPrepForm = new StackPrepForm();
	$errorMsg .= $stackPrepForm->validate( $_POST );
	
	// reload the form with the error messages
	if ( $errorMsg ) jobForm( $errorMsg );

	/* *******************
	 PART 2: Create program command
	 ******************** */
	// make the first letter of the method upper case
	$method = ucfirst($_POST['method']);
	$refineScript = "prepRefine".$method.".py ";
	$command = $refineScript;
	
	// add run parameters
	$command .= $runParametersForm->buildCommand( $_POST );
	
	// add stack prep parameters
	$command .= $stackPrepForm->buildCommand( $_POST );
	
	// collect the user selected stack id
	$command.='--stackid='.$_POST['stackval'].' ';
	
	// collect the user selected model id(s)
	foreach( $_POST as $key=>$value ) {
		if (strpos($key,"model_" ) !== False) {
			$modelids.= "$value,";
		}
	}
	$modelids = trim($modelids, ",");
	$command.='--modelid='.$modelids.' ';
	
	/* *******************
	 PART 4: Create header info, i.e., references
	 ******************** */
	// Add reference to top of the page
	$headinfo .= showReference( $_POST['method'] );

	/* *******************
	 PART 5: Show or Run Command
	 ******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'preprefine', $nproc);
	// if error display them
	if ($errors) jobForm($errors);
};

?>

