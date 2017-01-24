<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/graph.inc";

$defaultId=3956;
$defaultpreset='en';
$histogram=($_GET['hg']==1) ? true : false;
$histaxis=($_GET['haxis']) ? $_GET['haxis'] : 'y';
$sessionId=($_GET['Id']) ? $_GET['Id'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata=($_GET['vdata']==1) ? true : false;
$viewsql=$_GET['vs'];
$width=$_GET['w'];
$height=$GET['h'];
$runId = $_GET['rId'];

$particle = new particledata();
$inspect = false;
$positiondata=$particle->getParticles($runId);
$rundata=$particle->getSelectionParams($runId);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
$axes = array('xcoord','ycoord');
if ($histogram == true && $histaxis == 'xcoord') 
	$axes = array('ycoord','xcoord');
$dbemgraph = new dbemgraph($positiondata, $axes[0], $axes[1]);
$dbemgraph->lineplot=False;
$dbemgraph->title="particle positions for ".$rundata[0]['name'];
$dbemgraph->yaxistitle=$axes[1]." (pixel)";
$dbemgraph->xaxistitle="x (pixel)";

if ($viewdata) {
	$dbemgraph->dumpData(array('xcoord', 'ycoord'));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

#$dbemgraph->scalex(1e-6);
#$dbemgraph->scaley(1e-6);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
