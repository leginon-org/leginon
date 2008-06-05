<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/viewer.inc";
require"inc/processing.inc";

$expId= $_GET['expId'];
$particle = new particledata();
$projectId=getProjectFromExpId($expId);
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

$models = $particle->getModelsFromProject($projectId);

$javascript = editTextJava();

processing_header("Initial Models","Initial Models",$javascript);

// edit description form
echo "<form name='modelform' method='post' action='$formAction'>\n";

foreach ($models as $model) {
	$modelid = $model['DEF_id'];
	// get updated description
	if ($_POST['updateDesc'.$modelid]) {
		updateDescription('ApInitialModelData', $modelid, $_POST['newdescription'.$modelid]);
		$model['description']=$_POST['newdescription'.$modelid];
	}

	# get list of png files in directory
	$pngfiles=array();
	$modeldir= opendir($model['path']);
	while ($f = readdir($modeldir)) {
		if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
	}
	sort($pngfiles);
  
# display starting model
	echo apdivtitle("Model ID: $modelid");
	foreach ($pngfiles as $snapshot) {
		$snapfile = $model['path'].'/'.$snapshot;
		echo "<a border='0' href='loadimg.php?filename=$snapfile' target='snapshot'>";
		echo "<img src='loadimg.php?filename=$snapfile' height='80'></a>\n";
	}
	$sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($modelid,$model['description']) : $model['description'];
	
	echo "<br />\n";
	echo"<b>pixel size:</b> $model[pixelsize]<br />\n";
	echo"<b>box size:</b> $model[boxsize]<br />\n";
	echo"<b>symmetry:</b> $sym[symmetry]<br />\n";
	echo"<b>resolution:</b> $model[resolution]<br />\n";
	echo"<b>Filename:</b><br />$model[path]/$model[name]<br />\n";
	echo"<b>Description:</b><br />$descDiv<br />\n";
	echo"<br />\n";
}

echo "</form>\n";
processing_footer();

?>