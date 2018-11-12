<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
  
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
$projectId=getProjectId();

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("SIMPLE Common Lines Summary","SIMPLE Common Lines Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$simpleRuns = $particle->getSIMPLEOrigamiRuns($sessionId);

if ($simpleRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ('SIMPLE Common Lines runname', 'description', 'path', 'conformations', '',
		'num_classes', 'num parts', 'box size', 'pixel size');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($simpleRuns as $simplerun) {
		$simpleid = $simplerun['DEF_id'];
		$simpleparams = $particle->getSIMPLEOrigamiParams($simplerun['REF|ApSIMPLEOrigamiParamsData|simple_params']);

		// update description
		if ($_POST['updateDesc'.$simpleid]) {
			updateDescription('ApSIMPLEOrigamiRunData', $simpleid, $_POST['newdescription'.$simpleid]);
			$simplerun['description']=$_POST['newdescription'.$simpleid];

		}

		// hide simple
		if ($_POST['hideItem'.$simpleid]) {
			echo "Hiding run $simpleid\n<br/>\n";
			$particle->updateHide('ApSIMPLEOrigamiRunData', $simpleid, '1');
			continue;
		}

		if ($simplerun['REF|ApClusteringStackData|clusteringstack']) {
			$clusterid = $simplerun['REF|ApClusteringStackData|clusteringstack'];
			$clusterparams = $particle->getClusteringStackParams($clusterid);
			$nclasses = $clusterparams['num_classes'];
			$numparts = $clusterparams['num_particles'];
		}

		// GET INFO
		$simplename = $simplerun['runname'];
		$path = $simplerun['path'];
		$description = $simplerun['description'];
		$nconformers = $simpleparams['tos'];
		$box = $simplerun['box'];
		$apix = $simplerun['apix'];	
	
		$html .= "<tr>\n";
		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($simpleid,$simplerun['description']) : $simplerun['description'];

		// display simple info		
		$html .= "<td><font size='+1'><a href='simpleCommonLinesReport.php?expId=$expId&simpleId=$simpleid'>$simplename</a></font>\n"
			." <br/><i>(ID: $simpleid)</i>\n"
			." <input class='edit' type='submit' name='hideItem".$simpleid."' value='hide'>\n"
			."</td>\n";
		$html .= "<td><font size=-2>$descDiv</font></td>\n";
		$html .= "<td><font size=-2>$path</font></td>\n";
		$html .= "<td>$nconformers</td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";
		$html .= "<td>$nclasses</td>\n";
		$html .= "<td>$numparts</td>\n";
		$html .= "<td>$box</td>\n";
		$html .= "<td>$apix</td>\n";
		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no common lines reconstruction information available";
}

processing_footer();

?>
