<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$pic=ImageCreate(255,1);
imagecolorallocate($pic, 255, 255, 255);
header("Content-type: image/png");
ImagePNG($pic);
ImageDestroy($pic);
?>
