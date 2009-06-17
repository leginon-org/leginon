<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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

	var $binning_types = array (
				'auto' => 'auto',
				1 => 1,
				2 => 2,
				3 => 3,
				4 => 4,
				5 => 5
			);

	function getFilterTypes() {
		return $this->filter_types;
	}

	function getBinningTypes() {
		return $this->binning_types;
	}

}

function getfft($filename="", $minpix="", $maxpix="", $binning=1, $autoscale=false) {
	list($type,$arg1, $arg2)=explode(";", $autoscale);
	$mrcimg = mrcread($filename);
	mrcfftw($mrcimg,10);
	mrcbinning($mrcimg, $binning);
	if ($autoscale) {
		if ($type=="c") {
			list($minpix, $maxpix)=mrccdfscale($mrcimg, $arg1, $arg2);
		} else {
			list($minpix, $maxpix) = mrcstdevscale($mrcimg, $arg1);
		}
	}
	$img = mrctoimage($mrcimg, $minpix, $maxpix);
	mrcdestroy($mrcimg);
	return $img;
}

function getdefault($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1, $type='default') {
	$densitymax = MAX_PIXEL_VAL;
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : $densitymax;
	
	if (!is_file($filename))
		return false;
	$mrcimg = mrcread($filename);
	$info = mrcgetinfo($mrcimg);
	mrcbinning($mrcimg, $binning);
	$img = mrctoimage($mrcimg, $minpix, $maxpix);
	mrcdestroy($mrcimg);
	return $img;

}

function smooth1($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
	$minpix = ($minpix) ? $minpix : MIN_PIXEL_VAL;
	$maxpix = ($maxpix) ? $maxpix : MAX_PIXEL_VAL;
	if (!is_file($filename))
		return false;
	$kernel = 5;
	$sigma = 2.73;
	$mrcimg = mrcread($filename);
	mrcgaussianfilter($mrcimg, $binning, $kernel, $sigma);
	$img = mrctoimage($mrcimg, $minpix, $maxpix);
	mrcdestroy($mrcimg);
	return $img;
}

function smooth2($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
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

function smooth3($filename="", $minpix="", $maxpix="", $colormap=false, $binning=1 ) {
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
