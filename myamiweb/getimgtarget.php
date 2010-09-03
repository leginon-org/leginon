<?php

require "inc/image.inc";

$img = imagecreatetruecolor(15,15);
$bg= imageColorAllocate($img, 255, 255, 255);
imagefill($img,0,0,$bg);
$col = imageColorAllocate($img, 0, 0, 0);
$cx = 7;
$cy = 7;
$size = 15;
$angle = 45;
$shadow=false;
$arc = 0;
$target = trim($_GET['target']);
$c=$_GET['c'];
if (is_numeric($c)) {
	$hexc = $pick_colors[$c];
	$col = imagecolorallocatehex($img, $hexc);
}
switch ($target) {

	case "cir1":
		drawcircle($img, $cx, $cy, $size, $col, $shadow);
		break;
	case "cross1":
		$size = 15;
		drawcross ($img, $cx, $cy, $size, $col, $arc, $angle, $shadow);
		break;
	case "cross2":
		$size = 10;
		$angle = 0;
		drawcross ($img, $cx, $cy, $size, $col, $arc, $angle, $shadow);
		break;
	case "box1":
		$size = 9;
		$angle = 0;
		drawbox ($img, $cx, $cy, $size, $col, $angle, $shadow);
		break;
}

header("Content-type: image/png");
imagepng($img);
imagedestroy($img);

?>
