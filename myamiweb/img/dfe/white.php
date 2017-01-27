<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

$pic=ImageCreate(255,1);
imagecolorallocate($pic, 255, 255, 255);
header("Content-type: image/png");
ImagePNG($pic);
ImageDestroy($pic);
?>
