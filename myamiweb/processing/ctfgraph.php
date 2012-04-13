<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";

require "inc/graph.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$sessionId = $_GET['expId'];
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$f = $_GET['f'];
$preset= ($_GET['preset']) ? $_GET['preset'] : '';
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = ($_GET['mconf']) ? $_GET['mconf'] : 0.2;
$width=$_GET['w'];
$height=$_GET['h'];

$ctf = new particledata();

//If summary is true, get only the data with the best confidence
if ($summary) {
	$ctfinfo = $ctf->getBestCtfInfoForSessionId($sessionId, $minimum);
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfo($runId);
}

foreach($ctfinfo as $t) {
	$id = $t['REF|leginondata|AcquisitionImageData|image'];
	$p = $leginondata->getPresetFromImageId($id);
	if ($preset && $p['name']!=$preset) {
		continue;
	}
	// if looking for confidence, get highest of 3
	if ($f=='confidence') 
		$conf = max($t['confidence'],$t['confidence_d'],$t['cross_correlation']);
	else $conf=$t[$f];

	$data[$id] = $conf;
	$where[] = "DEF_id=".$id;
}
$sqlwhere = "WHERE (".join(' OR ',$where).") and a.`REF|SessionData|session`=".$sessionId ;
$q = 	"select DEF_id, unix_timestamp(DEF_timestamp) as unix_timestamp, "
	." DEF_timestamp as timestamp from AcquisitionImageData a "
	.$sqlwhere;
	$r = $leginondata->getSQLResult($q);
	foreach($r as $row) {
		$e = $leginondata->getPresetFromImageId($row['DEF_id']);
		$ndata[]=array("unix_timestamp" => $row['unix_timestamp'], "$f"=>$data[$row['DEF_id']]);
		$datax[]=$row['unix_timestamp'];
		$yval = $data[$row['DEF_id']];
		if (!$yval) $yval='';
		$datay[]=$yval;
	}

$display_x = 'unix_timestamp';
$display_y = $f;
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph=&new dbemgraph($ndata, $axes[0], $axes[1]);
$dbemgraph->lineplot=true;
$dbemgraph->title=$fieldname. ($preset) ? " for preset $preset":'';
$yunit = ($f == 'defocus1' || $f == 'defocus2') ? ' (um)':'';
$dbemgraph->yaxistitle=$axes[1].$yunit;

if ($viewdata) {
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}


$dbemgraph->scalex(1);
$yscale = ($f == 'defocus1' || $f == 'defocus2') ? 1e-6:1;
$dbemgraph->scaley($yscale);
$dbemgraph->dim($width,$height);
$dbemgraph->graph();

?>
