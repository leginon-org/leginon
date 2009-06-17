<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


require "inc/leginon.inc";
require "inc/image.inc";
@require_once "inc/project.inc";

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


$colormap = ($_GET['colormap']==1) ? "1" : "0";
$gradient= ($_GET['gr']) ? $_GET['gr']:false;
$autoscale = ($_GET['autoscale']) ? $_GET['autoscale'] : false;
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;
$nptclsel = ($_GET['psel']) ? $_GET['psel'] : 0;
$displaynptcl = ($_GET['nptcl']) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$binning=$_GET['binning']) 
	$binning = 'auto';

$displayloadingtime = false;
$displayfilename = ($_GET['df']&1) ? true : false;
$displaysample= ($_GET['df']&2) ? true : false;
$loadjpg= ($_GET['lj']==1) ? true : false;
$displaynptcl = ($_GET['nptcl']) ? true : false;
$correlationmin=($_GET['cm']) ? $_GET['cm'] : false;
$correlationmax=($_GET['cx']) ? $_GET['cx'] : false;
$ptclparams= ($displaynptcl) ? array('cm'=>$correlationmin, 'cx'=>$correlationmax, 'info'=>trim($_GET['nptcl'])) : false;

if ($g) {

	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'colormap' => $colormap,
		'gradient' => $gradient,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'loadjpg' => $loadjpg,
		'autoscale' => $autoscale,
		'newptcl' => $ptclparams,
		'ptclsel' => $nptclsel
	);

	if ($preset=='atlas') {
		
		$dtypes = $leginondata->getDataTypes($sessionId);
		foreach ($dtypes as $dtype) {
			$d = $leginondata->findImage($id, $dtype);
			$nId = $d['id'];
			if ($gridIds = $leginondata->getImageList($nId))
				break;
		}

		$imgparams = array (
				 // 'displaytargets' => $displaytarget,
				'displaytargets' => false,
				'filter' => $filter,
				'minpix' => $minpix,
				'maxpix' => $maxpix,
				'binning' => $binning,
				'colormap' => $colormap,
				'autoscale' => $autoscale,
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

	$nimgId = $leginondata->findImage($id, $preset);
	list($res) = $leginondata->getFilename($nimgId['id']);
	$filename = $res['filename'];
	if ($displayfilename) {
		imagestringshadow($img, 2, 10, 10, $filename, imagecolorallocate($img,255,255,255));
	}
	if ($displaysample) {
		$projectdata = new project();
		$info=$leginondata->getSessionInfo($sessionId);
		$tag=$projectdata->getSample($info);
		$margin=10;
		$tagoffset=strlen($tag)*6+$margin;
		$xpos=imagesx($img)-$tagoffset;
		imagestringshadow($img, 2, $xpos, 10, $tag, imagecolorallocate($img,255,255,255));
	}

	$filename = ereg_replace('mrc$', $ext, $filename);

	header( "Content-type: $type ");
	header( "Content-Disposition: inline; filename=".$filename);
        if ($t=='png')
                imagepng($img);
        else
                imagejpeg($img,'',$quality);
	imagedestroy($img);
} else {
	header("Content-type: image/x-png");
	$blkimg = blankimage();
	imagepng($blkimg);
	imagedestroy($blkimg);
}

?>
