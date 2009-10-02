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
} else {
	$sessionId=$_POST['sessionId'];
	$formAction=$_SERVER['PHP_SELF'];
}
if ($_GET['showHidden'])
	$formAction.="&showHidden=1";
$projectId = (int) getProjectFromExpId($expId);

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("OTR Volume Summary","OTR Volume Summary Page", $javascript);

// edit description form
echo "<form name='otrform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get OTR Data
$otrRuns = $particle->getOtrRunsFromSession($sessionId, False);

if (!$_GET['showHidden']) {
	$otrRuns = $particle->getOtrRunsFromSession($sessionId, False);
	$hideotrRuns = $particle->getOtrRunsFromSession($sessionId, True);
} else {
	$otrRuns = $particle->getOtrRunsFromSession($sessionId, True);
	$hideotrRuns = $otrRuns;
}

if (!$_GET['showHidden'] && count($otrRuns) != count($hideotrRuns)) {
	$numhidden = count($hideotrRuns) - count($otrRuns);
	echo "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=1'>[Show ".$numhidden." hidden otr runs]</a><br/><br/>\n";
} elseif ($_GET['showHidden']) {
	echo "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=0'>[Hide hidden otr runs]</a><br/><br/>\n";
}

if ($otrRuns) { 

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'defid', 'name', 'image', 'num part', 'pixel size', 'box size', 'fsc res', 'rmeasure', 'description');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	srand(time());
	foreach ($otrRuns as $otrrun) {
		$otrid = $otrrun['DEF_id'];
		$numpart = commafy($otrrun['numpart']);

		// update description
		if ($_POST['updateDesc'.$otrid]) {
			updateDescription('ApOtrRunData', $otrid, $_POST['newdescription'.$otrid]);
			$otrrun['description']=$_POST['newdescription'.$otrrun];
		}

		if ($_POST['hideItem'.$otrid] == 'hide') {
			$particle->updateHide('ApOtrRunData', $otrid, '1');
			$otrrun['hidden']=1;
		} elseif ($_POST['unhideItem'.$otrid] == 'unhide') {
			$particle->updateHide('ApOtrRunData', $otrid, '0');
			$otrrun['hidden']=0;
		}

		// GET INFO
		$stackcount= commafy($particle->getNumStackParticles($otrrun['REF|ApStackData|tiltstack']));
		$stackmpix = $particle->getStackPixelSizeFromStackId($otrrun['REF|ApStackData|tiltstack']);
		$stackapix = format_angstrom_number($stackmpix);

		// PRINT INFO
		$html .= "<TR>\n";
		// runid and hide
		$html .= "<TD valign='center' align='center'>$otrrun[DEF_id]\n";
		if ($otrrun['hidden'] == 1) {
			$html.= "<br/><font color='#cc0000'>HIDDEN</font>\n";
			$html.= " <input class='edit' type='submit' name='unhideItem".$otrid."' value='unhide'>\n";
		} else $html .= "<br/><input class='edit' type='submit' name='hideItem".$otrid."' value='hide'>\n";
		$html .= "</td>\n";

		// runname and link
		$html .= "<TD valign='center' align='center'>"
			."<A HREF='otrreport.php?expId=$expId&otrId=$otrrun[DEF_id]'>$otrrun[runname]</A></td>\n";



		// SAMPLE PNG FILE

		$giffiles = glob($otrrun['path']."/volume*".$otrrun['numiter'].".mrc.animate.gif");
		$pngfiles = glob($otrrun['path']."/volume*".$otrrun['numiter'].".mrc.1.png");
		if ($giffiles && file_exists($giffiles[0]))
			$html .= "<td valign='center' align='center'><img src='loadimg.php?rawgif=1&filename=".$giffiles[0]."' height='128'></td>\n";
		elseif ($pngfiles && file_exists($pngfiles[0]))
			$html .= "<td valign='center' align='center'><img src='loadimg.php?h=128&filename=".$pngfiles[0]."' height='128'></TD>\n";
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
		$boxsize = $otrrun['boxsize'];
		$html .= "<TD valign='center' align='center'>$boxsize </TD>\n";

		// RESOLUTION
		if ($otrrun['fsc']) {
			$html .= "<TD valign='center' align='center'>\n".round($otrrun['fsc'],2)." &Aring;<br/>\n";

			$halfint = (int) floor($otrrun['fsc']);
			$fscfile = $otrrun['path']."/".$otrrun['fscfile'];
			$html .= "<a href='fscplot.php?expId=$expId&width=800&height=600&apix=$stackapix&box=$boxsize&fscfile=$fscfile&half=$halfint'>"
			."<img border='0' src='fscplot.php?expId=$expId&width=120&height=90&apix=$stackapix&box=$boxsize"
			."&nomargin=TRUE&fscfile=$fscfile&half=$halfint'></a>\n";
			$html .= "</td>\n";

			$html .= "<TD valign='center' align='center'>\n".round($otrrun['rmeas'],2)." &Aring;</TD>\n";
		} else {
			$html .= "<td></TD>\n<td></TD>\n";
		}

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($otrid,$otrrun['description']) : $otrrun['description'];

		$html .= "<td>$descDiv</td>\n";
		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no otr volume information available";
}

if (!$_GET['showHidden'] && count($otrRuns) != count($hideotrRuns)) {
	$numhidden = count($hideotrRuns) - count($otrRuns);
	echo "<a href='".$formAction."&showHidden=1'>[Show ".$numhidden." hidden otr runs]</a><br/><br/>\n";
} elseif ($_GET['showHidden']) {
	echo "<a href='".$formAction."&showHidden=0'>[Hide hidden otr runs]</a><br/><br/>\n";
}

processing_footer();
?>
