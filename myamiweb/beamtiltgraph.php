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

$defaultId= 7623;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET[vs];

// :TODO: the conversion here is hardcoded for now.  Need to use the
// database query result eventually.
$thicknessdata = $leginondata->getBeamTiltMeasurements($sessionId);
foreach($thicknessdata as $t) {
	if ($t['mean defocus'] > 0.0000003) {
		$datax[] = $t['unix_timestamp'];
		$datay[] = $t['btiltx']/232;
		$datay2[] = $t['btilty']/99.12;
		$datay3[] = $t['mean defocus']*1000;
	}
}

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
if ($viewdata) {
	$keys = array("unix_timestamp", "btiltx");
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
	$graph->SetMargin(50,40,30,70);    
	if ($histogram) {
		$histogram = new histogram($datay);
		$histogram->setBarsNumber(50);
		$rdata = $histogram->getData();
		$rdatax = $rdata['x'];
		$rdatay = $rdata['y'];

		$graph->SetScale("linlin");
		$bplot = new BarPlot($rdatay, $rdatax);
		$graph->Add($bplot);
		$graph->title->Set("Drift");
		$graph->xaxis->title->Set("drift rate pix/s");
		$graph->yaxis->title->Set("Frequency");

	} else {
		$graph->title->Set('Date: '.Date('Y-m-d',$datax[0]));
		$graph->SetAlphaBlending();
		$graph->SetScale("intlin",0,'auto'); 
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(30);
		$graph->xaxis->title->Set("time");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->title->Set("drift rate pix/s");

		$sp1 = new ScatterPlot($datay3,$datax);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$graph->Add($sp1);
		$p1 = new LinePlot($datay,$datax);
		$p1->SetColor("blue");
		$graph->Add($p1);
		$p2 = new LinePlot($datay2,$datax);
		$p2->SetColor("red");
		$graph->Add($p2);

	}
	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
