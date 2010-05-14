<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$sessionId = $_GET['expId'];
$appiondb = new particledata();

$ctfrundatas = $appiondb->getCtfRunIds($sessionId, True);
if (!$ctfrundatas) {
	echo "No CTF information available<br/>\n";
	exit;
}

$ctfdatas = $appiondb->getBestCtfInfoForSessionId($sessionId);

$data[] = "nominal_def\tdefocus1\tdefocus2\tangle_astig\tamp_contrast\timage_name\n";
//echo "</br>\n";

foreach ($ctfdatas as $ctfdata) {
	$filename = $appiondb->getImageNameFromId($ctfdata['REF|leginondata|AcquisitionImageData|image']);
	$data[] = sprintf("%.4e\t%.6e\t%.6e\t%.6f\t%.6f\t%s\n",
		$ctfdata['defocus'],
		$ctfdata['defocus1'],
		$ctfdata['defocus2'],
		$ctfdata['angle_astigmatism'],
		$ctfdata['amplitude_contrast'],
		$filename);
}

$size = 0;
foreach ($data as $line) {
	$size += strlen($line);
}

header("Content-Type: application/text");
header("Content-Type: application/force-download");
header("Content-Type: application/download");
header("Content-Transfer-Encoding: binary");
header("Content-Length: $size");
$downname = sprintf("ctfdata-%04d.dat", $sessionId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}
//echo "filesize $size\n";



