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
$templateStackId=$_GET['templateStackId'];
$alignId=$_GET['alignId'];
$stackId=$_GET['stackId'];
$substack=$_GET['substack'];
$refinement=$_GET['refinement'];
$refinetype=$_GET['refinetype'];
$subprtls=False;
$iter1=$_GET['itr1'];
$iter2=$_GET['itr2'];
$reconId=$_GET['recon'];

$updateheader=($_GET['uh']==1) ? 1 : 0;

$particle = new particledata();
$maxangle = $particle->getMaxTiltAngle($expId);

if ($reconId) {
  $stackId=$particle->getStackIdFromReconId($reconId);
	$stack = $particle->getStackParams($stackId);
	$refine = array();
  $filename=$stack['path'].'/'.$stack['name'];
	$arrayall=array(array());
	for ($i=$iter1;$i<=$iter2;$i++) {
		$ref = $particle->getRefinementData($reconId,$i);
		$refine[$i] = $ref[0];
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
	$classnumber=$particle->getNoRefClassParticleNumber($norefClassId);
} elseif ($alignId) {
	$classnumber=$particle->getAlignParticleNumber($alignId);
} elseif ($clusterId) {
	$classnumber=$particle->getClusteringParticleNumber($clusterId);
}

if ($refinement) {
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
var templateStackId="<?=$templateStackId?>"
var alignId="<?=$alignId?>"

<?php
if ($norefClassId || $alignId || $clusterId) {
	$c=array();
	foreach($classnumber as $cn) {
		$c[]=$cn['number'];
	}
echo 'var stackinfo=['.implode(',',$c).']'."\n";
}
if ($norefClassId || $reclassId || $clusterId || $templateStackId || $alignId) {
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
	var projections=$('selectedIndex').value
	if (norefClassId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&norefId="+norefId+"&norefClassId="+norefClassId,"width=400,height=200")
	}
	if (reclassId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&reclassId="+reclassId,"width=400,height=200")
	}
	if (clusterId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&clusterId="+clusterId,"width=400,height=200")
	}
	if (templateStackId!="") {
		window.open("imagic3d0.php?expId="+expId+"&projections="+projections+"&templateStackId="+templateStackId,"width=400,height=200")
	}
}

function uploadTemplate() {
	var templateId=$('selectedIndex').value
	if (templateId!="") {
		if (stackId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateIds="+templateId+"&stackId="+stackId,"width=400,height=200")
		} else if (alignId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateIds="+templateId+"&alignId="+alignId,"width=400,height=200") 
		} else if (clusterId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateIds="+templateId+"&clusterId="+clusterId,"width=400,height=200") 
		}
	}
}

function uploadavg() {
  if (stackId!="") {
    window.open("uploadtemplate.php?expId="+expId+"&stackId="+stackId+"&avg=True","width=400,height=200")
  }
}

function runCommonLines() {
	if (clusterId=="") {
		return
	}
	var selindex = $('selectedIndex').value
	var exindex = $('excludedIndex').value
	if (selindex!="" && exindex!="") {
		if (selindex.length > exindex.length) {
			selindex = ""
		} else {
			exindex = ""
		}
	}
	if (selindex!="") {
		window.open("createmodel.php?expId="+expId+"&include="+selindex+"&clusterid="+clusterId+"",'height=250,width=400');
	} 
	if (exindex!="") {
		window.open("createmodel.php?expId="+expId+"&exclude="+exindex+"&clusterid="+clusterId+"",'height=250,width=400');
	}
}

function createAlignSubStack() {
	var index = $('selectedIndex').value
	if (index!="") {
		if (clusterId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&include="+index+"&clusterId="+clusterId+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&include="+index+"&alignId="+alignId+"",'height=250,width=400');
		}
	} 
	var index = $('excludedIndex').value
	if (index!="") {
		if (clusterId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&exclude="+index+"&clusterId="+clusterId+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&exclude="+index+"&alignId="+alignId+"",'height=250,width=400');
		}
	}
}

function createRctVolume() {
	var index = $('selectedIndex').value
	if (index!="") {
		if (clusterId!="") {
			window.open("runRctVolume.php?expId="+expId+"&clusterid="+clusterId+"&classnum="+index+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("runRctVolume.php?expId="+expId+"&alignid="+alignId+"&classnum="+index+"",'height=250,width=400');
		}
	}
}

function createSubStack() {
	var index = $('excludedIndex').value
	window.open("subStack.php?expId="+expId+"&sId="+stackId+"&exclude="+index+"",'height=250,width=400');
}

function createTemplateStackExcluded() {
	var index = $('excludedIndex').value
	window.open("uploadTemplateStack.php?expId="+expId+"&clusterId="+clusterId+"&exclude="+index+"",'height=250,width=400');
}

function createTemplateStackIncluded() {
	var index = $('selectedIndex').value
	window.open("uploadTemplateStack.php?expId="+expId+"&clusterId="+clusterId+"&include="+index+"",'height=250,width=400');
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
		<option value="50">jpeg 50</option>
		<option value="80">jpeg 80</option>
		<option value="90">jpeg 90</option>
		<option value="png">png</option>
	</select>
<input id="loadbutton" type="button" alt="Load" value="Load" onclick="load();">
<?


//Buttons for exclusion
$excludebuttons = "";
if ($stackId)
	$excludebuttons .= "<input type='button' value='Remove Particles' onClick='createSubStack()' >\n";
if ($clusterId || $alignId) 
	$excludebuttons .= "<input type='button' value='Create SubStack' onClick='createAlignSubStack()'>\n";
if ($clusterId) 
	$excludebuttons .= "<input type='button' value='Create Template Stack' onClick='createTemplateStackExcluded()'>\n";
if ($clusterId)
	$excludebuttons .= "<input type='button' value='Run Common Lines' onClick='runCommonLines()'>\n";



//Buttons for inclusion
$includebuttons = "";
// Substack
if ($clusterId || $alignId)
	$includebuttons .= "<input type='button' value='Create SubStack' onClick='createAlignSubStack()'>\n";
if ($clusterId)
	$includebuttons .= "<input type='button' value='Create Template Stack' onClick='createTemplateStackIncluded()'>\n";
if (($clusterId || $alignId) && $maxangle > 5)
	$includebuttons .= "<input type='button' value='Create RCT Volume' onClick='createRctVolume()'>\n";
// Upload Template
if ($stackId || $clusterId || $alignId)
	$includebuttons .= "<input id='uploadbutton' type='button' value='Create Templates' onclick='uploadTemplate();'>\n";
// Imagic 3d0
if ($norefClassId || $reclassId || $clusterId || $templateStackId)
	$includebuttons .= "<input id='3d0button' type='button' alt='Create 3D0' value='Run Imagic 3d0' onclick='create3d0();'>\n";
if ($clusterId)
	$includebuttons .= "<input type='button' value='Run Common Lines' onClick='runCommonLines()'>\n";

echo "<table border='0' cellpading='6' cellspacing='10'><tr><td>\n";
echo "  <span>Selection mode:</span>\n";
echo "  <input id='mode' style='font-size: 12px; border: 1px solid #F00' type='button' value='exclude' onclick='setMode()'>\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#aa3333'>Excluded images:</font>\n <input type='text' id='excludedIndex' value=''>\n";
echo $excludebuttons."\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#33aa33'>Selected images:</font>\n <input type='text' id='selectedIndex' value=''>\n";
echo $includebuttons."\n";
echo "</td></tr></table>\n";


if ($stackId)
	echo "<input id='uploadavg' type='button' alt='upload average' value='Average images as template' onclick='uploadavg();'>\n";

?>


<br />
<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
