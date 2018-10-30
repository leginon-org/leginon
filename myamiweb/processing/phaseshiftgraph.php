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

define (PARTICLE_DB, $_SESSION['processingdb']);

$sessionId = $_GET['expId'];
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$cutoff = ($_GET['cutoff']) ? $_GET['cutoff'] : false;
$bydf = ($_GET['bydf']) ? $_GET['bydf'] : 'confidence';
$f = 'extra_phase_shift';
$preset= ($_GET['preset']) ? $_GET['preset'] : '';
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = ($_GET['mres']) ? $_GET['mres'] : 20.0; //fit resolution minimal resolution in Angstroms
$width=$_GET['w'];
$height=$_GET['h'];
$xmin = ($_GET['xmin']) ? $_GET['xmin'] : false;
$xmax = ($_GET['xmax']) ? $_GET['xmax'] : false;
$color = ($_GET['color']) ? $_GET['color'] : false;

$ctf = new particledata();

$pp_ctfruns = array();
//If summary is true, get only the data with the best confidence
if ($summary) {
	$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);
	// Parameters
	$ctfrunparams = $ctf->getCTFParameterFields();
	foreach($ctfrunparams as $params) {
		if ( array_key_exists('shift_phase', $params) && $params['shift_phase'] )
			$pp_ctfruns[] = $params['acerun'];
	}
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfo($runId);
	$pp_ctfruns[] = $runId;
}


foreach($ctfinfo as $t) {
	// Only show ones that shifts phases
	if ( !in_array($t['REF|ApAceRunData|acerun'], $pp_ctfruns) ) continue;
	if ($preset) {
		$p = $leginondata->getPresetFromImageId($id);
		if ($p['name']!=$preset) {
			continue;
		}
	}

	$value = $t[$f];
	// if grouping by defocus, set cutoff
	if ($cutoff) {
		// first check if value exists
		if (!$t[$bydf]) continue;
		// check if within set range
		if ((substr($bydf,0,10)=='resolution' && $t[$bydf] > $cutoff) ||
		   (substr($bydf,0,10)!='resolution' && $t[$bydf] < $cutoff))
			continue;
		$value = $t[$f];
	} else {
		//every value
		$value = $t[$f];
	}

	if ($xmax && $value > $xmax)
		continue;
	if ($xmin && $value < $xmin)
		continue;

	$imageid = $t['imageid'];
	$value = $value * 180 / 3.14159;
	$data[$imageid] = $value;
	$where[] = "DEF_id=".$id;
	$ndata[]=array('unix_timestamp' => $t['unix_timestamp'], "$f"=>$value);
}

if ( empty($ndata) ) exit;	

$display_x = 'unix_timestamp';
$display_y = $f;
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph = new dbemgraph($ndata, $axes[0], $axes[1]);
$dbemgraph->lineplot=true;
$titlename = "Phase Shift by Phase Plate over Time";
$dbemgraph->title = ($preset) ? "$titlename for preset $preset": $titlename;
$yunit = ' (degrees)';
$dbemgraph->yaxistitle= $axes[1].$yunit;

if ($viewdata) {
	//$dbemgraph->dumpData(array($display_x, $display_y));
	$dbemgraph->dumpData();
}
if ($histogram) {
	$dbemgraph->histogram=true;
}


$dbemgraph->scalex(1);
$yscale = 1;
if ($color)
	$dbemgraph->mark->SetFillColor($color);

$dbemgraph->scaley($yscale);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
