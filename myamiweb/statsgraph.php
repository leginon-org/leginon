<?php
require_once "inc/jpgraph.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/image.inc";
require_once "inc/leginon.inc";

function getColorMap($v) {
        $c = floor($v%255);
        if ($v<255) {
                $colormap = ((255 << 16) + ($c << 8) + 0);
        } else if ($v<255*2) {
                $colormap = (((255-$c) << 16) + (255 << 8) + 0);
        } else if ($v<255*3) {
                $colormap = ((0 << 16) + (255 << 8) + $c);
        } else if ($v<255*4) {
                $colormap = ((0 << 16) + ((255-$c) << 8) + 255);
        } else if ($v<=255*5) {
                $colormap = (($c << 16) + (0 << 8) + 255);
        }
        return $colormap;
}

$defaultId= 1445;
$defaultpreset='en';
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;
$viewsql = $_GET[vs];

$stats = $leginondata->getRelatedStats($sessionId, $preset);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

if ($viewdata) {
	echo dumpData($stats);
	exit;
}


foreach ($stats as $stat) {
	// no stat
	if ($stat['prefId']+0 == 0) continue;
	//no parent
	if ($stat['parent mean'] == '') continue;
	$prefId = $stat['preftable'].$stat['prefId'];
	$datay[$prefId][] = $stat['mean']+0;
  $datax[$prefId][] = $stat['parent mean']+0;
	
}

$keys = (array_keys($datax));
if (empty(end($keys))) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {
	$parentinfo = $leginondata->getParent($stats[0]['Id']);
	$graph = new Graph(800,600,"auto");
	$graph->SetScale("linlin");

	$graph->img->SetMargin(50,40,40,40);        

	$graph->title->Set("Pixel Density $preset vs ".$parentinfo['parentpreset']);
	$graph->title->SetFont(FF_FONT1,FS_BOLD);
	$graph->xaxis->title->Set("density ".$parentinfo['preset']);
	$graph->yaxis->SetTitlemargin(35);
	$graph->yaxis->title->Set("density ".$parentinfo['parentpreset']);

	foreach ($keys as $k=>$v) {
		$sp[$k] = new ScatterPlot($datay[$v],$datax[$v]);
		$color = '#'.dechex(getColorMap($k));
		$sp[$k]->mark->SetFillColor($color);
		$sp[$k]->mark->SetColor($color);
		$graph->Add($sp[$k]);
	}

	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
