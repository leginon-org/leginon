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
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;

$thicknessdata = $leginondata->getIceThickness($sessionId, $preset);
foreach($thicknessdata as $t) {
	$data[] = $t['thickness-mean'];
}
if ($viewdata) {
		echo "<pre>";
		echo "timestamp	thickness-mean<br>";
	foreach($thicknessdata as $t) {
		echo $t['timestamp']."	".$t['thickness-mean']."\n";
	}
		echo "</pre>";
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
