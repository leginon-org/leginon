<?php

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/leginon.inc";
require_once "inc/image.inc";

$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$histogram = ($_GET['hg']==1) ? true : false;
$maxrate = $_GET['maxr'];
$minrate = $_GET['minr'];
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];

$result = $leginondata->getDriftDataFromSessionId($sessionId);
$driftdata = $result[0];
$unit = $result[1];
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

foreach ($driftdata as $drift) {
	$id = $drift['targetId'];
	$data[$id] = $drift;
}

if ($viewdata) {
	$keys = array("timestamp", "filename", "imageId", "targetId", "driftx",
		"drifty", "driftvalue", "interval", "rate");
	echo dumpData($data, $keys);
	exit;
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}

$ratescalefactor = 1.0;
if ($unit === 'Meters') {
	$ratescalefactor = 1e10;
	$unit = 'Angstrom';
}
if ($data)
foreach ($data as $drift) {
	if ($maxrate && $drift['rate'] * $ratescalefactor > $maxrate)
		continue;
	$datax[] = $drift['unix_timestamp'];
	$datay[] = $drift['rate'] * $ratescalefactor;
}
$width = $_GET['w'];
$height = $_GET['h'];
if (!$datax && !$datay) {
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
		$graph->xaxis->title->Set("drift rate ".$unit."/s");
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
		$graph->yaxis->title->Set("drift rate ".$unit."/s");

		$sp1 = new ScatterPlot($datay,$datax);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$graph->Add($sp1);
		$p1 = new LinePlot($datay,$datax);
		$p1->SetColor("blue");
		$graph->Add($p1);

	}
	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
