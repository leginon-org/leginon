<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/array_pystruct.inc');
require('inc/image.inc');

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
		'loadtime' => $displayloadingtime
	);

	if ($preset=='atlas') {
		$mid = $leginondata->getId(
			array('REF|SessionData|session' => $sessionId),
			'MosaicData');

		$mosaic = $leginondata->getMosaicDataInfo($mid);
		$dataIds = get_pystruct_elements(pystruct_to_array($mosaic[0]['SEQ|data IDs']));

		$gridIds = array();
		foreach($dataIds as $did) {
			$gridId = $leginondata->getId(
				array('SEQ|id'=>$did, 'REF|SessionData|session'=>$sessionId)
				);
			if (is_array($gridId)) {
				foreach($gridId as $g)
					if (!in_array($g, $gridIds))
						$gridIds[]=$g;
			}
			else if (!in_array($gridId, $gridIds))
				$gridIds[] = $gridId;
		}

		$imgparams = array(
				 // 'displaytargets' => $displaytarget,
				'displaytargets' => false,
				'filter' => $filter,
				'minpix' => $minpix,
				'maxpix' => $maxpix,
				'scalebar'=>false
			);
		$mosaic = new Mosaic();
		$mosaic->setImageIds($gridIds);
		$mosaic->setImageParams($imgparams);
		$mosaic->setCurrentImageId($id);
		$mosaic->setFrameColor(0,255,0);
		$mosaic->setSize($size);
		$mosaic->displayLoadtime($displayloadingtime);
		$mosaic->displayFrame($displaytarget);
		$mosaic->displayScalebar($displayscalebar);
		$img = $mosaic->getMosaic();
	} else {
		$img = getImage($sessionId, $id, $preset, $params);
	}
	Header( "Content-type: $type ");
	if ($t=='png')
		imagepng($img);
	else
		imagejpeg($img,'',$quality);

	imagedestroy($img);
} else {
	Header("Content-type: image/x-png");
	$blkimg = imagecreate(256,256);
}
?>
