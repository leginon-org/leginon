<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";
require_once "inc/leginon.inc";

$defaultId= 1445;
$defaultpreset='hl';
$histogram = ($_GET['hg']==1) ? true : false;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$preset = ($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET['vs'];
$data_name='acquisitiontime';

$timingdata = $leginondata->getTiming($sessionId, $preset);
foreach($timingdata as $t) {
	$datax[] = $t['unix_timestamp'];
	$datay[] = $t[$data_name];
}
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
if ($viewdata) {
	$keys = array("timestamp", "filename", $data_name);
	echo dumpData($timingdata, $keys);
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

		$graph->title->Set("$data_name histogram for preset $preset");
		$graph->xaxis->title->Set("$data_name");

		$graph->yaxis->title->Set("Frequency");
	} else {
		$graph->title->Set("$data_name for preset $preset");
		$graph->SetAlphaBlending();
		$graph->SetScale("intlin",0,'auto'); //,$datax[0],$datax[$n-1]);
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(25);
		$graph->xaxis->title->Set("time");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->title->Set("$data_name");

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
