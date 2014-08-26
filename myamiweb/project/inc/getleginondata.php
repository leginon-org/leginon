<?php
// These are functions specifically made for report pages that was developed at NIS.
// They might be merged with project/inc/experiment.inc.php in the future

require_once "../config.php";
require_once('inc/leginon.inc');

$leginondata->mysql=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

function getExemplars($sessionId) {
	global $leginondata;
	$filenames=$leginondata->getFilenames($sessionId, $name="exemplar");
	return $filenames;
}

function getExperimentInfo($id_array_or_name, $hidden=false) {
	global $leginondata;
	$id_or_name = (is_array($id_array_or_name) && array_key_exists('leginonId',$id_array_or_name)) ? $id_array_or_name['leginonId']:$id_array_or_name;
	$sessioninfo = $leginondata->getSessionInfo($id_or_name);
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
