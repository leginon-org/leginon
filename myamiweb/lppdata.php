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

$stats=false;
$xy_fieldnames = array('phase plate plane shift','phase plate plane tilt');
$scaler_fieldnames = array('phase plate focus');
$fielddata=$leginondata->getImageScopeValues($sessionId, $preset, $scaler_fieldnames, $xy_fieldnames, $stats);
if ($viewsql) {
	$sql = $leginondata->mysql->getSQLQuery();
	echo $sql;
	exit;
}

// Add lpp fit results to data
$new_fielddata = array();
$lppfit_keys = array();
foreach ($fielddata as $d) {
	$r_array = $leginondata->getImageLppFitResults($d['image_id']);
	$new_fielddata[] = array_merge($d, $r_array);
	$lppfit_keys = array_unique(array_merge($lppfit_keys,array_keys($r_array)));
}

$scaler_fieldnames = array_merge($scaler_fieldnames, $lppfit_keys);
$display_names = array('image_id', 'timestamp', 'filename');
foreach ($scaler_fieldnames as $fieldname) {
	$display_names[] = str_replace(' ','_',$fieldname);
}
foreach ($xy_fieldnames as $fieldname) {
	$display_names[] = str_replace(' ','_',$fieldname).'_x';
	$display_names[] = str_replace(' ','_',$fieldname).'_y';
}
if ($viewdata) {
	echo dumpData($new_fielddata, $display_names);
}

?>
