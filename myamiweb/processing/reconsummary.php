<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
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

$javascript="<script src='js/viewer.js'></script>\n";

writeTop("Reconstruction Summary","Reconstruction Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);


// --- Get Stack Data
$particle = new particledata();
$stackIds = $particle->getStackIds($sessionId);
$stackruns=count($stackIds);
// --- Get Reconstruction Data
echo"<P>\n";
if ($stackruns>0){ 
	$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'name', 'num prtls', 'symmetry', 'pixel size', 'box size', 'highest res.(iter)', 'description');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}
	foreach ($stackIds as $stackid) {
		$reconRuns = $particle->getReconIds($stackid['stackid']);
		if (!$reconRuns) {
			//No recons go to next stack
			continue;
		}
		$stackcount=$particle->getNumStackParticles($stackid['stackid']);
		$stackparam=$particle->getStackParams($stackid['stackid']);

		//get stackapix from first image
		$stackpix = $particle->getStackPixelSizeFromStackId($stackid['stackid']);
		$stackapix = format_angstrom_number($stackpix);

		foreach ($reconRuns as $reconrun) {
			$stmodel = $particle->getInitModelInfo($reconrun['REF|ApInitialModelData|initialModel']);
			$sym = $particle->getSymInfo($stmodel['REF|ApSymmetryData|symmetry']);
			$res=$particle->getHighestResForRecon($reconrun[DEF_id]);
			$description=$reconrun['description'];
			$html .= "<TR>\n";
			$html .= "<TD><A HREF='reconreport.php?reconId=$reconrun[DEF_id]'>$reconrun[name]</A></TD>\n";
			$html .= "<TD>$stackcount</TD>\n";
			$html .= "<TD>";
			$html .= "$sym[symmetry]</TD>\n";
			$html .= "<TD>".$stackapix."</TD>\n";
			$html .= "<TD>$stmodel[boxsize]</TD>\n";
			$html .= sprintf("<TD>%.2f (%d)</TD>\n", $res[half],$res[iteration]);
			$html .= "<TD>".$description."</TD>\n";
			$html .= "</TR>\n";
		}
	}
	echo $html;
}

//        echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
else {
        echo "no reconstruction information available";
}


writeBottom();
?>
