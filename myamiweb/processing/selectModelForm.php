<?php
// compress this file if the browser accepts it.
if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip')) ob_start("ob_gzhandler"); else ob_start();
/**
 *      The Leginon software is Copyright 2007
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Selects a model for a reconstruction
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

// check if session provided
$expId 		= $_GET['expId'];
$method 	= $_POST['method'];
$type 		= $_POST['type'];
$projectId 	= getProjectId();
$stackval 	= $_POST['stackval'];

if (!$expId) {
	exit;
}

$particle = new particledata();

// get initial models associated with project
$models = $particle->getModelsFromProject($projectId);

if (is_array($models) && count($models)>0) {
	$modelTable = "<table class='tableborder' border='1'>\n";
	foreach ($models as $model) {
		$modelTable .= "<tr><td>\n";
		$modelid = $model['DEF_id'];
		$symdata = $particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
		$modelvals = "$model[DEF_id]|--|$model[path]|--|$model[name]|--|$model[boxsize]|--|$symdata[eman_name]";

		$value = "model_".$modelid;
		
		// if we want to be able to select multiple models, use checkboxes instead of radio buttons
		if ( $type == "multi" ) {
			$controlType = "checkbox";
			// we expect both the name and the value to be "model_#"		
			$name = $value;
		} else {
			$controlType = "radio";
			// ensure that only a single model is selected for single model methods
			// The radio control needs the name to be the same for all models
			$name = "model_";
		}
				
		$modelTable .= "<input type='$controlType' NAME='$name' value='$value' >\n";
		$modelTable .= "Use<br/>Model\n";

		$modelTable .= "</td><td>\n";

		$modelTable .= modelsummarytable($modelid, true);

		$modelTable .= "</td></tr>\n";
	}
	$modelTable .= "</table>\n\n";	
		
} else {
	$modelTable .=  "No initial models in database";
}

$javafunc="<script src='../js/viewer.js'></script>\n";

if ( $method == "external" ) {
	$action="runAppionLoop.php?expId=$expId&form=UploadExternalRefine";
} else {
	$action="prepRefineForm.php?expId=$expId";
}
?>

<?php processing_header("Appion: Recon Refinement","Select Initial Model for Refinement",$javafunc); ?>

<form name='select_model_form' method='POST' action='<?php echo $action; ?>' >
	<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=<?php echo $expId; ?> '>[Upload a new initial model]</A><br /><br />
	
	<input type='SUBMIT' NAME='submitstackmodel' VALUE='Use selected model(s)'><br>
	<?php echo $modelTable; ?>
	
	<input type='hidden' name='method' value='<?php echo $method; ?>'>
	<input type='hidden' name='type' value='<?php echo $type; ?>'>
	<input type='hidden' name='stackval' value='<?php echo $stackval; ?>'>
	
	<br />

	<input type='SUBMIT' NAME='submitstackmodel' VALUE='Use selected model(s)'>
</form>

<?php echo showReference( $method ); ?>

<?php processing_footer(); ?>
