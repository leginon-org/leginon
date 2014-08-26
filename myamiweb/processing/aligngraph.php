<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/jpgraph.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";

define ('PARTICLE_DB', $_SESSION['processingdb']);

$alignid= $_GET['alignid'];
$type= $_GET['type'] ? $_GET['type'] : 'score';
$width= $_GET['w'] ? $_GET['w'] : 640;
$height= $_GET['h'] ? $_GET['h'] : (int) $width*3/4.0;
$histogram = true;
$viewdata = false;

$particle = new particledata();

//If summary is true, get only the data with the best confidence
$aligninfo = $particle->getAlignParticleData($alignid);

function scicallback($a) {
	return format_sci_number($a,3,true);
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}

foreach($aligninfo as $a) {
	$data[] = $a[$type];
}

$width = $_GET['w'];
$height = $_GET['h'];
if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width, $height);
} else {
	$histogram = new histogram($data);
	$histogram->setBarsNumber(70);
	if ($type == 'spread')
		$histogram->maxval = 1.0;
	$rdata = $histogram->getData();
	$rdatax = $rdata['x'];
	$rdatay = $rdata['y'];

	$graph = new Graph(640,480,"auto");    
	$graph->img->SetMargin(60,30,40,50);

	$graph->SetScale("linlin", 0.0, $histogram->idealmaxy, $histogram->idealminx, $histogram->idealmaxx);
	//$graph->SetScale("linlin"); 
      
	$bplot = new BarPlot($rdatay, $rdatax);
	$graph->Add($bplot);
	$graph->title->Set("Alignment '$type' Histogram");
	$graph->xaxis->title->Set("$f");
	$graph->xaxis->SetTextLabelInterval(3);
	$graph->xaxis->SetLabelFormatCallback('scicallback');
	$graph->yaxis->title->Set("Frequency");
	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>
