<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/graph.inc";

$defaultId=4963;
$defaultpreset='en';
$histogram=($_GET['hg']==1) ? true : false;
$sessionId=($_GET['Id']) ? $_GET['Id'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata=($_GET['vdata']==1) ? true : false;
$viewsql=$_GET['vs'];
$width=$_GET['w'];
$height=$_GET['h'];

$stats=false;
$defocusdata=$leginondata->getDefocus($sessionId, $preset, $stats);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

$dbemgraph= new dbemgraph($defocusdata, 'unix_timestamp', 'defocus');
$dbemgraph->title="defocus for preset $preset";
$dbemgraph->yaxistitle="defocus (um)";

if ($viewdata) {
	$dbemgraph->dumpData(array('timestamp', 'defocus'));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$dbemgraph->scaley(1e-6);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
