<?php
include ("inc/jpgraph.php");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
include ("inc/jpgraph_bar.php");
require ("inc/leginon.inc");
require ("inc/image.inc");
require ("inc/histogram.inc");

$defaultId= 1445;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;

$width = $_GET['w'];
$height = $_GET['h'];
$viewdata = $_GET['vd'];
$viewsql = $_GET['vs'];
$histogram = ($_GET[hg]==1) ? true : false;
$maxrate = $_GET[maxr];
$minrate = $_GET[minr];
$optimizedpoint = ($_GET['opt']==1) ? true : false;

if($ch0 = $_GET['ch0'])
	$channels[] = '0';
if($ch1 = $_GET['ch1'])
	$channels[] = '1';
if($ch2 = $_GET['ch2'])
	$channels[] = '2';
if($ch3 = $_GET['ch3'])
	$channels[] = '3';
if($ch4 = $_GET['ch4'])
	$channels[] = '4';
if($ch5 = $_GET['ch5'])
	$channels[] = '5';
if($ch6 = $_GET['ch6'])
	$channels[] = '6';
if($ch7 = $_GET['ch7'])
	$channels[] = '7';

$TEMP_DB_HOST = 'cronus1';
$TEMP_DB_USER = 'usr_object';
$TEMP_DB_PASS = '';
$TEMP_DB = 'temperature';

$db =  new mysql ($TEMP_DB_HOST, $TEMP_DB_USER, $TEMP_DB_PASS, $TEMP_DB);

$sessionInfo = $leginondata->getSessionInfo($sessionId);
$begintime = $sessionInfo['Begin Time'];
$endtime = $sessionInfo['End Time'];
$begints = $sessionInfo['Begin unixTimestamp'];
$endts = $sessionInfo['End unixTimestamp'];
if (!$endtime) {
	$q = "select @nr:=adddate(from_unixtime('$begints'), interval 1 day) as `nt`, unix_timestamp(@nr) as nts, date_format(@nr, '%Y-%d-%m %T') as fnt ";
	list($r) = $db->getSQLResult($q);
	$endtime = $r['fnt'];
	$endts= $r['fnt'];
}

$q = 'SELECT `name` , `description`, `color` '
        . ' FROM `channelinfo` '
        . ' ORDER BY name ASC '
        . ' LIMIT 8 ';
$channelinfo = $db->getSQLResult($q);
foreach ($channelinfo as $k=>$a) {
	$channel = $k; 
	$labels[$channel] = (empty($a[description])) ? $channel : $a[description];
	$colors[$channel] = $a['color'];
}

$gJpgBrandTiming=true;
$totsum = count($channels);
$numcols = ($totsum < 4) ? 3 : round($totsum/2); 
$nmax=0;
$delta = 0.025;

function reducearray($data,$delta) {
	$newdata = array();
	if (is_array($data)) {
		$n = count($data);
		foreach ($data as $k=>$d) {
			$temp = $d[temperature];
			$next = $data[$k+1][temperature];
			if (($k+2)>$n)
				break;
			if ($next-$temp>$delta)
				$newdata[] = $d;
			}
		}
	return $newdata;
}

function gettemp($channel,$sdate,$edate,$delta=1,$optimize=false) {
	global $db;
	$tdata = array();
	if ($channel>=0) {
		$q="SELECT distinct UNIX_TIMESTAMP(time) as timestamp, temperature  
		from temperature 
		where channel = '$channel'
		and time between from_unixtime('".$sdate."') and from_unixtime('".$edate."') 
		order by time ASC"; 
	}
	$tdata = $db->getSQLResult($q);
	if ($optimize) {
		$tdata = reducearray($tdata,$delta);
		}
	return $tdata;
}

function createlines($datay,$datax,$color,$label) {
	$pl = new LinePlot($datay,$datax);
	$pl->SetColor("$color");
	$pl->SetWeight(2);
	$pl->mark->SetType(MARK_FILLEDCIRCLE);
	$pl->mark->SetColor("$color");
	$pl->mark->SetFillColor("$color");
	$pl->mark->SetWeight(1);
	$pl->mark->SetWidth(2);
	$pl->SetLegend($label);
	return $pl;
}

