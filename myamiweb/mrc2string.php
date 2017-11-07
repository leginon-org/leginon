<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";

$g=true;
if (!$session=stripslashes($_GET['session'])) {
	$g=false;
}
if (!$table=stripslashes($_GET['table'])) {
	$table="AcquisitionImageData";
	// $g=false;
}
if (!$id=stripslashes($_GET['id'])) {
	$g=false;
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
$displayscalebar = ($_GET['sb']==1) ? true : false;


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	// --- get image path
	$path = $leginondata->getImagePath($session);
	// --- get filename
	$filename = $leginondata->getFilenameFromId($id);
	$pic = $path.$filename;
	if (file_exists($pic)) {
		require_once "inc/mrc.inc";
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

	  /* display scale bar */
	  if ($displayscalebar) {
		$scales = array (
			'1nm'  => 1e-9,
			'2nm'  => 2e-9,
			'5nm'  => 5e-9,
			'10nm'  => 10e-9,
			'20nm'  => 20e-9,
			'50nm'  => 50e-9,
			'100nm'  => 100e-9,
			'200nm'  => 200e-9,
			'500nm'  => 500e-9,
			'1um'  => 1e-6,
			'2um'  => 2e-6,
			'5um'  => 5e-6,
			'10um' => 10e-6,
			'20um' => 20e-6,
			'50um' => 50e-6,
			'100um' => 100e-6,
			'200um' => 200e-6
		);

		$imginfo = $leginondata->getImageInfo($id);
		if ($imginfo) {
			$pixelsize = $imginfo[pixelsize];
			$binning = $imginfo[binning];
			$size = ($size) ? $size : $imginfo[dimx];
			$ratio = $imginfo[dimx]/$size ;
			$nbpixels = 0;
			$label = "";
			foreach ($scales as $label=>$scale) {
				$nbpixels = $scale/($pixelsize*$binning)/$ratio;
				$r = $size/$nbpixels;
				if ($r > 2 && $r <5) 
					break;
			}

			$h = ($new_h) ? $new_h : $imginfo[dimy];
			$labelfontsize=4;
			$offsetbarX=10;
			$offsetbarY=20;
			$offsetbarlabelX=$offsetbarX+$nbpixels/2;
			$offsetbarlabelY=$h-$offsetbarY-$labelfontsize*4;
			$barX1 = $offsetbarX;
			$barX2 = $nbpixels+$offsetbarX;
			$barY1 = $h-$offsetbarY;
			$barY2 = $h-$offsetbarY+1;


			// --- display label / scale bar
			imagestring($img, $labelfontsize, $offsetbarlabelX+1,
				$offsetbarlabelY+1, $label,$black);
			imagestring($img, $labelfontsize, $offsetbarlabelX,
				$offsetbarlabelY, $label,$white);
			ImageRectangle($img,$barX1-1, $barY1, $barX2+1, $barY2+1,$black);
			ImageRectangle($img,$barX1, $barY1, $barX2, $barY2,$white);
		}
	  }


		Header( "Content-type: $type ");
		if ($t=='png')
			imagepng($img);
		else
			imagejpeg($img,NULL,$quality);

		imagedestroy($img);
	}
}
?>
