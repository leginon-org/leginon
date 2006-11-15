<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET[filename];
$scale=$_GET[scale];
$rescale=$_GET[rescale];

$src_mrc = mrcread($filename);
 
// --- scale image
$densitymax=255;

if ($rescale) {
        list($pmin, $pmax) = mrcgetscale($src_mrc, $densitymax);
        $img = mrctoimage($src_mrc,$pmin,$pmax);
}
else $img = mrctoimage($src_mrc);

if ($scale) {
        $width=imagesx($img);
	$height=imagesy($img);

	$new_width = $width * $scale;
	$new_height = $height * $scale;

	$image_p = imagecreatetruecolor($new_width, $new_height);
	imagecopyresampled($image_p, $img, 0, 0, 0, 0, $new_width, $new_height, $width, $height);
}
else $image_p=$img;

// --- create png image
header("Content-type: image/x-png");
imagepng($image_p);

// --- destroy resources in memory
mrcdestroy($src_mrc);
imagedestroy($img);
?>
