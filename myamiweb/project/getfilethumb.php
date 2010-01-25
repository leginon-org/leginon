<?php
require("inc/project.inc.php");
require("inc/note.inc.php");
require("inc/mysql.php");

$n_width = $_GET['w'];
$n_height = $_GET['h'];
$fileId=$_GET['f'];

$note = new notedata();
$fileinfo = $note->getFile($fileId);
$path = $note->getFilePath($fileinfo[projectId]);
$filename = $fileinfo[filename];
$file = $path.$filename;

if (!$source = @imagecreatefromstring(file_get_contents($file))) {
	$source = imagecreate(10,10);
	imagecolorallocate($source, 255, 255, 255);
}

$width  = imagesx($source);
$height = imagesy($source);

if ($n_width) {
        $n_height =  ($n_height) ? $n_height : $height/$width*$n_width;
}
if ($n_height) {
        $n_width = ($n_width) ? $n_width : $width/$height*$n_height;
}

header("Content-type: image/x-png");
if ($n_width && $n_height) {
        $dest = imagecreatetruecolor($n_width, $n_height);
        imagecopyresampled($dest, $source, 0, 0, 0, 0, $n_width, $n_height, $width, $height);
        imagepng($dest);
        imagedestroy($dest);
} else {
        imagepng($source);
}
imagedestroy($source);
?>
