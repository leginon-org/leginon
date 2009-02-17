<?php
/**
 *
 * stream a flv file
 *
 *
 **/


$file = htmlspecialchars($_GET["file"]);
$parts=explode("/",$file);
$filename=end($parts);
$ext=strrchr($filename, ".");


if((file_exists($file)) && ($ext==".flv") && (strlen($filename)>2) && (!eregi(basename($_SERVER['PHP_SELF']), $filename)) && (ereg('^[^./][^/]*$', $filename)))
{
        header("Content-Type: video/x-flv");
				header("Content-Disposition: attachment; filename=".$filename);
				readfile($file);
}
?>
