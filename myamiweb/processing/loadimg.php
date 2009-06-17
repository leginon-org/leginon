<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET['filename'];
$scale = ($_GET['scale']);
$rescale = ($_GET['rescale']);
$s = $_GET['s'];
$w = $_GET['w'];
$h = $_GET['h'];
$rawgif = $_GET['rawgif'];

if (preg_match('`\.mrc$`i',$filename)) {
	$src_mrc = mrcread($filename);
	if ($rescale) {
		// --- scale image values (not size)
		list($pmin, $pmax) = mrcstdevscale($src_mrc, 3);
		$image = mrctoimage($src_mrc,$pmin,$pmax);
	}
	else $image = mrctoimage($src_mrc);

	
}

elseif (preg_match('`\.jpg$`i',$filename) || preg_match('`\.jpeg$`i',$filename)) {
	$image = imagecreatefromjpeg($filename);
}

elseif (preg_match('`\.png$`i',$filename)) {
	$image = imagecreatefrompng($filename);
}

if ($scale){
	$width=imagesx($image);
	$height=imagesy($image);

	$new_width = $width * $scale;
	$new_height = $height * $scale;

	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}

elseif ($w) {
	// set width, maintain height ratio
	$width=imagesx($image);
	$height=imagesy($image);

	$new_width = $w;
	$new_height = $height * $w / $width;
	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}

elseif ($h) {
	// set height, maintain width ratio
	$width=imagesx($image);
	$height=imagesy($image);

	$new_height = $h;
	$new_width = $width * $h / $height;

	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}

elseif ($s) {
	// set width and height, force image to be square
	$width=imagesx($image);
	$height=imagesy($image);

	$new_width = $s;
	$new_height = $s;
	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}

else $image_p=$image;


if (preg_match('`\.gif$`i',$filename) && $rawgif) {
	// --- show raw gif
	header("Content-type: image/gif");
	readfile($filename);
} else {
	// --- create png image
	header("Content-type: image/x-png");
	imagepng($image_p);
}

// --- destroy resources in memory
imagedestroy($image_p);
if (is_resource($image))
	imagedestroy($image);
?>
