<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

define(MIN_PIXEL_VAL, 0); 
define(MAX_PIXEL_VAL, 255); 
define(MAX_COLOR_PIXEL_VAL, 1274); 

function getdefault($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1, $type='default') {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : (($colormap) ? MAX_COLOR_PIXEL_VAL : MAX_PIXEL_VAL);
	if (!is_file($filename))
		return false;

	return imageCreateFromMRC (
		$filename, 
		$minpix, $maxpix,
		$colormap,
		$binning
		);
}

function smooth1($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : (($colormap) ? MAX_COLOR_PIXEL_VAL : MAX_PIXEL_VAL);
	if (!is_file($filename))
		return false;
	$kernel = 5;
	$sigma = 2.73;
	return imageFilteredCreateFromMRC (
			$filename, 
			$minpix, $maxpix,
			$colormap,
			$binning,
			$kernel, $sigma
			);
}

function smooth2($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : (($colormap) ? MAX_COLOR_PIXEL_VAL : MAX_PIXEL_VAL);
	if (!is_file($filename))
		return false;
	$kernel = 5;
	$sigma = 1;
	$img = imageFilteredCreateFromMRC (
			$filename, $minpix,
			$maxpix,
			$colormap,
			$binning,
			$kernel, $sigma
	);
	$kernel = 3;
	$sigma = 2.12;
	imagefiltergaussian($img, $kernel, $sigma);
	return $img;
}

function smooth3($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : (($colormap) ? MAX_COLOR_PIXEL_VAL : MAX_PIXEL_VAL);
	if (!is_file($filename))
		return false;
	$kernel = 3;
	$sigma = 1;
	$img = imageFilteredCreateFromMRC (
			$filename,
			$minpix,
			$maxpix,
			$colormap,
			2,
			$kernel, $sigma
			);
	imagescale($img, .25);
	$kernel = 3;
	$sigma = 1;
	imagefiltergaussian($img, $kernel, $sigma);
	return $img;
}

function smooth4($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : (($colormap) ? MAX_COLOR_PIXEL_VAL : MAX_PIXEL_VAL);
	if (!is_file($filename))
		return false;
	$kernel = 5;
	$sigma = 1;
	$img = imageFilteredCreateFromMRC (
		$filename, $minpix,
		$maxpix, 1,
		$kernel, $sigma
		);
	imagescale($img, .5);
	return $img;
}
