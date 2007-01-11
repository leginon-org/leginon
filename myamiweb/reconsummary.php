<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
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
        $display_keys = array ( 'name', 'num prtls', 'symmetry', 'pixel size', 'box size');
	foreach($display_keys as $key) {
	        $html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
        }
        foreach ($stackIds as $stackid) {
                $stackcount=$particle->getNumStackParticles($stackid);
		$reconIds = $particle->getReconIds($stackid);
		foreach ($reconIds as $reconid) {
		        $stmodel = $particle->getInitModelInfo($reconid['REF|initialModel|initialModelId']);
			$sym = $particle->getSymInfo($stmodel['REF|symmetry|symmetryId']);
			$res = $particle->getResolutionInfo($reconid['REF|resolution|resolutionId']);
		        $html .= "<TR>\n";
		        $html .= "<TD><A HREF='reconreport.php?reconId=$reconid[DEF_id]'>$reconid[name]</A></TD>\n";
			$html .= "<TD>$stackcount</TD>\n";
			$html .= "<TD>$sym[symmetry]</TD>\n";
			$html .= "<TD>$stmodel[pixelsize]</TD>\n";
			$html .= "<TD>$stmodel[boxsize]</TD>\n";
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
