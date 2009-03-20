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
$fulltomoId = $_GET['fullId'];
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

processing_header("SubTomographic Reconstruction Summary","SubTomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Fulltomograms
$tiltseries = $particle->getTiltSeries($sessionId);
$html = "<h4>Full Tomograms</h4>";
$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$html .= "<TR>\n";
$display_keys = array ( 'tiltseries','id','runname','description','subtomograms');
foreach($display_keys as $key) {
	$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
}

// --- Get Subvolume Tomograms
$tomograms = $particle->getSubTomogramsFromFullTomogram($fulltomoId);
if ($tomograms) {
	$html = "<h4>Subvolume tomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'tiltseries','full','volume<br/>xycenter,zoffset<br/>dimension','snapshot','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	foreach ($tomograms as $tomo) {
		$tomogramid = $tomo['DEF_id'];
		$tomogram = $particle->getTomogramInfo($tomogramid);
		$dzprint = ($tomogram['dz'])?$tomogram['dz']:'?';
		$dimprint = '('.$tomogram['dx'].','.$tomogram['dy'].','.$dzprint.')';
		if ($tomogram['prtlimage']) {
			$number = $tomogram['number'];
			$center0 = $particle->getTomoCenter($tomogram['centerx'],
					$tomogram['centery'],$tomogram['prtlimage'],$tomogram['tiltseries']);
			$center0['x'] = floor($center0['x']);
			$center0['y'] = floor($center0['y']);
			$offsetz = floor($tomogram['offsetz']);
		} else {
			if ($tomogram['full']) {
				$number = $tomogram['number'];
				$center0 = array('x'=>'?','y'=>'?');
				$offsetz = '?';
			} else {
				$number = '';
				$center0 = Null;
				$offsetz = 0;
			}
		}
		$centerprint = ($tomogram['full']) ? '('.$center0['x'].','.$center0['y'].')' : 'Full';
		$offsetprint = $offsetz;
		// update description
		if ($_POST['updateDesc'.$tomogramid]) {
			updateDescription('ApTomogramData', $tomogramid, $_POST['newdescription'.$tomogramid]);

			$tomogram['description']=$_POST['newdescription'.$tomogramid];

		}
		$tiltseriesnumber = $tomogram['tiltnumber'];
		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<td>$tiltseriesnumber</TD>\n";
		$html .= "<td>".$tomogram['full']."</TD>\n";
		$html .= "<td><A HREF='tomoreport.php?expId=$expId&tomoId=$tomogramid'>$number<br/>$centerprint,$offsetprint<br/>$dimprint</A></TD>\n";
		$html .= "<td>";
    $snapfile = $tomogram['path'].'/snapshot.png';
		if (!file_exists($snapfile)) 
			$snapfile = $tomogram['path'].'/projectiona.jpg';
		$maxheight = 80;
		$maxwidth = 400;
		$imgsize = array(10,10);
		if (file_exists($snapfile)) 
			$imgsize = getimagesize($snapfile);
		if ($imgsize[1] < $maxheight) {
			$imglimit = "WIDTH='".min($imgsize[0],$maxwidth)."'";
		} else {
			$imglimit = "HEIGHT='".$maxheight."'";
		}
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><img src='loadimg.php?filename=$snapfile' ".$imglimit." >\n";
		$html .= "</td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($tomogramid,$tomogram['description']) : $tomogram['description'];

		$html .= "<td>$descDiv</td>\n";
#		$downloadDiv = "<a href=downloadtomo.php?tomogramId=$tomogramid>[Download Tomogram]</a><br>";
#		$html .= "<td>$downloadDiv</td>\n";
		$html .= "</tr>\n";
	}
	$html .= "</table>\n";
	echo $html;
} else {
	echo "no subvolume tomograms available";
}


processing_footer();
?>
