<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "clitools.php";
require "inc/leginon.inc";
require "inc/image.inc";
require_once "Console/ProgressBar.php";

$CHECKSUM_FILE=0;

$args=getargs($argv);
if (!$args['t'])
	$args['t']=80;
if (!$args['binning'])
	$args['binning']=1;
if (!$args['autoscale'])
	$args['autoscale']=1;
if (!$args['outpath'])
	$args['path']="";

$array_fct=($args['invert']==1) ? "array_diff" : "array_intersect";

$sessionId=$args['session'];
$preset=$args['preset'];
$sessioninfo=$leginondata->getSessionInfo($sessionId);
$sessionId=$sessioninfo['SessionId'];
$datatypes = $leginondata->getDatatypes($sessionId);
if ($preset) {
	if (!is_array($preset)) {
		$preset=array($preset);
	}
	$preset=$array_fct($datatypes, $preset);
	echo "presets: ".implode(", ",$preset)."\n";
	$filenames=array();
	foreach ($preset as $p) {
		if ($p) {
			$filenames=array_merge($filenames, $leginondata->getFilenames($sessionId, $p));
		}
	}
} else {
	$filenames=$leginondata->getFilenames($sessionId, "all");
}

if (!$path=$sessioninfo['Image path'])
	$path="/tmp/".$sessioninfo['Name']."/";

$path = ereg_replace("rawdata", "jpegs", $path);

if ($args['outpath'])
	$path=$args['outpath'];

foreach($filenames as $f) {
	if ($id=$f['id'])
		$imageIds[]=$id;
}
mkdirs($path);
if (!$filenames) {
	echo "images not found \n";
	exit;
}
echo "destination: $path\n";
$g=true;
if (!$imageIds) {
	$g=false;
}

$t = $args['t'];
if ($t=='png') {
        $type = "image/x-png";
	$ext = "png";
} else {
        $type = "image/jpeg";
	$quality=$t;
	$ext = "jpg";
}

if (!$displayparticle = $data['psel']) 
	$displayparticle = false;

$autoscale = ($args['autoscale']==1) ? true : false;
$minpix = ($args['np']) ? $args['np'] : 0;
$maxpix = ($args['xp']) ? $args['xp'] : 255;
$size = $args['s'];
$displaytarget = ($args['tg']==1) ? true : false;
$displayscalebar = ($args['sb']==1) ? true : false;
$fft = ($args['fft']==1) ? true : false;
if (!$filter=$args['flt']) 
	$filter = 'default';
if (!$binning=$args['binning']) 
	$binning = 'auto';

$n_images = count($imageIds);
$existing_files = getfiles($path);
# set progress bar
$pbar = new Console_ProgressBar('* %fraction% %bar% %percent% %estimate% ', '#', '-',60, $n_images);
foreach ($imageIds as $i=>$id) {
	list($res) = $leginondata->getFilename($id);
	$filename = ereg_replace('mrc$', $ext, $res['filename']);

	$filename=$path."/".$filename;
	
	$params = array (
		'size'=> $size,
		'minpix' => $minpix,
		'maxpix' => $maxpix,
		'filter' => $filter,
		'fft' => $fft,
		'binning' => $binning,
		'scalebar' => $displayscalebar,
		'displaytargets' => $displaytarget,
		'loadtime' => $displayloadingtime,
		'autoscale' => $autoscale,
		'newptcl' => $displaynptcl,
		'ptcl' => urldecode($displayparticle)
	);

	# udpate progress bar
	$pbar->update($i+1);

	if (file_exists($filename)) {
			# continue if exists 
			continue;
	}

	$img = getImage($sessionId, $id, "", $params);
	
	// when there is no image. skip it....
	if($img == false)
		continue;
		
	# write filename
	if ($t=='png') {
		imagepng($img, $filename);
	} else {
		imagejpeg($img,$filename,$quality);
	}

	imagedestroy($img);
	
}
echo "\n";

function mkchecksum($string) {
	return 	md5($string);
}

?>
