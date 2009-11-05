<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";
require "inc/summarytables.inc";

$expId= $_GET['expId'];
$projectId=getProjectFromExpId($expId);
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

function modelEntry($model,$particle,$hidden=False) {
  	$modelid = $model['DEF_id'];
	$expId= $_GET['expId'];
	// get updated description
	if ($_POST['updateDesc'.$modelid]) {
		updateDescription('ApInitialModelData', $modelid, $_POST['newdescription'.$modelid]);
		$model['description']=$_POST['newdescription'.$modelid];
	}

	# get list of png files in directory
	$searchstr = $model['path']."/".$model['name']."*.png";
	$pngfiles = glob($searchstr);
	sort($pngfiles);
	$gifsearchstr = $model['path']."/".$model['name']."*.gif";
	$giffiles = glob($gifsearchstr);
  	sort($giffiles);

        // display starting model
	$j = "Model ID: $modelid";
	if ($hidden)  $j.= " <input class='edit' type='submit' name='unhideModel".$modelid."' value='unhide'>";
	else $j.= " <input class='edit' type='submit' name='hideModel".$modelid."' value='hide'>";
	$modeltable = apdivtitle($j);
	foreach ($giffiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		if (file_exists($snapshot)) {
			$modeltable.= "<img src='loadimg.php?rawgif=1&filename=$snapshot' height='64'>\n";
		}
	}
	foreach ($pngfiles as $snapshot) {
		$snapfile = $snapshot;
		$modeltable.= "<a border='0' href='loadimg.php?filename=$snapfile' target='snapshot'>";
		$modeltable.= "<img src='loadimg.php?filename=$snapfile&h=80' height='80'></a>\n";
	}
	$sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($modelid,$model['description']) : $model['description'];
	
	$modeltable.= "<br />\n";
	$modeltable.= "<b>pixel size:</b> $model[pixelsize]<br />\n";
	$modeltable.= "<b>box size:</b> $model[boxsize]<br />\n";
	$modeltable.= "<b>symmetry:</b> $sym[symmetry]<br />\n";
	$modeltable.= "<b>resolution:</b> $model[resolution]<br />\n";
	$modeltable.= "<b>Filename:</b><br />$model[path]/$model[name]<br />\n";
	$modeltable.= "<b>Description:</b><br />$descDiv<br />\n";
	return $modeltable;
}

?>
