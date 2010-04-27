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
$projectId=getProjectId();

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Imagic 3d Refinement Summary","Imagic 3d Refinement Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();

// --- Get Reconstruction Data
$refineruns = $particle->getImagic3dRefinementRunsFromSessionId($sessionId);
if ($refineruns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'run name', 'num particles', 'symmetry', 'num iters', 'pixel size', 'box size', 'description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($refineruns as $refinerun) {
		$refineid = $refinerun['DEF_id'];
		$numiters = count($particle->getImagic3dRefinementParamsFromRefineId($refineid));
		$stackid = $refinerun['REF|ApStackData|stackrun'];
		$numpart = $particle->getNumStackParticles($stackid);
		$refineparams = $particle->getImagic3dRefinementParamsFromRefineId($refineid);
		$symmetry = $refineparams[0]['symmetry'];

		// update description
		if ($_POST['updateDesc'.$refineid]) {
			updateDescription('ApImagic3dRefineRunData', $refineid, $_POST['newdescription'.$refineid]);
			$refinerun['description']=$_POST['newdescription'.$refineid];

		}

/*		// GET INFO
		if ($refinerun['REF|ApNoRefClassRunData|norefclass']) {
			$norefClassId = $refinerun['REF|ApNoRefClassRunData|norefclass'];
			$norefclassdata = $particle->getNoRefClassRunData($norefClassId);
			$norefId = $norefclassdata['REF|ApNoRefRunData|norefRun'];
			$norefdata = $particle->getNoRefParams($norefId);
			$norefpath = $norefdata['path'];
			$norefclassfilepath = $norefclassdata['classFile'];
			$clsavgfile = $norefpath."/".$norefclassfilepath.".img";
		}
		elseif ($refinerun['REF|ApClusteringStackData|clusterclass']) {
			$clusterId = $refinerun['REF|ApClusteringStackData|clusterclass'];
			$clusterdata = $particle->getClusteringStackParams($clusterId);
			$clusterpath = $clusterdata['path'];
			$clsavgfile = $clusterpath."/".$clusterdata['avg_imagicfile'];
		}
		elseif ($refinerun['REF|ApTemplateStackData|templatestack']) {
			$tsId = $refinerun['REF|ApTemplateStackData|templatestack'];
			$tsdata = $particle->getTemplateStackParams($tsId);
			$tspath = $tsdata['path'];
			$clsavgfile = $tspath."/".$tsdata['templatename'];
		}
*/


		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<td>$refineid</TD>\n";
		$html .= "<td><A HREF='imagic3dRefineItnReport.php?expId=$expId&refineId=$refineid'>$refinerun[runname]</A></TD>\n";
		$html .= "<td>$numpart</TD>\n";
		$html .= "<td>$symmetry</TD>\n";
		$html .= "<td>$numiters</TD>\n";
		$html .= "<td>$refinerun[pixelsize]</TD>\n";
		$html .= "<td>$refinerun[boxsize]</TD>\n";
	
		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($refineid,$refinerun['description']) : $refinerun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no refinement information available";
}


processing_footer();
?>
