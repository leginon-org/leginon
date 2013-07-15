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

define (PARTICLE_DB, $_SESSION['processingdb']);

$reconRunId= $_GET['recon'];
$multiModelReconRunId= $_GET['multimodelreconid'];
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$width = $_GET['w'] ? (int) $_GET['w'] : 800 ;
$height = $_GET['h'] ? (int) $_GET['h'] : (int) $width*0.75 ;

$particle = new particledata();

//If summary is true, get only the data with the best confidence
if ($multiModelReconRunId) {
	$eulerinfo = $particle->getEulerJumpsMM($multiModelReconRunId);
} else {
	$eulerinfo = $particle->getEulerJumps($reconRunId);
}

foreach($eulerinfo as $e) {
	$data[$e['DEF_id']] = $e['median'];
}

//print_r($data);

if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width, $height);
} else {
	$graph = new Graph($width,$height,"auto");    

	$graph->img->SetMargin(60,30,40,50);
	$histogram = new histogram($data);
	$histogram->minval = 0.0;
	//$histogram->setInterval(1.0);
	$histogram->setBarsNumber(80);
	$rdata = $histogram->getData();
	$rdatax = $rdata['x'];
	$rdatay = $rdata['y'];

	//$graph->SetScale("linlin",0.0,1.0,$sx[0],$last);
	$graph->SetScale("linlin", 0.0, $histogram->idealmaxy, 0.0, $histogram->idealmaxx);
               
	$bplot = new BarPlot($rdatay, $rdatax);
	$graph->Add($bplot);

	$graph->title->Set("Euler Jump Histogram");
	$graph->xaxis->title->Set("Median Euler Jump");
	$graph->xaxis->SetLabelFormat('%d');
	$graph->yaxis->SetLabelFormat('%d');
	$graph->yaxis->title->Set("Frequency");

	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>
