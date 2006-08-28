<?php

require_once('config.php');
require_once('inc/image.inc');

$parameters = array(
	'size' => 64,
	'autoscale' => true,
	'scalebar' => false,
);
$quality = 75;

$imageId = $_GET['imageId'];
$img = getImage($session, $imageId, '', $parameters);

header("Content-type: image/jpeg");
imagejpeg($img, '', $quality);
imagedestroy($img);

?> 
