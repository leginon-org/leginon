<?php
require_once "inc/particledata.inc";
$field = $_GET['f'];
$id = $_GET['id'];
$n_width = $_GET['w'];
$n_height = $_GET['h'];
$ctf = new particledata;
$blob = $ctf->getCTFBlobs($field, $id);
header("Content-type: image/png");
$source = imagecreatefromstring($blob);
$width  = imagesx($source);
$height = imagesy($source);
if ($n_width) {
	$n_height =  ($n_height) ? $n_height : $height/$width*$n_width;
}
if ($n_height) {
	$n_width = ($n_width) ? $n_width : $width/$height*$n_height;
}
if ($n_width && $n_height) {
	$dest = imagecreatetruecolor($n_width, $n_height);
	imagecopyresampled($dest, $source, 0, 0, 0, 0, $n_width, $n_height, $width, $height);
	imagepng($dest);
	imagedestroy($dest);
} else {
	imagepng($source);
}
imagedestroy($source);
?>
