<?php

require_once "inc/leginon.inc";

$f="06oct10rct_00028sq_00_00276en_00.mrc";
$f="06oct10rct_00028sq_00.mrc";

$f="06oct26a_00022gr_00021sr_v00_00002sr_v04_00007ex_v00_00.mrc";
$f="06oct31rct_00049sr_v06_00002ex_00.mrc";

// --- Iwould like this:

function getRTC($f) {
	global $leginondata;
	list($filename) = $leginondata->getFilename($f);
	$id = $filename['id'];
	$rct = getRTCfilename2($id);
	$filenames = $leginondata->getFilename($rct);
	$filename = $filenames[count($filenames)-1];
	return $filename['filename'];
}

function getRTCfilename2($id) {
	global $leginondata;
	$info=$leginondata->getImageInfo($id);
	$name = $info['filename'];
	$p=$info['preset'];
	$pp=$info['parentpreset'];

	if ($pp) {
		$pattern = '/'.$pp.'_(\d+)_(.*)'.$p.'_(\d+)/';
		$pattern = '/'.$pp.'_v(\d+)_(.*)'.$p.'_(\d+)/';
	}else
		$pattern = '/'.$p.'_(\d+)/';

	if (!preg_match($pattern, $name, $result))
		return "";
	print_r($result);
	$split='/'.$result[0].'/';
	if ($pp)
	$replacement = $pp.'_v00'
		.'_'.$result[2]
		.$p.'_'
		.sprintf("%02d", $result[4]+1);
	else
	$replacement = $p.'_v0_'
		.sprintf("%02d", $result[1]+1);

	$rctfilename=preg_replace($split, $replacement, $name);
	$rctfilename=preg_replace('/v(\d+)/', 'v__', $rctfilename);
	echo "re: $rctfilename";
	return $rctfilename;
}


$rctf=getRTC($f);
echo "\nfilename: $f\n";
echo "RCT:$rctf \n";


echo "What should be\n";
$goodf="06oct26a_00022gr_00021sr_v00_00002sr_v01_00007ex_v00_01.mrc";
$goodf="06oct31rct_00049sr_v01_00002ex_01.mrc";
echo " $goodf\n";
echo "\n";
?>
