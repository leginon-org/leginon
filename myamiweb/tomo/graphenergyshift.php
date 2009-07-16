<?php

require_once('../config.php');
require_once('tomography.php');
require_once('../inc/jpgraph.php');
require_once('../inc/jpgraph_line.php');

$session_id = $_GET['sessionId'];
if(!$session_id)
   exit('no session specified');
$width = $_GET['width'];
$height = $_GET['height'];

$results = $tomography->getEnergyShift($session_id);
$times = array();
$timesstamps = array();
$shifts = array();
foreach($results as $result) {
    if(is_null($result['after']))
        continue;
    $times[] = $result['unix_timestamp'];
    $timestamps[] = $result['timestamp'];
    $shifts[] = $result['after'];
}

function callback($label) {
    return strftime('%m/%d %H:%M', $label);
}

function graphEnergyShift($times, $timestamps, $shifts, $width, $height) {
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("intlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(100, 100, 50, 100);
    $graph->img->SetAntiAliasing();
    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');
    
    $plot= new LinePlot($shifts, $times);
    $plot->SetColor("orange");
    
    $graph->Add($plot);
    
    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set('Internal Energy Shift');
    $graph->title->SetMargin(12);
    
    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Time");
    
    $graph->xaxis->SetPos("min");
    $graph->xaxis->SetLabelFormatCallback('callback');
    $graph->xaxis->SetLabelAngle(45);
    $graph->xaxis->SetTitleMargin(50);
    
    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Internal Energy Shift (eV)");
    $graph->yaxis->SetTitleMargin(50);
    
    $graph->Stroke();
}

graphEnergyShift($times, $timestamps, $shifts, $width, $height);

?>
