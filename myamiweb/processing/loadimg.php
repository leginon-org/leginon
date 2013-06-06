<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET['filename'];
$scale = ($_GET['scale']);
$rescale = ($_GET['rescale']);
$s = $_GET['s'];
$w = $_GET['w'];
$h = $_GET['h'];
$rawgif = $_GET['rawgif'];
$cacheOff = $_GET['coff'];
$overlay = $_GET['overlay'];

if (empty($filename)) {
	return;
}
if (preg_match('`\.gif$`i',$filename) && $rawgif) {
	// --- show raw gif
	header("Content-type: image/gif");
	readfile($filename);
} else {
	require_once "../inc/imagerequest.inc";
	$imagerequest = new imageRequester();
	// find out the proper x, y for display
	$imginfo = $imagerequest->requestInfo($filename);
	$pmin = $imginfo->amin;
	$pmax = $imginfo->amax;
	$height = $imginfo->ny;
	$width = $imginfo->nx;
	$oformat = 'PNG';
	$frame=0;
	if ($scale) {
		$new_width = (int) ($width * $scale);
		$new_height = (int) ($height * $scale);
	}
	elseif ($w) {
		// set width, maintain height ratio
		$new_width = (int) $w;
		$new_height = (int) ($height * $w / $width);
	}
	elseif ($h) {
		// set height, maintain width ratio
		$new_height = (int) $h;
		$new_width = (int) ($width * $h / $height);
	}
	elseif ($s) {
		// set width and height, force image to be square
		$new_width = (int) $s;
		$new_height = (int) $s;
	}
	else {
		// set to original width and heigth
		$new_width = (int) $width;
		$new_height = (int) $height;
	}
	$xyDim = array($new_width, $new_height);

	$rgb = (substr_compare($filename,'jpg',-3,true) || substr_compare($filename,'png',-3,true)) ? true:false;
	$frame = (substr_compare($filename,'jpg',-3,true) || substr_compare($filename,'png',-3,true)) ? null:$frame;
	// request image
	//TODO: this does not work. The minmax method seems to be not working in redux.
	if (0/*!$rescale && $pmin != $pmax*/) 
		$imgstr = $imagerequest->requestImage($filename,$oformat,$xyDim,'minmax',$pmin,$pmax,0,$rgb,false,$cacheOff,$frame,$overlay);
	else
		$imgstr = $imagerequest->requestImage($filename,$oformat,$xyDim,'stdev',-3,3,0,$rgb,false,$cacheOff,$frame,$overlay);
	$imagerequest->displayImageString($imgstr,$oformat,$filename);
}

?>
