<?php
require "inc/jpgraph.php";
require "inc/jpgraph_line.php";
require "inc/jpgraph_scatter.php";
require "inc/jpgraph_bar.php";
require "inc/histogram.inc";
require "inc/image.inc";

$db = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

$defaultId=1;
$id= ($_GET['id']) ? $_GET['id'] : $defaultId;
$histogram = ($_GET['hg']==1) ? true : false;
$maxrate = $_GET['maxr'];
$minrate = $_GET['minr'];
$minrate = ($minrate=="NaN") ? null : $minrate;
$maxrate = ($maxrate=="NaN") ? null : $maxrate;
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];

$start = $_GET['st'];
$points = $_GET['pt'];

$gwidth=600;
$gheight=300;

if ($_GET['type']=="s") {
	$alias="nsession";
	$gtitle="Number of Sessions";
	$yaxistitle="#sessions";

	$sql="select "
		."@QT:=concat(YEAR(ns.DEF_timestamp),'-',LPAD(QUARTER(ns.DEF_timestamp)*3-2,2,'0'),'-01') as `timestamp`, "
		."UNIX_TIMESTAMP(@QT) as `unix_timestamp`, "
		."count(ns.DEF_id) as $alias, "
		."year (ns.DEF_timestamp) year, quarter(ns.DEF_timestamp) quarter "
		."from (select "
		."	s.DEF_timestamp, s.DEF_id "
		."from AcquisitionImageData a "
		."left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) "
		."where a.`REF|SessionData|Session` IS NOT NULL "
		."group by a.`REF|SessionData|Session`) ns "
		."where ns.DEF_timestamp<>'0000-00-00 00:00:00' group by year,quarter";
	
} else {
	$alias="nimage";
	$gtitle="Number of Images";
	$yaxistitle="#images";
	$sql="select "
		."@QT:=concat(YEAR(DEF_timestamp),'-',LPAD(QUARTER(DEF_timestamp)*3-2,2,'0'),'-01') as `timestamp`, "
		."UNIX_TIMESTAMP(@QT) as `unix_timestamp`, "
		."count(DEF_id) as $alias, "
		."year(DEF_timestamp) year, quarter(DEF_timestamp) quarter "
		."from `AcquisitionImageData` "
		."where DEF_timestamp<>'0000-00-00 00:00:00' "
		."group by year, quarter"
		." $limit ";
}
$nimagedata = $db->getSQLResult($sql);
if ($viewsql) {
	$sql = $db->getSQLQuery();
	echo $sql;
	exit;
}

if ($viewdata) {
	$keys = array("timestamp", "$alias");
	echo dumpData($nimagedata, $keys);
	exit;
}

function TimeCallback($aVal) {
    return Date('M Y',$aVal);
}

if ($nimagedata)
foreach ($nimagedata as $d) {
	$datax[] = $d['unix_timestamp'];
	$datay[] = $d[$alias];
}
$width = $_GET['w'];
$height = $_GET['h'];
if (!$datax && !$datay) {
	$width = 12;
	$height = 12;
	$source = blankimage($width,$height);
} else {

	$graph = new Graph($gwidth,$gheight,"auto");    
	$graph->SetMargin(70,40,30,70);    
	if ($histogram) {
		$histogram = new histogram($datay);
		$histogram->setBarsNumber(50);
		$rdata = $histogram->getData();
		$rdatax = $rdata['x'];
		$rdatay = $rdata['y'];

		$graph->SetScale("linlin");
		$bplot = new BarPlot($rdatay, $rdatax);
		$graph->Add($bplot);
		$graph->title->Set("Images");
		$graph->xaxis->title->Set("Images");
		$graph->yaxis->title->Set("Frequency");

	} else {

//		$graph->title->SetFont(FF_COURIER,FS_BOLD,12);
		$graph->title->Set($gtitle);
		$graph->SetAlphaBlending();
		$graph->SetScale("intlin",0,"auto");
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitlemargin(30);
		$graph->xaxis->SetPos("min");
		$graph->yaxis->SetTitlemargin(50);
		$graph->yaxis->title->Set($yaxistitle);
		$graph->yaxis->title->SetFont(FF_FONT2,FS_BOLD);

		$sp1 = new ScatterPlot($datay,$datax);
		$sp1->value->SetFormat( "%0.0f");
		$sp1->value->SetMargin(10);
		$sp1->value->show();
		$sp1->mark->SetColor('red');
		$sp1->mark->SetWidth(4);
		$sp1->mark->SetType(MARK_UTRIANGLE);
		$sp1->value->SetFont( FF_FONT1, FS_BOLD);
		$graph->Add($sp1);
		$p1 = new LinePlot($datay,$datax);
		$p1->SetColor("blue");
		$graph->Add($p1);

	}
	$source = $graph->Stroke(_IMG_HANDLER);
}
resample($source, $width, $height);
?>
