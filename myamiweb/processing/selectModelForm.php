<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
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

		// if we want to be able to select multiple models, use checkboxes instead of radio buttons
		$controlType = ( $type == "multi" ) ? "checkbox" : "radio";
		
		$modelTable .= "<input type='$controlType' NAME='model_$modelid' value='$modelvals' ";
		$modelTable .= ">\n";
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
?>

<?php processing_header("Appion: Recon Refinement","Select Initial Model for Refinement",$javafunc); ?>

<form name='select_model_form' method='POST' action='prepRefineForm.php?expId=<?php echo $expId; ?>' >
	<P><B>Model:</B><br><A HREF='uploadmodel.php?expId=<?php $expId; ?> '>[Upload a new initial model]</A><br>
	
	<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use selected model(s)'><br>
	<?php echo $modelTable; ?>
	
	<input type='hidden' name='method' value='<?php echo $method; ?>'>
	<input type='hidden' name='type' value='<?php echo $type; ?>'>
	<input type='hidden' name='stackval' value='<?php echo $stackval; ?>'>
	
	<P><input type='SUBMIT' NAME='submitstackmodel' VALUE='Use selected model(s)'>
</form>

<?php echo showReference( $method ); ?>

<?php processing_footer(); ?>
