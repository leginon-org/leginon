<?php
$paths = array('.', '..', get_include_path());
set_include_path(implode(PATH_SEPARATOR, $paths));
require_once "config.php";
require_once "inc/leginon.inc";
require_once "inc/imagerequest.inc";

$sigma = 1;
$quality = 75;

$imageId = $_GET['imageId'];
$path = $leginondata->getImagePathFromImageId($imageId);
$filename = $leginondata->getFilenameFromId($imageId);

$filepath = $path.$filename;
$imagerequest = new imageRequester();
$imgstr = $imagerequest->requestImage($filepath,'JPEG',array(128,128),'stdev',-3,3,$sigma,false,false,false,0);
$img = imagecreatefromstring($imgstr);

// --- create png image
header("Content-type: image/jpeg");
imagejpeg($img, '', $quality);
// --- destroy resources in memory
imagedestroy($img);

?> 
