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
$reclassId=$_GET['reclassId'];
$norefId=$_GET['norefId'];
$norefClassId=$_GET['norefClassId'];
$clusterId=$_GET['clusterId'];
$imagicClusterId=$_GET['imagicClusterId'];
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
if ($norefClassId) {
	$particle = new particledata();
	$classnumber=$particle->getNoRefClassParticleNumber($norefClassId);
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
<script type="text/javascript">
var expId="<?=$expId?>"
var sessionname="<?=$sessionname?>"
var filename="<?=$filename?>"
var norefId="<?=$norefId?>"
var norefClassId="<?=$norefClassId?>"
var stackId="<?=$stackId?>"
var reclassId="<?=$reclassId?>"
var clusterId="<?=$clusterId?>"
var imagicClusterId="<?=$imagicClusterId?>"
<?php
if ($norefClassId) {
	$c=array();
	foreach($classnumber as $cn) {
		$c[]=$cn['number'];
	}
echo 'var stackinfo=['.implode(',',$c).']'."\n";
}
if ($norefClassId || $reclassId || $clusterId || $imagicClusterId) {
echo 'var addselectfn=selectextra'."\n";

}
?>

function selectextra() {
	select2exclude()
	if (o=$('templateId')) {
		getSelectImages()
		o.value=getLastSelectedImage()
	}
	if (o=$('projectionId')) {
		o.value= getSelectImages()
	}
}

function create3d0() {
	var projections=$('projectionId').value
	if (norefClassId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&norefId="+norefId+"&norefClassId="+norefClassId,"width=400,height=200")
	}
	if (reclassId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&reclassId="+reclassId,"width=400,height=200")
	}
	if (clusterId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&clusterId="+clusterId,"width=400,height=200")
	}
	if (imagicClusterId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&imagicClusterId="+imagicClusterId,"width=400,height=200")
	}
}

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

function createModel() {
	var index = $('excludedIndex').value
	window.open("createmodel.php?expId="+expId+"&file="+filename+"&exclude="+index+"&noref="+norefId+"&norefClass="+norefClassId+"",'height=250,width=400');
}
	
function createNorefSubStack() {
	var index = $('excludedIndex').value
	window.open("norefSubStack.php?expId="+expId+"&file="+filename+"&exclude="+index+"&noref="+norefId+"&norefClass="+norefClassId+"",'height=250,width=400');
}

function createAlignSubStack() {
	var index = $('excludedIndex').value
	window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&exclude="+index+"&clusterId="+clusterId+"",'height=250,width=400');
}

function createSubStack() {
	var index = $('excludedIndex').value
	window.open("subStack.php?expId="+expId+"&sId="+stackId+"&exclude="+index+"",'height=250,width=400');
}

function createTiltPairSubStack() {
	var index = $('excludedIndex').value
	window.open("norefTiltPairSubStack.php?expId="+expId+"&file="+filename+"&exclude="+index+"&noref="+norefId+"&norefClass="+norefClassId+"",'height=250,width=400');
}	

</script>
</head>
<body onload='load()'>
<?
echo "stack: $file_hed";
echo "<br \>";
echo "#images: $n_images";
echo "<br \>";
$defendimg = ($_GET['endimg']) ? $_GET['endimg'] : (($n_images > 40) ? 40 : $n_images-1);
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
<p style="margin-top: 2px; margin-bottom: 4px">
<span>selection mode: </span><input id="mode" style="font-size: 12px; border: 1px solid #F00" type="button" value="exclude" onclick="setMode()">
</p>
<?

if ($stackId || $clusterId || $norefId) echo "Upload as Template:<input id='templateId' type='text' alt='Upload' value='' size='5'>
        <input id='uploadbutton' type='button' alt='upload' value='upload' onclick='upload();'>
        <br />\n";
if ($norefClassId || $reclassId || $clusterId || $imagicClusterId) echo "Imagic 3D0 generator (choose 3 projections):<input id='projectionId' type='text' alt='projection' value='' size='10'>
        <input id='3d0button' type='button' alt='Create 3D0' value='Create 3D0' onclick='create3d0();'>
        <br />\n";

if ($norefId) {
  echo "Create initial model using these class averages <br /> exclude these classes (e.g. 0,1,5): <input type='text' id='excludedIndex' value=''>
<input type='button' value='Create Model' onClick='createModel()' >
<input type='button' value='Create SubStack' onClick='createNorefSubStack()' > 
<input type='button' value='Create Tilt Pair SubStack' onClick='createTiltPairSubStack()'>\n";
}
elseif ($clusterId) {
  echo "Create initial model using these class averages <br /> exclude these classes (e.g. 0,1,5): <input type='text' id='excludedIndex' value=''>
<input type='button' value='Create Model' onClick='createModel()' >
<input type='button' value='Create SubStack' onClick='createAlignSubStack()' > 
<input type='button' value='Create Tilt Pair SubStack' onClick='createTiltPairSubStack()'>\n";
}
elseif ($stackId) {
	echo "<input id='uploadavg' type='button' alt='upload average' value='Average images as template' onclick='uploadavg();'>\n";
  	echo "<br />\n";

	echo "Remove particles from stack: <input type='text' id='excludedIndex' value=''>
		<input type='button' value='Create SubStack' onClick='createSubStack()' >\n";

  	
}

?>


<br />
<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
