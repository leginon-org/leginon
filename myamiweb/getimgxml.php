<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


require 'inc/xmldata.inc';
require 'inc/image.inc';

$g=true;
if (!$sessionId=stripslashes($_GET['session'])) {
	$g=false;
}
if (!$id=stripslashes($_GET['id'])) {
	$g=false;
}

$preset = stripslashes($_GET['preset']);
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/x-png";
	$ext = "png";
} else {
        $type = "image/jpeg";
	$quality=$t;
	$ext = "jpg";
}

if (!$displayparticle = $_GET['psel']) 
	$displayparticle = false;

$gradient= ($_GET['gr']) ? $_GET['gr']:false;
$autoscale = ($_GET['autoscale']) ? $_GET['autoscale'] : false;
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$binning=$_GET['binning']) 
	$binning = 'auto';

$displayloadingtime = false;

if ($g) {
	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'autoscale' => $autoscale,
		'ptcl' => urldecode($displayparticle)
	);

	$img = getImageXML($XML_DATA, $id, $preset, $params);

	Header( "Content-type: $type ");
	Header( "Content-Disposition: inline; filename=".$filename);
        if ($t=='png')
                imagepng($img);
        else
                imagejpeg($img,'',$quality);
	imagedestroy($img);
} else {
	Header("Content-type: image/x-png");
	$blkimg = blankimage();
	imagedestroy($blkimg);
}

?>
