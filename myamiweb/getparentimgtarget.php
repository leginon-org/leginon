<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/square.inc');
require('inc/scalebar.inc');
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
$fft = ($_GET['fft']==1) ? true : false;


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	require_once('inc/mrc.inc');
	// --- get image path
	$path = $leginondata->getImagePath($session);

	// --- find image
	$newimage = $leginondata->findImage($id, $preset);
	$id = $newimage[id];
	$parent = $leginondata->getImageInfo($newimage[childid]);

	// --- get filename
	if ($fft) {
		$displaytarget=false;
		$displayscalebar=false;
		$fft = $leginondata->getImageFFT($id);
		$filename = $fft[fftimage];
	} else {
		$filename = $leginondata->getFilename($id);
	}

	$pic = $path.$filename;
	if (is_file($pic)) {
		$begin=time();
		$img = $mrc->imagecreatefromMRC($pic,$new_w,$new_h,$minpix, $maxpix, $quality);
		$end=time();
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
			$targetinfo = $leginondata->getImageInfo($tId);
			$targetcal = $leginondata->getImageMatrixCalibration($tId);
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
		if ($displaytime=0) {
			imagestring($img, 4, 11, 11, "load time: ".($end-$begin), $black);
			imagestring($img, 4, 10, 10, "load time: ".($end-$begin), $blue);
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
		$imginfo = $leginondata->getImageInfo($id);
		if ($imginfo) {
			$size = ($size) ? $size : $imginfo[dimx];
			$ratio = $imginfo[dimx]/$size ;
			$value = $imginfo[pixelsize]*$imginfo[binning]*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display();
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
