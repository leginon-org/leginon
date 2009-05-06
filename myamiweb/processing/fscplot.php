<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include ("inc/particledata.inc");
include ("inc/jpgraph.php");
include ("inc/jpgraph_utils.inc");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
require ("inc/leginon.inc");
require "inc/project.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$fsc=$_GET['fscfile'];
$width=$_GET['width'];
$height=$_GET['height'];
$nomargin=$_GET['nomargin'];
$apix=$_GET['apix'];
$box=$_GET['box'];
$fscid=$_GET['fscid'];
$half=$_GET['half'];

if (!$width || !$height){
	$width=800;
	$height=600;
}

if (!$apix) $apix=1;
if (!$box) $box=100;

$sx = array();
$sy = array();

if ($fscid) {
	$particle=new particledata;
	$data = $particle->getFscFromRefinementDataId($fscid);
	foreach ($data as $line) {
		$sx[]=$line['pix'];
		$sy[]=$line['value'];
		$xpix[]=sprintf("%.2f",$box*$apix/$line['pix']);
	}
}

else {
	$data = file($fsc);
	if (is_array($data))
		foreach ($data as $line) {
			$line=rtrim($line);
			list($x,$sy[])=split("\t",$line);
			$sx[]=$x;
			// convert pixels to resolution in angstroms
			$res = $box*$apix/$x;
			$xpix[] = sprintf("%.2f",$res);
			// hack to not show everything
			if ($half && $res < $half/3.0)
				break;
		}
}

// Setup the basic graph
$graph = new Graph($width,$height,"auto");
//$graph->SetScale("linlin");

$last=end($sx);
$graph->SetAlphaBlending();

if (!$nomargin) {
	$graph->SetScale("linlin",0.0,1.0,$sx[0],$last);
	//Margin: Left, Right, Top, Bottom
	$graph->img->SetMargin(45, 10, 15, 80);	
	$graph->title->Set('Fourier Shell Correlation ');
	$graph->xaxis->SetTitlemargin(40);
	$graph->xaxis->title->Set("Resolution (A/pix)");
	$graph->yaxis->SetTitlemargin(30);
	$graph->yaxis->title->Set("Correlation");
	$graph->xaxis->SetTickLabels($xpix);
	$graph->xaxis->SetLabelAngle(90);
	$graph->AddLine(new PlotLine(HORIZONTAL,0.5,"black",1));
} else {
	$graph->SetScale("intlin",0.0,1.0,$sx[0],$last);
	$graph->img->SetMargin(2,4,4,4);	
	$graph->ygrid->Show(false,false);
	$graph->xgrid->Show(false,false);
	$graph->xaxis->Hide(true);
	//$graph->AddLine(new PlotLine(HORIZONTAL,0,"black",1));
}  

$lp1 = new LinePlot($sy,$sx);
$lp1->SetColor('blue');
$lp1->SetWeight(1);

$graph->Add($lp1);

$graph->Stroke();

?>
