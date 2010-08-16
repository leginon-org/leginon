<?php
// These are functions specifically made for report pages that was developed at NIS.
// They might be merged with project/inc/experiment.inc.php in the future

require_once "../config.php";
require('inc/leginon.inc');

$leginondata->mysql=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

function getExemplars($sessionId) {
	global $leginondata;
	$filenames=$leginondata->getFilenames($sessionId, $name="exemplar");
	return $filenames;
}

function getExperimentInfo($id, $hidden=false) {
	global $leginondata;
	$sessioninfo = $leginondata->getSessionInfo($id);
	$summary = $leginondata->getSummary($sessioninfo['SessionId'],false, $hidden=$hidden);
	if (!empty($summary)) {
		foreach($summary as $s) {
			$s['defocusmin']=$leginondata->formatDefocus($s['defocusmin']);
			$s['defocusmax']=$leginondata->formatDefocus($s['defocusmax']);
			$dose=number_format(($s['dose']/1e20), 1,'.','');
			$imginfo = $dose."	".$s['defocusmin']."	".$s['defocusmax'];
			$tot_per_mag_key="Total_".$s['name']." x".$s['magnification'];
			$tot_per_mag_val=$s['nb']."	".$imginfo;
			$sessioninfo[$tot_per_mag_key]=$tot_per_mag_val;
			$tot_imgs += $s['nb'];
		}

	$sessioninfo['Total images']=$tot_imgs;
	}
	return $sessioninfo;
}

?>
