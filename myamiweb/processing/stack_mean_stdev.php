<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";

define (PARTICLE_DB, $_SESSION['processingdb']);

$stackid = ($_GET['sId']);
$minx = ($_GET['minx']);
$miny = ($_GET['miny']);
$maxx = ($_GET['maxx']);
$maxy = ($_GET['maxy']);
$rev = ($_GET['rev']);

if (!is_null($minx)) {
	$linex[] = $minx;
	$linex[] = $maxx;
	$liney[] = $miny;
	$liney[] = $maxy;
}

$particle = new particledata();
$stackparts = $particle->getStackMeanAndStdev($stackid);
#print_r($stackparts[0])."<br/>\n";
$nump = count($stackparts);
$skipval = intval($nump/100000);
if ($skipval > 1) {
	$newstackparts = array();
	for($i = 0; $i<$nump; $i+=$skipval) {
		$newstackparts[]=$stackparts[$i];
	}
	$stackparts=$newstackparts;
}

$minstdev = 100000;
$maxstdev = 0;
foreach ($stackparts as $part) {
	$datax[] = $part['mean'];
	if ($part['stdev'] < $minstdev)
		$minstdev = $part['stdev'];
	if ($part['stdev'] > $maxstdev)
		$maxstdev = $part['stdev'];
	$datay[] = $part['stdev'];
}

if (!is_null($minx)) {
	$dlinex[] = $minx;
	$dlinex[] = $minx;
	$dliney[] = (!is_null($rev)) ? $maxstdev*1.02: $minstdev*0.9;
	$dliney[] = $miny;
}

if (!is_null($maxx)) {
	$ulinex[] = $maxx;
	$ulinex[] = $maxx;
	$uliney[] = (!is_null($rev)) ? $maxstdev*1.02: $minstdev*0.9;
	$uliney[] = $maxy;
}

$width = $_GET['w'] ? (int) $_GET['w'] : 512 ;
$height = $_GET['h'] ? (int) $_GET['h'] : (int) $width*0.75 ;
//echo "$width,$height<br/>\n";

if (is_null($datax[0])) {
	echo "FAIL<br/>\n";
	#$width = 12;
	#$height = 12;
	#$source = blankimage($width,$height);
} else {
	//echo "HERE<br/>\n";
	$graph = new Graph($width, $height, "auto");    
	$graph->SetMargin(60,10,10,60);
	$graph->SetAlphaBlending();
	$graph->SetScale("intlin",'auto','auto'); 

	$graph->xaxis->SetTitlemargin(30);
	$graph->xaxis->title->Set("Particle Mean Intensity");
	$graph->yaxis->SetTitlemargin(30);
	$graph->yaxis->title->Set("Standard Deviation of Particle Intensity");

	$sp1 = new ScatterPlot($datay,$datax);
	$sp1->mark->SetType(MARK_CIRCLE);
	$sp1->mark->SetColor('blue');
	$sp1->mark->SetWidth(1);
	$graph->Add($sp1);

	if (!is_null($liney[0])) {
		$p1 = new LinePlot($liney,$linex);
		$p1->SetColor("green");
		$p1->SetLineWeight(30);
		$graph->Add($p1);

		$p2 = new LinePlot($uliney,$ulinex);
		$p2->SetColor("green");
		$p2->SetLineWeight(30);
		$graph->Add($p2);

		$p3 = new LinePlot($dliney,$dlinex);
		$p3->SetColor("green");
		$p3->SetLineWeight(30);
		$graph->Add($p3);
	}
	$graph->Stroke();
}



?> 
