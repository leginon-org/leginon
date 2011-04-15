<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$expId = $_GET['expId'];
$stackId = $_GET['stackId'];
checkExptAccessPrivilege($expId,'data');

$appiondb = new particledata();

if (!$appiondb->hasParticleData($expId)) {
	echo "No particle information available<br/>\n";
	exit;
}

$partdatas = $appiondb->getParticlesFromStack($stackId);

$data[] = "particle #\tmean\tstdev\tskew\tkurtosis\tedgemean\tedgestdev\tcentermean\tcenterstdev\tmin\tmax\n";
//echo "</br>\n";

foreach ($partdatas as $partdata) {
	$data[] = sprintf("%d\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f\n",
		$partdata['particleId'],
		$partdata['mean'],
		$partdata['stdev'],
		$partdata['skew'],
		$partdata['kurtosis'],
		$partdata['edgemean'],
		$partdata['edgestdev'],
		$partdata['centermean'],
		$partdata['centerstdev'],
		$partdata['min'],
		$partdata['max']);
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
$downname = sprintf("stackparticledata_stackId_%04d.dat", $stackId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}




