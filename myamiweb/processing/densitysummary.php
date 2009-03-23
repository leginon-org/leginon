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

processing_header("3d Density Volume Summary","3d Density Volume Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get 3d Density Data
$densityRuns = $particle->get3dDensitysFromSession($sessionId);
if ($densityRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'name', 'image', 'history', 'pixel size', 'box size', 'resolution', 'description', 'path', );
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($densityRuns as $densityrun) {
		$densityid = $densityrun['DEF_id'];

		// update description
		if ($_POST['updateDesc'.$densityid]) {
			updateDescription('Ap3dDensityData', $densityid, $_POST['newdescription'.$densityrun]);
			$densityrun['description']=$_POST['newdescription'.$densityrun];
		}

		// PRINT INFO
		$html .= "<TR>\n";
		# def if
		$html .= "<td>$densityrun[DEF_id]</TD>\n";
		# name
		$html .= "<td><A HREF='densityreport.php?expId=$expId&densityId=$densityid'>$densityrun[name]</A></TD>\n";

		# sample image
		$imgfile = $densityrun['path']."/".$densityrun['name'].".1.png";
		if (file_exists($imgfile))
			$html .= "<td><img src='loadimg.php?scale=0.07&filename=$imgfile' HEIGHT=71></TD>\n";
		else
			$html .= "<td></TD>\n";

		if ($densityrun['REF|ApRctRunData|rctrun'])
			$html .= "<td><A HREF='rctreport.php?expId=$expId&rctId="
				.$densityrun['REF|ApRctRunData|rctrun']."'>rctrun #"
				.$densityrun['REF|ApRctRunData|rctrun']."</A></TD>\n";
		elseif ($densityrun['REF|ApRefinementData|iterid'])
			$html .= "<td><A HREF='reconreport.php?expId=$expId&reconId="
				.$densityrun['refrun']."'> refine run #"
				.$densityrun['refrun']."</A></TD>\n";
		elseif ($densityrun['pdbid'])
			$html .= "<td><A HREF='http://www.rcsb.org/pdb/cgi/explore.cgi?pdbId="
				.$densityrun['pdbid']."'> PDB id "
				.$densityrun['pdbid']."&nbsp;<img src='img/external.png' BORDER='0' HEIGHT='10' WIDTH='10'>"
				."</A></TD>\n";
		elseif ($densityrun['emdbid'])
			$html .= "<td><A HREF='http://www.ebi.ac.uk/msd-srv/emsearch/atlas/"
				.$densityrun['emdbid']."_visualization.html'> EMDB id "
				.$densityrun['emdbid']."&nbsp;<img src='img/external.png' BORDER='0' HEIGHT='10' WIDTH='10'>"
				."</A></TD>\n";
		else
			$html .= "<td><I>unknown</I></TD>\n";

		$html .= "<td>".round($densityrun[pixelsize],2)."</TD>\n";
		$html .= "<td>$densityrun[boxsize]</TD>\n";
		$html .= "<td>".round($densityrun[resolution],2)."</TD>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($densityid,$densityrun['description']) : $densityrun['description'];
		$html .= "<td>$descDiv</td>\n";

		$html .= "<td>$densityrun[path]</TD>\n";

		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no 3d density volume information available";
}


processing_footer();
?>
