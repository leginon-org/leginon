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
	$showhidden = True;
$projectId = getProjectId();

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Tomographic Reconstruction Summary","Tomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
$allavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
if ($_POST) {
	foreach ($allavgtomos as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApTomoAverageRunData',$t['avgid']);
}
// --- Get Averaged tomograms
if (!$_GET['showHidden']) {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, False);
	$allavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
} else {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
	$allavgtomos = $allavgtomos;
}
echo $particle->displayHidingOption($expId,$allavgtomos,$shownavgtomos,$showhidden);
if ($shownavgtomos) {
	$html = "<h4>Averaged SubTomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'avgid','runname','stack','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</TR>\n";
	foreach ($shownavgtomos as $t) {
		$stackid = $t['stackid'];
		$stackparams = $particle->getStackParams($stackid);
		$stackname = $stackparams['shownstackname'];
		$t['stack'] = array('link'=>$stackid,'display'=>$stackname);
		$html .= $particle->displayParametersInSummary($t,$display_keys,$expId,$hide_button_field='avgid');
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	echo $html;
} else {
	$html = "<p>no averaged tomograms available</p>";
	echo $html;
}
echo $particle->displayHidingOption($expId,$alltomoaligns,$showntomoaligns,$showhidden);
// --- 

processing_footer();
?>
