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

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Reconstruction Summary","Reconstruction Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$reconRuns = $particle->getReconIdsFromSession($sessionId);
if ($reconRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'name', 'num prtls', 'symmetry', 'pixel size', 'box size', 
		'best: fsc / rMeas (iter)', 'avg median<br/>euler jump','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($reconRuns as $reconrun) {
		$reconid = $reconrun['DEF_id'];

		// update description
		if ($_POST['updateDesc'.$reconid]) {
			updateDescription('ApRefinementRunData', $reconid, $_POST['newdescription'.$reconid]);
			$reconrun['description']=$_POST['newdescription'.$reconid];

		}

		// GET INFO
		$stackcount=$particle->getNumStackParticles($reconrun['REF|ApStackData|stack']);
		$stackmpix = $particle->getStackPixelSizeFromStackId($reconrun['REF|ApStackData|stack']);
		$stackapix = format_angstrom_number($stackmpix);
		$stmodel = $particle->getInitModelInfo($reconrun['REF|ApInitialModelData|initialModel']);
		$sym = $particle->getSymInfo($stmodel['REF|ApSymmetryData|symmetry']);
		$res = $particle->getHighestResForRecon($reconid);
		$avgmedjump = $particle->getAverageMedianJump($reconid);

		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<td>$reconrun[DEF_id]</TD>\n";
		$html .= "<td><A HREF='reconreport.php?expId=$expId&reconId=$reconrun[DEF_id]'>$reconrun[name]</A></TD>\n";
		$html .= "<td>$stackcount</TD>\n";
		$html .= "<td>";
		$html .= "$sym[symmetry]</TD>\n";
		$html .= "<td>".$stackapix."</TD>\n";
		$html .= "<td>$stmodel[boxsize]</TD>\n";
		$html .= sprintf("<td>% 2.2f / % 2.1f &Aring; (%d)</TD>\n", $res[half],$res[rmeas],$res[iter]);
		if ($avgmedjump['count'] > 0) {
			$html .= "<td><A HREF='eulergraph.php?expId=$expId&hg=1&recon=$reconrun[DEF_id]'>";
			$html .= sprintf("%2.2f &plusmn; %2.1f </A>", $avgmedjump['average'], $avgmedjump['stdev']);
			$html .= " <font size=-2><A HREF='jumpSubStack.php?expId=$expId&reconId=$reconrun[DEF_id]'>[sub]</a></font>";
			$html .= "</td>\n";
		} else
			$html .= "<td></TD>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($reconid,$reconrun['description']) : $reconrun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
//	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
} else {
	echo "no reconstruction information available";
}


processing_footer();
?>
