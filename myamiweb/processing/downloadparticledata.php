<?php

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

//This file dumps the best CTF parameters for all images in the session

$sessionId = $_GET['expId'];
checkExptAccessPrivilege($sessionId,'data');
$particleSelectionId = $_GET['pSelectionId'];
$preset = $_GET['preset'];
$appiondb = new particledata();

if (!$appiondb->hasParticleData($sessionId)) {
	echo "No particle information available<br/>\n";
	exit;
}

if ($preset == 'ef'){
	$data[] = "particle#\tx_coord\ty_coord\timage#\tpImage#\tshiftX\tshiftY\n";
	$partdatas = $appiondb->getParticlesDataWithDeforcusPair($particleSelectionId);
} 
else{ 
	$data[] = "particle#\tx_coord\ty_coord\timage#\n";
	$partdatas = $appiondb->getParticles($particleSelectionId);
}

//echo "</br>\n";

foreach ($partdatas as $partdata) {

	switch($preset){
		case 'ef':
			$data[] = sprintf("%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
				$partdata['DEF_id'],
				$partdata['xcoord'],
				$partdata['ycoord'],
				$partdata['imageNum'],
				$partdata['pImage'],
				$partdata['shiftx'],
				$partdata['shifty']);			
			break;
		default:		
			$data[] = sprintf("%d\t%d\t%d\t%d\n",
				$partdata['DEF_id'],
				$partdata['xcoord'],
				$partdata['ycoord'],
				$partdata['REF|leginondata|AcquisitionImageData|image']);			
			break;
	}
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
$downname = sprintf("particledata-%04d_%04d.dat", $sessionId, $particleSelectionId);
header("Content-Disposition: attachment; filename=$downname;");
foreach ($data as $line) {
	echo $line;
}




