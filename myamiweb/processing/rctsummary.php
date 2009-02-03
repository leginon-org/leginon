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

processing_header("RCT Volume Summary","RCT Volume Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get RCT Data
$rctRuns = $particle->getRctRunsFromSession($sessionId);
if ($rctRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'name', 'image', 'num prtls', 'pixel size', 'box size','description');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($rctRuns as $rctrun) {
		$rctid = $rctrun['DEF_id'];

		// update description
		if ($_POST['updateDesc'.$rctid]) {
			updateDescription('ApRctRunData', $rctid, $_POST['newdescription'.$rctid]);
			$rctrun['description']=$_POST['newdescription'.$rctrun];
		}

		// GET INFO
		$stackcount= $particle->getNumStackParticles($rctrun['REF|ApStackData|tiltstack']);
		$stackmpix = $particle->getStackPixelSizeFromStackId($rctrun['REF|ApStackData|tiltstack']);
		$stackapix = format_angstrom_number($stackmpix);

		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$rctrun[DEF_id]</TD>\n";
		$html .= "<TD><A HREF='rctreport.php?expId=$expId&rctId=$rctrun[DEF_id]'>$rctrun[runname]</A></TD>\n";

		# sample image
		$pngfile = "";
		$rctrundir= opendir($rctrun['path']);
		while ($f = readdir($rctrundir)) {
			if (eregi('^volume.*'.$rctrun['numiter'].'\.mrc\.1\.png$', $f))
				$pngfile = $rctrun['path']."/".$f;
		}
		if (file_exists($pngfile))
			$html .= "<TD><IMG SRC='loadimg.php?h=80&filename=$pngfile' height='80'></TD>\n";
		else
			$html .= "<TD>$pngfile</TD>\n";

		$html .= "<TD>$stackcount</TD>\n";
		$html .= "<TD>$stackapix</TD>\n";
		$html .= "<TD>$rctrun[boxsize]</TD>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($rctid,$rctrun['description']) : $rctrun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</TR>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no rct volume information available";
}


processing_footer();
?>
