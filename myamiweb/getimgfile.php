<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */


require_once 'inc/leginon.inc';
require_once 'inc/image.inc';

$g=true;
if (!$filename=trim($_GET['id'])) {
	$g=false;
}
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/png";
	$ext = "png";
} else {
        $type = "image/jpeg";
	$quality=$t;
	$ext = "jpg";
}


$autoscale = ($_GET['autoscale']==1) ? true : false;
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$fftbin=$_GET['fftbin']) 
	$fftbin = 'b';
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
		'fftbin' => $fftbin,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'autoscale' => $autoscale,
		'ptcl' => urldecode($displayparticle)
	);

	$img = getImageFromFile($filename, $params);

	Header( "Content-type: $type ");
	Header( "Content-Disposition: inline; filename=".$filename);
        if ($t=='png')
                imagepng($img);
        else
                imagejpeg($img,Null,$quality);
	imagedestroy($img);
} else {
	Header("Content-type: image/png");
	$blkimg = blankimage();
	imagedestroy($blkimg);
}

function getImageFromFile($filename, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
		'fftbin' => 'b',
		'binning' => 'auto',
		'scalebar' => true,
		'loadtime' => false,
		'autoscale' => false,
		'loadjpg' => false,
		'mrc' => false
	);

	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$size = $p['size'];
	$binning = $p['binning'];
	$loadjpg = $p['loadjpg'];

	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['scalebar']=false;
	}

    $imagerequest = new imageRequester();
	$pic = $filename;
    $infoarray = array();
	if (@is_file($pic)) {
	    $info = $imagerequest->requestInfo($pic);
	    $infoarray['dimx']=$info->nx;
	    $infoarray['dimy']=$info->ny;
        $img = getImageFromRequester($pic,$infoarray,$p);

	} else {
		$img = blankimage();
	}
	return $img;

}

?>
