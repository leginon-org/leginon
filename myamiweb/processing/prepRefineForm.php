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

// TODO: should be able to remove this
$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";


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
function createSelectedRefineForm( $method )
{
	switch ( $method ) {
		case eman:
			$selectedRefineForm = new EmanRefineForm();
			break;
		case frealign:
			$selectedRefineForm = new FrealignRefineForm();
			break;
		case xmipp:
			$selectedRefineForm = new XmippRefineForm();
			break;
		case xmippml3d:
			$selectedRefineForm = new XmippML3DRefineForm();
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
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	foreach( $_POST as $key=>$value ) {
		if (strpos($key,"model_" ) !== False) {
			$modelinfo = explode('|--|',$_POST['model']);
			$modelid = $modelinfo[0];
			$modelArray[] = array( 'name'=>$key, 'id'=>$modelid );
		}
	}
	
	if (!$modelArray)
		$extra = "ERROR: no initial model selected";
	if (!$_POST['stackval'])
		$extra = "ERROR: no stack selected";

	// Instantiate the class that defines the forms for the selected method of refinement.
	$selectedRefineForm = createSelectedRefineForm( $_POST['method'] );
	
	## get path data for this session for output
	$leginondata = new leginondata();
	$sessiondata = $leginondata->getSessionInfo($expId);
	$sessionpath = getBaseAppionPath($sessiondata).'/recon/';

	if ($leginondata->getCsValueFromSession($expId) === false) {
		$extra = "ERROR: Cs value of the images in this session is not unique or known, can't process.";
	}
	
	$particle = new particledata();

	// find if there are ctffind runs (for frealign option)
	$ctffindruns = $particle->getCtfRunIds($expId, $showHidden=False, $ctffind=True);
	
	// create a default run name
	// TODO: make sure changes to this in eman are carried over
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$reconruns = count($particle->getReconIdsFromSession($expId));
	while (glob($outdir.'*recon'.($reconruns+1))) {
		$reconruns += 1;
	}
	$reconMethod = $selectedRefineForm->getMethodType();
	$defrunid = $reconMethod.'_recon'.($reconruns+1);

	## get stack data
	$stackinfo = explode('|--|',$_POST['stackval']);
	$stackid=$stackinfo[0];
	$nump=$particle->getNumStackParticles($stackid);
	$apix=$stackinfo[1];
	$box=$stackinfo[2];

	// TODO: error handling
	if ($_POST['reconstackval']) {
		$reconstackinfo = explode('|--|',$_POST['reconstackval']);
		$reconstackid=$reconstackinfo[0];
		$reconapix=$reconstackinfo[1];
		$reconbox=$reconstackinfo[2];
		$reconnumpart=$particle->getNumStackParticles($reconstackid);
		if ($reconbox != $box)
		stackModelForm("ERROR: refine stack boxsize ($box) is different from recon stack boxsize ($reconbox)");
		if ($reconapix != $apix)
		stackModelForm("ERROR: refine stack apix ($apix) is different from recon stack apix ($reconapix)");
		if ($reconnumpart != $nump)
		stackModelForm("ERROR: refine stack particle count ($nump) is different from recon stack particle count ($reconnumpart)");
	}

	// TODO: parse POST for all selected models
	//print_r($_POST);
	## get model data
	$modelinfo = explode('|--|',$_POST['model']);
	$modelid = $modelinfo[0];
	$modelpath = $modelinfo[1];
	$modelname = $modelinfo[2];

	$syminfo = explode(' ',$modelinfo[4]);
	$modsym = $syminfo[0];
	if ($modsym == 'Icosahedral') $modsym='icos';

	$nodes = ($_POST['nodes']) ? $_POST['nodes'] : C_NODES_DEF;
	$ppn = ($_POST['ppn']) ? $_POST['ppn'] : C_PPN_DEF;
	$rpn = ($_POST['rpn']) ? $_POST['rpn'] : C_RPROCS_DEF;

	// preset information from stackid
	$presetinfo = $particle->getPresetFromStackId($stackid);
	$kv = $presetinfo['hightension']/1e3;

	$javafunc .= $selectedRefineForm->setGeneralDefaults($box);
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
	
	foreach ( $modelArray as $model ) {
		echo "<input type='hidden' name='".$model['name']."' value='".$_POST[$model['name']]."'>\n";
	}
	echo "<input type='hidden' name='model' value='".$_POST['model']."'>\n";
	echo "<input type='hidden' name='stackval' value='".$_POST['stackval']."'>\n";
	echo "<input type='hidden' name='method' value='".$_POST['method']."'>\n";
	echo "<input type='hidden' NAME='kv' value='$kv'>";
	echo "<input type='hidden' NAME='apix' value='$apix'>";
	if ($_POST['reconstackval'] && $stackid != $reconstackid) {
		echo "<input type='hidden' name='reconstackval' value='".$_POST['reconstackval']."'>\n";
	}

	$sym = ($_POST['sym']) ? $_POST['sym'] : $modsym;

	// -----------------------------------------------
	// add forms for all the needed parameters
	// -----------------------------------------------
	
	// add Processing Run Parameter fields
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunid;
	$runParametersForm = new RunParametersForm( $runname, $outdir );
	echo $runParametersForm->generateForm( $_POST );
	
	// add stack preparation parameters
	$stackPrepForm = new StackPrepForm();
	echo $stackPrepForm->generateForm( $_POST );
	
	// add the parameters that apply to all methods of reconstruction
	$selectedRefineForm->generalParamForm();
	
	// add parameters specific to the refine method selected
	echo "<INPUT TYPE='checkbox' NAME='showAdvanceParams' onChange='javascript:unhide();' VALUE='' >";
	echo " Show Advanced Parameters <br />";
	echo "<div align='left' id='div1' class='hidden' >";
	$selectedRefineForm->advancedParamForm();
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
	if ($_POST['reconstackval'] && $stackid != $reconstackid) {
		echo "</td></tr><tr><td>\n";
		echo stacksummarytable($reconstackid, true);
	}
	echo "</td></tr><tr><td>\n";
	echo modelsummarytable($modelid, true);
	echo "</td></tr></table>\n";

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
			$modelids.= "$key:";
		}
	}
	
	$commandAddOn.='--modelid='.$modelids.' ';
	
	// collect processing run parameters
	$runParametersForm = new RunParametersForm();
	$commandAddOn .= $runParametersForm->buildCommand( $_POST );
	
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

