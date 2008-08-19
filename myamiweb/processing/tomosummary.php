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

processing_header("Tomographic Reconstruction Summary","Reconstruction Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$tomograms = $particle->getTomogramsFromSession($sessionId);
if ($tomograms) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'tiltseries','snapshot','description','download');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($tomograms as $reconrun) {
		$reconid = $reconrun['DEF_id'];
		$tiltseriesinfo = $particle->getTiltSeriesInfo($reconrun['tiltseries']);
		// update description
		if ($_POST['updateDesc'.$reconid]) {
			updateDescription('ApTomogramData', $reconid, $_POST['newdescription'.$reconid]);

			$reconrun['description']=$_POST['newdescription'.$reconid];

		}
		$tiltseriesnumber = $tiltseriesinfo[0]['number'];
		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$tiltseriesnumber</TD>\n";
#		$html .= "<td>$reconrun[name]</td>\n";
#		$html .= "<TD><A HREF='reconreport.php?expId=$expId&reconId=$reconrun[DEF_id]'>$reconrun[name]</A></TD>\n";
		$html .= "<td>";
    $snapfile = $reconrun['path'].'/snapshot.png';
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
		$html .= "</td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($reconid,$reconrun['description']) : $reconrun['description'];

		$html .= "<td>$descDiv</td>\n";
$downloadDiv = "<a href=downloadtomo.php?tomogramId=$reconrun[DEF_id]>[Download Tomogram]</a><br>";
		$html .= "<td>$downloadDiv</td>\n";
		$html .= "</TR>\n";
	}

	$html .= "</table>\n";
	echo $html;
//	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
} else {
	echo "no reconstruction information available";
}


processing_footer();
?>
