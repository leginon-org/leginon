<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
$g=true;
if (!$session=stripslashes($_GET[session])) {
	$g=false;
}
if (!$table=stripslashes($_GET[table])) {
	$g=false;
}
if (!$id=stripslashes($_GET[id])) {
	$g=false;
}
$t = $_GET['t'];
if ($t=='png') {
        $type = "image/x-png";
} else {
        $type = "image/jpeg";
	$quality=$t;
}

$minpix = $_GET['np'];
$maxpix = $_GET['xp'];
$size = $_GET['s'];


if ($size) {
	$new_w = $size;
	$new_h = $size;
}

if ($g) {
	// --- get filename
	$pic = $leginondata->getFilename($id);
	if (file_exists($pic)) {
		require_once('inc/mrc.inc');
		$img = $mrc->imagecreatefromMRC($pic,$new_w,$new_h,$minpix, $maxpix);
		// --- output a jpeg image with a quality of 100%
		Header( "Content-type: $type ");
		if ($t=='png')
			imagepng($img);
		else
			imagejpeg($img,'',$quality);

		imagedestroy($img);
	}
}
?>
