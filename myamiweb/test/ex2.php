<?php
require_once "../inc/imagerequest.inc";
// --- Read a MRC file and display as a PNG
$filename=WEB_ROOT."/test/img/mymrc.mrc";
// --- create a mrc resource
$xyDim = array(256,256);
$imagerequest = new imageRequester();
$imgstr = $imagerequest->requestImage($filename,'JPEG',$xyDim,'stdev',-3,3,0,false, true, false);
$imagerequest->displayImageString($imgstr,'JPEG',$filepath='');
?>
