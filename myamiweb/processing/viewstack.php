<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

$filename=$_GET['file'];
$expId =$_GET['expId'];
$norefId=$_GET['norefId'];
$norefClassId=$_GET['norefClassId'];
$stackId=$_GET['stackId'];
$substack=$_GET['substack'];
$refinement=$_GET['refinement'];
$refinetype=$_GET['refinetype'];
$subprtls=False;
$iter1=$_GET['itr1'];
$iter2=$_GET['itr2'];
$reconId=$_GET['recon'];

$updateheader=($_GET['uh']==1) ? 1 : 0;

if ($reconId) {
  $particle = new particledata();
  $stackId=$particle->getStackIdFromReconId($reconId);
	$stack = $particle->getStackParams($stackId);
	$refine = array();
  $filename=$stack['path'].'/'.$stack['name'];
	$arrayall=array(array());
	for ($i=$iter1;$i<=$iter2;$i++) {
		$refine[$i] = $particle->getRefinementData($reconId,$i);
		$refineId = $refine[$i][DEF_id];
		// get all bad particles in stack
		$subprtlsarray[$i]=$particle->getSubsetParticlesInStack($refineId,$substack,$refinetype);
		foreach ($subprtlsarray[$i] as $s) $arrays[$i][]=$s['p'];
		if ($i == $iter1) $arrayall = $arrays[$i];
		$arrayall=array_intersect($arrayall,$arrays[$i]);
	}
	foreach ($arrayall as $s) $subprtls[]=array('p' => $s);
	$numbad = count($subprtls);
}

if ($refinement) {
  $particle = new particledata();
  $stack=$particle->getStackFromRefinement($refinement);
  //echo print_r($stack);
  $filename=$stack['path'].'/'.$stack['name'];
  if ($substack) {
			// get all bad particles in stack
		$subprtls=$particle->getSubsetParticlesInStack($refinement,$substack,$refinetype);
    $numbad = count($subprtls);
  }
}

function getimagicfilenames($file) {
	$file = substr($file, 0, -3);
	$file_hed = $file."hed";
	$file_img = $file."img";
	return array($file_hed, $file_img);
}

list($file_hed, $file_img)=getimagicfilenames($filename);

//get session name
if ($expId){
	$sessionId=$expId;
	$projectId=getProjectFromExpId($expId);
}

$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessionname=$sessioninfo['Name'];

$info=imagicinfo($file_hed);
$n_images = ($substack) ? $numbad : $info['count']+1;
?>
<html>
<head>
<? echo stackViewer($file_hed,$file_img,$n_images,$updateheader, $subprtls);?>
<script>
var expId="<?=$expId?>"
var sessionname="<?=$sessionname?>"
var filename="<?=$filename?>"
var norefId="<?=$norefId?>"
var norefClassId="<?=$norefClassId?>"
var stackId="<?=$stackId?>"

function upload() {
	var templateId=$('templateId').value
	if (templateId!=""&& templateId <= n_images-1 && templateId >=0 ) {
		if (stackId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateId="+templateId+"&stackId="+stackId+"&file="+filename+"","width=400,height=200")
		}
		if (norefId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateId="+templateId+"&norefId="+norefId+"&norefClassId="+norefClassId+"&file="+filename+"","width=400,height=200") 
		}
	}
}

function uploadavg() {
  if (stackId!="") {
    window.open("uploadtemplate.php?expId="+expId+"&stackId="+stackId+"&file="+filename+"&avg=True","width=400,height=200")
  }
}

function goTo() {
	var index = $('excludedIndex').value
	window.open("createmodel.php?expId="+expId+"&file="+filename+"&exclude="+index+"&noref="+norefId+"&norefClass="+norefClassId+"",'height=250,width=400');
	
	
}
</script>
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
<input id="loadbutton" type="button" alt="Load" value="Load" onclick="load();"> <br />
<?
if ($stackId || $norefId) echo "Upload as Template:<input id='templateId' type='text' alt='Upload' value='' size='5'>
        <input id='uploadbutton' type='button' alt='upload' value='upload' onclick='upload();'>
        <br />\n";

if ($norefId) {
  echo "Create initial model using these class averages <BR/> exclude these classes (e.g. 0,1,5): <INPUT TYPE='text' INPUT ID='excludedIndex' VALUE=''> <INPUT TYPE='button' value='Create Model' onClick=goTo()>\n";
}
elseif ($stackId) {
  echo "<input id='uploadavg' type='button' alt='upload average' value='Average images as template' onclick='uploadavg();'>\n";
  echo "<br />\n";
}

?>


<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
