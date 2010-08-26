<?php
if (!extension_loaded('mrc')) {
        dl('mrc.so');
}
// --- Read a MRC file and display as a PNG
$filename="./img/mymrc.mrc";
// --- create a mrc resource
$src_mrc = mrcread($filename);

// --- scale image :: average +/- n_stdev
$n_stdev = 3;
list($pmin, $pmax) = mrcstdevscale($src_mrc, $n_stdev);
$img = mrctoimage($src_mrc,$pmin,$pmax);

// --- create png image
header("Content-type: image/x-png");
imagepng($img);
// --- destroy resources in memory
mrcdestroy($src_mrc);
imagedestroy($img);
?>
