<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require '../../config.php';
require '../../inc/gradient.php';

if (!$colormap=$_GET['colormap'])
	$colormap=false;
if (!$imgwidth=$_GET['w'])
	$imgwidth=255;
if (!$imgheight=$_GET['h'])
	$imgheight=1;
if (!$displaymark=$_GET['dm'])
	$displaymark=0;
$gradientsize = ($colormap) ? 1275 : 256; 
$step = $gradientsize/$imgwidth; 
$cLeft=0;
if (!$min=$_GET['min'])
	$min = 0;
$max = (is_numeric($_GET['max'])) ? $_GET['max'] : $gradientsize-1;

if (!$gmin=$_GET['gmin'])
	$gmin = 0;
$gmax = (is_numeric($_GET['gmax'])) ? $_GET['gmax'] : $gradientsize-1;


$save=false;
 
$pic=ImageCreateTrueColor($imgwidth,$imgheight);
$gradfunc = ($colormap) ? 'getColorMap' : 'getGrayColor';
if ($_GET['map']) {
	if ($gradients=getGradient($_GET['map'])) {
		$gradfunc = 'getGradientColor';
	}
}
$black = imagecolorallocate($pic, 0, 0, 0);
$green = imagecolorallocate($pic, 0, 255, 0);
$red = imagecolorallocate($pic, 255, 0, 0);

$ratio = ($max-$min<>0) ? $gradientsize/($max-$min):0;

for($gradientval=0;$gradientval<$gradientsize;$gradientval+=$step) {
	$col = ($gradientval-$min)*$ratio;
	$col = ($col>$gmax) ? $gmax : $col;
	$col = ($col<$gmin) ? $gmin : $col;
	$col = $gradfunc($col);
	ImageFilledRectangle($pic, $cLeft, 0, $cLeft+$step, $cTop+$imgheight, $col);
	$cLeft+=1;
}

if ($displaymark) {
	$col = $imgwidth-1;
	imageline ($pic , $col , 0, $col, $cTop+$imgheight, $black);
	$col = $max/$step;
	imageline ($pic , $col, 0, $col, $cTop+$imgheight, $red);
	$col = $min/$step;
	imageline ($pic , $col, 0, $col, $cTop+$imgheight, $green);
}

function getGradientColor($col) {
	global $gradients;
	$c=$gradients[$col];
	return $c;
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
imagepng($pic);
ImageDestroy($pic);
?>
