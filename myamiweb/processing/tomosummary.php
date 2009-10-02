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
if ($_GET['showHidden']) {
	$formAction.="&showHidden=1";
	$showhidden = True;
}
$projectId=$_POST['projectId'];

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Tomographic Reconstruction Summary","Tomogram Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();
if ($_POST) {
$allfulltomos = $particle->getFullTomogramsFromSession($sessionId,True,True);
	foreach ($allfulltomos as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApFullTomogramData',$t['DEF_id']);
}
// --- Get Fulltomograms
$allfulltomos = $particle->getFullTomogramsFromSession($sessionId,True,True);
$shownfulltomos = $particle->getFullTomogramsFromSession($sessionId,False,True);
echo $particle->displayHidingOption($expId,$allfulltomos,$shownfulltomos,$showhidden);
if ($shownfulltomos) {
	$tiltseries = $particle->getTiltSeries($sessionId);
	$html = "<h4>Full Tomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$selected_keys = array ( 'tiltseries','fulltomoid','runname','description','subtomo');
	$display_keys = $selected_keys;
	$display_keys[1] = 'id';
	$display_keys[4] = 'subtomograms';
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	foreach ($tiltseries as $t) {
		$fulltomos = $particle->checkforFulltomogram($t['id'], $showhidden);
		foreach ($fulltomos as $fulltomo) {
			$fulltomoid = $fulltomo['DEF_id'];
			$a = array('tiltseries'=>$t['number'],'fulltomoid'=>$fulltomoid);
			$a = array_merge($a,$fulltomo);
			$a['subtomo'] = ($a['subtomo'] > 0) ? array('display'=>$a['subtomo'],'link'=>$fulltomoid) : 0;
			$html .= $particle->displayParametersInSummary($a,$selected_keys,$expId,'fulltomoid');
		}
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	echo $html;
} else {
	$html = "<p>no full tomograms available</p>";
	echo $html;
}
echo $particle->displayHidingOption($expId,$allfulltomos,$shownfulltomos,$_GET['showHidden']);

// --- Get Subvolume Tomograms
$tomograms = $particle->getOrphanSubTomogramsFromSession($sessionId);
if ($tomograms) {
	$html = "<h4>Directly Uploaded Subvolume tomograms</h4>";
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
		$html .= "<td><A HREF='tomoreport.php?expId=$expId&tomoId=$tomogramid'>Direct Upload<br/>Unknown Location</A></TD>\n";
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
	echo "no other subvolume tomograms available";
}
// --- Get Averaged tomograms
if (!$showhidden) {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, False);
	$allavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
} else {
	$shownavgtomos = $particle->getAveragedTomogramsFromSession($sessionId, True);
	$allavgtomos = $allavgtomos;
}
echo $particle->displayHidingOption($expId,$allavgtomos,$shownavgtomos,$showhidden);
if ($shownavgtomos) {
	$html = "<h4>Averaged SubTomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'avgid','runname','stack','description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	$html .= "</TR>\n";
	foreach ($shownavgtomos as $t) {
		$stackid = $t['stackid'];
		$stackparams = $particle->getStackParams($stackid);
		$stackname = $stackparams['shownstackname'];
		$t['stack'] = array('link'=>$stackid,'display'=>$stackname);
		$html .= $particle->displayParametersInSummary($t,$display_keys,$expId,'');
	}
	$html .= "</table>\n";
	$html .= "<br>\n";
	echo $html;
} else {
	$html = "<p>no averaged tomograms available</p>";
	echo $html;
}

// --- 

processing_footer();
?>
