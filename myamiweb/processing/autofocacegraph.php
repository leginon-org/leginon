<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

require_once "inc/graph.inc";

$defaultId= 1766;
$sessionId= ($_GET['expId']) ? $_GET['expId'] : $defaultId;
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$f = $_GET[f];
$preset=$_GET['preset'];
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = ($_GET['mres']) ? $_GET['mres']: false;
$width=$_GET['w'];
$height=$_GET['h'];

$ctf = new particledata();

$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);
foreach($ctfinfo as $t) {
	$id = $t['REF|leginondata|AcquisitionImageData|image'];
	$p = $leginondata->getPresetFromImageId($id);
	if ($p['name']!=$preset) {
		continue;
	}
	$data[$id] = $t[$f];
	$datadef[$id] = $t['nominal_defocus'];
	$where[] = "DEF_id=".$id;
}

$sqlwhere = "WHERE (".join(' OR ',$where).") and a.`REF|SessionData|session`=".$sessionId ;
$q = 	"select DEF_id, unix_timestamp(DEF_timestamp) as unix_timestamp, "
	." DEF_timestamp as timestamp from AcquisitionImageData a "
	.$sqlwhere;
	$r = $leginondata->getSQLResult($q);
	foreach($r as $row) {
		$e = $leginondata->getPresetFromImageId($row['DEF_id']);
		$ndata[]=array("unix_timestamp" => $row['unix_timestamp'], "timestamp"=>$row['timestamp'], $f=>$data[$row['DEF_id']], "nominal_defocus"=>$datadef[$row['DEF_id']]);
		$datax[]=$datadef[$row['DEF_id']];
		$datay[]=$data[$row['DEF_id']];
	}

if ($viewdata) {
	$keys = array("timestamp", "$f" );
	echo dumpData($ndata, $keys);
	exit;
}

# data key for display
$display_x = 'nominal_defocus';
$display_y = $f;
# axis names
$axes = array($display_x,$display_y);
$dbemgraph = new dbemgraph($ndata, $axes[0], $axes[1]);
$dbemgraph->lineplot=false;
//Define graph title
$graph_title = ($display_y == 'difference_from_mean') ? 'precent astig from mean':$display_y;
$graph_title = ($preset) ? $graph_title." for preset $preset": $graph_title;
$dbemgraph->title=$graph_title;
//Define yunit
$yunit = ($display_y == 'defocus1' || $f == 'defocus2' || $f == 'difference_from_nom') ? ' (um)':'';
$yunit = ($display_y == 'difference_from_mean') ? ' (%)':$yunit;
//Define y axis title
$ytitle = $display_y;
$dbemgraph->yaxistitle=$ytitle.$yunit;
//y axis title depends on the type of graph
$xunit = ($histogram) ? $yunit: ' (um)';
$dbemgraph->xaxistitle=$axes[0].$xunit;

if ($viewdata) {
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}
//x axis is nominal defocus normally
$xscale = ($histogram) ? 1: 1e-6;
$dbemgraph->scalex($xscale);
//yscale
$yscale = ($display_y == 'defocus1' || $display_y == 'defocus2' || $display_y == 'difference_from_nom') ? 1e-6:1;
$yscale = ($display_y == 'difference_from_mean') ? 1e-2:$yscale;
$dbemgraph->scaley($yscale);
$dbemgraph->dim($width,$height);
if (strpos($f,'difference') !== false)
	$dbemgraph->baselineplot=true;
$dbemgraph->graph();

?>
