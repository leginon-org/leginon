<?php
// --- Download a video file
$filename=$_GET['filename'];

if (empty($filename)) {
	return;
}
if (file_exists($filename)) {
	header('Content-Length: ' . filesize($filename));
	header("Content-Type: application/octet-stream");
	header("Content-Type: application/force-download");
	header("Content-Type: application/download");
	header('Content-Disposition: attachment; filename="'.basename($filename).'"');
	readfile($filename);
} 
?>