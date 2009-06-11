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
$projectId = (int) getProjectFromExpId($expId);

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Tomographic Reconstruction Summary","Tomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
// --- Get Averaged tomograms
if (!$_GET['showHidden']) {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, False);
	$allavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
} else {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
	$allavgtomos = $allavgtomos;
}
if (!$_GET['showHidden'] && count($allavgtomos) != count($shownavgtomos)) {
	$numhidden = count($allavgtomos) - count($shownavgtomos);
	echo "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=1'>[Show ".$numhidden." hidden runs]</a><br/><br/>\n";
} elseif ($_GET['showHidden']) {
	echo "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=0'>[Hide hidden runs]</a><br/><br/>\n";
}
if ($shownavgtomos) {
	$html = "<h4>Averaged SubTomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'id','runname','stack','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</TR>\n";
	foreach ($shownavgtomos as $t) {
		$avgid = $t['avgid'];
		// update description
		if ($_POST['updateDesc'.$avgid]) {
			updateDescription('ApTomoAverageRunData', $avgid, $_POST['newdescription'.$avgid]);
			$t['description']=$_POST['newdescription'.$avgid];
		}

		if ($_POST['hideStack'.$avgid] == 'hide') {
			$particle->updateHide('ApTomoAverageRunData', $avgid, '1');
			$t['hidden']=1;
		} elseif ($_POST['unhideStack'.$avgid] == 'unhide') {
			$particle->updateHide('ApTomoAverageRunData', $avgid, '0');
			$t['hidden']=0;
		}

		$stackid = $t['stackid'];
		$stackparams = $particle->getStackParams($stackid);
		$stackname = $stackparams['shownstackname'];
		$html .= "<TR>\n";
		// runid and hide
		$html .= "<TD valign='center' align='center'>$avgid\n";
		if ($t['hidden'] == 1) {
			$html.= "<br/><font color='#cc0000'>HIDDEN</font>\n";
			$html.= " <input class='edit' type='submit' name='unhideStack".$avgid."' value='unhide'>\n";
		} else $html .= "<br/><input class='edit' type='submit' name='hideStack".$avgid."' value='hide'>\n";
		$html .= "</td>\n";
		$html .= "<td><A HREF='tomoavgreport.php?expId=$expId&avgId=$avgid'>".$t['runname']."</A></TD>\n";
		$html .= "<td><A HREF='stackreport.php?expId=$expId&sId=$stackid']'>$stackname</A></TD>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($avgid,$t['description']) : $t['description'];
		$html .= "<td>$descDiv</td>\n";
		$html .= "</tr>\n";
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	echo $html;
} else {
	$html = "<p>no averaged tomograms available</p>";
	echo $html;
}

if (!$_GET['showHidden'] && count($allavgtomos) != count($shownavgtomos)) {
	$numhidden = count($allavgtomos) - count($shownavgtomos);
	echo "<a href='".$formAction."&showHidden=1'>[Show ".$numhidden." hidden runs]</a><br/><br/>\n";
} elseif ($_GET['showHidden']) {
	echo "<a href='".$formAction."&showHidden=0'>[Hide hidden runs]</a><br/><br/>\n";
}
// --- 

processing_footer();
?>
