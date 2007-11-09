<?php

require ('inc/particledata.inc');
require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/processing.inc');

// --- change with query --- //

$refinement=$_GET['refinement'];

$particle = new particledata();
// get all bad particles in stack
$badprtls=$particle->getBadParticlesInStack($refinement);
$numbad = count($badprtls);
$stack=$particle->getStackFromRefinement($refinement);
//echo print_r($stack);
$filename=$stack['path'].'/'.$stack['name'];

$updateheader=($_GET['uh']==1) ? 1 : 0;

function getimagicfilenames($file) {
	$file = substr($file, 0, -3);
	$file_hed = $file."hed";
	$file_img = $file."img";
	return array($file_hed, $file_img);	
}

list($file_hed, $file_img)=getimagicfilenames($filename);

$info=imagicinfo($file_hed);
$n_images=$numbad;

?>
<html>
<head>
<? echo stackViewer($file_hed,$file_img,$n_images,$updateheader, $badprtls);?>
</head>
<body onload='load()'>
<?
echo "stack: $file_hed";
echo "<br \>";
echo "#images: $n_images";
echo "<br \>";

$defendimg = ($_GET['endimg']) ? $_GET['endimg'] : (($n_images > 20) ? 20 : $n_images-1);
$lastimg=($_POST['endimg']) ? $_POST['endimg'] : $defendimg;
?>

from: <input id="startimg" type="text" alt="Start" value="0" size="10">
to: <input id="endimg" type="text" alt="End" value="<?=$lastimg?>" size="10">
binning: <select id="binning">
		<option value="1">1</option>
		<option value="2">2</option>
		<option value="4">4</option>
		<option value="8">8</option>
	</select>
quality: <select id="quality">
		<option value="80">jpeg 80</option>
		<option value="90">jpeg 90</option>
		<option value="png">png</option>
	</select>
<input id="loadbutton" type="button" alt="Load" value="Load" onclick="load();">
<br />
<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
