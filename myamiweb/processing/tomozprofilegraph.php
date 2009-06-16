<?php

require "../inc/jpgraph.php";
require "../inc/jpgraph_line.php";
require "../inc/jpgraph_scatter.php";
require "../inc/jpgraph_bar.php";
require "../inc/histogram.inc";
require "inc/particledata.inc";
require "inc/leginon.inc";
require "../inc/image.inc";
require "inc/project.inc";
require "inc/processing.inc";

$defaultId= 1;
$zprofilename = ($_GET['file']) ? $_GET['file'] : $defaultId;
$zcenter = ($_GET['center']) ? $_GET['center'] : 0;
$histogram = ($_GET['hg']==1) ? true : false;
$maxrate = $_GET['maxr'];
$minrate = $_GET['minr'];
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];

$particle = new particledata();
$profiledata = $particle->loadTomoZProfile($zprofilename);
$data = $profiledata[0];

$namearray = explode("/",$zprofilename);
$profilename = trim($namearray[count($namearray)-1]);
$subtomoid = 0 + substr($profilename,8,5);
if ($viewdata) {
	$keys = array("z", "profile");
	echo dumpData($data, $keys);
	exit;
}
$miny = 1e37;
$maxy = -1e37;
if ($data)
foreach ($data as $profile) {
	$datax[] = $profile['z'];
	$datay[] = $profile['profile'];
	$maxy = ($profile['profile'] > $maxy) ? $profile['profile'] : $maxy;
	$miny = ($profile['profile'] < $miny) ? $profile['profile'] : $miny;
}
$zdim = count($datay);
if ($zcenter) {
	$data1x = array($zcenter+$zdim/2-0.5,$zcenter+$zdim/2-0.5);
	$data1y = array($miny,$maxy);
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
		$graph->title->Set("Z Profile");
		$graph->xaxis->title->Set("z");
		$graph->yaxis->title->Set("intensity");

	} else {

		$graph->title->Set('Z profile of Subtomogram Id '.$subtomoid);
		$graph->SetAlphaBlending();
		$graph->SetScale("linlin",0,'auto'); 
		//$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(30);
		$graph->xaxis->title->Set("Z");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->title->Set("intensity");

//		$sp1 = new ScatterPlot($datay,$datax);
//		$sp1->mark->SetType(MARK_CIRCLE);
//		$sp1->mark->SetColor('red');
//		$sp1->mark->SetWidth(4);
//		$graph->Add($sp1);
#		$datax = array(0,1);
#		$datay = array(0,1);
		$p1 = new LinePlot($datay,$datax);
		$p1->SetColor("blue");
		$graph->Add($p1);
		$p2 = new LinePlot($data1y,$data1x);
		$p2->SetColor("red");
		$graph->Add($p2);

	}
	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
