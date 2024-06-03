<?php
// This code is hideous. 
// I just added the option to print out the number of Processing Runs and jammed it in here because we need it quickly.
// Sorry to make it even worse. This whole file needs to be refactored. AH. 

require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
//require_once "inc/histogram.inc";
require_once('config.php');
require_once('inc/mysql.inc');
require_once "inc/image.inc";

$defaultId=1;
$id= (array_key_exists('id',$_GET) && $_GET['id']) ? $_GET['id'] : $defaultId;
$histogram = (array_key_exists('hg',$_GET) && $_GET['hg']==1) ? true : false;
$viewdata = (array_key_exists('vd',$_GET)) ? $_GET['vd']: false;
$viewsql = (array_key_exists('vs',$_GET)) ? $_GET['vs']: false;
$cumulative = (!array_key_exists('cu',$_GET) || empty($_GET['cu'])) ? false : true;
$type = (array_key_exists('type',$_GET)) ? $_GET['type']: '';

$start = (array_key_exists('st',$_GET)) ? $_GET['st']: false;
$points = (array_key_exists('pt',$_GET)) ? $_GET['pt']: false;

$gwidth=800;
$gheight=400;

$width = (array_key_exists('w',$_GET)) ? $_GET['w']: false;
$height = (array_key_exists('h',$_GET)) ? $_GET['h']: false;

// determine appropriate timegroup
$sql = "select DEF_id, year (DEF_timestamp) year from projectexperiments";
$db = new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
$results = $db->getSQLResult($sql);
if (empty($timegroup)) {
	// stats by years if db used for a while
	if (count($results) > 1 && $results[count($results)-1]['year']-$results[0]['year']> 5) {
		$timegroup = 'year';
	} else {
		$timegroup = 'month';
	}
}
$alltimekeys = array('year','month','date');
$timekeys = array_slice($alltimekeys, 0, array_search($timegroup, $alltimekeys)+1);

$datax = array();
$datay = array();

if ($type=="r") {
	$alias="njobs";
	$gtitle="Number of Processing Runs";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every ".$timegroup.")";
	$yaxistitle="#processingruns";

	$q="select "
		."count(DEF_id) as $alias, "
		."year (DEF_timestamp) year, "
		."".$timegroup." (DEF_timestamp) ".$timegroup." "
		."from ApAppionJobData "
		."where DEF_timestamp<>'0000-00-00 00:00:00' group by year,".$timegroup;
		
	$link = mysqli_connect(DB_HOST, DB_USER, DB_PASS);
   if (mysqli_connect_errno()) {
       die("Could not connect: " . mysqli_connect_error());
   }
	
	/* use the project database */
	mysqli_select_db($link, DB_PROJECT);
	
	/* get all the ap database names */
	$result = mysqli_query($link, "select distinct appiondb from processingdb") or die("Query error: " . mysqli_error($link));

	// $keyedData uses the unix timestamp for each quarter as the key and stores the total number
	// of runs for the quarter across all projects as the value. 
	$keyedData = array();
	
	// for each appion database, get the number of processing runs per quarter
	while ($row = mysqli_fetch_array($result, MYSQLI_ASSOC)) {

		mysqli_select_db($link, $row['appiondb']);
		
		$rexists = mysqli_query($link, "SHOW TABLES LIKE 'ApAppionJobData'");
		$tableExists = mysqli_num_rows($rexists) > 0;
		if ( $tableExists ) {
			$r = mysqli_query($link, $q) or die("Database query error: " . mysqli_error($link));
			
			// add the processing runs from this project to the appropriate quarter
			while ($rowInner = mysqli_fetch_array($r, MYSQLI_ASSOC)) {
				$k = array();
				foreach ($timekeys as $t) $k[] = sprintf('%02d', (int) $rowInner[$t]);
				// combine data from different appiondb
				$keyedData[implode('-',$k)] += $rowInner[$alias];
			}
		}
	}

	// sort the data by the timestamp
	ksort($keyedData);
	
	// remove the last data point as it represents an incomplete time group.
	if (count($keyedData) > 5) array_pop($keyedData);
	

	// put the data into seperate arrays for display
	$displayData = array();
	foreach ($keyedData as $time=>$nruns) {
		$keyedTime = array();
		if ( $time ){
			$timeArray = explode("-", $time);
			foreach ($timekeys as $j=>$k) { $keyedTime[$k] = $timeArray[$j]; };
		} else {
			foreach ($timekeys as $j=>$k) { $keyedTime[$k]="empty"; };
		}
		$datax[] = ($keyedTime['year']-$year0)*12+$keyedTime['month'];
		if(!$cumulative){
			$datay[] = $nruns;
		} else {
			$index = count($datay)-1;
			$datay[] = $datay[$index] + $nruns;
		}
		$displayData[] = array_merge($keyedTime, array("$alias"=>$datay[count($datay)-1]));
	}
	
	// if the user just wants to see the data, display it here
	if ($viewdata) {

		$keys = array_merge($timekeys, array("$alias"));
		echo dumpData($displayData, $keys);
		exit;
	}
	
	graphData($datax, $datay, $gwidth, $gheight, $histogram, $gtitle);
	exit();
		
} else if ($type=="s") {
	$alias="nsession";
	$gtitle="Number of Sessions";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every ".$timegroup.")";
	$yaxistitle="#sessions";

	$sql="select "
		."count(ns.DEF_id) as $alias "
		.", year (ns.DEF_timestamp) year "
		.", ".$timegroup." (ns.DEF_timestamp) ".$timegroup." "
		."from (select "
		."	s.DEF_timestamp, s.DEF_id "
		."from AcquisitionImageData a "
		."left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) "
		."where a.`REF|SessionData|Session` IS NOT NULL "
		."group by a.`REF|SessionData|Session`) ns "
		."where ns.DEF_timestamp<>'0000-00-00 00:00:00' group by year,".$timegroup;
	
} else {
	$alias="nimage";
	$gtitle="Number of Images";
	$gtitle .= ($cumulative) ? " (cumulative)" : " (every ".$timegroup.")";
	$yaxistitle="#images";
	$limit='';
	$sql="select "
		."count(DEF_id) as $alias, "
		."".$timegroup."(DEF_timestamp) ".$timegroup." "
		.", year(DEF_timestamp) year "
		."from `AcquisitionImageData` "
		."where DEF_timestamp<>'0000-00-00 00:00:00' "
		."group by year, ".$timegroup
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
	$keys = ($timegroup == 'month') ? array('year'): array();
	$keys = array_merge($keys, array($timegroup, "$alias"));
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
		if ($timegroup == 'month') {
			$datax[] = ($d['year']-$nimagedata[0]['year'])*12+$d[$timegroup];
		} else {
			$datax[] = $d['year'];
		}
		if(!$cumulative){
			$datay[] = (int) $d[$alias];
		}
		else {
            if (count($datay) > 0) {
			    $index = count($datay)-1;
			    $datay[] = $datay[$index] + (int) $d[$alias];
            } else {
			    $datay[] = (int) $d[$alias];
            }

		}
	}
}
graphData($datax, $datay, $gwidth, $gheight, $histogram, $gtitle, $yaxistitle);

function graphData($datax, $datay, $width, $height, $histogram, $title, $yaxistitle='')
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

			$graph->title->SetFont(FF_FONT2,FS_BOLD,12);
			$graph->title->Set($title);
			$graph->SetAlphaBlending();
			$graph->SetScale("intlin");
			$graph->xaxis->scale->SetAutoMin(0);
			$graph->yaxis->scale->SetAutoMin(0);
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
