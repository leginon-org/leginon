<?php

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "../inc/jpgraph.php";
require "../inc/jpgraph_line.php";
require "../inc/jpgraph_scatter.php";
require "../inc/jpgraph_bar.php";
require "../inc/histogram.inc";
require "../inc/image.inc";


$stackid = ($_GET['sId']);

$minx = ($_GET['minx']);
$miny = ($_GET['miny']);
$maxx = ($_GET['maxx']);
$maxy = ($_GET['maxy']);

if (!is_null($minx)) {
	$linex[] = $minx;
	$linex[] = $maxx;
	$liney[] = $miny;
	$liney[] = $maxy;
}

$particle = new particledata();

$stackparts = $particle->getStackParticles($stackid);

$minstdev = 100000;
foreach ($stackparts as $part) {
	$datax[] = $part['mean'];
	if ($part['stdev'] < $minstdev)
		$minstdev = $part['stdev'];
	$datay[] = $part['stdev'];
}

if (!is_null($minx)) {
	$dlinex[] = $minx;
	$dlinex[] = $minx;
	$dliney[] = $minstdev*0.9;
	$dliney[] = $miny;
}

if (!is_null($maxx)) {
	$ulinex[] = $maxx;
	$ulinex[] = $maxx;
	$uliney[] = $minstdev*0.9;
	$uliney[] = $maxy;
}

$width = $_GET['w'];
$height = $_GET['h'];

if (is_null($datax[0])) {
#	$width = 12;
#	$height = 12;
#	$source = blankimage($width,$height);
} else {

	$graph = new Graph(600,400,"auto");    
	$graph->SetMargin(50,40,30,70);    

#	$graph->title->Set('Date: '.Date('Y-m-d',$datax[0]));
	$graph->SetAlphaBlending();
	$graph->SetScale("intlin",0,'auto'); 
#	$graph->xaxis->SetLabelFormatCallback('TimeCallback');
#	$graph->xaxis->SetLabelAngle(90);
	$graph->xaxis->SetTitlemargin(30);
	$graph->xaxis->title->Set("Mean");
	$graph->yaxis->SetTitlemargin(35);
	$graph->yaxis->title->Set("Standard Deviation");

	$sp1 = new ScatterPlot($datay,$datax);
	$sp1->mark->SetType(MARK_CIRCLE);
	$sp1->mark->SetColor('blue');
	$sp1->mark->SetWidth(2);
	$graph->Add($sp1);

	if (!is_null($liney[0])) {
		$p1 = new LinePlot($liney,$linex);
		$p1->SetColor("green");
		$p1->SetLineWeight(30);
		$graph->Add($p1);
		$p2 = new LinePlot($uliney,$ulinex);
		$p2->SetLineWeight(30);
		$p2->SetColor("green");
		$graph->Add($p2);
		$p3 = new LinePlot($dliney,$dlinex);
		$p3->SetColor("green");
		$p3->SetLineWeight(30);
		$graph->Add($p3);
	}

	$source = $graph->Stroke(_IMG_HANDLER);
	
	resample($source, $width, $height);
	
}



#print_r($stackparts);

?> 
