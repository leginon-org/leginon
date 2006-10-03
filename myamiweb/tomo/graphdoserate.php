<?php

require_once('config.php');
require_once('tomography.php');
require_once('../inc/jpgraph.php');
require_once('../inc/jpgraph_line.php');

$session_id = $_GET['sessionId'];
if(!$session_id)
   exit('no session specified');
$width = $_GET['width'];
$height = $_GET['height'];

$results = $tomography->getDose($session_id, "Tomography");

$times = array();
$timesstamps = array();
$rates = array();
$t0 = $results[0]['unix_timestamp'];
foreach($results as $result) {
    $times[] = ($result['unix_timestamp'] - $t0)/(60*60);
    $timestamps[] = $result['timestamp'];
    $rates[] = $result['dose']/$result['exposure_time'];
}

function graphDoseRate($times, $timestamps, $rates, $width, $height) {
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("intlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();
    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');
    
    $plot= new LinePlot($rates, $times);
    $plot->SetColor("orange");
    
    $graph->Add($plot);
    
    $graph->title->SetFont(FF_ARIAL, FS_BOLD, 14);
    $graph->title->Set('Dose Rate');
    $graph->title->SetMargin(12);
    
    $graph->xaxis->SetFont(FF_COURIER, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_ARIAL);
    $graph->xaxis->title->Set("Time (hours)");
    
    #$graph->xaxis->SetTickLabels($timestamps);
    #$graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");
    
    $graph->yaxis->SetFont(FF_COURIER, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_ARIAL);
    $graph->yaxis->title->Set("Dose Rate (e-/A^2/s)");
    $graph->yaxis->SetTitleMargin(50);
    
    $graph->Stroke();
}

graphDoseRate($times, $timestamps, $rates, $width, $height);

?>
