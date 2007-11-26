<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";
require_once "inc/leginon.inc";

$defaultId= 1445;
$defaultpreset='hl';
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET[vs];

$thicknessdata = $leginondata->getIceThickness($sessionId, $preset);
foreach($thicknessdata as $t) {
	$data[] = $t['thickness-mean'];
}
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
if ($viewdata) {
	$keys = array("timestamp", "thickness-mean");
	echo dumpData($thicknessdata, $keys);
	exit;
}

$width = $_GET['w'];
$height = $_GET['h'];
if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {
	$histogram = new histogram($data);
	$histogram->setBarsNumber(50);
	$rdata = $histogram->getData();

	$rdatax = $rdata['x'];
	$rdatay = $rdata['y'];

	$graph = new Graph(600,400,"auto");    
	$graph->SetScale("linlin");

	$graph->img->SetMargin(40,30,20,40);

	$bplot = new BarPlot($rdatay, $rdatax);
	$graph->Add($bplot);

	$graph->title->Set("Ice Thickness histogram for preset $preset");
	$graph->xaxis->title->Set("ice thickness");
	$graph->yaxis->title->Set("Frequency");
	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>
