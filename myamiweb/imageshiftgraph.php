<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";
require "inc/graph.inc";

$defaultId=3956;
$defaultpreset='en';
$histogram=($_GET['hg']==1) ? true : false;
$histaxis=($_GET['haxis']) ? $_GET['haxis'] : 'y';
$sessionId=($_GET['Id']) ? $_GET['Id'] : $defaultId;
$preset=($_GET['preset']) ? $_GET['preset'] : $defaultpreset;
$viewdata=($_GET['vdata']==1) ? true : false;
$viewsql=$_GET['vs'];
$width=$_GET['w'];
$height=$_GET['h'];

$stats=false;
$imageshiftdata=$leginondata->getImageShift($sessionId, $preset, $stats);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
$axes = array('image_shift_x','image_shift_y');
if ($histogram == true && $histaxis == 'x') 
	$axes = array('image_shift_y','image_shift_x');
$dbemgraph=&new dbemgraph($imageshiftdata, $axes[0], $axes[1]);
$dbemgraph->lineplot=False;
$dbemgraph->title="image shift for preset $preset";
$dbemgraph->yaxistitle=$axes[1]." (um)";

if ($viewdata) {
	$dbemgraph->dumpData(array('image_shift_x', 'image_shift_y'));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$dbemgraph->scalex(1e-6);
$dbemgraph->scaley(1e-6);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
