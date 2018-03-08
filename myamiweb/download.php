<?php
require_once 'inc/leginon.inc';
require_once 'inc/image.inc';
require_once "inc/imagerequest.inc";
$imgId  = $_GET['id'];
$preset = $_GET['preset'];
$fft = ($_GET['fft']==1) ? true : false;
$format = ($_GET['f']) ? $_GET['f']: false;

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];
if (!$sessionId) {
	$sessionId = $leginondata->getSessionInfoFromImage($imgId);
}
$path = $leginondata->getImagePath($sessionId);

//Block unauthorized user
checkExptAccessPrivilege($sessionId,'data');

$pic = getImageFile($leginondata,$imgId,$preset,false,$fft);

$size=filesize($pic);

if (file_exists($pic))  {
	$filename= basename($pic);
	if ($format && $format!="mrc") {
		if ($format=="tiff") {
			$fileformat="TIFF";
			$fileext="tif";
		}
		if ($format=="jpeg") {
			$fileformat="JPEG";
			$fileext="jpg";
		}
		$imagerequest = new imageRequester();
		$imgstr = $imagerequest->requestDefaultFullImage($pic,$fileformat,$fft);
		$filename= preg_replace("%mrc$%",$fileext,$filename);
		$tmpfile=tempnam("/tmp", "leginon");
		file_put_contents($tmpfile,$imgstr);
		$pic=$tmpfile;
		$size=filesize($pic);
	}
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header("Content-Length: $size");
	header('Content-Disposition: attachment; filename="'.$filename.'"');	
	readfile($pic);
} else {
echo "
<script>
alert('file: $pic \\n is not available');
history.go(-1);
</script>
";
}
?>
