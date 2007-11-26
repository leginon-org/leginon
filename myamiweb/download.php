<?php
require "inc/leginon.inc";

$imgId  = $_GET['id'];
$preset = $_GET['preset'];
$fft = ($_GET['fft']==1) ? true : false;

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage[id];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
if ($fft) {
	$fftimg = $leginondata->getImageFFT($imgId);
	$filename = $fftimg[fftimage];
} else {
	$filename = $leginondata->getFilenameFromId($imgId);
}


$pic  = $path.$filename;
$size = filesize($path.$filename);
if (file_exists($pic))  {
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header("Content-Length: $size");
	header("Content-Disposition: attachment; filename=".$filename);
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
