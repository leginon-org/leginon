<?php
// --- Read an mp4, webm, or ogv file for HTML5 video
$filename=$_GET['filename'];

if (empty($filename)) {
	return;
}
if (file_exists($filename)) {
	header('Content-Length: ' . filesize($filename));
	readfile($filename);
} 
?>
