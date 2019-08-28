<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/datatocsv.inc";
#ini_set('memory_limit', '10240M'); // enough for ~5E6 particles  wjr 
//This file dumps the best CTF parameters for all images in the session
// wjr changed 7/12/19 -- old function with sprintf took 30X as much memory as the final filesize
//                     -- example: > 1GB RAM needed for 524,000 particles, a 39MB file
//                     -- NOTE: eliminated distinction between 'ef' and other presets

$sessionId = $_GET['expId'];
checkExptAccessPrivilege($sessionId,'data');
$particleSelectionId = $_GET['pSelectionId'];
$preset = $_GET['preset'];
$appiondb = new particledata();

if (!$appiondb->hasParticleData($sessionId)) {
	echo "No particle information available<br/>\n";
	exit;
}

$partdatas = $appiondb->getParticles($particleSelectionId);
$data = array(array_keys($partdatas[0]));
$partdatas = array_merge($data,$partdatas); 
$downname = sprintf("particledata-%05d_%03d.csv", $sessionId, $particleSelectionId);
array_to_csv_download($partdatas,$downname,"\t");

?>
