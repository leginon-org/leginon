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

	echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
	# get list of png files in directory
	$pngfiles=array();
	$modeldir= opendir($model['path']);
	while ($f = readdir($modeldir)) {
		if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
	}
	sort($pngfiles);
  
# display starting model
	echo "<TR><TD COLSPAN=2>\n";
	echo "<B>Model ID: $modelid</b><br />\n";
	foreach ($pngfiles as $snapshot) {
		$snapfile = $model['path'].'/'.$snapshot;
		echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
	}
	echo "</TD>\n";
	echo "</TR>\n";
	$sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);

	# add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($modelid,$model['description']) : $model['description'];
	
	echo"<TR><TD COLSPAN=2>$descDiv</TD></TR>\n";
	echo"<TR><TD COLSPAN=2>$model[path]/$model[name]</TD></TR>\n";
	echo"<TR><TD>pixel size:</TD><TD>$model[pixelsize]</TD></TR>\n";
	echo"<TR><TD>box size:</TD><TD>$model[boxsize]</TD></TR>\n";
	echo"<TR><TD>symmetry:</TD><TD>$sym[symmetry]</TD></TR>\n";
	echo"<TR><TD>resolution:</TD><TD>$model[resolution]</TD></TR>\n";
	echo "</table>\n";
}

echo "</form>\n";
processing_footer();

?>