<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
  
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

processing_header("HIP Summary","Helical Reconstruction Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$hipRuns = $particle->getHIPIdsFromSession($sessionId);
//var_dump($hipRuns);


if ($hipRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'final image', 'run name', 'description', 'path', '',
		'stack info', 'num parts', 'box size', 'pixel size',  '',
		'FSC&frac12; Rmeasure resolution',);
	$numcols = count($display_keys);
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($hipRuns as $hiprun) {
		$hipid = $hiprun['DEF_id'];
		$hipParams = $particle->getHipParamsInfo($hipid);

		// update description
		if ($_POST['updateDesc'.$hipid]) {
			updateDescription('ApHipRunData', $hipid, $_POST['newdescription'.$hipid]);
			$hiprun['description']=$_POST['newdescription'.$hipid];

		}

		// hide recon
		if ($_POST['hideItem'.$hipid]) {
			echo "Hiding Run $hipid\n<br/>\n";
			$particle->updateHide('ApHipRunData', $hipid, '1');
			continue;
		}

		// GET INFO
		$runname = $hiprun['runname'];
		$path = $hiprun['path'];
		$stackid = $hiprun['REF|ApStackData|stack'];
		$stackcount = commafy($particle->getNumStackParticles($stackid));
		$stackmpix = $particle->getStackPixelSizeFromStackId($stackid);
		$stackparams = $particle->getStackParams($stackid);
		$stackapix = format_angstrom_number($stackmpix);
		$stackbox = (int) $stackparams['boxsize'];
		$res = $particle->getHighestResForHip($hipid);
		//print_r($hiprun['path']);
		$rescut = $hipParams['rescut'];
		$bestimage = ($path.'/avgsnif1/avgsnif2/avg3/avglist3_'.$rescut.'p.mrc.2.png');

		// recon info
		$html .= "<tr>\n";
		// image
		if (file_exists($bestimage)) 
			$html .= "<td><a href='loadimg.php?filename=$bestimage' target='snapshot'>"
				."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a></td>\n";
		else
			$html .= "<td>'$bestimage not found'</td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($hipid,$hiprun['description']) : $hiprun['description'];

		// recon info		
		$html .= "<td><font size='+1'><a href='hipreport.php?expId=$expId&hipId=$hipid'>$runname</a></font>\n"
			." <br/><i>(ID: $hipid)</i>\n"
			." <br/><input class='edit' type='submit' name='hideItem".$hipid."' value='hide'>\n"
			."</td>\n";
		$html .= "<td><font size=-2>$descDiv</font></td>\n";
		$html .= "<td><font size=-2>$path</font></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// stack info
		$html .= "<td><a href='stackreport.php?expId=$expId&sId=$stackid'>".$stackparams['shownstackname']."</a>"
			." <br/><i>(ID: $stackid)</i></td>\n";
		$html .= "<td>$stackcount</td>\n";
		$html .= "<td>$stackbox</td>\n";
		$html .= "<td>$stackapix</td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";
		$html .= sprintf("<td>% 2.1f &Aring; <font size=-2>(FSC&frac12;)</font><br/>% 2.1f &Aring; <font size=-2>(Rm)<br/><i>(iter #%d)</i></font></td>\n", $res['half'], $res['rmeas'], $res['iter']);

	}

	$html .= "</table>\n";
	echo $html;

} else {
	echo "no reconstruction information available";
}

processing_footer();
?>
