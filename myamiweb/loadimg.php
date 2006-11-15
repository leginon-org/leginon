<?php
// --- Read an MRC file and display as a PNG
$filename=$_GET[filename];
$scale=$_GET[scale];

list($width, $height) = getimagesize($filename);
$new_width = $width * $scale;
$new_height = $height * $scale;

$image_p = imagecreatetruecolor($new_width, $new_height);
$image = imagecreatefromjpeg($filename);
imagecopyresampled($image_p, $image, 0, 0, 0, 0, $new_width, $new_height, $width, $height);

// Output
//imagejpeg($image_p, null, 100);

 
// --- create png image
header("Content-type: image/x-png");
imagepng($image_p);

// --- destroy resources in memory
imagedestroy($image);
imagedestroy($image_p);
?>
