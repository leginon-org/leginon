<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

// ---  Gray gradient
$gradientsize=255; 
$pixelsize=1; 
$imgheight=1; 
$cLeft=0;
$min=$_GET['min'];
$max=$_GET['max'];
$min = ($min) ? $min : 0;
$max = ($max || $max==0) ? $max : $gradientsize;
 
$pic=ImageCreate($gradientsize*$pixelsize,$imgheight);
for($gradientval=0;$gradientval<$gradientsize;$gradientval++){
	$gray = ($max-$min<>0) ? ($gradientval-$min)*$gradientsize/($max-$min):0;
	$gray = ($gray>$gradientsize) ? $gradientsize : $gray;
	$gray = ($gray<0) ? $gray=0 : $gray;
	ImageFilledRectangle($pic, $cLeft, 0, $cLeft+$pixelsize, $cTop+$imgheight, ImageColorAllocate($pic, $gray, $gray, $gray));
	$cLeft+=$pixelsize;
 }
header("Content-type: image/x-png");
ImagePNG($pic);
ImageDestroy($pic);
?>
