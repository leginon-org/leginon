<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";
require "inc/summarytables.inc";

$expId= $_GET['expId'];
$projectId=getProjectId();
$particle = new particledata();

$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) {
	$formAction.="&showHidden=1";
	$models = $particle->getModelsFromProject($projectId, True);
} else {
	$models = $particle->getModelsFromProject($projectId, False);
}

$javascript = editTextJava();

processing_header("Initial Models", "Initial Models", $javascript);

if (!$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=1'>Show Hidden Models</a><br />\n";

if ($models) {
	$modeltable = "<form name='modelform' method='post' action='$formAction'>\n";
	foreach($models as $model) {
		if (is_array($model)) {
			$modelid=$model['DEF_id'];
			$modeltable .= modelsummarytable($modelid);
		}
	}
	$modeltable .= "</form>\n";
	echo $modeltable;
} else echo "<B>Project does not contain any models.</B>\n";

if (!$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=1'>Show Hidden Models</a><br />\n";

processing_footer();
exit;

?>
