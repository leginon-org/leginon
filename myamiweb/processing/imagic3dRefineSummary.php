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

processing_header("Imagic 3d Refinement Summary","Imagic 3d Refinement Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$refineruns = $particle->getImagic3dRefinementRunsFromSessionId($sessionId);
if ($refineruns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'run name', 'class averages', 'num cls avgs (original)', 'num iters', 'pixel size', 'box size', 'description');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($refineruns as $refinerun) {
		$refineid = $refinerun['DEF_id'];
		$numiters = count($particle->getImagic3dRefinementParamsFromRefineId($refineid));

		// update description
		if ($_POST['updateDesc'.$refineid]) {
			updateDescription('ApImagic3dRefineRunData', $refineid, $_POST['newdescription'.$refineid]);
			$refinerun['description']=$_POST['newdescription'.$refineid];

		}

		// GET INFO
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

		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$refineid</TD>\n";
		$html .= "<TD><A HREF='imagic3dRefineItnReport.php?expId=$expId&refineId=$refineid'>$refinerun[runname]</A></TD>\n";
		if ($refinerun['REF|ApNoRefClassRunData|norefclass']) {
			$html .= "<TD><A HREF='viewstack.php?file=$clsavgfile&expId=$sessionId&norefId=$norefId&norefClassId=
			$norefClassId'>View Class Averages</A></TD>\n";
			$html .= "<TD>$norefclassdata[num_classes]</TD>\n";
		}
		elseif ($refinerun['REF|ApClusteringStackData|clusterclass']) {
			$html .= "<TD><A HREF='viewstack.php?file=$clsavgfile&expId=$sessionId&clusterId=$clusterId'
			>View Class Averages</A></TD>\n";
			$html .= "<TD>$clusterdata[num_classes]</TD>\n";
		}
		$html .= "<TD>$numiters</TD>\n";
		$html .= "<TD>$refinerun[pixelsize]</TD>\n";
		$html .= "<TD>$refinerun[boxsize]</TD>\n";
	
		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($refineid,$refinerun['description']) : $refinerun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</TR>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no refinement information available";
}


processing_footer();
?>
