<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

include_once ("processing/inc/particledata.inc");
require_once ("inc/leginon.inc");
include_once "inc/project.inc";
require_once "inc/graph.inc";
require_once "inc/imageutil.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$aligned_imgid=$_GET['id'];
$size = ($_GET['s']) ? $_GET['s'] : 255;
$viewdata=($_GET['vdata']==1) ? true : false;

$width=$size;
$height=$size;

$imageinfo = $leginondata->getImageInfo($aligned_imgid);
$presets = $leginondata->getPresets($aligned_imgid, array('pixelsize'));
// pixelsize from getPresets is camera pixel ?
$pixelsize = $presets['pixelsize']*$imageinfo['binning'];

$particle=new particledata;
// returned data has n, positions, last as keys
$data = $particle->getAlignLogShiftFromDDAlignedImageId($aligned_imgid,$pixelsize*1e10);

if (is_array($data) && $data['n']> 1) {
	$dbemgraph= new dbemgraph($data['positions'], 'x', 'y');
	if ($viewdata) {
		$dbemgraph->dumpData(array('x', 'y'));
	} else {
		$dbemgraph->title="Frame Positions (Angstrom)";
		$dbemgraph->subtitle="solid blue=1st frame";
		$dbemgraph->xaxistitle="x drift (Angstrom)";
		$dbemgraph->yaxistitle="y drift (Angstrom)";
		$dbemgraph->markstart=true;
		$saved_n = count($data['positions']);
		if ($data['n'] > $saved_n) {
			// not all frame positions are saved in db.
			$dbemgraph->subtitle=$dbemgraph->subtitle.", showing first ".$saved_n." frames + solid red=last frame";
			$dbemgraph->extend2last=true;
			$dbemgraph->lastx= (float) $data['last']['x'];
			$dbemgraph->lasty= (float) $data['last']['y'];
		}

		$dbemgraph->proportion(0.0);
		$dbemgraph->dim($width,$height);
		$dbemgraph->graph();
	}
} else {
	$image_util = new imageUtil();
	$error_text = "No movie alignment log available";
	$img = $image_util->makeBlankImageWithErrorMessage($error_text);
	$imagerequest = new imageRequester();
	$imagerequest->displayImageObj($img,'jpg',80,$filename);
}
?>
