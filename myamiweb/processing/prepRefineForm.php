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

// include each refinement type file
// todo: autodiscovery
require_once "inc/forms/xmippRefineForm.inc";
require_once "inc/forms/frealignRefineForm.inc";
require_once "inc/forms/emanRefineForm.inc";
require_once "inc/forms/stackPrepForm.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/xmippML3DRefineForm.inc";

if ($_POST['process']) {
	createCommand(); // generate command
} else {
	jobForm(); // set parameters
}

// based on the type of refinement the user has selected,
// create the proper form type here. If a new type is added to
// Appion, it's form class should be included in this file
// and it should be added to this function. No other modifications
// to this file should be necessary.
function createSelectedRefineForm( $method, $stackId='', $modelArray='', $kv=''  )
{
	switch ( $method ) {
		case eman:
			$selectedRefineForm = new EmanRefineForm( $method, $stackId, $modelArray, $kv );
			break;
		case frealign:
			$selectedRefineForm = new FrealignRefineForm( $method, $stackId, $modelArray, $kv );
			break;
		case xmipp:
			$selectedRefineForm = new XmippRefineForm( $method, $stackId, $modelArray, $kv );
			break;
		case xmippml3d:
			$selectedRefineForm = new XmippML3DRefineForm( $method, $stackId, $modelArray, $kv );
			break;
		default:
			assert(false); //TODO: not yet implemented exception??
	}		
	
	return $selectedRefineForm;
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
	foreach( $_POST as $key=>$value ) {
		if (strpos($key,"model_" ) !== False) {
			preg_match('/(\D+)_(\d+)/', $key, $matches);
			$id = $matches[2];
			
			$modelArray[] = array( 'name'=>$key, 'id'=>$id );
		}
	}
	
	if (!$modelArray)
		$extra = "ERROR: no initial model selected";
	if (!$_POST['stackval'])
		$extra = "ERROR: no stack selected";

	// get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = getBaseAppionPath($sessiondata).'/recon/';

	// ensure the cs value is set, or don't process
	if ($leginondata->getCsValueFromSession($expId) === false) {
		$extra = "ERROR: Cs value of the images in this session is not unique or known, can't process.";
	}
	
	// set the runname
	// the default run name is the jobtype followed by an ever incrementing number
	$jobType = $reconMethod.'_recon';
	$particle = new particledata();
	$reconruns = $particle->getMaxRunNumber( $jobType, $expId );
	
	// sanity check - make certain we are not going to overwrite data
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	
	// TODO: should '*recon' be repaced with $jobType??
	while (file_exists($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$defrunid = $jobType.($reconruns+1);
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	
	// get stack data
	$stackinfo 	= explode('|--|',$_POST['stackval']);
	$stackid	= $stackinfo[0];
	$apix		= $stackinfo[1];
	$box		= $stackinfo[2];

	// preset information from stackid
	$presetinfo = $particle->getPresetFromStackId($stackid);
	$kv = $presetinfo['hightension']/1e3;

	// Instantiate the class that defines the forms for the selected method of refinement.
	$selectedRefineForm = createSelectedRefineForm( $reconMethod, $stackid, $modelArray, $kv );
	
	// add javascript functions
	$javafunc .= $selectedRefineForm->setDefaults();
	$javafunc .= $selectedRefineForm->additionalJavaScript();
	$javafunc .= writeJavaPopupFunctions('appion');
	$javafunc .= writeJavaPopupFunctions('frealign');
	$javafunc .= writeJavaPopupFunctions('eman');
	$javafunc .= showAdvancedParams();
	
	// add the appion processing header
	processing_header("Appion: Recon Refinement","Prepare Recon Refinement",$javafunc);
	
	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

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
	echo $runParametersForm->generateForm( $_POST );
	
	// add stack preparation parameters
	$stackPrepForm = new StackPrepForm();
	echo $stackPrepForm->generateForm( $_POST );
	
	// add the parameters that apply to all methods of reconstruction
	echo $selectedRefineForm->generalParamForm();
	
	// add parameters specific to the refine method selected
	echo "<INPUT TYPE='checkbox' NAME='showAdvanceParams' onChange='javascript:unhide();' VALUE='' >";
	echo " Show Advanced Parameters <br />";
	echo "<div align='left' id='div1' class='hidden' >";
	echo $selectedRefineForm->advancedParamForm();
	echo "</div>";
	
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
	// collect the user selected stack id
	$commandAddOn.='--stackid='.$_POST['stackval'].' ';
	
	// collect the user selected model id(s)
	foreach( $_POST as $key=>$value ) {
		if (strpos($key,"model_" ) !== False) {
			$modelids.= "$value,";
		}
	}
	
	$commandAddOn.='--modelid='.$modelids.' ';
	
	// collect stack preparation parameters
	$stackPrepForm = new StackPrepForm();
	$commandAddOn .= $stackPrepForm->buildCommand( $_POST );
	
	// Instantiate the class the defines the forms for the selected method of refinement.
	$selectedRefineForm = createSelectedRefineForm( $_POST['method'] );
	$selectedRefineForm->createRunCommand( $_POST, "jobForm", $commandAddOn );
};

// javascript to show or hide the advanced parameters section
function showAdvancedParams()
{
	$javafunc = "
	<script type='text/javascript'>
	 function unhide() {
	 var item = document.getElementById('div1');
	 if (item) {
	 item.className=(item.className=='hidden')?'unhidden':'hidden';
	 }
	 }
	 </script>\n";
	return $javafunc;
}
?>

