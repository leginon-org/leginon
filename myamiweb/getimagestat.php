<?php
require 'inc/leginon.inc';
$id=$_GET['id'];
$preset=$_GET['pr'];
$newimage = $leginondata->findImage($id, $preset);
$id=$newimage['id'];
list($info) = $leginondata->getImageStat($id);
if ($info) {
	$min = $info['min'];
	$max = $info['max'];
	$mean = $info['mean'];
	$stdev = $info['stdev'];
} else {
	$filename=$leginondata->getFilenameFromId($id, true);
	$mrc = mrcread($path.$filename);
	mrcupdateheader($mrc);
	$info = mrcgetinfo($mrc);
	mrcdestroy($mrc);
	$min = $info['amin'];
	$max = $info['amax'];
	$mean = $info['amean'];
	$stdev = $info['rms'];
}

function formatnumber($number) {
	$number=number_format($number,1,'.','');
	return $number;
}
$min=formatnumber($min);
$max=formatnumber($max);
$mean=formatnumber($mean);
$stdev=formatnumber($stdev);

header('Content-Type: text/xml');
echo '<?xml version="1.0" standalone="yes"?>';
echo "<data>";
echo "<min>";
echo $min;
echo "</min>";
echo "<max>";
echo $max;
echo "</max>";
echo "<mean>";
echo $mean;
echo "</mean>";
echo "<stdev>";
echo $stdev;
echo "</stdev>";
echo "</data>";
