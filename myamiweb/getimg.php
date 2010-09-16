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
$displaylabel = ($_GET['dlbl']) ? true : false;
$colorby = ($_GET['pcb']) ? $_GET['pcb'] : false;
$ptclparams= ($displaynptcl) ? array('colorby'=>$colorby, 'displaylabel'=>$displaylabel, 'info'=>trim($_GET['nptcl'])) : false;

if ($g) {

	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
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
$tag = "123-c test tewwsdetgdga sdfasdfdadf test# testd";
		$margin=10;
		$ypos=10;
		$wx = imagesx($img);
		$taglen = strlen($tag);
		$filenamelen = strlen($filename);
		$tagoffset = $taglen*6+$margin;
		$xpos = $wx - $tagoffset;
		$pixperchar=6;
		$strlength = ($taglen + $filenamelen ) * 6 + 2 * $margin + 5;
		if ($wx<$strlength) {
			// --- display sample 12 pix under, if filename is too long
			$ypos+=12;
			// --- check if filename string fits in imagewidth --- //
			$filenamepixlen = $filenamelen * $pixperchar;
			if ($filenamepixlen>$wx) {
			// --- display rest of filename --- //
			$strlen = -(int)(($filenamepixlen-$wx)/$pixperchar+2);
			$subfilename=substr($filename, $strlen);
			imagestringshadow($img, 2, 10, $ypos, $subfilename, imagecolorallocate($img,255,255,255));
			$ypos+=12;
			}
		}
		$tagstrlen = $taglen*$pixperchar + 2 * margin + 5;
		$xpos = 5;
		while ($tagstrlen > $wx) {
			$tagbits = explode(' ',$tag);
			$tagbitscopy = $tagbits;
			$tagbitlens = array();
			$tagrunninglength = array();
			foreach ($tagbits as $ti=>$t) {
				$tagbitlens[] = strlen($t);
				$tagrunninglength[] = (array_sum($tagbitlens)+$ti)*$pixperchar + 2 * margin + 5;
				if ($tagrunninglength[$ti] > $wx) {
					$tagline = implode(' ',array_slice($tagbitscopy,0,$ti-1));
					imagestringshadow($img, 2, $xpos, $ypos, $tagline, imagecolorallocate($img,255,255,255));
					$tag = substr($tag,strlen($tagline));
					$taglen = strlen($tag);
					$tagstrlen = $taglen*$pixperchar + 2 * margin + 5;
					$ypos+=12;
				}
			}
		}
		imagestringshadow($img, 2, $xpos, $ypos, $tag, imagecolorallocate($img,255,255,255));
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
