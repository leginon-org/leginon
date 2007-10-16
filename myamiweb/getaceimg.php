<?php
require('inc/leginon.inc');
require('inc/image.inc');
require('inc/ctf.inc');

$imgId=$_GET['id'];
$preset=$_GET['preset'];
$imgsize=$_GET['s'];
$graph=($_GET['g']=="1") ? "graph1" : "graph2";

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];

$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilenameFromId($imgId);
$ctf = new ctfdata();
$runId = $ctf->getLastCtfRun($sessionId);
list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId);
$filename=$ctfdata['path']."/opimages/".$ctfdata[$graph];
if ($img=@imagecreatefrompng($filename)) {
		resample($img, $imgsize);
} else {
	header("Content-type: image/x-png");
	$blkimg = blankimage();
	imagepng($blkimg);
	imagedestroy($blkimg);
}
?>
