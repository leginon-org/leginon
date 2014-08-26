<?php
// This code is hideous. 
// I just added the option to print out the number of Processing Runs and jammed it in here because we need it quickly.
// Sorry to make it even worse. This whole file needs to be refactored. AH. 

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";


$defaultId=1;
$id= ($_GET['id']) ? $_GET['id'] : $defaultId;
$histogram = ($_GET['hg']==1) ? true : false;
$maxrate = $_GET['maxr'];
$minrate = $_GET['minr'];
$minrate = ($minrate=="NaN") ? null : $minrate;
$maxrate = ($maxrate=="NaN") ? null : $maxrate;
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];
$cumulative = empty($_GET['cu']) ? false : true;
$type = $_GET['type'];

$start = $_GET['st'];
$points = $_GET['pt'];

$gwidth=800;
$gheight=400;

$width = $_GET['w'];
$height = $_GET['h'];

if ($type=="r") {
	$alias="njobs";
	$gtitle="Number of Processing Runs";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every year)";
	$yaxistitle="#processingruns";

	$q="select "
		."count(DEF_id) as $alias, "
		."year (DEF_timestamp) year"
		."from ApAppionJobData "
		."where DEF_timestamp<>'0000-00-00 00:00:00' group by year";
		
	mysql_connect(DB_HOST, DB_USER, DB_PASS) or die("Could not connect: " . mysql_error());
	
	/* use the project database */
	mysql_select_db(DB_PROJECT);
	
	/* get all the ap database names */
	$result = mysql_query("select distinct appiondb from processingdb") or die("Query error: " . mysql_error());

	// $keyedData uses the unix timestamp for each quarter as the key and stores the total number
	// of runs for the quarter across all projects as the value. 
	$keyedData = array();
	
	// for each appion database, get the number of processing runs per quarter
	while ($row = mysql_fetch_array($result, MYSQL_ASSOC)) {

		mysql_select_db($row['appiondb']);
		
		$rexists = mysql_query("SHOW TABLES LIKE 'ApAppionJobData'");
		$tableExists = mysql_num_rows($rexists) > 0;
		if ( $tableExists ) {
			$r = mysql_query($q) or die("Database query error: " . mysql_error());
			
			// add the processing runs from this project to the appropriate quarter
			while ($rowInner = mysql_fetch_array($r, MYSQL_ASSOC)) {
				$keyedData[$rowInner['unix_timestamp']] += $rowInner[$alias];
			}
		}
	}

	// sort the data by the timestamp
	ksort($keyedData);
	
	// remove the last data point as it represents an incomplete quarter.
	array_pop($keyedData);
	
	// put the data into seperate arrays for display
	foreach ($keyedData as $time=>$nruns) {
		$datax[] = $time;
		if(!$cumulative){
			$datay[] = $nruns;
		}
		else{
			$index = count($datay)-1;
			$datay[] = $datay[$index] + $nruns;
		}
	}
	
	// if the user just wants to see the data, display it here
	if ($viewdata) {
		$displayData = array();
		foreach ( $datax as $i=>$date ) {
			if ( $date ){
				$formattedDate = strftime("%Y-%m-%d", $date);
			} else {
				$formattedDate = "empty";
			}
			$displayData[] = array( "timestamp"=>$formattedDate, "$alias"=>$datay[$i] );
		}
		$keys = array("timestamp", "$alias");
		echo dumpData($displayData, $keys);
		exit;
	}
	
	graphData($datax, $datay, $gwidth, $gheight, $histogram, $gtitle);
	exit();
		
} else if ($type=="s") {
	$alias="nsession";
	$gtitle="Number of Sessions";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every year)";
	$yaxistitle="#sessions";

	$sql="select "
		."count(ns.DEF_id) as $alias, "
		."year (ns.DEF_timestamp) year "
		."from (select "
		."	s.DEF_timestamp, s.DEF_id "
		."from AcquisitionImageData a "
		."left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) "
		."where a.`REF|SessionData|Session` IS NOT NULL "
		."group by a.`REF|SessionData|Session`) ns "
		."where ns.DEF_timestamp<>'0000-00-00 00:00:00' group by year";
	
} else {
	$alias="nimage";
	$gtitle="Number of Images";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every year)";
	$yaxistitle="#images";
	$sql="select "
		."count(DEF_id) as $alias, "
		."year(DEF_timestamp) year "
		."from `AcquisitionImageData` "
		."where DEF_timestamp<>'0000-00-00 00:00:00' "
		."group by year"
		." $limit ";
}
/* use leginon database */
$db = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

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
    return $aVal;
}

if ($nimagedata){
	//suppress the last data, (not the whole 3 month data).
	unset($nimagedata[count($nimagedata)-1]);
	foreach ($nimagedata as $d) {
		$datax[] = $d['year'];
		if(!$cumulative){
			$datay[] = $d[$alias];
		}
		else{
			$index = count($datay)-1;
			$datay[] = $datay[$index] + $d[$alias];
		}
	}
}

graphData($datax, $datay, $gwidth, $gheight, $histogram, $gtitle);

function graphData($datax, $datay, $width, $height, $histogram, $title) 
{
	if (!$datax && !$datay) {
		$width = 12;
		$height = 12;
		$source = blankimage($width,$height);
	} else {
	
		$graph = new Graph($width,$height,"auto");    
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
			$graph->title->Set($title);
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
}
?>
