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
$alignId = $_GET['alignId'];
if ($alignId) $formAction.="&alignId=$alignId";

if ($_GET['showHidden']) {
	$showhidden = True;
	$formAction.="&showHidden=1";
}

$projectId = (int) getProjectFromExpId($expId);

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Tomographic Alignment Run Report","Tilt Series Alignment Report Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
$runinfo = $particle->getTomoAlignmentInfo($alignId);
$rundir = $runinfo['path'];
if ($runinfo['method'] == 'protomo') {
	$allcycles = $particle->getProtomoAlignerInfoFromAlignmentRun($alignId,False);
}
if ($_POST && $allcycles) {
	foreach ($allcycles as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApProtomoAlignerParamsData',$t['alignerid']);
}

// --- Get Aligner cycles
if (!$showhidden) {
	$showncycles = $particle->getProtomoAlignerInfoFromAlignmentRun($alignId,False);
	$allcycles = $particle->getProtomoAlignerInfoFromAlignmentRun($alignId,True);
} else {
	$showncycles = $particle->getProtomoAlignerInfoFromAlignmentRun($alignId,True);
	$allcycles = $allcycles;
}
echo $particle->displayHidingOption($expId,$allcycles,$showncycles,$showhidden);
if ($showncycles) {
	$html = "<h4>Protomo Alignment Cycles</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$selected_keys = array ( 'refine cycle','alignerid','reset cycle','align sampling','align box size','description');
	$display_keys = $selected_keys;
	$display_keys[2] = "reset cycle<br>[accept range]";
	$display_keys[3] = "align<br>sampling";
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</TR>\n";
	foreach ($showncycles as $t) {
		if ($t['good cycle'])
			$t['reset cycle'] = $t['good cycle'].'<br>['.$t['good start'].' : '.$t['good end'].']';
		$t['align box size'] = '('.$t['align box x']*$t['align sampling'].','.$t['align box y']*$t['align sampling'].')';
	$t['refine cycle'] = array('display'=>$t['refine cycle'],'link'=>$t['alignerid']);
		$html .= $particle->displayParametersInSummary($t,$selected_keys,$expId,$hide_button_field='alignerid');
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	$total = count($showncycles);
	if ($total >= 2) {
		$html .= "<a href='runTomoAligner.php?expId=".$expId."&lastaId=".$showncycles[$total-2]['alignerid']."'><b>[Repeat Last Aligner Cycle]</b></a>";
	} else {
		$html .= "<a href='runTomoAligner.php?expId=".$expId."'>[Repeat Last Aligner Cycle]</b></a>";
	}
	$html .= "<a href='runTomoAligner.php?expId=".$expId."&lastaId=".$t['alignerid']."'><b>[Set up Next Aligner Cycle]</b></a>";
	echo $html;
} else {
	$html = "<p>no alignment information available</p>";
	echo $html;
}
echo $particle->displayHidingOption($expId,$allcycles,$showncycles,$showhidden);
// --- 

processing_footer();
?>
