<?php
require ("inc/jpgraph.php");
require ("inc/jpgraph_scatter.php");
require ("inc/jpgraph_log.php");
require ("inc/image.inc");
require ("inc/leginon.inc");

$defaultId= 1445;
$defaultpreset='en';
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
$preset = ($_GET[preset]) ? $_GET[preset] : $defaultpreset;
$viewdata = ($_GET['vdata']==1) ? true : false;

$stats = $leginondata->getRelatedStats($sessionId, $preset);

if ($viewdata) {
	$sep="	";
	$crlf="\n";
	if (!$stats)
		exit;
	echo "<pre>";
	foreach($stats[0] as $k=>$v) {
		$fields[]=$k;
	}
	echo implode($sep, $fields).$crlf;
	foreach($stats as $stat) {
		echo implode($sep, $stat).$crlf;
	}
		echo "</pre>";
	exit;
}

foreach ($stats as $stat) {
	if ($stat['parent thickness-mean'] > 0.5)
		continue;
	$datay[] = $stat['mean'];
	$datax[] = $stat['parent mean'];
//	$datax[] = $stat['parent thickness-mean'];
	
}
if (!$datax && !$datay) {
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

	$sp1 = new ScatterPlot($datay,$datax);

	$graph->Add($sp1);
	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