function createhistogram($datay,$color,$label) {
	$histogram = new histogram($datay);
	$histogram->setBarsNumber(50);
	$rdata = $histogram->getData();
	$rdatax = $rdata['x'];
	$rdatay = $rdata['y'];

	$bplot = new BarPlot($rdatay, $rdatax);
	$bplot->SetFillColor("$color");
	$bplot->SetLegend($label);
	return $bplot;
}


function TimeCallback($unixtimestamp) {
    	return Date("H:i:s",$unixtimestamp);
}

if($channels)
foreach ($channels as $k=>$channel) {
	$tdata = gettemp($channel,$begints,$endts,$delta, $optimizedpoint);
	if ($viewdata && $tdata) {
		echo "--- Channel: ".$labels[$channel]." --- <BR>";
		echo dumpData($tdata);
		continue;
	}
	if ($viewsql) {
		echo $db->getSQLQuery();
		echo ';<br>';
	}
	foreach ($tdata as $d) {
		if ($maxrate && $d['temperature'] > $maxrate)
			continue;
		if ($minrate && $d['temperature'] < $minrate)
			continue;
		$datax[$channel][] = $d[timestamp];
		$datay[$channel][] = $d[temperature];
	}
	$n[$channel] = count($datax[$channel]);
}

if ($viewsql || $viewdata) {
	exit;
}

// Setup the basic graph
$Ymax = (empty($datay)) ? 25 : 'auto';


	if ($histogram) {

		$graph = new Graph(700,400,"auto");
		$graph->SetMargin(70,50,50,105);    
		$graph->title->Set("Histogram");
		$graph->SetScale("linlin");
		$graph->xaxis->SetTextLabelInterval(2);
		$graph->xaxis->SetTitle("Temperature (deg C)", 'center');
		$graph->yaxis->title->Set("Frequency");

	} else {

		$graph = new Graph(700,500,"auto");
		$graph->SetMargin(70,50,50,170);    
		$graph->SetScale('intlin',0, $Ymax, $begints, $endts); 
		$graph->title->Set("Temperature vs. Time,\n $begintime to $endtime ");
		$graph->title->SetMargin(10);
		$graph->SetAlphaBlending();


		// Setup the x-axis with a format callback to convert the timestamp
		// to a user readable time
		$graph->xaxis->SetLabelFormatCallback('TimeCallback');
		$graph->xaxis->SetLabelAngle(90);
		$graph->xaxis->SetTitleMargin(60);
		$graph->xaxis->SetTitle('Date/Time (Hr:Min:Sec)', 'center');

		// y-axis
		$graph->yaxis->SetTitle("Temperature (deg C)", 'center');
		$graph->yaxis->SetTitleMargin(45);
		$graph->SetTickDensity(TICKD_SPARSE);
		$graph->yscale->SetAutoTicks();

		// Show gridlines
		$graph->ygrid->Show(true,false);
		$graph->xgrid->Show(true,false);
	}


if ($channels)
foreach ($channels as $k=>$c) {
	if ($datay[$c]) {
		if ($histogram) {
			$p[$c] = createhistogram($datay[$c],$colors[$c],$labels[$c]);
			$graph->Add($p[$c]);
		} else { 
			$p[$c] = createlines($datay[$c],$datax[$c],$colors[$c],$labels[$c]);
			if ($c==7 && count($p)>1) {
				$graph->SetY2Scale("lin");
				$graph->AddY2($p[$c]);
			} else {
				$graph->Add($p[$c]);
			}
		}
	}
	$nmax += $n[$c];
}

// Add arbitrary text to include the number of points
$txt = new Text("$nmax points");
if ($histogram)
	$txt->Pos(630,380);
else
	$txt->Pos(630,480);
$txt->SetColor("black");
$graph->AddText($txt);

// Legend
$graph->legend->SetLayout(LEGEND_HOR);
$graph->legend->SetColumns($numcols);
$graph->legend->Pos(0.5,0.88,'center','center');

// Output line
$source = $graph->Stroke(_IMG_HANDLER);
resample($source, $width, $height);

?>
