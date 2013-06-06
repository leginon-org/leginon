<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session to an EMX file format

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
	$ctfdatas = $appiondb->getBestCtfInfoForSessionId($sessionId);
else
	$ctfdatas = $appiondb->getCtfInfo($runId);

//$data[] = sprintf("<?xml version=\"1.0\"/>\n");
$data[] = sprintf("<EMX version=\"1.0\">\n");

foreach ($ctfdatas as $ctfdata) {
	$filename = $appiondb->getImageNameFromId($ctfdata['REF|leginondata|AcquisitionImageData|image']);
	//$short = $filename; # remove session stamp
	$pieces = explode("_", $filename);
	array_shift($pieces);
	$short = implode("_", $pieces);
	$data[] = sprintf("\t<micrograph fileName=\"%s\">\n", $short);
	// Xmipp requires us to flip the defocus values relative to the Appion standard
	$data[] = sprintf("\t\t<defocusU unit=\"nm\">%.3f</defocusU>\n", $ctfdata['defocus2']*1e9);
	$data[] = sprintf("\t\t<defocusV unit=\"nm\">%.3f</defocusV>\n", $ctfdata['defocus1']*1e9);
	// Need to convert to astig angle for both defocus flip (add 90) and using other image origin convention
	$angle = $ctfdata['angle_astigmatism'];
	$angle = -$angle; // fix for image origin
	$angle = $angle + 90; // fix for defocus flip
	$data[] = sprintf("\t\t<defocusUAngle unit=\"deg\">%.3f</defocusUAngle>\n", $angle);

	// additional parameters not in CTF competition
	$data[] = sprintf("\t\t<amplitudeContrast>%.3f</amplitudeContrast>\n", $ctfdata['amplitude_contrast']);
	//$data[] = sprintf("\t\t<acceleratingVoltage unit=\"kV\">%.3f</acceleratingVoltage>\n", ??????);
	$data[] = sprintf("\t\t<cs unit=\"mm\">%.3f</cs>\n", $ctfdata['cs']);
	//$data[] = sprintf("\t\t<pixelSpacing>\n");
	//$data[] = sprintf("\t\t\t<X unit="A/px">%.3f</X>\n", ??????);
	//$data[] = sprintf("\t\t\t<Y unit="A/px">%.3f</X>\n", ??????);
	//$data[] = sprintf("\t\t</pixelSpacing>\n");
	$data[] = sprintf("\t</micrograph>\n");
}

$data[] = sprintf("</EMX>\n");

/*
<?xml version="1.0"?>
<EMX version="1.0">
	<micrograph fileName="image001.mrc">
		<defocusU unit="nm"></defocusU>
		<defocusV unit="nm"></defocusV>
		<defocusUAngle unit="deg"></defocusUAngle>
	</micrograph>
	<micrograph fileName="image002.mrc">
		<defocusU unit="nm"></defocusU>
		<defocusV unit="nm"></defocusV>
		<defocusUangle unit="deg"></defocusUAngle>
	</micrograph>
</EMX>
*/

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
$downname = (empty($runId)) ? sprintf("ctfdata-session%04d.emx", $sessionId) : sprintf("ctfdata-run%04d.dat", $runId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}




