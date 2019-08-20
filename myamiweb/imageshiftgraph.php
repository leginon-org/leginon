<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
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
$height=$_GET['h'];

$fieldname = 'image shift';
$displayname = str_replace(' ','_',$fieldname);
$stats=false;
$imageshiftdata=$leginondata->getImageScopeXYValues($sessionId, $preset, $fieldname, $stats);

if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}
$display_x = $displayname.'_x';
$display_y = $displayname.'_y';
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph= new dbemgraph($imageshiftdata, $axes[0], $axes[1]);
$dbemgraph->lineplot=False;
$dbemgraph->title=$fieldname." for preset $preset";
$dbemgraph->yaxistitle=$axes[1]." (mrad)";

if ($viewdata) {
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$dbemgraph->scalex(1e-3);
$dbemgraph->scaley(1e-3);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
