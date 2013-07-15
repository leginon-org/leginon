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

$defaultId= 1766;
$sessionId= ($_GET['expId']) ? $_GET['expId'] : $defaultId;
$viewdata = ($_GET['vd']==1) ? true : false;
$histogram = ($_GET['hg']==1) ? true : false;
$f = $_GET[f];
$preset=$_GET['preset'];
$summary = ($_GET['s']==1 ) ? true : false;
$minimum = $_GET['mconf'];
$width=$_GET['w'];
$height=$_GET['h'];

$ctf = new particledata();

//If summary is true, get only the data with the best confidence
if ($summary) {
	$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);
} else {
	$runId= ($_GET[rId]);
	$ctfinfo = $ctf->getCtfInfoWithNominal($sessionId, $runId);
}

foreach($ctfinfo as $t) {
	$id = $t['REF|leginondata|AcquisitionImageData|image'];
	$p = $leginondata->getPresetFromImageId($id);
	if ($p['name']!=$preset) {
		continue;
	}
	$data[$id] = $t[$f];
	$datadef[$id] = $t['defocus'];
	$where[] = "DEF_id=".$id;
}

$sqlwhere = "WHERE (".join(' OR ',$where).") and a.`REF|SessionData|session`=".$sessionId ;
$q = 	"select DEF_id, unix_timestamp(DEF_timestamp) as unix_timestamp, "
	." DEF_timestamp as timestamp from AcquisitionImageData a "
	.$sqlwhere;
	$r = $leginondata->getSQLResult($q);
	foreach($r as $row) {
		$e = $leginondata->getPresetFromImageId($row['DEF_id']);
		$ndata[]=array("unix_timestamp" => $row['unix_timestamp'], "$f"=>$data[$row['DEF_id']], "nom_defocus"=>$datadef[$row['DEF_id']]);
//		$datax[]=$row['unix_timestamp'];
		$datax[]=$datadef[$row['DEF_id']];
		$datay[]=$data[$row['DEF_id']];
	}

if ($viewdata) {
	$keys = array("timestamp", "$f" );
	echo dumpData($ndata, $keys);
	exit;
}

$display_x = 'nom_defocus';
$display_y = $f;
$axes = array($display_x,$display_y);
if ($histogram == true && $histaxis == 'x') 
	$axes = array($display_y,$display_x);
$dbemgraph= new dbemgraph($ndata, $axes[0], $axes[1]);
$dbemgraph->lineplot=false;
$dbemgraph->title=$fieldname. ($preset) ? " for preset $preset":'';
$yunit = ($f == 'defocus1' || $f == 'defocus2' || $f == 'difference') ? ' (um)':'';
$dbemgraph->yaxistitle=$axes[1].$yunit;
$dbemgraph->xaxistitle=$axes[0].$yunit;

if ($viewdata) {
	$dbemgraph->dumpData(array($display_x, $display_y));
}
if ($histogram) {
	$dbemgraph->histogram=true;
}

$xscale = ($histogram) ? 1: 1e-6;
$dbemgraph->scalex($xscale);
$yscale = ($f == 'defocus1' || $f == 'defocus2' || $f == 'difference') ? 1e-6:1;
$dbemgraph->scaley($yscale);
$dbemgraph->dim($width,$height);
if ($f == 'difference')
	$dbemgraph->baselineplot=true;

$dbemgraph->graph();

?>
