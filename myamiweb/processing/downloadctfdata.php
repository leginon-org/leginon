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

$data[] = "nominal_def\tdefocus_1\tdefocus_2\tangle_astig\tamp_cont\tconfidence_1\tconfidence_2\timage_name\n";
//echo "</br>\n";

foreach ($ctfdatas as $ctfdata) {
	$filename = $appiondb->getImageNameFromId($ctfdata['REF|leginondata|AcquisitionImageData|image']);
	$data[] = sprintf("%.4e\t%.5e\t%.5e\t%.5e\t%.4f\t%.4f\t%.4f\t%s\n",
		$ctfdata['defocus'],
		$ctfdata['defocus1'],
		$ctfdata['defocus2'],
		$ctfdata['angle_astigmatism'],
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
$downname = sprintf("ctfdata-%04d.dat", $sessionId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}




