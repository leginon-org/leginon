<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

if (!$colormap=$_GET['colormap'])
	$colormap=false;
if (!$imgwidth=$_GET['w'])
	$imgwidth=255;
if (!$imgheight=$_GET['h'])
	$imgheight=1;
$gradientsize = ($colormap) ? 1275 : 256; 
$step = $gradientsize/$imgwidth; 
$cLeft=0;
if (!$min=$_GET['min'])
	$min = 0;
$max = (is_numeric($_GET['max'])) ? $_GET['max'] : $gradientsize-1;

if (!$gmin=$_GET['gmin'])
	$gmin = 0;
$gmax = (is_numeric($_GET['gmax'])) ? $_GET['gmax'] : $gradientsize-1;


 
$pic=ImageCreateTrueColor($imgwidth,$imgheight);
$gradfunc = ($colormap) ? 'getColorMap' : 'getGrayColor';

for($gradientval=0;$gradientval<$gradientsize;$gradientval+=$step) {
	$col = ($max-$min<>0) ? ($gradientval-$min)*$gradientsize/($max-$min):0;
	$col = ($col>$gmax) ? $gmax : $col;
	$col = ($col<$gmin) ? $gmin : $col;
	$col = $gradfunc($col);
	ImageFilledRectangle($pic, $cLeft, 0, $cLeft+$step, $cTop+$imgheight, $col);
	$cLeft+=1;
}

function getGrayColor($v) {
	$col = ($v << 16) + ($v << 8) + $v;
	return $col;
}

function getColorMap($v) {
	$c = floor($v%255);
	if ($v<255) {
		$colormap = ((255 << 16) + ($c << 8) + 0);
	} else if ($v<255*2) {
		$colormap = (((255-$c) << 16) + (255 << 8) + 0);
	} else if ($v<255*3) {
		$colormap = ((0 << 16) + (255 << 8) + $c);
	} else if ($v<255*4) {
		$colormap = ((0 << 16) + ((255-$c) << 8) + 255);
	} else if ($v<=255*5) {
		$colormap = (($c << 16) + (0 << 8) + 255);
	} 
	return $colormap;
}

header("Content-type: image/x-png");
ImagePNG($pic);
ImageDestroy($pic);
?>
