<?php

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/leginon.inc";
require_once "inc/image.inc";

$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$histogram = ($_GET['hg']==1) ? true : false;
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];


$data0 = $leginondata->getFocusResultData($sessionId, 'Stage Z','all','ok');
if(empty($data0))
	exit();

// show only the last Stage Z corrected result per parent image
$data1 = array();
$imgids = array();
for ($i = count($data0); $i >= 0; $i--) {
	$imgId_str = $data0[$i]['imageId'];
	if (!is_null($imgId_str) && !in_array($imgId_str,$imgids)) {
		$data1[]=$data0[$i];
		$imgids[] = $imgId_str;
	}
}
if(empty($data1))
	exit();

$positions = array();
$zmax = -1.0;
$zmin = 1.0;
foreach($data1 as $data) {
	$focId = $data['foc_resultId'];
	if (empty($focId)) continue;
	$position = $leginondata->getStagePositionFromScopeReference($focId,'FocuserResultData');
	$position2 = $leginondata->getStagePositionFromScopeReference($data['imageId'],'AcquisitionImageData');
	//Not sure whether should add defocus correction value to ScopeEMData reference
	//Or not. Not to use for now.
	//$position['stage_z'] += $data['defocus'];
	$position['defocus'] = $data['defocus'];
	$position['imageId'] = $data['imageId'];
	$position['unix_timestamp'] = $data['unix_timestamp'];
	$zmax = ($position['stage_z'] > $zmax) ? $position['stage_z']:$zmax;
	$zmin = ($position['stage_z'] < $zmin) ? $position['stage_z']:$zmin;
	$positions[] = $position;
}

if ($viewdata) {
	$keys = array("stage_x","stage_y","stage_z","defocus","imageId");
	echo dumpData($positions, $keys);
	exit;
}

$scale = 1e6;

if (!empty($positions)) {
	$data1x = array();
	$data1y = array();
	$data1z = array();
  // Gray-scale color mapping of the stage z values
	for ($i = 0; $i < 256; $i++) {
		$data1z[$i] = array();
	}
	$zscale = ($zmax-$zmin > 0) ? 1/($zmax-$zmin):$scale;
	$zscale *= 255;
	foreach ($positions as $p) {
		$zindex = (int) (($p['stage_z']-$zmin)*$zscale);
		$data1x[$zindex][] = $p['stage_x']*$scale;
		$data1y[$zindex][] = $p['stage_y']*$scale;
	}
}

$width = $_GET['w'];
$height = $_GET['h'];
$sp = array();

if (!$data1x && !$data1y) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {

	$graph = new Graph(600,600,"auto");    
	$graph->SetMargin(50,40,30,70);    

	$graph->title->Set('Grid Height Map: black-'.(int) ($zmin*$scale).' white-'.(int) ($zmax*$scale).' um');
	$graph->SetAlphaBlending();
	$graph->SetColor(array(100,0,0));
	$graph->SetScale("linlin",-1000,1000,-1000,1000); 
	$graph->xaxis->SetTitlemargin(30);
	$graph->xaxis->SetPos(-1000);
	$graph->xaxis->title->Set("x (um)");
	$graph->yaxis->title->Set("y (um)");
	$graph->yaxis->SetPos(-1000);

	//cross hair to mark the center
	$lp1 = new LinePlot(array(-1000,1000),array(0,0));
	$lp1->SetColor("yellow");
	$graph->Add($lp1);
	$lp2 = new LinePlot(array(0,0),array(-1000,1000));
	$lp2->SetColor("yellow");
	$graph->Add($lp2);

	// show colormap as separate plots
	foreach(array_keys($data1x) as $index)	{
		if (empty($data1x[$index])) continue;
		$color = array($index,$index,$index);
		$sp[$index] = new ScatterPlot($data1y[$index],$data1x[$index]);
		$sp[$index]->mark->SetType(MARK_FILLEDCIRCLE);
		$sp[$index]->mark->SetColor($color);
		$sp[$index]->mark->SetFillColor($color);
		$sp[$index]->mark->SetWidth(20);
		$graph->Add($sp[$index]);
	}

	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);
?>
