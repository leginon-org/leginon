<?
require('inc/leginon.inc');
$imgId  = $_GET[id];
$preset = $_GET[preset];

$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage[id];
$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilename($imgId);

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
