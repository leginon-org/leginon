<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
  
// check if coming directly from a session
$expId = $_GET['expId'];
if ($expId) {
        $sessionId=$expId;
        $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
        $sessionId=$_POST['sessionId'];
        $formAction=$_SERVER['PHP_SELF'];
}
$projectId=$_POST['projectId'];

$javascript="<script src='../js/viewer.js'></script>\n";

writeTop("Reconstruction Summary","Reconstruction Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);


// --- Get Stack Data
$particle = new particledata();
#$stackIds = $particle->getStackIds($sessionId);
// --- Get Reconstruction Data
echo"<P>\n";
$reconRuns = $particle->getReconIdsFromSession($sessionId);
if ($reconRuns) {

	$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'name', 'num prtls', 'symmetry', 'pixel size', 'box size', 
		'best: fsc / rMeas (iter)', 'avg median<br/>euler jump','description');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($reconRuns as $reconrun) {
		// GET INFO
		$stackcount=$particle->getNumStackParticles($reconrun['REF|ApStackData|stack']);
		$stackmpix = $particle->getStackPixelSizeFromStackId($reconrun['REF|ApStackData|stack']);
		$stackapix = format_angstrom_number($stackmpix);
		$stmodel = $particle->getInitModelInfo($reconrun['REF|ApInitialModelData|initialModel']);
		$sym = $particle->getSymInfo($stmodel['REF|ApSymmetryData|symmetry']);
		$res = $particle->getHighestResForRecon($reconrun['DEF_id']);
		$avgmedjump = $particle->getAverageMedianJump($reconrun['DEF_id']);

		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$reconrun[DEF_id]</TD>\n";
		$html .= "<TD><A HREF='reconreport.php?expId=$expId&reconId=$reconrun[DEF_id]'>$reconrun[name]</A></TD>\n";
		$html .= "<TD>$stackcount</TD>\n";
		$html .= "<TD>";
		$html .= "$sym[symmetry]</TD>\n";
		$html .= "<TD>".$stackapix."</TD>\n";
		$html .= "<TD>$stmodel[boxsize]</TD>\n";
		$html .= sprintf("<TD>% 2.2f / % 2.1f &Aring; (%d)</TD>\n", $res[half],$res[rmeas],$res[iter]);
		if ($avgmedjump['count'] > 0)
			$html .= sprintf("<TD>%2.2f &plusmn; %2.1f </TD>\n", $avgmedjump['average'], $avgmedjump['stdev']);
		else
			$html .= "<TD></TD>\n";
		$html .= "<TD>".$reconrun['description']."</TD>\n";
		$html .= "</TR>\n";
	}

	$html .= "</table>\n";
	echo $html;
//	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
} else {
	echo "no reconstruction information available";
}


writeBottom();
?>
