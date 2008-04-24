<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET['filename'];
$scale = ($_GET['scale']);
$rescale = ($_GET['rescale']);
$s = $_GET['s'];

if (preg_match('`\.mrc$`i',$filename)) {
	$src_mrc = mrcread($filename);
	if ($rescale) {
		// --- scale image values (not size)
		$densitymax=255;
		list($pmin, $pmax) = mrcstdevscale($src_mrc, $densitymax);
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

elseif ($s) {
	$width=imagesx($image);
	$height=imagesy($image);

	$new_width = $s;
	$new_height = $s;
	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}

else $image_p=$image;

// --- create png image
header("Content-type: image/x-png");
imagepng($image_p);

// --- destroy resources in memory
imagedestroy($image_p);
if (is_resource($image))
	imagedestroy($image);
?>
