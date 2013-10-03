<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


require_once "inc/leginon.inc";
require_once "inc/image.inc";
@require_once "inc/project.inc";

$g=true;
if (!$sessionId=stripslashes($_GET['session'])) {
	$g=false;
}

//Block unauthorized user
checkExptAccessPrivilege($sessionId,'data');

if (!$id=stripslashes($_GET['id'])) {
	$g=false;
}

$preset = stripslashes($_GET['preset']);
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/png";
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
if (!$fftbin=$_GET['fftbin']) 
	$fftbin = 'a';

$displayloadingtime = false;
$displayfilename = ($_GET['df']&1) ? true : false;
$displaysample= ($_GET['df']&2) ? true : false;
$loadjpg= ($_GET['lj']==1) ? true : false;
$cacheonly= ($_GET['conly']==1) ? true : false;
$displaynptcl = ($_GET['nptcl']) ? true : false;
$displaylabel = ($_GET['dlbl']) ? true : false;
$colorby = ($_GET['pcb']) ? $_GET['pcb'] : false;
$ptclparams= ($displaynptcl) ? array('colorby'=>$colorby, 'displaylabel'=>$displaylabel, 'info'=>trim($_GET['nptcl'])) : false;

if (!$g) {
	header("Content-type: image/png");
	$blkimg = blankimage(256, 64, "missing sessionid or imgid");
	imagepng($blkimg);
	imagedestroy($blkimg);
} else {
	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'fftbin' => $fftbin,
		'gradient' => $gradient,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'loadjpg' => $loadjpg,
		'cacheonly' => $cacheonly,
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
				'fftbin' => $fftbin,
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

	if (!$img) {
		header("Content-type: image/png");
		$blkimg = blankimage(256, 64, "image not found");
		imagepng($blkimg);
		imagedestroy($blkimg);
		exit();
	}
	
	$nimgId = $leginondata->findImage($id, $preset);
	list($res) = $leginondata->getFilename($nimgId['id']);
	$filename = $res['filename'];
	$filenamelen = strlen($filename);
	$wx = imagesx($img);
	$ypos=10;
	$xpos0=10;
	$pixperchar=6;
	$margin=10;
	$font=5;
	if ($displayfilename) {
		$filenamepixlen = $filenamelen * $pixperchar;
		imagestringshadow($img, $font, $xpos0, $ypos, $filename, imagecolorallocate($img,255,255,255));
		// --- check if filename string fits in imagewidth --- //
		if ($filenamepixlen>$wx) {
			$ypos+=12;
			// --- display rest of filename --- //
			$strlen = -(int)(($filenamepixlen-$wx)/$pixperchar+2);
			$subfilename=substr($filename, $strlen);
			imagestringshadow($img, $font, $xpos0, $ypos, $subfilename, imagecolorallocate($img,255,255,255));
			// --- display sample 12 pix under, if filename is too long
		}
	} else {
		$filenamelen = 0;
	}

	if ($displaysample & SAMPLE_TRACK) {
		$projectdata = new project();
		$info=$leginondata->getSessionInfo($sessionId);
		$tag=$projectdata->getSample($info);
		$taglen = strlen($tag);
		$strlength = ($taglen + $filenamelen ) * 6 + 2 * $margin;
		if ($filenamelen*$pixperchar < $wx && $strlength < $wx) {
			$tagoffset = $taglen*$pixperchar+$margin;
			$xpos = $wx - $tagoffset;
		} else {
			$ypos+=12;
			$xpos = $margin / 2;
		}
		// Wrap sample tag string by syntext
		$tagstrlen = $taglen*$pixperchar + 2 * $margin;
		$tagparsers = array(' ','-',',','_','#','+','%','(');
		while ($tagstrlen > $wx) {
			foreach ($tagparsers as $parser) {
				$tagbits = explode($parser,$tag);
				if (count($tagbits) > 1 && strlen($tagbits[0])*$pixperchar+2*$margin <= $wx) break;
			}
			$tagbitscopy = $tagbits;
			$tagbitlens = array();
			$tagrunninglength = array();
			foreach ($tagbits as $ti=>$ttt) {
				$tagbitlens[] = strlen($ttt);
				$tagrunninglength[] = (array_sum($tagbitlens)+$ti)*$pixperchar + 2 * $margin;
				if ($tagrunninglength[$ti] > $wx) break;
			}
			$tagline = implode($parser,array_slice($tagbitscopy,0,$ti));
			if (strlen($tagline) * $pixperchar + 2 * $margin > $wx) continue;
			// append parser if not the last item
			$tagline = $tagline.$parser;
			imagestringshadow($img, $font, $xpos, $ypos, $tagline, imagecolorallocate($img,255,255,255));
			$tag = substr($tag,strlen($tagline));
			$taglen = strlen($tag);
			$tagstrlen = $taglen*$pixperchar + 2 * $margin;
			$ypos+=12;
		}
		imagestringshadow($img, $font, $xpos, $ypos, $tag, imagecolorallocate($img,255,255,255));
	}

	$filename = preg_replace('%mrc$%', $ext, $filename);

	$imagerequest = new imageRequester();
	$imagerequest->displayImageObj($img,$ext,$quality,$filename);

}

?>
