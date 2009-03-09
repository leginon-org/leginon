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
	$display_keys = array ( 'defid', 'name', 'image', 'num part', 'pixel size', 'box size', 'fsc res', 'rmeasure', 'description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($rctRuns as $rctrun) {
		$rctid = $rctrun['DEF_id'];
		$numpart = commafy($rctrun['numpart']);

		// update description
		if ($_POST['updateDesc'.$rctid]) {
			updateDescription('ApRctRunData', $rctid, $_POST['newdescription'.$rctid]);
			$rctrun['description']=$_POST['newdescription'.$rctrun];
		}

		// GET INFO
		$stackcount= commafy($particle->getNumStackParticles($rctrun['REF|ApStackData|tiltstack']));
		$stackmpix = $particle->getStackPixelSizeFromStackId($rctrun['REF|ApStackData|tiltstack']);
		$stackapix = format_angstrom_number($stackmpix);

		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD valign='center' align='center'>$rctrun[DEF_id]</TD>\n";
		$html .= "<TD valign='center' align='center'>"
			."<A HREF='rctreport.php?expId=$expId&rctId=$rctrun[DEF_id]'>$rctrun[runname]</A></TD>\n";

		// SAMPLE PNG FILE
		$pngfiles = glob($rctrun['path']."/"."volume*".$rctrun['numiter'].".mrc.1.png");
		if ($pngfiles && file_exists($pngfiles[0]))
			$html .= "<TD valign='center' align='center'><img src='loadimg.php?h=80&filename=".$pngfiles[0]."' height='80'></TD>\n";
		else
			$html .= "<td></TD>\n";

		// NUMBER OF PARTICLES
		if ($numpart)
			$html .= "<TD valign='center' align='center'>$numpart<br/>of<br/>$stackcount</TD>\n";
		else
			$html .= "<td></TD>\n";

		// APIX
		$html .= "<TD valign='center' align='center'>$stackapix</TD>\n";

		// BOXSIZE
		$boxsize = $rctrun['boxsize'];
		$html .= "<TD valign='center' align='center'>$boxsize </TD>\n";

		// RESOLUTION
		if ($rctrun['fsc']) {
			$html .= "<TD valign='center' align='center'>\n".round($rctrun['fsc'],2)." &Aring;<br/>\n";

			$halfint = (int) floor($rctrun['fsc']);
			$fscfile = $rctrun['path']."/".$rctrun['fscfile'];
			$html .= "<a href='fscplot.php?expId=$expId&width=800&height=600&apix=$stackapix&box=$boxsize&fscfile=$fscfile&half=$halfint'>"
			."<img border='0' src='fscplot.php?expId=$expId&width=100&height=50&apix=$stackapix&box=$boxsize"
			."&nomargin=TRUE&fscfile=$fscfile&half=$halfint'></a>\n";
			$html .= "</td>\n";

			$html .= "<TD valign='center' align='center'>\n".round($rctrun['rmeas'],2)." &Aring;</TD>\n";
		} else {
			$html .= "<td></TD>\n<td></TD>\n";
		}

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($rctid,$rctrun['description']) : $rctrun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no rct volume information available";
}


processing_footer();
?>
