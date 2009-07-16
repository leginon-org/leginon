<?php

require_once('../config.php');
require_once('tomography.php');
require_once('../inc/jpgraph.php');
require_once('../inc/jpgraph_line.php');

$tilt_series_id = $_GET['tiltSeriesId'];
if(!$tilt_series_id)
   exit('no tilt series specified');
$width = $_GET['width'];
$height = $_GET['height'];

$results = $tomography->getMeanValues($tilt_series_id);

$means = array();
$tilts = array();
foreach($results as $result) {
    $means[] = $result['mean'];
    $tilts[] = $result['alpha'];
}

function graphMeanValues($tilts, $means, $width, $height) {
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();
    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');
    
    $plot= new LinePlot($means);
    $plot->SetColor("orange");
    
    $graph->Add($plot);
    
    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set('Image Mean');
    $graph->title->SetMargin(12);
    
    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");
    
    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");
    
    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Mean (counts)");
    $graph->yaxis->SetTitleMargin(50);
    
    $graph->Stroke();
}

graphMeanValues($tilts, $means, $width, $height);

?>
