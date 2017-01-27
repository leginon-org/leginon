<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

define('MIN_PIXEL_VAL', 0); 
define('MAX_PIXEL_VAL', 255); 

class filter {


	var $filter_types = array (
				'default' => 'Default',
				'smooth1' => 'Smooth 1',
				'smooth2' => 'Smooth 2',
				'smooth3' => 'Smooth 3'
			);

	var $fftbin_types = array (
				'a'=> 'after',
				'b'=> 'before'
			);
	var $binning_types = array (
				'auto' => 'auto',
				1 => 1,
				2 => 2,
				3 => 3,
				4 => 4,
				8 => 8
			);

	function getFilterTypes() {
		return $this->filter_types;
	}

	function getFFTBinTypes() {
		return $this->fftbin_types;
	}

	function getBinningTypes() {
		return $this->binning_types;
	}

}

function getdefault() {
	$sigma = 0;
	return $sigma;

}

function smooth1() {
	$sigma = 2.73;
	return $sigma;
}

function smooth2() {
	$sigma = 1;
	return $sigma;
}

function smooth3() {
	$sigma = 5;
	return $sigma;
}

/*  These old smoothing function requires two pass of lpf that redux does
not handle, yet.

function smooth2($filename="", $minpix="", $maxpix="", $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : MAX_PIXEL_VAL;
	if (!is_file($filename))
		return false;
	$mrcimg = mrcread($filename);
	$kernel = 5;
	$sigma = 1;
	mrcgaussianfilter($mrcimg, $binning, $kernel, $sigma);
	$img = mrctoimage($mrcimg, $minpix, $maxpix);
	mrcdestroy($mrcimg);
	$kernel = 3;
	$sigma = 2.12;
	imagegaussianfilter($img, $kernel, $sigma);
	return $img;
}

function smooth3($filename="", $minpix="", $maxpix="", $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : MAX_PIXEL_VAL;
	if (!is_file($filename))
		return false;
	$mrcimg = mrcread($filename);
	$kernel = 3;
	$sigma = 1;
	mrcgaussianfilter($mrcimg, 2, $kernel, $sigma);
	$img = mrctoimage($mrcimg, $minpix, $maxpix);
	mrcdestroy($mrcimg);
	myimagescale($img, .25);
	$kernel = 3;
	$sigma = 1;
	imagegaussianfilter($img, $kernel, $sigma);
	
	return $img;
}
*/
