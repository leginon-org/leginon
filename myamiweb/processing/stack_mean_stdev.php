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

$particle = new particledata();

$stackparts = $particle->getStackParticles($stackid);

foreach ($stackparts as $part) {
	$datax[] = $part['mean'];
	$datay[] = $part['stdev'];
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

	$source = $graph->Stroke(_IMG_HANDLER);
	
	resample($source, $width, $height);
	
}



#print_r($stackparts);

?> 
