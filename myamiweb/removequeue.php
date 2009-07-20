<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

function getSessionByImage($imageId) {
  global $leginondata;
	$q = 'SELECT '
		.'a . `REF|SessionData|session` as session FROM `AcquisitionImageData` a '
		.'WHERE a . `DEF_id` = '.$imageId.' ';
	list($r) = $leginondata->mysql->getSQLResult($q);
	return $r;
}

function getDeQueuedTargetListIdsByImage($imageId) {
	global $leginondata;
	$q="SELECT "
		."dqlist.`REF|ImageTargetListData|list` as doneid "
		."FROM "
		."`DequeuedImageTargetListData` AS `dqlist` "
		."LEFT JOIN `ImageTargetListData` AS `itlist` " 
		."ON (`itlist`.`DEF_id`=`dqlist`.`REF|ImageTargetListData|list`) "
		."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`dqlist`.`REF|QueueData|queue`) "
		."where "
		."`itlist`.`REF|AcquisitionImageData|image` = ".$imageId." "
		."";
	return $leginondata->mysql->getSQLResult($q);
}

function getTargetListIdsByImage($imageId,$sublist='all') {
	global $leginondata;
	$q="SELECT "
		."itlist.`DEF_id` as itlid, "
		."itlist.`REF|QueueData|queue` as queue "
		."FROM "
		."`ImageTargetListData` AS `itlist` "
		."where "
		."`itlist`.`REF|AcquisitionImageData|image` = ".$imageId." "
		."";
	if ($sublist !='all') {
		$q = $q." AND `itlist`.`sublist`=".$sublist." ";
	}
	return $leginondata->mysql->getSQLResult($q);
}

function getChildren($imgId) {
  global $leginondata;
	$q = " select "
		."child.`DEF_id` as childId, "
		."child.`MRC|image` as childimage, "
		."pp.`name` as parentpreset, "
		."target.`type` as childtype, "
		."target.`number` as childnumber, "
		."p.`name` as preset, "
		."parent.`DEF_id` as imageId, "
		."parent.`MRC|image` as image "
		."from AcquisitionImageData parent "
		."left join AcquisitionImageTargetData target "
		."on (parent.`DEF_id`=target.`REF|AcquisitionImageData|image`) "
		."left join AcquisitionImageData child "
		."on (target.`DEF_id`=child.`REF|AcquisitionImageTargetData|target`) "
		."left join PresetData pp "
		."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
		."left join PresetData p "
		."on (p.DEF_id=child.`REF|PresetData|preset`) "
		."where " 
		."parent.`DEF_id` ='".$imgId."' "; 

	if($Rchild = $leginondata->mysql->getSQLResult($q)) {
		return $Rchild;
	} else {
		return NULL;
	}
}

function getDriftedImage($imgId,$direction) {
	if ($direction ==1) {
		$from = 'new';
		$to = 'old';
	} else {
		$from = 'old';
		$to = 'new';
	}
 	global $leginondata;
	$q = " select "
		."`REF|AcquisitionImageData|".$from." image` as nextId "
		."from AcquisitionImageDriftData "
		."where "
		." `REF|AcquisitionImageData|".$to." image`=$imgId "
		." ";
	if($newimg = $leginondata->mysql->getSQLResult($q)) {
		return $newimg;
	}
	else return NULL;
}

	
function getTwins($imgId) {
	$me = $imgId;
	$twins = array($me);
	while ($me) {
		$twin = getDriftedImage($me,0);
		if ($twin) {
			array_push($twins,$twin[0]['nextId']);
			$newme = $twin[0]['nextId'];
		} else {
			$newme = NULL;
		}
		$me= $newme;
	}
	$me = $imgId;
	while ($me) {
		$twin = getDriftedImage($me,1);
		if ($twin) {
			array_push($twins,$twin[0]['nextId']);
			$newme = $twin[0]['nextId'];
		} else {
			$newme = NULL;
		}
		$me= $newme;
	}

	return $twins;
}		

function getDescendants($imgId) {
	$descendants = array();
	$parentIds = array($imgId);
	while ($parentIds) {
		$newparentIds = array();
		foreach ($parentIds as $parent) {
			$children = getChildren($parent);
			foreach ($children as $child) {
				if ($child['childId']) {
					array_push($descendants,$child['childId']);
					array_push($newparentIds,$child['childId']);
				}
			}
		}
		$parentIds = $newparentIds;
	}
	return $descendants;
}

