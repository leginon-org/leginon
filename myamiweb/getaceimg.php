<?php
require "inc/leginon.inc";
require "inc/image.inc";
@require_once "inc/project.inc";
require "inc/particledata.inc";

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
$ctf = new particledata();
$runId = $ctf->getLastCtfRun($sessionId);
list($ctfdata)  = $ctf->getCtfInfoFromImageId($imgId);
$filename=$ctfdata['path']."/opimages/".$ctfdata[$graph];
(array)$imageinfo = @getimagesize($filename);
$imagecreate = 'imagecreatefrompng';
$imagemime = 'image/png';
switch ($imageinfo['mime']) {
	case 'image/jpeg':
		$imagecreate = "imagecreatefromjpeg";
		$imagemime = $imageinfo['mime'];
	break;
}

if ($img=@$imagecreate($filename)) {
		resample($img, $imgsize);
} else {
	header('Content-type: '.$imagemime);
	$blkimg = blankimage();
	imagepng($blkimg);
	imagedestroy($blkimg);
}
?>
