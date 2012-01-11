<?php
// --- steam flash video --- //


// --- full path to dir with video.
$file = htmlspecialchars($_GET["file"]);
$parts=explode("/",$file);
$filename=end($parts);
$ext=strrchr($filename, ".");

if((file_exists($file)) && ($ext==".flv") && (strlen($filename)>2) && (!preg_match('%'.basename($_SERVER['PHP_SELF']).'%i', $filename)) && (preg_match('%^[^./][^/]*$%', $filename)))
{
        header("Content-Type: video/x-flv");
				header("Content-Disposition: attachment; filename=".$filename);
				readfile($file);
}
?>
