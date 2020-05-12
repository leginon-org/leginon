<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "inc/leginon.inc";
require_once "inc/graph.inc";
#require_once "inc/stats.inc";

// Function to calculate  mean
function mean($array) {
	return array_sum($array)/count($array);
}
// Function to calculate square of value - mean
function sd_square($x, $mean) { return pow($x - $mean,2); }
// Function to calculate standard deviation (uses sd_square)    
function sd($array) {
   // square root of sum of squares devided by N-1
	return sqrt(array_sum(array_map("sd_square", $array, array_fill(0,count($array), (array_sum($array) / count($array)) ) ) ) / (count($array)-1) );
}

$defaultId= 4828;
//$defaultpreset='en';
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
//$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET['vs'];

$histogram= true;
$truncated= ($_GET['truncate']) ? $_GET['truncate'] : false;
$histaxis=($_GET['haxis']) ? $_GET['haxis'] : 'y';
$width=$_GET['w'];
$height=$_GET['h'];
$thicknessdata = $leginondata->getZeroLossIceThickness($sessionId);

foreach($thicknessdata as $t) {
	if ( !preg_match('/-[a-z](\.mrc)?$/',$t['filename'] ) and ( !preg_match('/-(DW|td)(\.mrc)?$/',$t['filename']))) {
		$data[] = $t['thickness'];
		$filtered_thicknessdata[] = $t;
	}
}
$mean = mean($data);

if (count($data) >1) {
	$sd = sd($data);
	$limit = 3 * $sd;  //truncate to mean +/- 3 sd if desired
}

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
if ($viewdata) {
	$keys = array("unix_timestamp", "filename", "slit mean", "no slit mean", "thickness");
	echo dumpData($filtered_thicknessdata, $keys);
	exit;
}

$display_x = 'unix_timestamp';
$display_y = 'thickness';
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
if ($truncated != true && count($data) >1) {
	$dbemgraph= new dbemgraph($filtered_thicknessdata, $axes[0], $axes[1]);
}
else {
	foreach($filtered_thicknessdata as $t) {
		if (abs($t['thickness'] - $mean) <= $limit) {$truncateddata[] = $t;}
	}
	$dbemgraph= new dbemgraph($truncateddata, $axes[0], $axes[1]);
}
$dbemgraph->lineplot=False;
$dbemgraph->title="Ice Thickness using zero loss peak";
$dbemgraph->yaxistitle="Thickness /nm";

if ($viewdata) {
	$keys = array("unix_timestamp", "thickness");
	echo dumpData($filtered_thicknessdata, $keys);
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$dbemgraph->scalex(1e-0);
$dbemgraph->scaley(1e-0);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();


?>
