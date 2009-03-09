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

$file=$_GET['file'];
$width=$_GET['width'];
$height=$_GET['height'];
$nomargin=$_GET['nomargin'];

if (!$width || !$height){
	$width=800;
	$height=600;
}

$data = file($file);

$sx = array();
$sy = array();
$sr = array();
if (is_array($data))
	foreach ($data as $line) {
		$line=trim($line);
		list($x,$a,$r,$y)=split("[\t ]+",$line);
		$sr[]=$r;
		$sx[]=$x;
		$y=floatval($y);
		$sy[]=log($y);
#		echo "$x, $y<br>\n";
	}
// Setup the basic graph
$graph = new Graph($width,$height,"auto");
//$graph->SetScale("linlin");

$last=end($sx);
$graph->SetAlphaBlending();
if (!$nomargin) {
  $graph->SetScale("linlin",0,'auto',$sx[0],$last);
  $graph->img->SetMargin(50,40, 30,70);	
	$graph->xaxis->SetTitlemargin(30);
	$graph->xaxis->SetTickLabels($sr);
	$graph->yaxis->SetTitlemargin(35);
}
else {
  $graph->SetScale("intlin",0,'auto',$sx[0],$last);
  $graph->img->SetMargin(2,4,4,4);	
	$graph->ygrid->Show(false,false);
	$graph->xgrid->Show(false,false);
	$graph->xaxis->Hide(true);
}  

$lp1 = new LinePlot($sy,$sx);
$lp1->SetColor('blue');
$lp1->SetWeight(1);

$graph->Add($lp1);

$graph->Stroke();

?>
