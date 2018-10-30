<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
include_once "inc/project.inc";
include_once "inc/leginon.inc";
require_once "inc/graph.inc";
require_once ("processing/inc/particledata.inc");


$defaultId=1445;
$defaultpreset='hl';
$histogram=($_GET['hg']==1) ? true : false;
// named as expId ensures processing database is set.
$sessionId=($_GET['expId']) ? $_GET['expId'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata=($_GET['vdata']==1) ? true : false;
$viewsql=$_GET['vs'];
$width=$_GET['w'];
$height=$_GET['h'];
$topn=($_GET['top'] > 1 ) ? (int) $_GET['top'] : 1;
$offsetn=($_GET['offset']) ? (int) $_GET['offset'] : 0;
$data_name= ( $topn == 1 ) ? 'maximal movemnet':'top '.$topn.' movement average';

//function in project.inc that sets $_SESSION
//setDatabase($sessionId);

$imagestatsdata = $leginondata->getImageStats($sessionId, $preset);

$particle=new particledata;

$data = array();
foreach ($imagestatsdata as $imagestats ) {
	$imageId = $imagestats['imageId'];
	$aligned_imgId = $particle->getRecentAlignedImage($imageId);
	$imageinfo = $leginondata->getImageInfo($aligned_imgId);
	$presets = $leginondata->getPresets($aligned_imgId, array('pixelsize'));
	// pixelsize from getPresets is camera pixel ?
	$pixelsize = $presets['pixelsize']*$imageinfo['binning'];
	$shift_data = $particle->getAlignLogShiftFromDDAlignedImageId($aligned_imgId,$pixelsize*1e10);
	if (is_array($shift_data) && count($shift_data) > 0 ) {
		$shift_distances = $particle->getShiftDistancesFromPositions($shift_data);
		// sorted from high to low
		rsort($shift_distances);
		if ( count($shift_distances) < $topn+$offsetn ) continue;
		$top_avg = array_sum(array_slice($shift_distances,$offsetn,$topn)) / $topn;
		$data[] = array('timestamp'=>$imagestats['timestamp'],'unix_timestamp'=>$imagestats['unix_timestamp'],$data_name=>$top_avg);
	}
}
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

$dbemgraph= new dbemgraph($data, 'unix_timestamp', $data_name);
$dbemgraph->lineplot=false;
$dbemgraph->baselineplot=true;
$dbemgraph->baselinevalue=1;
$dbemgraph->title="$data_name between frames for preset $preset";
$dbemgraph->yaxistitle="distance (Angstrom / frame)";
$dbemgraph->setScaleType("lin","log");
if ($viewdata) {
	$dbemgraph->dumpData(array('timestamp', $data_name));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}
$dbemgraph->dim($width,$height);
$dbemgraph->graph();
?>
