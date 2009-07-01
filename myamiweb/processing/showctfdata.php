<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require "inc/particledata.inc";
require_once "inc/leginon.inc";

$sessionId= $_GET['Id'];
$minimum = $_GET['mconf'];
$viewdata = ($_GET['vd']==1) ? true : false;
$viewsql = ($_GET['vs']==1) ? true : false;

$ctf = new particledata();

$ctfinfo = $ctf->getBestCtfInfoForSessionId($sessionId, $minimum);

if ($viewdata) {
	//Could use keys for a cleaner output
	$keys=array('filename','REF|leginondata|ScopeEMData|defocus','defocus1','defocus2','confidence','confidence_d','difference');
	echo dumpData($ctfinfo,$keys);
	//echo dumpData($ctfinfo);
}

if ($viewsql) {
	$sql = $ctf->mysql->getSQLQuery();
	echo $sql;
	exit;
}
?>
