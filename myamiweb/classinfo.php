<?php
/**
 *	The Leginon software is Copyright 2007 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display classification info for an iteration
 */

include ("inc/jpgraph.php");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
include ("inc/jpgraph_bar.php");
include ("inc/histogram.inc");
require ("inc/particledata.inc");
require ("inc/image.inc");
require_once ("inc/leginon.inc");

$refinement=$_GET['refinement'];
$width = $_GET['w'];
$height = $_GET['h'];

$particle = new particledata();
$numclasses=$particle->getNumClasses($refinement);
$eulers=$particle->getEulerIds($refinement);

foreach ($eulers as $eulerId){
        $euler=$particle->getEulerAngles($eulerId['eulers']);
	$numinclass=$particle->getNumInClass($refinement,$eulerId['eulers']);
	$data[]=$numinclass;
}

if (!$data) {
        $width = 12;
        $height = 12;
        $source = blankimage($width,$height);
} 
else {
	$graph = new Graph($width,$height,"auto");    
	$graph->SetScale("intlin",0,"auto",0,$numclasses);
	$graph->img->SetMargin(50,40,30,70);
	$graph->title->Set("Particle Distribution");
	$graph->xaxis->title->Set("class");

        $bplot = new BarPlot($data);    
	$graph->Add($bplot);

	$graph->Stroke();
}

?>