<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/leginon.inc";

$g=true;
if (!$session=stripslashes($_GET['session'])) {
	$g=false;
}
if (!$table=stripslashes($_GET['table'])) {
	$table="AcquisitionImageData";
}
if (!$id=stripslashes($_GET['id'])) {
	$g=false;
}
if (!$preset=stripslashes($_GET['preset'])) {
	// $g=false;
}
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/png";
} else {
        $type = "image/jpeg";
	$quality=$t;
}

$minpix = $_GET['np'];
$maxpix = $_GET['xp'];
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	require_once "inc/mrc.inc";
	// --- get image path
	$path = $leginondata->getImagePath($session);
	// --- get parent image info
	$parent = $leginondata->getParent($id, $preset);
	// --- get filename
	$id = $parent[parentId];
	$filename = $leginondata->getFilenameFromId($Id);
	$pic = $path.$filename;
	if (file_exists($pic) && $parent[parentpreset]==$preset) {
		$img = $mrc->imagecreatefromMRC($pic,$new_w,$new_h,$minpix, $maxpix, $quality);
		$white = imagecolorallocate($img, 255, 255, 255);
		$black = imagecolorallocate($img, 0, 0, 0);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$yellow= imagecolorallocate($img, 255, 255, 0);
	  if ($displaytarget) {
		$targets = $leginondata->getImageTargets($id);
		$line=20;
		$diam=20;
		$tn=0;
		foreach ($targets as $target) {
			if (abs($target[x]-$parent[targetx])<5
				&& abs($target[y]-$parent[targety])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$tn++;
			$ratioX = ($size) ? $size/$target[dimx] : 1;
			$ratioY = ($size) ? $size/$target[dimy] : 1;
			$xc = $target[x]*$ratioX;
			$yc = $target[y]*$ratioY;
			imagearc($img, ($target[x]*$ratioX), ($target[y]*$ratioY), $diam*$ratioX, $diam*$ratioY, 0, 360, $crosscol);
			imageline($img, ($target[x]-$line)*$ratioX, ($target[y]*$ratioY), ($target[x]+$line)*$ratioX, ($target[y]*$ratioY), $crosscol); 
			imageline($img, $target[x]*$ratioX, ($target[y]-$line)*$ratioY, $target[x]*$ratioX, ($target[y]+$line)*$ratioY, $crosscol); 
			imagestring($img, 4, $xc+1, $yc+1, $tn, $black);
			imagestring($img, 4, $xc, $yc, $tn, $col);
		}

		$targets = $leginondata->getImageFocusTargets($id);
		$line=20;
		$diam=20;
		$tn='focus';
		foreach ($targets as $target) {
			if (abs($target[x]-$parent[targetx])<5
				&& abs($target[y]-$parent[targety])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$ratioX = ($size) ? $size/$target[dimx] : 1;
			$ratioY = ($size) ? $size/$target[dimy] : 1;
			$xc = $target[x]*$ratioX;
			$yc = $target[y]*$ratioY;
			imagearc($img, ($target[x]*$ratioX), ($target[y]*$ratioY), $diam*$ratioX, $diam*$ratioY, 0, 360, $crosscol);
			imageline($img, ($target[x]-$line)*$ratioX, ($target[y]*$ratioY), ($target[x]+$line)*$ratioX, ($target[y]*$ratioY), $crosscol); 
			imageline($img, $target[x]*$ratioX, ($target[y]-$line)*$ratioY, $target[x]*$ratioX, ($target[y]+$line)*$ratioY, $crosscol); 
			imagestring($img, 4, $xc+1, $yc+1, $tn, $black);
			imagestring($img, 4, $xc, $yc, $tn, $col);
		}
	  }

		Header( "Content-type: $type ");
		if ($t=='png')
			imagepng($img);
		else
			imagejpeg($img,'',$quality);

		imagedestroy($img);
	} else {
		Header("Content-type: image/png");
		$blkimg = imagecreate(256,256);
		$white = imagecolorallocate($blkimg, 255, 255, 255);
//		$black = imagecolorallocate($blkimg, 0, 0, 0);
//		imagestring($blkimg, 4, 10, 128, $preset." ".$parent[0], $black);
		imagepng($blkimg);
		imagedestroy($blkimg);
	}
}
?>
