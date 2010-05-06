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

processing_header("3d Density Volume Summary","3d Density Volume Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get 3d Density Data
$allDensityRuns = $particle->get3dDensitysFromSession($sessionId, false);
// --- Only show models
if ($allDensityRuns) {
	$densityRuns=array();
	foreach ($allDensityRuns as $drun) {
		if (!$drun['REF|ApRefineIterData|iterid']) $densityRuns[]=$drun;
	}
}
$densityRuns = $allDensityRuns;

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
			updateDescription('Ap3dDensityData', $densityid, $_POST['newdescription'.$densityid]);
			$densityrun['description']=$_POST['newdescription'.$densityid];
		}

		if ($_POST['hideItem'.$densityid] == 'hide') {
			$particle->updateHide('Ap3dDensityData', $densityid, '1');
			$densityrun['hidden']=1;
		} elseif ($_POST['unhideItem'.$densityid] == 'unhide') {
			$particle->updateHide('Ap3dDensityData', $densityid, '0');
			$densityrun['hidden']=0;
		}

		// PRINT INFO
		$html .= "<TR>\n";

		# def id
		$html .= "<td>$densityrun[DEF_id]\n";
		if ($rctrun['hidden'] == 1) {
			$html.= "<br/><font color='#cc0000'>HIDDEN</font>\n";
			$html.= " <input class='edit' type='submit' name='unhideItem".$densityid."' value='unhide'>\n";
		} else $html .= "<br/><input class='edit' type='submit' name='hideItem".$densityid."' value='hide'>\n";
		$html .= "</td>\n";

		# name
		$html .= "<td><A HREF='densityreport.php?expId=$expId&densityId=$densityid'>$densityrun[name]</A></TD>\n";

		# sample image
		$giffile = $densityrun['path']."/".$densityrun['name'].".animate.gif";
		$pngfile = $densityrun['path']."/".$densityrun['name'].".1.png";
		if ($giffile && file_exists($giffile))
			$html .= "<td valign='center' align='center'><img src='loadimg.php?rawgif=1&filename=".$giffile."' height='128'></td>\n";
		elseif ($pngfile && file_exists($pngfile))
			$html .= "<td valign='center' align='center'><img src='loadimg.php?h=128&filename=".$pngfile."' height='128'></td>\n";
		else
			$html .= "<td></td>\n";


		if ($densityrun['REF|ApRctRunData|rctrun'])
			$html .= "<td><A HREF='rctreport.php?expId=$expId&rctId="
				.$densityrun['REF|ApRctRunData|rctrun']."'>rctrun #"
				.$densityrun['REF|ApRctRunData|rctrun']."</A></TD>\n";
		elseif ($densityrun['REF|ApRefineIterData|iterid'])
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
