<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include ("inc/jpgraph.php");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
include ("inc/jpgraph_bar.php");
include ("inc/histogram.inc");
include ("inc/image.inc");
require ("inc/leginon.inc");

$defaultId= 1445;
$defaultpreset='hl';
$histogram = ($_GET[hg]==1) ? true : false;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET[vs];
$stdev = ($_GET['stdev']==1) ? true : false;
if ($stdev) {
	$data_name='stdev';
} else {
	$data_name='mean';
}

$thicknessdata = $leginondata->getImageStats($sessionId, $preset);
foreach($thicknessdata as $t) {
	$datax[] = $t['unix_timestamp'];
	$datay[] = $t[$data_name];
}
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
if ($viewdata) {
	$keys = array("timestamp", $data_name);
	echo dumpData($thicknessdata, $keys);
	exit;
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}

$width = $_GET['w'];
$height = $_GET['h'];
if (!$datay) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {
		$graph = new Graph(600,400,"auto");    
	if ($histogram) {
		$histogram = new histogram($datay);
		$histogram->setBarsNumber(50);
		$rdata = $histogram->getData();

		$rdatax = $rdata['x'];
		$rdatay = $rdata['y'];

		$graph->SetScale("linlin");

		$graph->img->SetMargin(40,30,20,40);

		$bplot = new BarPlot($rdatay, $rdatax);
		$graph->Add($bplot);

		$graph->title->Set("Pixel $data_name histogram for preset $preset");
		$graph->xaxis->title->Set("pixel $data_name");

		$graph->yaxis->title->Set("Frequency");
	} else {
		$graph->title->Set("Pixel $data_name for preset $preset");
		$graph->SetAlphaBlending();
		$graph->SetScale("intlin",0,'auto'); //,$datax[0],$datax[$n-1]);
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(25);
		$graph->xaxis->title->Set("time");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->title->Set("pixel $data_name");

		$sp1 = new ScatterPlot($datay,$datax);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$graph->Add($sp1);
		$p1 = new LinePlot($datay,$datax);
	}
	$source = $graph->Stroke(_IMG_HANDLER);
}

	resample($source, $width, $height);

?>
