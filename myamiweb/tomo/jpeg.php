<?php
$paths = array('.', '..', get_include_path());
set_include_path(implode(PATH_SEPARATOR, $paths));
require_once "config.php";
require_once "inc/leginon.inc";
require_once "inc/image.inc";

$binning = 16;
$sigma = 3;
$kernel = 3;
$quality = 75;

$imageId = $_GET['imageId'];
$path = $leginondata->getImagePathFromImageId($imageId);
$filename = $leginondata->getFilenameFromId($imageId);

$src_mrc = mrcread($path.$filename);
list($pmin, $pmax) = mrcstdevscale($src_mrc, 3);
mrcgaussianfilter($src_mrc, $binning, $kernel, $sigma);
$img = mrctoimage($src_mrc,$pmin,$pmax);

// --- create png image
header("Content-type: image/jpeg");
imagejpeg($img, '', $quality);
// --- destroy resources in memory
mrcdestroy($src_mrc);
imagedestroy($img);

?> 