function createData() {
  	global $leginondata;
	$g=true;
	if (!$imgId=stripslashes($_GET['id'])) {
		$g=false;
	}
	if (!$g) {
		echo "image id not specified";
		exit;
	}

	$preset=$_GET[preset];
	// --- find image
	$newimage = $leginondata->findImage($imgId, $preset);
	$parentimageId = $newimage[id];
	
	$sessionId = getSessionByImage($parentimageId);
	$_POST['image']=$parentimageId;
	$sessioninfo = $leginondata->getSessionInfo($sessionId);

	$imagetls = array();
	$dqimagetls = array();
	$queues = array();

	$parentimage_all = getTwins($parentimageId);
	$descimages = $parentimage_all;
	foreach ($parentimage_all as $p) {
		$descendants = getDescendants($p);
		foreach ((array)$descendants as $d) {
			array_push($descimages,$d);
		}
	}
	foreach ($descimages as $d3) {
		$desctlist = getTargetListIdsByImage($d3,'0');
		foreach ((array)$desctlist as $d3tl) {
			array_push($imagetls,$d3tl['itlid']);
			array_push($queues,$d3tl['queue']);
		};
		$descdqlist = getDeQueuedTargetListIdsByImage($d3);
		foreach ((aray)$descdqlist as $d3tl) {
			array_push($dqimagetls,$d3tl['doneid']);
		}
	}
	$active = array_diff($imagetls,$dqimagetls);
	$active_keys = array_keys($active);
	$n=0;
	$aborting = array();
	foreach ($active as $v) {
		$k=$active_keys[$n];
		$deq = array('REF|QueueData|queue'=>$queues[$k],'REF|ImageTargetListData|list'=>$v,'REF|SessionData|session'=>$sessionId);
	array_push($aborting,$deq);
	$n = $n+1;
	}
	
	return array($imagetls,$dqimagetls,$aborting);
}

function test() {
  	global $leginondata;
	$sessionId=4861;
	$sessioninfo = $leginondata->getSessionInfo($sessionId);
	return array(array($sessionId),array($sessionId),array($sessionId));
}

function createForm() {
  global $leginondata;
	$results=createData();
	$imagetls=$results[0];
	$dqimagetls=$results[1];
	$aborting=$results[2];
	$formAction=$_SERVER['PHP_SELF']."?session=".$_POST['session']."&id=".$_POST['image'];
	?>
<html>
	<head>
		<title><?=$title; ?> queue remover</title>
		<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
		<STYLE type="text/css">
			 DIV.comment_section { text-align: justify; 
		margin-top: 5px;
		font-size: 10pt}
			 DIV.comment_subsection { text-indent: 2em;
		font-size: 10pt;
		margin-top: 5px ;
		margin-bottom: 15px ;
	}
		</STYLE>
		<script>
			 function init() {
	 this.focus();
			 }
		</script>
	</head>
	<body onload="init();" >
		<table border=0 cellspacing="0" cellpadding=0>
			<tr>
				<td colspan = "2"><h5>*Only work for the lists not yet start processing
						 </br>Use the ABORT button in Leginon for the current list</h5>
				</td>
			</tr>
			<tr>
				<td>
					<table>
						<tr>
							<td>total target list =
							</td>
							<td> <? echo count($imagetls); ?>
							</td>
						</tr>
						<tr>
							<td>total dequeued image target list =
							</td>
							<td> <? echo count($dqimagetls); ?>
							</td>
						</tr>
					</table>
				</td>
				<TD ALIGN='RIGHT' VALIGN='BOTTOM'>
 <FORM name='removeform' method='POST' ACTION='<?$formAction?>' >
					<input type='submit' name='remove' value='Remove Active'><BR>
	</FORM>
				</TD>
			</tr>
			<tr valign="top">
				 <td colspan="4"> 
	 <?php echo divtitle("Active Target List");?>
		<table width=100% class='tableborder' cellspacing='1' cellpadding='2'>
			<tr>
				<td>
	<?
	if (count($aborting)>0) {
		foreach ($aborting as $deq) {
			$targetimage = $leginondata->getTargetListInfo($deq['REF|ImageTargetListData|list']);
			if ($targetimage[0]['count']) {
			echo $targetimage[0]['count'];
			?></td><td> targets from 
			</td><td><?
			echo $targetimage[0]['filename'].".mrc";
	?>
				</td>
			</tr>
			<tr>
				<td>
	<?
			}
		}
	} else {
		echo "NO ACTIVE LIST FOR THIS IMAGE AND DESCENDENTS";
	}
	?>
			 </td>
			</tr>
		</table>
	</td></tr></table>
	</body>
</html>
<?
}

function runQueueRemover() {
	global $leginondata;
	$remove = $_POST['remove'];
	if ($remove=='Remove Active') {
		$results=createData();
		$aborting=$results[2];
		foreach ($aborting as $data) {
			$leginondata->mysql->SQLInsert('DequeuedImageTargetListData',$data);
		}
		createForm();
	} else {
		createForm();
	}
}

runQueueRemover($deqarray);
?>
