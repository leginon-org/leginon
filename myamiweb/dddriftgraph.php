<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include_once ("processing/inc/particledata.inc");
require_once ("inc/leginon.inc");
include_once "inc/project.inc";
require_once "inc/graph.inc";
require_once "inc/imageutil.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$aligned_imgid=$_GET['id'];
$size = ($_GET['s']) ? $_GET['s'] : 255;

$width=$size;
$height=$size;

$particle=new particledata;
$data = $particle->getAlignLogFromDDAlignedImageId($aligned_imgid);

if (is_array($data) && (count($data)> 1)) {
	$dbemgraph= new dbemgraph($data, 'x', 'y');
	$dbemgraph->title="drift (pixels per frame)";
	$dbemgraph->xaxistitle="x drift (pixels)";
	$dbemgraph->yaxistitle="y drift (pixels)";
	$dbemgraph->markstart=true;

	$dbemgraph->proportion(0.0);
	$dbemgraph->dim($width,$height);
	$dbemgraph->graph();
} else {
	$image_util = new imageUtil();
	$error_text = "No movie alignment log available";
	$img = $image_util->makeBlankImageWithErrorMessage($error_text);
	$imagerequest = new imageRequester();
	$imagerequest->displayImageObj($img,'jpg',80,$filename);
}
?>
