<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/image.inc');
require('inc/cachedb.inc');
$cachehost = 'cronus1';
// $cachehost = 'stratocaster';
// $cache=True;
$cache=False;

$g=true;
if (!$sessionId=stripslashes($_GET[session])) {
	$g=false;
}
if (!$table=stripslashes($_GET[table])) {
	$table="AcquisitionImageData";
}
if (!$id=stripslashes($_GET[id])) {
	$g=false;
}

$preset = stripslashes($_GET[preset]);
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/x-png";
} else {
        $type = "image/jpeg";
	$quality=$t;
}

if ($cache) {
	$begin=getmicrotime();
	$uri = "http://".$_SERVER[SERVER_NAME].$REQUEST_URI;
	$cachedb = new cachedb($cachehost, 'usr_object', '', 'cache');
	if ($image = $cachedb->get($uri)) {
		Header( "Content-type: $type ");
		$img = imagecreatefromstring($image);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$end=getmicrotime();
		imagestringshadow($img, 4, 10, 30, "cache time: ".($end-$begin), $blue);
		if ($t=='png')
			imagepng($img);
		else
			imagejpeg($img,'',$quality);
		imagedestroy($img);
		exit;
	}
}

$colormap = ($_GET['colormap']==1) ? "1" : "0";
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : (($colormap) ? 1274 : 255);
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$binning=$_GET['binning']) 
	$binning = 'auto';

$displayloadingtime = true;

if ($g) {
	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'colormap' => $colormap,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime
	);

	if ($preset=='atlas') {
		
		$dtypes = $leginondata->getDataTypes($sessionId);
		foreach ($dtypes as $dtype) {
			$d = $leginondata->findImage($id, $dtype);
			$nId = $d['id'];
			if ($gridIds = $leginondata->getMosaicImages($nId))
				break;
		}

		$imgparams = array(
				 // 'displaytargets' => $displaytarget,
				'displaytargets' => false,
				'filter' => $filter,
				'minpix' => $minpix,
				'maxpix' => $maxpix,
				'binning' => $binning,
				'scalebar'=>false
			);
		
		$mosaic = new Mosaic();
		$mosaic->setImageIds($gridIds);
		$mosaic->setImageParams($imgparams);
		$mosaic->setCurrentImageId($nId);
		$mosaic->setFrameColor(0,255,0);
		$mosaic->setSize($size);
		$mosaic->displayLoadtime($displayloadingtime);
		$mosaic->displayFrame($displaytarget);
		$mosaic->displayScalebar($displayscalebar);
		$img = $mosaic->getMosaic();
	} else {
		$img = getImage($sessionId, $id, $preset, $params);
	}
if ($cache) {
	ob_start();
	Header( "Content-type: $type ");
	if ($t=='png')
		imagepng($img);
	else
		imagejpeg($img,'',$quality);
	$stringimage = ob_get_contents();
	imagedestroy($img);
	ob_clean();
	$re = $cachedb->put($uri, $stringimage);
	echo $stringimage;
} else {
	Header( "Content-type: $type ");
        if ($t=='png')
                imagepng($img);
        else
                imagejpeg($img,'',$quality);
	imagedestroy($img);
}
} else {
	Header("Content-type: image/x-png");
	$blkimg = blankimage();
	imagedestroy($blkimg);
}
?>
