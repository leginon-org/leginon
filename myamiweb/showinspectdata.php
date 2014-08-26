<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once "inc/leginon.inc";
require_once "inc/particledata.inc";

$sessionId= $_GET['Id'];
$viewdata = ($_GET['vd']==1) ? true : false;
$viewsql = ($_GET['vs']==1) ? true : false;

$particle = new particledata();

$assessmentId=$particle->getLastAssessmentRun($sessionId);
$inspectinfo = $particle->getAssessmentDataForRun($assessmentId);
if ($viewdata) {
	echo dumpData($inspectinfo);
}

if ($viewsql) {
	$sql = $particle->mysql->getSQLQuery();
	echo $sql;
	exit;
}
?>
