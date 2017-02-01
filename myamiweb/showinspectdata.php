<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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
