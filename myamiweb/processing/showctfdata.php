<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

$sessionId= $_GET['Id'];
$minimum = ($_GET['mres']) ? $_GET['mres']: false;
$viewdata = ($_GET['vd']==1) ? true : false;
$viewsql = ($_GET['vs']==1) ? true : false;

$ctf = new particledata();

$ctfinfo = $ctf->getBestCtfInfoByResolution($sessionId, $minimum);

if ($viewdata) {
	//Could use keys for a cleaner output
	$keys=array('filename','defocus1','defocus2','angle_astigmatism','resolution_appion','confidence','confidence_d','nominal_defocus','difference_from_nom');
	echo dumpData($ctfinfo,$keys);
	//echo dumpData($ctfinfo);
}

if ($viewsql) {
	$sql = $ctf->mysql->getSQLQuery();
	echo $sql;
	exit;
}
?>
