<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$expId = $_GET['expId'];
checkExptAccessPrivilege($expId,'data');
$selectionId = $_GET['selectionId'];
$appiondb = new particledata();

if (!$appiondb->hasParticleData($expId)) {
	echo "No particle information available<br/>\n";
	exit;
}

$partdatas = $appiondb->getParticles($selectionId);

$data[] = "particle #\tx_coord\ty_coord\timage_#\n";
//echo "</br>\n";

foreach ($partdatas as $partdata) {
	//$filename = $appiondb->getImageNameFromId($partdata['REF|leginondata|AcquisitionImageData|image']);
	$data[] = sprintf("%d\t%d\t%d\t%d\n",
		$partdata['DEF_id'],
		$partdata['xcoord'],
		$partdata['ycoord'],
		$partdata['REF|leginondata|AcquisitionImageData|image']);
}

$size = 0;
foreach ($data as $line) {
	$size += strlen($line);
}
//echo "filesize $size";

header("Content-Type: application/text");
header("Content-Type: application/force-download");
header("Content-Type: application/download");
header("Content-Transfer-Encoding: binary");
header("Content-Length: $size");
$downname = sprintf("particledata-%04d_%04d.dat", $expId, $selectionId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}




