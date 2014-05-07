<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/leginon.inc";
require_once "inc/graph.inc";

$defaultId=1445;
$defaultpreset='hl';
$histogram=($_GET['hg']==1) ? true : false;
$sessionId=($_GET['Id']) ? $_GET['Id'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata=($_GET['vdata']==1) ? true : false;
$viewsql=$_GET['vs'];
$width=$_GET['w'];
$height=$_GET['h'];
$stdev=($_GET['stdev']==1) ? true : false;
$data_name=($stdev) ? 'stdev': 'mean';

$thicknessdata = $leginondata->getImageStats($sessionId, $preset);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

$dbemgraph= new dbemgraph($thicknessdata, 'unix_timestamp', $data_name);
$dbemgraph->lineplot=false;
$dbemgraph->title="Pixel $data_name for preset $preset";
$dbemgraph->yaxistitle="pixel $data_name";
if ($viewdata) {
	$dbemgraph->dumpData(array('timestamp', $data_name));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}
$dbemgraph->dim($width,$height);
$dbemgraph->graph();
?>
