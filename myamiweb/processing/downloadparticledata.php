<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

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
	$data[] = "particle#\tx_coord\ty_coord\timage_name\tpImage#\tshiftX\tshiftY\n";
	$partdatas = $appiondb->getParticlesDataWithDeforcusPair($particleSelectionId);
} 
else{ 
	$data[] = "particle#\tx_coord\ty_coord\timage_name\n";
	$partdatas = $appiondb->getParticles($particleSelectionId);
}

//echo "</br>\n";

foreach ($partdatas as $partdata) {

	switch($preset){
		case 'ef':
			$data[] = sprintf("%d\t%d\t%d\t%s\t%d\t%d\t%d\n",
				$partdata['DEF_id'],
				$partdata['xcoord'],
				$partdata['ycoord'],
				$partdata['filename'],
				$partdata['pImage'],
				$partdata['shiftx'],
				$partdata['shifty']);			
			break;
		default:
			$data[] = sprintf("%d\t%d\t%d\t%s\n",
				$partdata['DEF_id'],
				$partdata['xcoord'],
				$partdata['ycoord'],
				$partdata['filename']);
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

?>
