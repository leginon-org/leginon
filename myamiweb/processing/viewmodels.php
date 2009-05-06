<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";

$expId= $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";
$particle = new particledata();

$projectId=getProjectFromExpId($expId);

$models = $particle->getModelsFromProject($projectId,True);
$javascript = editTextJava();

processing_header("Initial Models","Initial Models",$javascript);

if ($models) {
	// separate hidden from shown;
	$shown = array();
	$hidden = array();
	foreach($models as $model) { 
		if (is_array($model)) {
			$modelId=$model['DEF_id'];
			// first update hide value
			if ($_POST['hideModel'.$modelId]) {
				$particle->updateHide('ApInitialModelData',$modelId,1);
				$model['hidden']=1;
			}
			elseif ($_POST['unhideModel'.$modelId]) {
				$particle->updateHide('ApInitialModelData',$modelId,0);
				$model['hidden']='';
			}
			if ($model['hidden']==1) $hidden[]=$model;
			else $shown[]=$model;
		}
	}
	$modeltable = "<form name='modelform' method='post' action='$formAction'>\n";
	foreach ($shown as $m) $modeltable.= modelEntry($m,$particle);
	// show hidden templates
	if ($_GET['showHidden'] && $hidden) {
		if ($shown) $modeltable.="<hr />\n";
		$modeltable.="<b>Hidden Models</b> ";
		$modeltable.="<a href='".$_SERVER['PHP_SELF']."?expId=$expId'>[hide]</a><br />\n";
		foreach ($hidden as $m) $modeltable.= modelEntry($m,$particle,True);
	}

	$modeltable.= "</form>\n";
}

if ($hidden && !$_GET['showHidden']) echo "<a href='".$formAction."&showHidden=True'>Show Hidden Models</a><br />\n";

if ($shown || $hidden) echo $modeltable;
else echo "<B>Project does not contain any models.</B>\n";
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
