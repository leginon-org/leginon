<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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
$f = $_GET['f'];
$preset= ($_GET['preset']) ? $_GET['preset'] : '';
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = ($_GET['mconf']) ? $_GET['mconf'] : 0.2;
$width=$_GET['w'];
$height=$_GET['h'];
$xmin = ($_GET['xmin']) ? $_GET['xmin'] : false;
$xmax = ($_GET['xmax']) ? $_GET['xmax'] : false;
$color = ($_GET['color']) ? $_GET['color'] : false;

$ctf = new particledata();

//If summary is true, get only the data with the best confidence
if ($summary) {
	$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfo($runId);
}

foreach($ctfinfo as $t) {
	if ($preset) {
		$p = $leginondata->getPresetFromImageId($id);
		if ($p['name']!=$preset) {
			continue;
		}
	}
	// if looking for confidence, get highest of 3
	if ($f=='confidence') 
		$value = max($t['confidence'],$t['confidence_d'],$t['cross_correlation']);
	else
		$value=$t[$f];

	// if grouping by defocus, set cutoff
	if ($cutoff) {
		// first check if value exists
		if (!$t[$bydf]) continue;
		// check if within set range
		if ((substr($bydf,0,10)=='resolution' && $t[$bydf] > $cutoff) ||
		   (substr($bydf,0,10)!='resolution' && $t[$bydf] < $cutoff))
			continue;
		// get average defocus
		$df1=$t['defocus1'];
		$df2=$t['defocus2'];
		$value = ($df1+$df2)/2;
	}

	if ($xmax && $value > $xmax)
		continue;
	if ($xmin && $value < $xmin)
		continue;

	$imageid = $t['imageid'];
	$data[$imageid] = $value;
	$where[] = "DEF_id=".$id;
	$ndata[]=array('unix_timestamp' => $t['unix_timestamp'], "$f"=>$value);
}

$display_x = 'unix_timestamp';
$display_y = $f;
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph = new dbemgraph($ndata, $axes[0], $axes[1]);
$dbemgraph->lineplot=true;
$dbemgraph->title=$fieldname. ($preset) ? " for preset $preset":'';
$yunit = ($f == 'defocus1' || $f == 'defocus2') ? ' (um)':'';
$dbemgraph->yaxistitle= ($cutoff) ? 'avg defocus (um)' : $axes[1].$yunit;

if ($viewdata) {
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}


$dbemgraph->scalex(1);
$yscale = ($f == 'defocus1' || $f == 'defocus2') ? 1e-6:1;
if ($color)
	$dbemgraph->mark->SetFillColor($color);

$dbemgraph->scaley($yscale);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
