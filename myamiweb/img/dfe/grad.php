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
$imgheight=5; 
$cLeft=0;
if (!$min=$_GET['min'])
	$min = 0;
$max = (is_numeric($_GET['max'])) ? $_GET['max'] : $gradientsize;

if (!$gmin=$_GET['gmin'])
	$gmin = 0;
$gmax = (is_numeric($_GET['gmax'])) ? $_GET['gmax'] : $gradientsize;


 
$pic=ImageCreate($gradientsize*$pixelsize,$imgheight);
for($gradientval=0;$gradientval<$gradientsize;$gradientval++){
	$gray = ($max-$min<>0) ? ($gradientval-$min)*$gradientsize/($max-$min):0;
	$gray = ($gray>$gmax) ? $gmax : $gray;
	$gray = ($gray<$gmin) ? $gmin : $gray;
	ImageFilledRectangle($pic, $cLeft, 0, $cLeft+$pixelsize, $cTop+$imgheight, ImageColorAllocate($pic, $gray, $gray, $gray));
	$cLeft+=$pixelsize;
 }
header("Content-type: image/x-png");
ImagePNG($pic);
ImageDestroy($pic);
?>
