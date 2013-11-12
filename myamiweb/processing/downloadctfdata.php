<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$sessionId = $_GET['expId'];
$runId = $_GET['runId'];

checkExptAccessPrivilege($sessionId,'data');
$appiondb = new particledata();

$ctfrundatas = $appiondb->getCtfRunIds($sessionId, True);
if (!$ctfrundatas) {
	echo "No CTF information available<br/>\n";
	exit;
}

if(empty($runId))
	$ctfdatas = $appiondb->getBestCtfInfoByResolution($sessionId);
else
	$ctfdatas = $appiondb->getCtfInfo($runId);


$data[] = "image #\tnominal_def\tdefocus_1\tdefocus_2\tangle_astig\tamp_cont\tconfidence_1\tconfidence_2\timage_name\n";
//echo "</br>\n";

foreach ($ctfdatas as $ctfdata) {
	$filename = $appiondb->getImageNameFromId($ctfdata['REF|leginondata|AcquisitionImageData|image']);
	$angtxt = str_pad(sprintf("%.3f",$ctfdata['angle_astigmatism']), 9, " ", STR_PAD_LEFT);
	$data[] = sprintf("%d\t%.4e\t%.5e\t%.5e\t%s\t%.4f\t%.4f\t%.4f\t%s\n",
		$ctfdata['REF|leginondata|AcquisitionImageData|image'],
		$ctfdata['defocus'],
		$ctfdata['defocus1'],
		$ctfdata['defocus2'],
		$angtxt,
		$ctfdata['amplitude_contrast'],
		$ctfdata['confidence'],
		$ctfdata['confidence_d'],
		$filename);
}

$size = 0;
foreach ($data as $line) {
	$size += strlen($line);
}
//echo "filesize $size\n";

header("Content-Type: application/text");
header("Content-Type: application/force-download");
header("Content-Type: application/download");
header("Content-Transfer-Encoding: binary");
header("Content-Length: $size");
$downname = (empty($runId)) ? sprintf("ctfdata-session%04d.dat", $sessionId) : sprintf("ctfdata-run%04d.dat", $runId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}



