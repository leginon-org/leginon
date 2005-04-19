<?php
require('inc/image.inc');

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

switch ($_GET['target']) {

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
}

header("Content-type: image/png");
imagepng($img);
imagedestroy($img);

?>
