<?php
require "inc/leginon.inc";
$id=$_GET['id'];
list($info) = $leginondata->getImageStat($id);
if ($info) {
	$min = $info['min'];
	$max = $info['max'];
	$mean = $info['mean'];
	$stdev = $info['stdev'];
} else {
	$filename=$leginondata->getFilenameFromId($id, true);
	$info = mrcinfo($filename);
	$min = $info['amin'];
	$max = $info['amax'];
	$mean = $info['amean'];
	$stdev = $info['rms'];
}
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
?>
