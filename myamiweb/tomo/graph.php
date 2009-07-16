<?php
require_once "tomography.php";
require "../inc/jpgraph.php";
require "../inc/jpgraph_line.php";

$tiltSeriesId = $_GET['tiltSeriesId'];
$axis = $_GET['axis'];
$width = $_GET['width'];
$height = $_GET['height'];

function graphXY($prediction, $position, $correlation, $tilts, $pixel_size, $title, $width, $height) {
		// --- to avoid jpgraph plot warning image --- merci beaucoup --- //
		if (count($correlation)==1)
			$correlation[]=$correlation[0];

    for($i = 0; $i < count($prediction); $i++) {
        $prediction[$i] *= $pixel_size[$i]/1e-6;
        $position[$i] *= $pixel_size[$i]/1e-6;
		}
		if ($prediction[0]==0) $prediction[0]=$prediction;
		if ($position[0]==0) $position[0]=$position[1];
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetY2Scale("lin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();

    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');


    $correlationplot = new LinePlot($correlation);
    $correlationplot->SetColor("darkgreen");
    $correlationplot->SetLegend("Feature");

    $predictionplot= new LinePlot($prediction);
    $predictionplot->SetColor("blue");
    $predictionplot->SetLegend("Prediction");

    $positionplot= new LinePlot($position);
    $positionplot->SetColor("orange");
    $positionplot->SetLegend("Position");

    $graph->AddY2($correlationplot);
    $graph->Add($predictionplot);
    $graph->Add($positionplot);

    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set($title);
    $graph->title->SetMargin(12);

    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");

    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");

    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("um");
    $graph->yaxis->SetTitleMargin(50);

    $graph->y2axis->SetColor("darkgreen");
    $graph->y2axis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->y2axis->title->SetColor("darkgreen");
    $graph->y2axis->title->SetFont(FF_FONT2);
    $graph->y2axis->title->Set("pixels");
    $graph->y2axis->SetTitleMargin(40);

    $graph->legend->SetFillColor('#FFFFFF@0.25');
    $graph->legend->SetFont(FF_FONT2);
    $graph->legend->SetAbsPos(20, 20, 'right', 'top');
    $graph->legend->SetLayout(LEGEND_HOR);

    $graph->Stroke();
}

function graphZ($prediction, $position, $tilts, $pixel_size, $title, $width, $height) {
		// --- to avoid jpgraph plot warning image --- merci beaucoup --- //
		if (count($prediction)==1)
			$prediction[]=$prediction[0];
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();

    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');

    for($i = 0; $i < count($prediction); $i++) {
        $prediction[$i] *= $pixel_size[$i]/1e-6;
        $position[$i] /= 1e-6;
    }
    $predictionplot= new LinePlot($prediction);
    $predictionplot->SetColor("blue");
    $predictionplot->SetLegend("Prediction");

    $positionplot= new LinePlot($position);
    $positionplot->SetColor("orange");
    $positionplot->SetLegend("Measurement");

    $graph->Add($predictionplot);
    $graph->Add($positionplot);

    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set($title);
    $graph->title->SetMargin(12);

    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");

    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");

    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Prediction (microns)");
    $graph->yaxis->SetTitleMargin(50);

    $graph->legend->SetFillColor('#FFFFFF@0.25');
    $graph->legend->SetFont(FF_FONT2);
    $graph->legend->SetAbsPos(20, 20, 'right', 'top');
    $graph->legend->SetLayout(LEGEND_HOR);

    $graph->Stroke();
}

function graphDistance($prediction, $tilts, $pixel_size, $title, $width, $height) {
		// --- to avoid jpgraph plot warning image --- merci beaucoup --- //
		if (count($prediction)==1)
			$prediction[]=$prediction[0];
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();

    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');

    for($i = 0; $i < count($prediction); $i++) {
        $prediction[$i] *= $pixel_size[$i]/1e-6;
    }
    $predictionplot= new LinePlot($prediction);
    $predictionplot->SetColor("blue");
    $predictionplot->SetLegend("Prediction");

    $graph->Add($predictionplot);

    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set($title);
    $graph->title->SetMargin(12);

    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");

    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");

    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Prediction (microns)");
    $graph->yaxis->SetTitleMargin(50);

    $graph->legend->SetFillColor('#FFFFFF@0.25');
    $graph->legend->SetFont(FF_FONT2);
    $graph->legend->SetAbsPos(20, 20, 'right', 'top');
    $graph->legend->SetLayout(LEGEND_HOR);

    $graph->Stroke();
}

function graphNT($prediction, $tilts, $title, $width, $height) {
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();

    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');

    $predictionplot= new LinePlot($prediction);
    $predictionplot->SetColor("blue");

    $graph->Add($predictionplot);

    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set($title);
    $graph->title->SetMargin(12);

    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");

    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");

    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Prediction (pixels)");
    $graph->yaxis->SetTitleMargin(50);

    $graph->Stroke();
}

function graphTheta($prediction, $tilts, $title, $width, $height) {
    $graph = new Graph($width, $height, "auto");    
    $graph->SetScale("textlin");
    $graph->SetMarginColor('white');
    $graph->img->SetMargin(70, 70, 50, 50);
    $graph->img->SetAntiAliasing();

    $graph->xgrid->Show(true, false);
    $graph->ygrid->Show(true, false);
    $graph->ygrid->SetFill(true,'#EFEFEF@0.75','#BBCCFF@0.75');

    $prediction = ($prediction) ? array_map("rad2deg", $prediction) : array(0,0);

    $predictionplot= new LinePlot($prediction);
    $predictionplot->SetColor("blue");

    $graph->Add($predictionplot);

    $graph->title->SetFont(FF_FONT2, FS_BOLD, 14);
    $graph->title->Set($title);
    $graph->title->SetMargin(12);

    $graph->xaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->xaxis->title->SetFont(FF_FONT2);
    $graph->xaxis->title->Set("Tilt (degrees)");

    $graph->xaxis->SetTickLabels($tilts);
    $graph->xaxis->SetTextTickInterval(10);
    $graph->xaxis->SetPos("min");

    $graph->yaxis->SetFont(FF_FONT1, FS_NORMAL, 8);
    $graph->yaxis->title->SetFont(FF_FONT2);
    $graph->yaxis->title->Set("Prediction (degrees)");
    $graph->yaxis->SetTitleMargin(50);

    $graph->Stroke();
}

function emptyImage($width, $height, $message) {
    $im = imagecreate($width, $height);
    $white = imagecolorallocate ($im, 255, 255, 255);
    $black = imagecolorallocate ($im, 0, 0, 0);

    $font_size = 12;
    $font_angle = 0;
    $font_file = TTF_DIR.'arial.ttf';

    imagefill($im, 0, 0, $white);
    while (true) {
        imagerectangle($im, 0, 0, $width - 1, $height - 1, $black);
        $result = imageftbbox($font_size, $font_angle, $font_file, $message);
        $message_width  = abs($result[4]);
        $message_height = abs($result[5]);
        if(($message_width < $width - 2) and ($message_height < $height - 2)) {
            break;
        }
        $font_size--;
        if($font_size < 1) {
            $font_size = 1;
            break;
        }
    }
    $left = ($width - $message_width)/2;
    $bottom = ($height + $message_height)/2;
    imagettftext($im, $font_size, $font_angle, $left, $bottom, $black, $font_file, $message);

    header("Content-type: image/png");
    imagepng($im);
}

function formatTilt($tilt) {
    return sprintf("%.1f", $tilt);
}

if ($tiltSeriesId == NULL or $axis == NULL) {
    $message = 'No tilt series selected.';
    emptyImage($width, $height, $message);
    exit;
}

$predictionData = $tomography->getPredictionData($tiltSeriesId);
$predictionData = $tomography->sortPredictionData($predictionData);

$tilts = $predictionData['stage_alpha'];
if ($tilts == NULL) {
    $message = 'No tilt information in the database for this tilt series.';
    emptyImage($width, $height, $message);
    exit;
}
$tilts = array_map("rad2deg", $tilts);
$tilts = array_map("formatTilt", $tilts);

$title = $axis.'-axis';

$pixel_size = $predictionData['pixel size'];

if ($axis == 'z' || $axis == 'z0' ) {
    $prediction = $predictionData['SUBD|predicted position|'.$axis];
    $position = $predictionData['measured defocus'];
    graphZ($prediction, $position, $tilts, $pixel_size, $title, $width, $height);
} else if ($axis == 'x' || $axis == 'y') {
    $prediction = $predictionData['SUBD|predicted position|'.$axis];
#    $position = $predictionData['SUBD|correlated position|'.$axis];
    $position = $predictionData['SUBD|position|'.$axis];
    $correlation = $predictionData['SUBD|correlation|'.$axis];
    graphXY($prediction, $position, $correlation, $tilts, $pixel_size, $title, $width, $height);
} else if ($axis == 'optical axis') {
    $prediction = $predictionData['SUBD|predicted position|'.$axis];
    graphDistance($prediction, $tilts, $pixel_size, $axis, $width, $height);
} else if ($axis == 'phi') {
    $prediction = $predictionData['SUBD|predicted position|'.$axis];
    graphTheta($prediction, $tilts, "phi", $width, $height);
}

?>
