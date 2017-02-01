<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_utils.inc.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/leginon.inc";

$Id=$_GET['Id'];

$goniometer = $leginondata->getGoniometerModel($Id);
while(list($k, $v) = each($goniometer)) {
	// --- convert NULL value to 0
	if (!$v)
			$v=0;
	if (preg_match("%^ARRAY\|a%i", $k))
		$A[] = $v;
	if (preg_match("%^ARRAY\|b%i", $k))
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
if ($measurements = $leginondata->getMeasurements($label, $axis, $Id))
	foreach($measurements as $m) {
		$sx[]=$m[$axis];
		$sy[]=$m['norm'];
	}
$sxvalues = array_values($sx);
sort($sxvalues);
$sxmin = $sxvalues[0];
$sxmax = $sxvalues[count($sxvalues)-1];

$K = 2*M_PI/$T;
$x = '$x';

$serie[0]=1;
for ($n=0; $n<count($A); $n++)
	$serie[] = "$A[$n]*cos(".($n+1)."*$K*$x) + $B[$n]*sin(".($n+1)."*$K*$x)";
$serie_str = implode(" + ",$serie);

$f = new FuncGenerator($serie_str);
list($xdata,$ydata) = $f->E($sxmin,$sxmax,1000);



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

if ( $sxmin <=0 && $sxmax >=0) {
	$graph->yaxis->SetPos(0);
	$graph->yaxis->SetWeight(2);
} else {
	$graph->yaxis->SetPos($sxmin+0.05*($sxmax-$sxmin));
	$graph->yaxis->HideLine();
}
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


