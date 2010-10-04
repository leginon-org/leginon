<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


require 'inc/leginon.inc';
require 'inc/image.inc';

$g=true;
if (!$filename=trim($_GET['id'])) {
	$g=false;
}
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/x-png";
	$ext = "png";
} else {
        $type = "image/jpeg";
	$quality=$t;
	$ext = "jpg";
}


$autoscale = ($_GET['autoscale']==1) ? true : false;
$minpix = ($_GET['np']) ? $_GET['np'] : 0;
$maxpix = ($_GET['xp']) ? $_GET['xp'] : 255;
$size = $_GET['s'];
$displaytarget = ($_GET['tg']==1) ? true : false;
$displayscalebar = ($_GET['sb']==1) ? true : false;
$fft = ($_GET['fft']==1) ? true : false;
if (!$filter=$_GET['flt']) 
	$filter = 'default';
if (!$fftbin=$_GET['fftbin']) 
	$fftbin = 'b';
if (!$binning=$_GET['binning']) 
	$binning = 'auto';

$displayloadingtime = false;

if ($g) {
	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'fftbin' => $fftbin,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'autoscale' => $autoscale,
		'ptcl' => urldecode($displayparticle)
	);

	$img = getImageFile($filename, $params);

	Header( "Content-type: $type ");
	Header( "Content-Disposition: inline; filename=".$filename);
        if ($t=='png')
                imagepng($img);
        else
                imagejpeg($img,'',$quality);
	imagedestroy($img);
} else {
	Header("Content-type: image/x-png");
	$blkimg = blankimage();
	imagedestroy($blkimg);
}

function getImageFile($filename, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
		'fftbin' => 'b',
		'binning' => 'auto',
		'scalebar' => true,
		'loadtime' => false,
		'autoscale' => false,
		'loadjpg' => false,
		'mrc' => false
	);

	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$size = $p['size'];
	$binning = $p['binning'];
	$loadjpg = $p['loadjpg'];

	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['scalebar']=false;
	}

	$pic = $filename;
	if (@is_file($pic)) {
		$info = mrcinfo($pic);
		$dimx = $imginfo['nx'];
		if ($binning=='auto') {
			$binning = 1;
		}

		if ($p['autoscale']) {
			list($type,$arg1, $arg2)=explode(";", $p['autoscale']);
			
			$densitymax = MAX_PIXEL_VAL;
			if ($type=="c") {
				$mrcimg = mrcread($pic);
				list($p['minpix'], $p['maxpix'])=mrccdfscale($mrcimg, $densitymax, $arg1, $arg2);
				mrcdestroy($mrcimg);
			} else {
				$mrcimg = mrcread($pic);
				mrcupdateheader($mrcimg);
				mrcdestroy($mrcimg);
				$minval = $info['amin'];
				$minval = $info['amin'];
				$maxval = $info['amax'];
				$meanval = $info['amean'];
				$stdev = $info['rms'];
		
				if ($meanval && $stdev && $maxval-$minval) {
					$p['minpix'] = (($meanval - 3*$stdev)-$minval)*$densitymax/($maxval-$minval);
					$p['maxpix'] = (($meanval + 3*$stdev)-$minval)*$densitymax/($maxval-$minval);
				}
			}
		}
				
		if ($p['loadtime'])
			$begin=getmicrotime();

		if ($p['mrc']) {
			$imgmrc = mrcread($pic);
			mrcbinning($imgmrc, $binning);
			return $imgmrc;
		}
		if ($p['fft']) {
			$img = getfft($pic, $p['minpix'], $p['maxpix'], $binning, $p['autoscale'],$p['fftbin']);
		}

		else if (function_exists($p['filter']))
			$img = $p['filter']($pic, $p['minpix'], $p['maxpix'], $binning);

		else {
			$img = getdefault($pic, $p['minpix'], $p['maxpix'], $binning);
		}


		$scalefactor=1;
		if ($size) {
#			$scalefactor = (imagesx($img)) ? $size/imagesx($img) : 1;
#			myimagescale($img, $scalefactor);
		}

	} else {
		$img = blankimage();
	}
	return $img;

}

?>
