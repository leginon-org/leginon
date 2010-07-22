<?php

require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/leginon.inc";
require "inc/image.inc";

$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$histogram = ($_GET['hg']==1) ? true : false;
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];


//query order reversed so that sql dump shows the all autofocus results

$data3 = $leginondata->getFocusResultData($sessionId, 'both','all','bad');
$data2 = $leginondata->getFocusResultData($sessionId, 'Stage Z','all','ok');
$data1 = $leginondata->getFocusResultData($sessionId, 'both','all','ok');

if(empty($data3) || empty($data2) || empty($data1))
	exit();

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}


if ($viewdata) {
	$keys = array("timestamp", "filename", "imageId", "targetId", "defocus",
		"stigx", "stigy", "min", "drift","status","method");
	echo dumpData($data1, $keys);
	exit;
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}
$scale = 1e6;
if ($data1)
foreach ($data1 as $foc) {
	if ($foc['defocus']) {
		$data1x[] = $foc['unix_timestamp'];
		$data1y[] = $foc['defocus']*$scale;
	}
}

if ($data2)
foreach ($data2 as $foc) {
	if ($foc['defocus']) {
		$data2x[] = $foc['unix_timestamp'];
		$data2y[] = $foc['defocus']*$scale;
	}
}

if ($data3)
foreach ($data3 as $foc) {
	if ($foc['defocus']) {
		$data3x[] = $foc['unix_timestamp']-0.01;
		$data3y[] = 0.0;
		$data3x[] = $foc['unix_timestamp'];
		$data3y[] = max($data1y);
		$data3x[] = $foc['unix_timestamp']+0.01;
		$data3y[] = 0.0;
	}
} else {
		$data3x[] = $data1x[0];
		$data3y[] = 0.0;
}

$width = $_GET['w'];
$height = $_GET['h'];

if (!$data1x && !$data1y) {
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
		$graph->title->Set("Measured Defocus");
		$graph->xaxis->title->Set("defocus (micrometer)");
		$graph->yaxis->title->Set("Frequency");

	} else {

		$graph->title->Set('Date: '.Date('Y-m-d',$data1x[0]));
		$graph->SetAlphaBlending();
		$graph->SetScale("linlin"); 
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(30);
		$graph->xaxis->SetPos("min");
		$graph->xaxis->title->Set("time");
		$graph->yaxis->title->Set("defocus (um)");

		$sp1 = new ScatterPlot($data1y,$data1x);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$sp1->SetLegend('corrected by defocus');
		$graph->Add($sp1);

		$sp2 = new ScatterPlot($data2y,$data2x);
		$sp2->mark->SetType(MARK_FILLEDCIRCLE);
		$sp2->mark->SetColor('blue');
		$sp2->mark->SetWidth(4);
		$sp2->SetLegend('corrected by stage Z');
		$graph->Add($sp2);

		$p1 = new LinePlot($data1y,$data1x);
		$p1->SetColor("blue");
		$graph->Add($p1);

		$p2 = new LinePlot($data3y,$data3x);
		$p2->SetColor("red");
		$p2->SetLegend('failed autofocus');
		$graph->Add($p2);

// Legend
		$graph->legend->SetLayout(LEGEND_HOR);
		$graph->legend->SetColumns(3);
		$graph->legend->Pos(0.5,0.95,'center','center');
	}
	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>
