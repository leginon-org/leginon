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
require ("inc/leginon.inc");
include ("inc/image.inc");

if(!$imgId=$_GET[id]) {
	// --- if Id is not set, get the last acquired image from db
	$sessionId = $leginondata->getLastSessionId();
	$imgId = $leginondata->getLastFilenameId($sessionId);
}

$preset=$_GET[preset];

// --- find image
$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage[id];

$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilenameFromId($imgId);
$nb_bars = 50;
if ($_GET['tf']==1) {
	$img = imagecreatefrommrc($path.$filename);
	$data = imagehistogram($img, $nb_bars);
} else {
	$data = imagehistogramfrommrc($path.$filename, $nb_bars);
}
$datax = array_keys($data);
$datay = array_values($data);
$graph = new Graph(256,256,"auto");
$graph->SetMargin(50,40,30,30);

$graph->SetScale("linlin");
$bplot = new BarPlot($datay, $datax);
$graph->Add($bplot);
$graph->title->Set("Histogram");
$graph->xaxis->title->Set("");
$graph->yaxis->title->Set("");
$graph->xaxis->SetTextLabelInterval(2);
$source = $graph->Stroke(_IMG_HANDLER);
header("Content-type: image/x-png");
imagepng($source);
?>


