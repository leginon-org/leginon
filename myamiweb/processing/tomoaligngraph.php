<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";

define (PARTICLE_DB, $_SESSION['processingdb']);

$alignerid = ($_GET['aId']);

$particle = new particledata();
$refinedata = $particle->getProtomoAlignmentInfo($alignerid);
if ($_GET['ref']) {
	$refnum = $_GET['ref'];
} else {
	$refnum = NULL;
}
$plotbox = $_GET['box'];
if ($_GET['type']) {
	$type = $_GET['type'];
} else {
	$type = 'rot';
}
if ($_GET['minx']) {
	$minx = $_GET['minx'];
} else {
	$minx = 0;
}
if ($_GET['maxx']) {
	$maxx = $_GET['maxx'];
} else {
	$maxx = count($refinedata) - 1;
}
$width = $_GET['w'] ? (int) $_GET['w'] : 512 ;
$height = $_GET['h'] ? (int) $_GET['h'] : (int) $width*0.75 ;
//echo "$width,$height<br/>\n";

$keys = array('rot'=>'rotation','shiftx'=>'shift x','shifty'=>'shift y');
if ($height > 160) {
	$titles = array('rot'=>'Rotation (degrees)','shiftx'=>'X shift from center (pixels)','shifty'=>'Y shift from center (pixels)');
} else {
	$titles = array('rot'=>'Rotation (o)','shiftx'=>'X shift (pixels)','shifty'=>'Y shift (pixels)');
}
$key = $keys[$type];
$title = $titles[$type];
$miny = 100000;
$maxy = -100000;
foreach ($refinedata as $data) {
	$datax[] = $data['number'];
	$datay[] = $data[$key];
	$miny = ($miny > $data[$key] && $data['number'] <= $maxx && $data['number'] >= $minx) ? 
		$data[$key]:$miny;
	$maxy = ($maxy < $data[$key] && $data['number'] <= $maxx && $data['number'] >= $minx) ? 
		$data[$key]:$maxy;
}
// Draw a box showing the accepted range
if (!is_null($minx) && $plotbox) {
	$linex[] = $minx;
	$linex[] = $minx;
	$linex[] = $maxx;
	$linex[] = $maxx;
	$linex[] = $minx;
	$liney[] = $miny;
	$liney[] = $maxy;
	$liney[] = $maxy;
	$liney[] = $miny;
	$liney[] = $miny;
}


if (is_null($datax[0])) {
#if (true) {
	print_r($refinedata);
	echo "FAIL<br/>\n";
	#$width = 12;
	#$height = 12;
	#$source = blankimage($width,$height);
} else {
	if ($height > 160) {
		$xmargin = 20;
		$gxmargin = 60;
	} else {
		$xmargin = 10;
		$gxmargin = 40;
	}
	$graph = new Graph($width, $height, "auto");    
	$graph->SetMargin(60,10,10,$gxmargin);
	$graph->SetAlphaBlending();
	$graph->SetScale("intlin",'auto','auto'); 

	$graph->xaxis->SetTitlemargin($xmargin);
	$graph->xaxis->title->Set("sorted tilt number");
	$graph->yaxis->SetTitlemargin(40);
	$graph->xaxis->SetPos("min");
	$graph->yaxis->SetPos("min");
	$graph->yaxis->title->Set($title);

	$sp1 = new ScatterPlot($datay,$datax);
	$sp1->mark->SetType(MARK_CIRCLE);
	$sp1->mark->SetColor('blue');
	$sp1->mark->SetWidth(2);
	$graph->Add($sp1);
	if (!is_null($refnum)) {
		$sp2 = new ScatterPlot(array($datay[$refnum]),array($datax[$refnum]));
		$sp2->mark->SetType(MARK_FILLEDCIRCLE);
		$sp2->mark->SetColor('red');
		$sp2->mark->SetWidth(4);
		$graph->Add($sp2);
	}
	if (!is_null($liney[0]) && $plotbox) {
		$p3 = new LinePlot($liney,$linex);
		$p3->SetColor("green");
		$p3->SetLineWeight(30);
		$graph->Add($p3);
	}
	$graph->Stroke();
}



?> 
