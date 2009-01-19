<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/jpgraph.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$reconRunId= $_GET['recon'];
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;

$particle = new particledata();

//If summary is true, get only the data with the best confidence
$eulerinfo = $particle->getEulerJumps($reconRunId);

function scicallback($a) {
	return format_sci_number($a,3,true);
}

function TimeCallback($aVal) {
    return Date('H:i',$aVal);
}

foreach($eulerinfo as $e) {
	$data[$e['DEF_id']] = $e['median'];
}

//print_r($data);

/*
$sqlwhere = "WHERE (".join(' OR ',$where).") and a.`REF|SessionData|session`=".$sessionId ;
$q = 	"select DEF_id, unix_timestamp(DEF_timestamp) as unix_timestamp, "
	." DEF_timestamp as timestamp from AcquisitionImageData a "
	.$sqlwhere;
	$r = $leginondata->getSQLResult($q);
	foreach($r as $row) {
		$e = $leginondata->getPresetFromImageId($row['DEF_id']);
		$ndata[]=array("timestamp" => $row['timestamp'], "$f"=>$data[$row['DEF_id']]);
		$datax[]=$row['unix_timestamp'];
		$datay[]=$data[$row['DEF_id']];
	}


if ($viewdata) {
	$keys = array("timestamp", "$f" );
	echo dumpData($ndata, $keys);
	exit;
}
*/
$width = $_GET['w'];
$height = $_GET['h'];
if (!$data) {
	$width = 12;
	$height = 12;
	$source = blankimage($width, $height);
} else {
	$graph = new Graph(600,400,"auto");    
	if ($histogram) {
		$graph->img->SetMargin(60,30,40,50);
		$histogram = new histogram($data);
		$histogram->setBarsNumber(50);
		$rdata = $histogram->getData();
		$rdatax = $rdata['x'];
		$rdatay = $rdata['y'];
		
		$graph->SetScale("linlin");
                
		$bplot = new BarPlot($rdatay, $rdatax);
		$graph->Add($bplot);

		$graph->title->Set("Euler Jump Histogram");
		$graph->xaxis->title->Set("$f");
		$graph->xaxis->SetTextLabelInterval(3);
		$graph->xaxis->SetLabelFormatCallback('scicallback');
		$graph->yaxis->title->Set("Frequency");
	} else {

		$graph->SetAlphaBlending();
		$graph->SetScale("intlin",0,'auto'); //,$datax[0],$datax[$n-1]);
		$graph->img->SetMargin(60,40,40,80);
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(30);
		$graph->xaxis->title->Set("time");
		$graph->yaxis->SetTitlemargin(35);
		$graph->yaxis->SetLabelFormatCallback('scicallback');
		$graph->title->Set("$f : $preset ");

		$sp1 = new ScatterPlot($datay,$datax);
		$sp1->mark->SetType(MARK_CIRCLE);
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$graph->Add($sp1);
		$p1 = new LinePlot($datay,$datax);
		$p1->SetColor("blue");
		$graph->Add($p1);
	}
	$source = $graph->Stroke(_IMG_HANDLER);
}

resample($source, $width, $height);

?>
