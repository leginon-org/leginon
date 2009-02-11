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

processing_header("Tomographic Reconstruction Summary","Tomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Fulltomograms
$tiltseries = $particle->getTiltSeries($sessionId);
$html = "<h4>Full Tomograms</h4>";
$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'tiltseries','id','runname','description');
foreach($display_keys as $key) {
	$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
}
foreach ($tiltseries as $t) {
	$fulltomos = $particle->checkforFulltomogram($t['id']);
	foreach ($fulltomos as $fulltomo) {
		$fulltomoid = $fulltomo['DEF_id'];
			// update description
		if ($_POST['updateDesc'.$fulltomoid]) {
			updateDescription('ApFullTomogramData', $fulltomoid, $_POST['newdescription'.$fulltomoid]);

			$fulltomo['description']=$_POST['newdescription'.$fulltomoid];

		}
		$tiltseriesnumber = $t['number'];
		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$tiltseriesnumber</TD>\n";
		$html .= "<TD><A HREF='fulltomoreport.php?expId=$expId&tomoId=$fulltomoid'>$fulltomoid</A></TD>\n";
		$html .= "<TD>".$fulltomo['runname']."</TD>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($fulltomoid,$fulltomo['description']) : $fulltomo['description'];

		$html .= "<td>$descDiv</td>\n";
#		$downloadDiv = "<a href=downloadtomo.php?tomogramId=$tomogramid>[Download Tomogram]</a><br>";
#		$html .= "<td>$downloadDiv</td>\n";
		$html .= "</TR>\n";
	}
}
$html .= "</table>\n";
$html .= "<br>\n";
echo $html;

// --- Get Subvolume Tomograms
$tomograms = $particle->getTomogramsFromSession($sessionId);
if ($tomograms) {
	$html = "<h4>Subvolume tomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'tiltseries','full','volume','snapshot','description');
	foreach($display_keys as $key) {
		$html .= "<TD><span class='datafield0'>".$key."</span> </TD> ";
	}
	foreach ($tomograms as $tomo) {
		$tomogramid = $tomo['DEF_id'];
		$tomogram = $particle->getTomogramInfo($tomogramid);
		if ($tomogram['prtlimage']) {
			$number = $tomogram['number'];
			$center0 = $particle->getTomoCenter($tomogram['centerx'],
					$tomogram['centery'],$tomogram['prtlimage'],$tomogram['tiltseries']);
			$center0['x'] = floor($center0['x']);
			$center0['y'] = floor($center0['y']);
		} else {
			if ($tomogram['full']) {
				$number = $tomogram['number'];
				$center0 = array('x'=>'?','y'=>'?');
			} else {
				$number = '';
				$center0 = Null;
			}
		}
		$centerprint = ($tomogram['full']) ? '('.$center0['x'].','.$center0['y'].')' : 'Full';
		// update description
		if ($_POST['updateDesc'.$tomogramid]) {
			updateDescription('ApTomogramData', $tomogramid, $_POST['newdescription'.$tomogramid]);

			$tomogram['description']=$_POST['newdescription'.$tomogramid];

		}
		$tiltseriesnumber = $tomogram['tiltnumber'];
		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<TD>$tiltseriesnumber</TD>\n";
		$html .= "<TD>".$tomogram['full']."</TD>\n";
		$html .= "<TD><A HREF='tomoreport.php?expId=$expId&tomoId=$tomogramid'>$number<br/>$centerprint</A></TD>\n";
		$html .= "<td>";
    $snapfile = $tomogram['path'].'/snapshot.png';
		if (!file_exists($snapshotfile)) 
			$snapfile = $tomogram['path'].'/projectiona.jpg';
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
		$html .= "</td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($tomogramid,$tomogram['description']) : $tomogram['description'];

		$html .= "<td>$descDiv</td>\n";
#		$downloadDiv = "<a href=downloadtomo.php?tomogramId=$tomogramid>[Download Tomogram]</a><br>";
#		$html .= "<td>$downloadDiv</td>\n";
		$html .= "</TR>\n";
	}
	$html .= "</table>\n";
	echo $html;
} else {
	echo "no subvolume tomograms available";
}


processing_footer();
?>
