<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/square.inc');
$g=true;
if (!$session=stripslashes($_GET[session])) {
	$g=false;
}
if (!$table=stripslashes($_GET[table])) {
	$table="AcquisitionImageData";
}
if (!$id=stripslashes($_GET[id])) {
	$g=false;
}
if (!$preset=stripslashes($_GET[preset])) {
	// $g=false;
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
$displaytarget = ($_GET['tg']==1) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	require_once('inc/mrc.inc');
	// --- get image path
	$path = $leginondata->getImagePath($session);
	// --- get parent image info
	$parent = $leginondata->getParent($id, $preset);
	// --- get filename
	$id = $parent[parentId];
	$filename = $leginondata->getFilename($id);
	$pic = $path.$filename;
	if (file_exists($pic) && $parent[parentpreset]==$preset) {
		$img = $mrc->imagecreatefromMRC2($pic,$new_w,$new_h,$minpix, $maxpix, $quality);
		$white = imagecolorallocate($img, 255, 255, 255);
		$black = imagecolorallocate($img, 0, 0, 0);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$yellow= imagecolorallocate($img, 255, 255, 0);
	  if ($displaytarget) {
		$targets = $leginondata->getImageTargets($id);
		$line=20;
		$diam=20;
		foreach ($targets as $target) {
			$tId=$target[parentId];
			$targetinfo = $leginondata->getParentImageInfo($target[parentId]);
			$targetcal = $leginondata->getImageMatrixCalibration($target[parentId]);
			$parentcal = $leginondata->getImageMatrixCalibration($id);
			$truediam=$targetinfo[targetdiam];
			$truedim=$targetinfo[targetdim];
			if (abs($target[x]-$parent[targetx])<5
				&& abs($target[y]-$parent[targety])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$tn = $targetinfo[parentnumber];
			$ratioX = ($size) ? $size/$target[dimx] : 1;
			$ratioY = ($size) ? $size/$target[dimy] : 1;
			$xc = $target[x]*$ratioX;
			$yc = $target[y]*$ratioY;
			$square = new square($xc,$yc, $truedim*$ratioX);
			$angle= $targetcal['angle']-$parentcal['angle'];
			$squarepoints = $square->getRotatedPointCoords($angle);
			$txc = $squarepoints[0]+1;
			$tyc = $squarepoints[1]+1;
			$npoints=count($squarepoints)/2;
			if ($tId) {
				imagepolygon($img, $squarepoints, $npoints, $crosscol);
				imagestring($img, 4, $txc+1, $tyc+1, $tn, $black);
				imagestring($img, 4, $txc, $tyc, $tn, $col);
			}
			
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
			imagejpeg($img,'',$quality);

		imagedestroy($img);
	} else {
		Header("Content-type: image/x-png");
		$blkimg = imagecreate(256,256);
		$white = imagecolorallocate($blkimg, 255, 255, 255);
		imagepng($blkimg);
		imagedestroy($blkimg);
	}
}
?>
