<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$pic=ImageCreate(255,10);
ImageColorAllocat($pic, 255, 155, 255);
header("Content-type: image/x-png");
ImagePNG($pic);
ImageDestroy($pic);
?>
