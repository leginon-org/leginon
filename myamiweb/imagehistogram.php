<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/leginon.inc";
require_once "inc/image.inc";
require_once "inc/imagerequest.inc";
require_once "inc/cachedb.inc";

if(!$imgId=$_GET['id']) {
	$img = blankimage(200,60);
	header("Content-type: image/png");
	imagepng($img);
	imagedestroy($img);
	exit;
}
$preset=$_GET['preset'];
//default works for jpg images
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;

// --- find image
$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];

$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];
$filepath = $leginondata->getFilenameFromId($imgId,true);
$imagerequest = new imageRequester();
$fileinfo = $imagerequest->requestInfo($filepath);
$range = 3;
// mrc or redux cache
if ($fileinfo && !$_GET['np'] && !$_GET['xp']) {
	// allow external overwrite
	$minpix = $fileinfo->amean - $range * $fileinfo->rms;
	$maxpix = $fileinfo->amean + $range * $fileinfo->rms;
}

$nb_bars = 40;
if ($_GET['tf']==1) {
	// first attempt to get histogram.  This will succeed if
	// file exists or is in redux cache
	$data = $imagerequest->requestHistdata($filepath, $nb_bars, $minpix, $maxpix);

	if (!$data) {
		// Try cached jpg image
		$sessioninfo = $leginondata->getSessionInfoFromImage($imgId);
		$sessionname = $sessioninfo['name'];
		$filepath = useCache($filepath, $sessionname, false, true);
		// cached jpg default min/max is 0/255.
		$data = $imagerequest->requestHistdata($filepath, $nb_bars, $minpix, $maxpix);
	}
}

//handle extra values
if ($_GET['tf']==1) {
	if (count($data[1]) > count($data[0])) array_pop($data[1]);
	$datax = $data[1];
	$datay = $data[0];
}

if (!is_array($data) || !is_array($data[1]) || count($data[1]) < 2) {
       // Display blank if not have enough data
       $img = blankimage(200,60);
       header("Content-type: image/png");
       imagepng($img);
       imagedestroy($img);
       exit;
}

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
header("Content-type: image/png");
imagepng($source);
imagedestroy($source);

?>
