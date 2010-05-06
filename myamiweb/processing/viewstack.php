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
$clusterId=$_GET['clusterId'];
$templateStackId=$_GET['templateStackId'];
$alignId=$_GET['alignId'];
$stackId=$_GET['stackId'];
$substack=$_GET['substack'];
$refinement=$_GET['refineIter'];
$refinetype=$_GET['refinetype'];
$junksort=$_GET['junksort'];
$aligned=$_GET['aligned'];
$subprtls=False;
$substacktype = (array_key_exists('comm_param',$_POST)) ? $_POST['comm_param'] : $_GET['subtype'];
$iter1= (array_key_exists('iter1',$_POST)) ? $_POST['iter1'] : $_GET['itr1'];
$iter2= (array_key_exists('iter2',$_POST)) ? $_POST['iter2'] : $_GET['itr2'];
$reconId=$_GET['recon'];
$clusterIdForSubstack = $_GET['clusterIdForSubstack'];
$alignIdForSubstack = $_GET['alignIdForSubstack'];
$subStackClassesString=$_GET['include'];
if ($subStackClassesString != "") {
	$subStackClasses=explode(',',$subStackClassesString);
}

$updateheader=($_GET['uh']==1) ? 1 : 0;
$pixelsize=(is_numeric($_GET['ps'])) ? trim($_GET['ps']) : 0;

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
		$refineId = $refine[$i]['DEF_id'];
		// get all bad particles in stack
		$subprtlsarray[$i]=$particle->getSubsetParticlesInStack($refineId,$substacktype,$refinetype);
		foreach ($subprtlsarray[$i] as $s) $arrays[$i][]=$s['p'];
		if ($i == $iter1) $arrayall = $arrays[$i];
		$arrayall=array_intersect($arrayall,$arrays[$i]);
	}
	foreach ($arrayall as $s) $subprtls[]=array('p' => $s);
	$numbad = count($subprtls);
}
if ($alignId) {
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


if ($subStackClassesString != "") {
	if ($aligned == "1") {
		if ($clusterIdForSubstack) {
			$stack=$particle->getAlignedStackFromCluster($clusterIdForSubstack);
			$subprtls=$particle->getSubsetParticlesFromCluster($clusterIdForSubstack, $subStackClasses);
			for ($i=0;$i<count($subprtls);$i++) {
				$subprtls[$i]['p'] = intval($subprtls[$i]['p'])-1;
			}
		} elseif ($alignIdForSubstack) {
			$stack=$particle->getAlignedStackFromAlign($alignIdForSubstack);
			$subprtls=$particle->getSubsetParticlesFromAlign($alignIdForSubstack, $subStackClasses);
			for ($i=0;$i<count($subprtls);$i++) {
				$subprtls[$i]['p'] = intval($subprtls[$i]['p'])-1;
			}
		}
		
		$filename=$stack['path'].'/'.$stack['imagicfile'];
	} else {
		
		echo "yahoo";
	
		if ($clusterIdForSubstack) {
			$stack=$particle->getRawStackFromCluster($clusterIdForSubstack);
			$subprtls=$particle->getSubsetParticlesFromCluster($clusterIdForSubstack, $subStackClasses);
			for ($i=0;$i<count($subprtls);$i++) {
				$subprtls[$i]['p'] = intval($subprtls[$i]['p'])-1;
			}
		} elseif ($alignIdForSubstack) {
			$stack=$particle->getRawStackFromAlign($alignIdForSubstack);
			$subprtls=$particle->getSubsetParticlesFromAlign($alignIdForSubstack, $subStackClasses);
			for ($i=0;$i<count($subprtls);$i++) {
				$subprtls[$i]['p'] = intval($subprtls[$i]['p'])-1;
			}			
		}
	
		$filename=$stack['path'].'/'.$stack['name'];
	}
	
	$numbad = count($subprtls);
}

function getimagicfilenames($file) {
	$file = substr($file, 0, -3);
	$file_hed = $file."hed";
	$file_img = $file."img";
	return array($file_hed, $file_img);
}

if (ereg(".spi$", $filename)) {
	$file_hed=$file_img=$filename;
	$info=spiderinfo($file_hed);
	$n_images=$info['nimg'];
} else if (ereg(".hdf5$", $filename)) {
	$file_hed=$file_img=$filename;
	$n_images=100;
} else {
	list($file_hed, $file_img)=getimagicfilenames($filename);
	$info=imagicinfo($file_hed);
	$n_images=$info['count']+1;
}

//get session name
if ($expId){
	$sessionId=$expId;
	$projectId=getProjectId();
}

$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessionname=$sessioninfo['Name'];

$info=imagicinfo($file_hed);
$n_images = ($substack || $substacktype || $subStackClassesString != "") ? $numbad : $info['count']+1;

?>
<html>
<head>
<?php
	$stackoptions['updateheader']=$updateheader;
	$stackoptions['plist']=$subprtls;
	$stackoptions['stackinfoindex']=1;
	$stackoptions['pixelsize']=$_GET['ps'];
echo stackViewer($file_hed, $file_img, $n_images, $stackoptions);
?>

<script type="text/javascript">
var expId="<?=$expId?>"
var sessionname="<?=$sessionname?>"
var filename="<?=$filename?>"
var stackId="<?=$stackId?>"
var clusterId="<?=$clusterId?>"
var templateStackId="<?=$templateStackId?>"
var alignId="<?=$alignId?>"

<?php
if ($alignId || $clusterId) {
	$c=array();
	$numclass = count($classnumber);
	$classindex = 0;
	$i = 0;
	while ($classindex < $numclass && $i < $n_images) {
		if ($classnumber[$classindex]['classNumber'] == $i+1) {
			if (array_key_exists('resolution', $classnumber[$classindex]))
				$c[]= sprintf("'%d, %.1fA'", $classnumber[$classindex]['number'], $classnumber[$classindex]['resolution']);
			else
				$c[]= sprintf("'%d'", $classnumber[$classindex]['number']);
			$classindex++;
		} else {
			$c[]='0';
		}
		$i++;
	}
	echo 'var stackinfo=['.implode(',',$c).']'."\n";
}
if ($clusterId || $templateStackId || $alignId) {
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
	var sindex = $('selectedIndex').value
	var eindex = $('excludedIndex').value
	if (sindex!="" && seindex.length <= eindex.length) {
		window.open("createmodel.php?expId="+expId+"&include="+sindex+"&clusterid="+clusterId+"",'height=250,width=400');
	} else if (eindex!="") {
		window.open("createmodel.php?expId="+expId+"&exclude="+eindex+"&clusterid="+clusterId+"",'height=250,width=400');
	}
}

function createAlignSubStack() {
	var sindex = $('selectedIndex').value
	var eindex = $('excludedIndex').value
	window.status=sindex;
	if (sindex!="" && sindex.length <= eindex.length) {
		if (clusterId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&include="+sindex+"&clusterId="+clusterId+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&include="+sindex+"&alignId="+alignId+"",'height=250,width=400');
		}
	} else if (eindex!="") {
		if (clusterId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&exclude="+eindex+"&clusterId="+clusterId+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("alignSubStack.php?expId="+expId+"&file="+filename+"&exclude="+eindex+"&alignId="+alignId+"",'height=250,width=400');
		}
	}
	window.status="align sub stack error";
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

function createOtrVolume() {
	var index = $('selectedIndex').value
	if (index!="") {
		if (clusterId!="") {
			window.open("runOtrVolume.php?expId="+expId+"&clusterid="+clusterId+"&classnum="+index+"",'height=250,width=400');
		} else if (alignId!="") {
			window.open("runOtrVolume.php?expId="+expId+"&alignid="+alignId+"&classnum="+index+"",'height=250,width=400');
		}
	}
}

function applyJunkCutoff() {
	var index = $('selectedIndex').value
	if (index!="") {
		window.open("applyJunkCutoff.php?expId="+expId+"&stackId="+stackId+"&partnum="+index+"",'height=250,width=400');
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

function viewSubstack() {
	var index = $('selectedIndex').value
	if (clusterId!="") {
		window.open("viewstack.php?expId="+expId+"&clusterIdForSubstack="+clusterId+"&include="+index+"",'height=250,width=400');
	} else if (alignId!="") {
		window.open("viewstack.php?expId="+expId+"&alignIdForSubstack="+alignId+"&include="+index+"",'height=250,width=400');
	}
}

function viewAlignedSubstack() {
	var index = $('selectedIndex').value
	if (clusterId!="") {
		window.open("viewstack.php?expId="+expId+"&clusterIdForSubstack="+clusterId+"&include="+index+"&aligned=1"+"",'height=250,width=400');
	} else if (alignId!="") {
		window.open("viewstack.php?expId="+expId+"&alignIdForSubstack="+alignId+"&include="+index+"&aligned=1"+"",'height=250,width=400');
	}
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
info:<input type="checkbox" checked id="info" >
scale bar:<input type="checkbox" id="scalebar" >
<input id="loadbutton" type="button" alt="Load" value="Load" onclick="load();">
<?


//Buttons for inclusion
$includebuttons = "";
if ($clusterId || $alignId) {
	$includebuttons .= "<input type='button' value='View Raw Particles' onClick='viewSubstack()'>\n";
	$includebuttons .= "<input type='button' value='View Aligned Particles' onClick='viewAlignedSubstack()'>\n";
	$includebuttons .= "<input type='button' value='Create SubStack' onClick='createAlignSubStack()'>\n";
}
if (($clusterId || $alignId) && $maxangle > 5) {
	$includebuttons .= "<input type='button' value='Create RCT Volume' onClick='createRctVolume()'>\n";
	$includebuttons .= "<input type='button' value='Create OTR Volume' onClick='createOtrVolume()'>\n";
}
if ($junksort)
	$includebuttons .= "<input type='button' value='Apply junk cutoff' onClick='applyJunkCutoff()'>\n";
if ($stackId || $clusterId || $alignId)
	$includebuttons .= "<input type='button' value='Create Templates' onClick='uploadTemplate();' id='uploadbutton' >\n";
if ($clusterId) {
	$includebuttons .= "<input type='button' value='Create Template Stack' onClick='createTemplateStackIncluded()'>\n";
	$includebuttons .= "<input type='button' value='Run Common Lines' onClick='runCommonLines()'>\n";
}
if ($clusterId || $templateStackId)
	$includebuttons .= "<input type='button' value='Run Imagic 3d0' onClick='create3d0();' id='3d0button'>\n";
//END buttons for inclusion


//Buttons for exclusion
$excludebuttons = "";
if ($stackId)
	$excludebuttons .= "<input type='button' value='Remove Particles' onClick='createSubStack()' >\n";
if ($clusterId || $alignId) 
	$excludebuttons .= "<input type='button' value='Create SubStack' onClick='createAlignSubStack()'>\n";
if ($clusterId) {
	$excludebuttons .= "<input type='button' value='Create Template Stack' onClick='createTemplateStackExcluded()'>\n";
	$excludebuttons .= "<input type='button' value='Run Common Lines' onClick='runCommonLines()'>\n";
}
//END buttons for exclusion


echo "<table border='0' cellpading='0' cellspacing='0'><tr><td>\n";
echo "  <span>Selection mode:</span>\n";
echo "  <input id='mode' style='font-size: 12px; border: 1px solid #F00' type='button' value='exclude' onclick='setMode()'>\n<hr/>\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#33aa33'>Selected images:</font>\n <input type='text' id='selectedIndex' value='' size='55'>\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#33aa33'>Select:</font>\n ".$includebuttons."\n<hr/>\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#aa3333'>Excluded images:</font>\n <input type='text' id='excludedIndex' value='' size='55'>\n";
echo "</td></tr><tr><td>\n";
echo "  <font color='#aa3333'>Exclude:</font>\n ".$excludebuttons."\n<hr/>\n";
echo "</td></tr><tr><td>\n";
if ($stackId)
	echo "<input id='uploadavg' type='button' value='Average images as template' onClick='uploadavg();'>\n";
echo "</td></tr></table>\n";

?>


<br />
<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
