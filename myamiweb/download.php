<?php
require 'inc/leginon.inc';
$imgId  = $_GET['id'];
$preset = $_GET['preset'];
$fft = ($_GET['fft']==1) ? true : false;
$format = ($_GET['f']) ? $_GET['f']: false;

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage['id'];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo['sessionId'];
$path = $leginondata->getImagePath($sessionId);
if ($fft) {
	$fftimg = $leginondata->getImageFFT($imgId);
	$filename = $fftimg['fftimage'];
} else {
	$filename = $leginondata->getFilenameFromId($imgId);
}


$pic=$path.$filename;
$size=filesize($pic);
if (file_exists($pic))  {
	if ($format && $format!="mrc") {
		if ($format=="tiff") {
			$fileformat="TIFF";
			$fileext="tif";
		}
		if ($format=="jpeg") {
			$fileformat="JPEG";
			$fileext="jpg";
		}
		$filename=ereg_replace("mrc$", $fileext, $filename);
		$tmpfile=tempnam("/tmp", "dbem");
		if (!is_file(MRC2ANY)) {
			echo "
			<script>
			alert('file: ".MRC2ANY." \\n not found');
			history.go(-1);
			</script>
			";
			exit;
		}
		$cmd=MRC2ANY." $pic -f $fileformat $tmpfile";
		passthru($cmd);
		$pic=$tmpfile;
		$size=filesize($pic);
	}
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
