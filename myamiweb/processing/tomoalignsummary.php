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

if ($_GET['showHidden'])
	$formAction.="&showHidden=1";
$projectId = getProjectId();

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Tomographic Reconstruction Summary","Tomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
$alltomoaligns = $particle->getTomoAlignmentRunsFromSession($sessionId, True);
if ($_POST) {
	foreach ($alltomoaligns as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApTomoAlignmentRunData',$t['alignrun id']);
}

// --- Get Averaged tomograms
if (!$_GET['showHidden']) {
	$showntomoaligns = $particle->getTomoAlignmentRunsFromSession($sessionId, False);
	$alltomoaligns = $particle->getTomoAlignmentRunsFromSession($sessionId, True);
} else {
	$showntomoaligns = $particle->getTomoAlignmentRunsFromSession($sessionId, True);
	$alltomoaligns = $alltomoaligns;
}
echo $particle->displayHidingOption($expId,$alltomoaligns,$showntomoaligns,$_GET['showHidden']);
if ($showntomoaligns) {
	$html = "<h4>TiltSeries Alignment Runs</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'tilt number','alignrun id','alignrun name','method','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</TR>\n";
	foreach ($showntomoaligns as $t) {
		$html .= $particle->displayParametersInSummary($t,$display_keys,$expId,$hide_button_field='alignrun id');
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	echo $html;
} else {
	$html = "<p>no tilt series alignment available</p>";
	echo $html;
}
echo $particle->displayHidingOption($expId,$alltomoaligns,$showntomoaligns,$_GET['showHidden']);
// --- 

processing_footer();
?>
