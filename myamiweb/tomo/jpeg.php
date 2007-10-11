<?php
$paths = array('.', '..', get_include_path());
set_include_path(implode(PATH_SEPARATOR, $paths));
require_once "config.php";
require_once "inc/image.inc";

$binning = 16;
$sigma = 3;
$quality = 75;

$imageId = $_GET['imageId'];
$path = $leginondata->getImagePathFromImageId($imageId);
$filename = $leginondata->getFilenameFromId($imageId);
$input = fopen($path.$filename, 'rb');
if(!$input)
    exit('cannot open file');
$output = fopen('php://output', 'wb');
if(!$output)
    exit('cannot output');

header("Content-type: image/jpeg");
mrc2jpeg($input, $output, $binning, $sigma, $quality);
fclose($input);
fclose($output);

?> 
