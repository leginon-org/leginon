<?php
if (!extension_loaded('mrc')) {
        dl('mrc.so');
}
// --- Read a MRC file, compute dicret fourier transform and display as a PNG
$filename = "mymrc.mrc";
$src_mrc = mrcread($filename);

// --- get Fourier Transform
$mask=10; // --- radius of mask to block the 0 component
mrcfftw($src_mrc, $mask);

mrcupdateheader($src_mrc);

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
