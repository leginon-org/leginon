<?
require('inc/leginon.inc');
$id=$_GET[fileId];
$sessionId=$_GET[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilename($id);
$pic = $path.$filename;
if (file_exists($pic))  {
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header("Content-Disposition: attachment; filename=".$filename);
	readfile($pic);
	exit;
} else {
?>
<HTML>
<HEAD>
<LINK rel="stylesheet" href="css/viewer.css" type="text/css"> 
<TITLE>Leginon Image Viewer</TITLE>
</HEAD>
<BODY><H3>
<?
echo " file not found ";
?>
</H3>
<a href="javascript:history.go(-1)">&laquo; Back</a> 
</BODY>
</HTML>
<?
}
?>
