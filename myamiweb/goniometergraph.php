<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include ("inc/jpgraph.php");
include ("inc/jpgraph_utils.inc");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
require ("inc/leginon.inc");

$Id=$_GET[Id];

$goniometer = $leginondata->getGoniometerModel($Id);
while(list($k, $v) = each($goniometer)) {
	if (eregi("^ARRAY\|a", $k))
		$A[] = $v;
	if (eregi("^ARRAY\|b", $k))
		$B[] = $v;
	if ($k=="period")
		$T = $v;
	if ($k=="axis")
		$axis = $v;
	if ($k=="label")
		$label = $v;
}
$sx = array();
$sy = array();
if ($measurements = $leginondata->getMeasurements($label, $axis))
	foreach($measurements as $m) {
		$sx[]=$m[$axis];
		$sy[]=$m[norm];
	}

$K = 2*M_PI/$T;
$x = '$x';

$serie[0]=1;
for ($n=0; $n<count($A); $n++)
	$serie[] = "$A[$n]*cos(".($n+1)."*$K*$x) + $B[$n]*sin(".($n+1)."*$K*$x)";
$serie_str = implode(" + ",$serie);

$f = new FuncGenerator($serie_str);
list($xdata,$ydata) = $f->E(-0.00001,0.0004,1000);



// Setup the basic graph
$graph = new Graph(850,500,"auto");
$graph->SetScale("linlin");
//$graph->SetShadow();
$graph->img->SetMargin(5,10,60,9);	
$graph->SetBox(true,'lightgreen',1);	
$graph->SetMarginColor('black');
$graph->SetColor('black');

// ... and titles
$graph->title->Set('Goniometer '.$axis.' '.$label);
$graph->title->SetFont(FF_FONT1,FS_BOLD);
$graph->title->SetColor('lightgreen');
$graph->subtitle->SetFont(FF_FONT1,FS_NORMAL);
$graph->subtitle->SetColor('lightgreen');

$graph->xgrid->Show();
$graph->xgrid->SetColor('darkgreen');
$graph->ygrid->SetColor('darkgreen');

$graph->yaxis->SetPos(0);
$graph->yaxis->SetWeight(2);
$graph->yaxis->HideZeroLabel();
$graph->yaxis->SetFont(FF_FONT1,FS_BOLD);
$graph->yaxis->SetColor('lightgreen','lightgreen');
$graph->yaxis->HideTicks(true,true);
$graph->yaxis->HideFirstLastLabel();

$graph->xaxis->SetWeight(2);
$graph->xaxis->HideZeroLabel();
$graph->xaxis->HideFirstLastLabel();
$graph->xaxis->SetFont(FF_FONT1,FS_BOLD);
$graph->xaxis->SetColor('lightgreen','lightgreen');
$graph->xaxis->SetTextLabelInterval(2);

$lp1 = new LinePlot($ydata,$xdata);
$lp1->SetColor('blue');
$lp1->SetWeight(1);

$graph->Add($lp1);

if ($sy && $sy) {
	$sp1 = new ScatterPlot($sy,$sx);
	$sp1->mark->SetType(MARK_CIRCLE);
	$sp1->mark->SetColor('red');
	$sp1->mark->SetWidth(4);
	$graph->Add($sp1);
}

$graph->Stroke();

?>


