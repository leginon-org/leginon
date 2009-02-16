<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/jpgraph.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

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
	$data[$a['partnum']] = $a[$type];
}

$width = $_GET['w'];
$height = $_GET['h'];
if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width, $height);
} else {
	$graph = new Graph(640,480,"auto");    
	$graph->img->SetMargin(60,30,40,50);
	$histogram = new histogram($data);
	$histogram->setBarsNumber(50);
	$rdata = $histogram->getData();
	$rdatax = $rdata['x'];
	$rdatay = $rdata['y'];
	
	$graph->SetScale("linlin");
               
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
