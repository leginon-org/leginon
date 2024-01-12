<?php
/*
make cropped image of the target on parent image
*/
require_once "config.php";
require_once "inc/leginon.inc";
require_once "inc/image.inc";

$imageId = $_GET['imageId'];
$size = $_GET['size'] ? $_GET['size']:64;
$target_number = $_GET['tnumber'] ? $_GET['tnumber']:1;
$sigma = 0;
$path = $leginondata->getImagePathFromImageId($imageId);
$filename = $leginondata->getFilenameFromId($imageId);
$filepath = $path.$filename;
$target_results = $leginondata->getImageTargets($imageId, $type="acquisition", $target_number);
$t = $target_results[0];
$imagerequest = new imageRequester();
$image_shape = array($t['dimx'],$t['dimy']);
$imgstr = $imagerequest->requestImage($filepath,'JPEG',$image_shape,'stdev',-5,5,$sigma,false,false,false);
$img = imagecreatefromstring($imgstr);

$crop_params = array('x'=>$t['x']-$size/2,'y'=>$t['y']-$size/2,'width'=>$size,'height'=>$size);
// handle cases when the origin is before (0,0) that results in empty image
// if not apply offset
$under_flowed = false;
if ($crop_params['x'] < 0) {
	$x=0;
	$width = $size + $crop_params['x'];
	$offset_x = -$crop_params['x'];
	$under_flowed = true;
} else {
	$x=$crop_params['x'];
	$width = $size;
	$offset_x = 0;
}
if ($crop_params['y'] < 0) {
	$y=0;
	$height = $size + $crop_params['y'];
	$offset_y = -$crop_params['y'];
	$under_flowed = true;
} else {
	$y=$crop_params['y'];
	$height = $size;
	$offset_y = 0;
}
if (!$under_flowed) {
	// normal behavior
	$img = imagecrop($img,['x'=>$x,'y'=>$y,'width'=>$width,'height'=>$height]);
} else {
	// copy a smaller crop starts at the origin and then copy onto blank img
	$fg = imagecrop($img,['x'=>$x,'y'=>$y,'width'=>$width,'height'=>$height]);
	$img = imagecreate($size, $size);
	imagecopy($img, $fg, $offset_x,$offset_y,0,0,$width,$height);
}
// --- create png image
header("Content-type: image/jpeg");
imagejpeg($img, NULL, 80);
// --- destroy resources in memory
imagedestroy($img);

?>
