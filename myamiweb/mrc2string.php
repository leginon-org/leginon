<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
$g=true;
if (!$session=stripslashes($_GET[session])) {
	$g=false;
}
if (!$table=stripslashes($_GET[table])) {
	$table="AcquisitionImageData";
	// $g=false;
}
if (!$id=stripslashes($_GET[id])) {
	$g=false;
}
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/x-png";
} else {
        $type = "image/jpeg";
	$quality=$t;
}

$minpix = $_GET['np'];
$maxpix = $_GET['xp'];
$size = $_GET['s'];


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	// --- get image path
	$path = $leginondata->getImagePath($session);
	// --- get filename
	$filename = $leginondata->getFilename($id);
	$pic = $path.$filename;
	if (file_exists($pic)) {
		require_once('inc/mrc.inc');
		$img = $mrc->imagecreatefromMRC2($pic,$new_w,$new_h,$minpix, $maxpix, $quality);
		$white = imagecolorallocate($img, 255, 255, 255);
		$black = imagecolorallocate($img, 0, 0, 0);
		$col = imagecolorallocate($img, 255, 255, 255);

		$targets = $leginondata->getImageTargets($id);
		$line=20;
		$diam=20;
		$tn=0;
		foreach ($targets as $target) {
			$tn++;
			$ratioX = $size/$target[dimx];
			$ratioY = $size/$target[dimy];
			$xc = $target[x]*$ratioX;
			$yc = $target[y]*$ratioY;
			imagearc($img, ($target[x]*$ratioX), ($target[y]*$ratioY), $diam*$ratioX, $diam*$ratioY, 0, 360, $white);
			imageline($img, ($target[x]-$line)*$ratioX, ($target[y]*$ratioY), ($target[x]+$line)*$ratioX, ($target[y]*$ratioY), $white); 
			imageline($img, $target[x]*$ratioX, ($target[y]-$line)*$ratioY, $target[x]*$ratioX, ($target[y]+$line)*$ratioY, $white); 
			imagestring($img, 4, $xc+1, $yc+1, $tn, $black);
			imagestring($img, 4, $xc, $yc, $tn, $col);
		}

		$targets = $leginondata->getImageFocusTargets($id);
		$line=20;
		$diam=20;
		$tn='focus';
		foreach ($targets as $target) {
			$ratioX = $size/$target[dimx];
			$ratioY = $size/$target[dimy];
			$xc = $target[x]*$ratioX;
			$yc = $target[y]*$ratioY;
			imagearc($img, ($target[x]*$ratioX), ($target[y]*$ratioY), $diam*$ratioX, $diam*$ratioY, 0, 360, $white);
			imageline($img, ($target[x]-$line)*$ratioX, ($target[y]*$ratioY), ($target[x]+$line)*$ratioX, ($target[y]*$ratioY), $white); 
			imageline($img, $target[x]*$ratioX, ($target[y]-$line)*$ratioY, $target[x]*$ratioX, ($target[y]+$line)*$ratioY, $white); 
			imagestring($img, 4, $xc+1, $yc+1, $tn, $black);
			imagestring($img, 4, $xc, $yc, $tn, $col);
		}


		Header( "Content-type: $type ");
		if ($t=='png')
			imagepng($img);
		else
			imagejpeg($img,'',$quality);

		imagedestroy($img);
	}
}
?>
