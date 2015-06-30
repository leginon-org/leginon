<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$expId = $_GET['expId'];
$runId = $_GET['runId'];
$relion = $_GET['relion'];

checkExptAccessPrivilege($expId,'data');
$appiondb = new particledata();

$ctfrundatas = $appiondb->getCtfRunIds($expId, True);
if (!$ctfrundatas) {
	echo "No CTF information available<br/>\n";
	exit;
}

if(empty($runId))
	$ctfdatas = $appiondb->getBestCtfInfoByResolution($expId);
else
	$ctfdatas = $appiondb->getCtfInfo($runId);

if ($relion) {
	$leginon = new leginondata();
	$data[] = "\ndata_\n\nloop_\n";
	$data[] = "_rlnMicrographName #1\n";
	$data[] = "_rlnCtfImage #2\n";
	$data[] = "_rlnDefocusU #3\n";
	$data[] = "_rlnDefocusV #4\n";
	$data[] = "_rlnDefocusAngle #5\n";
	$data[] = "_rlnVoltage #6\n";
	$data[] = "_rlnSphericalAberration #7\n";
	$data[] = "_rlnAmplitudeContrast #8\n";
	$data[] = "_rlnMagnification #9\n";
	$data[] = "_rlnDetectorPixelSize #10\n";
	$data[] = "_rlnCtfFigureOfMerit #11\n";

	# get image info for first image,
	# assume same for all the rest
	$imgid = $ctfdatas[0]['REF|leginondata|AcquisitionImageData|image'];
	$imginfo = $leginon->getImageInfo($imgid);
	$pixelsize = $imginfo['pixelsize']*1e10;
	$kev = $imginfo['high tension']/1000;
	$cs = $leginon->getCsValueFromSession($expId);
}
else $data[] = "image #\tnominal_def\tdefocus_1\tdefocus_2\tangle_astig\tamp_cont\tres(0.8)\tres(0.5)\tconf(30/10)\tconf(5_peak)\tconf\timage_name\n";
//echo "</br>\n";

foreach ($ctfdatas as $ctfdata) {
	$filename = $appiondb->getImageNameFromId($ctfdata['REF|leginondata|AcquisitionImageData|image']);

	if ($relion) {
		$data[]=sprintf("micrographs/%s.mrc micrographs/%s.ctf:mrc %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f\n",
			$filename,
			$filename,
			$ctfdata['defocus1']*1e10,
			$ctfdata['defocus2']*1e10,
			$ctfdata['angle_astigmatism'],
			$kev,
			$cs,
			$ctfdata['amplitude_contrast'],
			10000,
			$pixelsize,
			$ctfdata['confidence']
			);
	}
	else {
		$angtxt = str_pad(sprintf("%.3f",$ctfdata['angle_astigmatism']), 9, " ", STR_PAD_LEFT);
		$data[] = sprintf("%d\t%.4e\t%.5e\t%.5e\t%s\t%.4f\t%.2f\t%.2f\t%.3f\t%.3f\t%.3f\t%s\n",
			$ctfdata['REF|leginondata|AcquisitionImageData|image'],
			$ctfdata['defocus'],
			$ctfdata['defocus1'],
			$ctfdata['defocus2'],
			$angtxt,
			$ctfdata['amplitude_contrast'],
			$ctfdata['resolution_80_percent'],
			$ctfdata['resolution_50_percent'],
			$ctfdata['confidence_30_10'],
			$ctfdata['confidence_5_peak'],
			$ctfdata['confidence'],
			$filename);
	}
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
if ($relion) $downname = sprintf("micrographs_ctf-%05d.star",$expId);
else $downname = (empty($runId)) ? sprintf("ctfdata-session%04d.dat", $expId) : sprintf("ctfdata-run%04d.dat", $runId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}
