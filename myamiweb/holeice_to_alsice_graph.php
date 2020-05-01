<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/graph.inc";

$defaultId= 1445;
$defaultpreset='enn';
$sessionId= ($_GET['Id']) ? $_GET[Id] : $defaultId;
$preset = ($_GET['preset']) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET[vs];

#$histogram= true;
$histaxis=($_GET['haxis']) ? $_GET['haxis'] : 'y';
$width=$_GET['w'];
$height=$_GET['h'];

$thicknessdata = $leginondata->getIceThickness($sessionId, $preset);
$alsthicknessdata = $leginondata->getObjIceThickness($sessionId);
# filter out the duplicates here
foreach($alsthicknessdata as $t) {
	if ( !preg_match('/-[a-z](\.mrc)?$/',$t['filename'] ) and ( !preg_match('/-(DW|td)(\.mrc)?$/',$t['filename']))) {
		$data[] = $t['thickness'];
		$filtered_thicknessdata[] = $t;
	}
}

	$hlthick = array();
	$hlcount = array();
	$alsthick = array();
	$alscount = array();
# determine average predicted thickness for all "good" holes in a hl image
# throw away any images with no good holes
	foreach ($thicknessdata as $t) {
		if (array_key_exists($t['image_id'], $hlthick)) {
			$hlthick[$t['image_id']] += $t['thickness-mean'] * $t['good'] ;
			$hlcount[$t['image_id']] += $t['good'];
		}
		else {
			$hlthick[$t['image_id']] = $t['thickness-mean'] * $t['good'] ;
			$hlcount[$t['image_id']] = $t['good'];
		}
	}
	$keys = array_keys($hlcount);
	foreach ($keys as $key) {
		if ($hlcount[$key] >0 ) {
				$hlthick[$key] /= $hlcount[$key];
		}
		else {
			unset($hlthick[$key]);
			unset($hlcount[$key]);
		}
	}
		
#	echo "als_thickness ParentID <br>";
# determine average calculated thickness for all images coming from the same hole
#
	#foreach($alsthicknessdata as $t) {
	foreach($filtered_thicknessdata as $t) {
		$thick['als'] = $t['thickness'];
		$p = $leginondata->getParent($t['DEF_id']) ;
		$thick['hl'] = $thdata[$p['parentId']];
		$tmp = $p['parentId'] ;
#		echo $thick['als'] . " " .     $p['parentId'] . "<br>";
		if (array_key_exists($p['parentId'], $alsthick)) {
			$alsthick[$p['parentId']] += $t['thickness'];
			$alscount[$p['parentId']] += 1;
		}
		else {
			$alsthick[$p['parentId']] = $t['thickness'];
			$alscount[$p['parentId']] = 1;
		}
	}
	$keys = array_keys($alscount);
	#echo "key     alsthickness hl thickness <br>";
	foreach ($keys as $key) {
		$alsthick[$key] /= $alscount[$key];
		if (array_key_exists($key,$hlthick)) {
	#		echo $key . " " . $alsthick[$key] . " " . $hlthick[$key] . "<br>";
			$p = array('hl_thickness' => $hlthick[$key], 'als_thickness' => $alsthick[$key]) ;
			$plt_thicknessdata[]  = $p;
		}
	}

	
#}
if ($viewdata) {
	$keys = array("image_id", "filename", "timestamp", "thickness-mean", "good");
	echo "Dump data from hole thickness averages <br>";
	echo dumpData($thicknessdata, $keys);
	$keys2 = array("DEF_id", "thickness");
	echo "Dump data from image ice thickness <br>";
	echo dumpData($alsthicknessdata, $keys2);
	$display_x = 'hl_thickness';
	$display_y = 'als_thickness';
	$axes = array($display_x,$display_y);
	echo "final dump\n";
	if (sizeof($plt_thicknessdata) >0) {
		echo "size of plt is >0\n";
	}
	else {
		echo "size is zero!!!\n";
	}
	echo dumpData($plt_thicknessdata, $axes);
####	#
	$keys = array_keys($alscount);
	echo "key     alsthickness hl thickness <br>";
	foreach ($keys as $key) {
		if (array_key_exists($key,$hlthick)) {
			echo $key . " " . $alsthick[$key] . " " . $hlthick[$key] . "<br>";
			$p = array('hl_thickness' => $hlthick[$key], 'als_thickness' => $alsthick[$key]) ;
			$plt_thicknessdata2[]  = $p;
		}
	}

####
	exit;
}

if ($viewsql) {
	$display_x = 'hl_thickness';
	$display_y = 'als_thickness';
	$axes = array($display_x,$display_y);
	if ($histogram == true && $histaxis == 'x') 
		$axes = array($display_y,$display_x);
	$dbemgraph= new dbemgraph($plt_thicknessdata, $axes[0], $axes[1]);
	$dbemgraph->lineplot=False;
	$dbemgraph->title="Predicted vs Measured Ice Thickness";
	$dbemgraph->yaxistitle=$axes[1];
	$dbemgraph->xaxistitle=$axes[0];
	
#	$width = 700;
#	$height = 500;
	$dbemgraph->dim($width,$height);
	$dbemgraph->graph();
	exit;
}

$display_x = 'hl_thickness';
$display_y = 'als_thickness';
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph= new dbemgraph($plt_thicknessdata, $axes[0], $axes[1]);
$dbemgraph->lineplot=False;
$dbemgraph->title="Predicted vs Measured Ice Thickness";
$dbemgraph->yaxistitle=$axes[1];
$dbemgraph->xaxistitle=$axes[0];

$width = 500;
$height = 300;
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
