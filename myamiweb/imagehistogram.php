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
require "inc/leginon.inc";
require "inc/image.inc";

if(!$imgId=$_GET['id']) {
	$img = blankimage(200,60);
	header("Content-type: image/x-png");
	imagepng($img);
	imagedestroy($img);
	exit;
}
$preset=$_GET['preset'];
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;
$size = $_GET['s'];
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$binning=$_GET['binning']) 
	$binning = 'auto';

$params = array (
	'size'=> $size,
	'minpix' => $minpix,
	'maxpix' => $maxpix,
	'filter' => $filter,
	'fft' => $fft,
	'binning' => $binning
);

// --- find image
$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];

$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilenameFromId($imgId);
$fileinfo = mrcinfo($path.$filename);
$minpix = $fileinfo[amin];
$maxpix = $fileinfo[amax];
$nb_bars = 60;
$scalefactor = .5;
$binning=4;
$interval = ($maxpix - $minpix) / $nb_bars;
if ($_GET['tf']==1) {
	$img = getImage($sessionId, $imgId, $preset, $params);
	$data = imagehistogram($img, $nb_bars);
	imagedestroy($img);
	for($k=0; $k<count($data); $k++) {
		$datax[] = $minpix+$k*$interval;
	}
} else {
	$data = imagehistogramfrommrc($path.$filename, $nb_bars);
	$datax = array_keys($data);
}
	$datay = array_values($data);

if ($_GET['rp']==1) {
	$graph = new Graph(256,256);
	$graph->title->Set("Histogram");
	$graph->SetMargin(50,40,20,20);
} else {
	$graph = new Graph(200,60);
	$graph->SetFrame(false);
	$graph->SetMargin(0,0,0,0);
}

$graph->SetScale("linlin");
$bplot = new BarPlot($datay, $datax);
$bplot->SetFillColor('black');
$graph->Add($bplot);
$graph->yaxis->Hide();
$graph->xaxis->HideFirstLastLabel();
$graph->xaxis->HideLastTickLabel();
$graph->xaxis->SetTextLabelInterval(2);
$source = $graph->Stroke(_IMG_HANDLER);
header("Content-type: image/x-png");
imagepng($source);
imagedestroy($source);
?>


