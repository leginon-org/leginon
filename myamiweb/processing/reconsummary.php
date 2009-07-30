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

processing_header("Reconstruction Summary","Reconstruction Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$reconRuns = $particle->getReconIdsFromSession($sessionId);
if ($reconRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'final image', 'recon name', 'description', '',
		'stack info', 'num parts', 'box size', 'pixel size',  '',
		'model info', 'model symm',  '',
		'FSC&frac12; Rmeasure resolution', 'avg median<br/>euler jump',);
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($reconRuns as $reconrun) {
		$reconid = $reconrun['DEF_id'];

		// update description
		if ($_POST['updateDesc'.$reconid]) {
			updateDescription('ApRefinementRunData', $reconid, $_POST['newdescription'.$reconid]);
			$reconrun['description']=$_POST['newdescription'.$reconid];

		}

		// GET INFO
		$reconname = $reconrun['name'];

		$stackid = $reconrun['REF|ApStackData|stack'];
		$stackcount = commafy($particle->getNumStackParticles($stackid));
		$stackmpix = $particle->getStackPixelSizeFromStackId($stackid);
		$stackparams = $particle->getStackParams($stackid);
		$stackapix = format_angstrom_number($stackmpix);
		$stackbox = (int) $stackparams['boxSize']/$stackparams['bin'];
		//print_r($stackparams);

		$modelid = $reconrun['REF|ApInitialModelData|initialModel'];
		$modelparams = $particle->getInitModelInfo($modelid);
		$symdata = $particle->getSymInfo($modelparams['REF|ApSymmetryData|symmetry']);
		$res = $particle->getHighestResForRecon($reconid);
		$avgmedjump = $particle->getAverageMedianJump($reconid);

		//print_r($reconrun);
		$bestimage = $reconrun['path'].'/threed.'.$res['iter'].'a.mrc.1.png';

		// recon info
		$html .= "<TR>\n";
		// image
		if (file_exists($bestimage)) 
			$html .= "<td><a href='loadimg.php?filename=$bestimage' target='snapshot'>"
				."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a></td>\n";
		else
			$html .= "<td></td>\n";

		// recon info		
		$html .= "<td><font size='+1'><a href='reconreport.php?expId=$expId&reconId=$reconid'>$reconname</a></font>"
			." <br/><i>(ID: $reconid)</i></td>\n";
		$html .= "<td><font size=-2>$descDiv</font></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// stack info
		$html .= "<td><a href='stackreport.php?expId=$expId&sId=$stackid'>".$stackparams['shownstackname']."</a>"
			." <br/><i>(ID: $stackid)</i></td>\n";
		$html .= "<td>$stackcount</td>\n";
		$html .= "<td>$stackbox</td>\n";
		$html .= "<td>$stackapix</td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// model info
		$html .= "<td><b>$modelid:</b> <font size=-2>".$modelparams['description']."</font></td>\n";
		$html .= "<td>".$symdata['symmetry']."</td>";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// recon stats
		$html .= sprintf("<td>% 2.1f &Aring; <font size=-2>(FSC&frac12;)</font><br/>% 2.1f &Aring; <font size=-2>(Rm)<br/><i>(iter #%d)</i></font></td>\n", $res['half'],$res['rmeas'],$res['iter']);
		if ($avgmedjump['count'] > 0) {
			$html .= "<td><A HREF='eulergraph.php?expId=$expId&hg=1&recon=$reconrun[DEF_id]'>";
			$html .= sprintf("%2.1f &plusmn; %2.0f </A>", $avgmedjump['average'], $avgmedjump['stdev']);
			$html .= " <font size=-2><A HREF='jumpSubStack.php?expId=$expId&reconId=$reconrun[DEF_id]'>[sub]</a></font>";
			$html .= "</td>\n";
		} else
			$html .= "<td></td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($reconid,$reconrun['description']) : $reconrun['description'];


		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
//	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
} else {
	echo "no reconstruction information available";
}


processing_footer();
?>
