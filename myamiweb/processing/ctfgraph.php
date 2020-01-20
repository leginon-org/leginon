<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/particledata.inc";
//require_once "inc/leginon.inc";
require_once "inc/project.inc";

require_once "inc/graph.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$sessionId = $_GET['expId'];
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$cutoff = ($_GET['cutoff']) ? $_GET['cutoff'] : false;
$bydf = ($_GET['bydf']) ? $_GET['bydf'] : 'resolution_50_percent';
$f = $_GET['f'];
$preset= ($_GET['preset']) ? $_GET['preset'] : '';
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = ($_GET['mres']) ? $_GET['mres'] : 20.0; //fit resolution minimal resolution in Angstroms
$width=$_GET['w'];
$height=$_GET['h'];
$xmin = ($_GET['xmin']) ? $_GET['xmin'] : false;
$xmax = ($_GET['xmax']) ? $_GET['xmax'] : false;
$color = ($_GET['color']) ? $_GET['color'] : false;
$pp = ($_GET['pp']) ? $_GET['pp'] : false; // phase plate test summary
$storedCTFinfo = $_GET['ctff'];

$ctf = new particledata();

//If summary is true, get only the data with the best confidence
if ($summary) {
	if ($storedCTFinfo) {
		$ctfinfo = json_decode(file_get_contents($storedCTFinfo), true);
	}
	//See Issue #8481 about why this is implemented
	// And #8482 on why it is reverted to use the old one
	//else $ctfinfo = $ctf->getRandomCtfInfoByResolution($sessionId, $minimum);
	else $ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);
	
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfo($runId);
}

foreach($ctfinfo as $t) {
	if ($preset) {
		$p = $leginondata->getPresetFromImageId($t['imageid']);
		if ($p['name']!=$preset) {
			continue;
		}
	}
	// if looking for confidence, get highest of 3
	if ($f=='confidence') 
		$value = max($t['confidence'],$t['confidence_d'],$t['cross_correlation']);
	elseif ($f=='astig_distribution')
		$value = $t['astig_x'];
	else
		$value=$t[$f];
	// if grouping by cutoff confidence or resolution with one cutoff
	if ($cutoff) {
		// first check if value exists
		if (!$t[$bydf]) continue;
		// check if within set range
		if ((strpos($bydf,'resolution')!== false && $t[$bydf] > $cutoff) ||
		   (strpos($bydf,'resolution') === false && $t[$bydf] < $cutoff))
			continue;
	}
	// group by value with specified max and min
	if ($xmax && $value > $xmax)
		continue;
	if ($xmin && $value < $xmin)
		continue;

	$imageid = $t['imageid'];
	$imageinfo = $leginondata->getMinimalImageInfo($t['imageid']);

	if ($pp ) {
		$ppinfo = $ctf->getPhasePlateInfoFromImageId($imageid);
		if ($ppinfo && $ppinfo['pp_number'] != $pp ) continue;
	}
	$data[$imageid] = $value;
	$where[] = "DEF_id=".$id;
	if ($f!='astig_distribution') {
		$ndata[]=array('unix_timestamp' => $t['unix_timestamp'], 'image_id' => $t['imageid'], 'filename'=>$imageinfo['filename'], "$f"=>$value);
	} else {
		$ndata[]=array('unix_timestamp' => $t['unix_timestamp'], 'image_id' => $t['imageid'], 'filename'=>$imageinfo['filename'], 'astig_x' => $t['astig_x'], "astig_y"=>$t['astig_y']);
	}
}
if ($f == 'astig_distribution') {
	$display_x = 'astig_x';
	$display_y = 'astig_y';
} else {
	$display_x = 'unix_timestamp';
	$display_y = $f;
}
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph = new dbemgraph($ndata, $axes[0], $axes[1]);
//plot type
$is_lineplot = ($f == 'astig_distribution') ? false:true;
$dbemgraph->lineplot=$is_lineplot;
$graph_title = ($f == 'ctffind4_resolution') ? 'package resolution' : $f;
$graph_title = ($preset) ? $graph_title." for preset $preset": $graph_title;
$dbemgraph->title=$graph_title;
//axis titles
//x
$xunit = ($f == 'astig_distribution') ? ' (um)':'';
$xtitle = $axes[0].$xunit;
$dbemgraph->xaxistitle= $xtitle;
//y
$yunit = ($f == 'defocus1' || $f == 'defocus2' || 'astig_distribution') ? ' (um)':'';
$yunit = (strpos($f,'resolution') !== false) ? ' (angstroms)': $yunit;
$ytitle = ($f == 'ctffind4_resolution') ? 'package_resolution': $axes[1];
$ytitle = ($cutoff) ? $ytitle.' avg defocus (um)' : $ytitle.$yunit;
$dbemgraph->yaxistitle= $ytitle;

if ($viewdata) {
	$dbemgraph->dumpData(array('unix_timestamp','image_id','filename',$display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$xscale = ($f == 'astig_distribution') ? 1e-6:1;
$dbemgraph->scalex($xscale);
//y
$yscale = ($f == 'defocus1' || $f == 'defocus2' || $f == 'difference_from_nom' || $f == 'astig_distribution') ? 1e-6:1;
$dbemgraph->scaley($yscale);

if ($color)
	$dbemgraph->mark->SetFillColor($color);


if ($f == 'astig_distribution') {
	$dbemgraph->proportion(0,false);
	$maxdim = max($width,$height);
	$maxdim = ($maxdim) ? $maxdim: max($dbemgraph->width,$dbemgraph->height);
	$width = $maxdim;
	$height = $maxdim;
	$dbemgraph->width = $maxdim;
	$dbemgraph->height = $maxdim;
}
$dbemgraph->dim($width,$height);
$dbemgraph->graph();
?>
