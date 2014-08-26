<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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

processing_header("Multi-model Reconstruction Summary","Multi-model Reconstruction Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$reconRuns = $particle->getMultiModelReconIdsFromSession($sessionId);
if ($reconRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'final image', 'recon name', 'description', 'path', '',
		'stack info', 'num parts', 'box size', 'pixel size',  '',
		'model info', 'model symm',  '',
		'FSC&frac12; Rmeasure resolution', 'avg median<br/>euler jump',);
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	$prevName = '';
	$bgcoloron = False;
	foreach ($reconRuns as $reconrun) {
		$reconid = $reconrun['DEF_id'];

		// update description
		if ($_POST['updateDesc'.$reconid]) {
			updateDescription('ApRefineRunData', $reconid, $_POST['newdescription'.$reconid]);
			$reconrun['description']=$_POST['newdescription'.$reconid];

		}

		// hide recon
		if ($_POST['hideItem'.$reconid]) {
			echo "Hiding Recon $reconid\n<br/>\n";
			$particle->updateHide('ApRefineRunData', $reconid, '1');
			continue;
		}

		// GET INFO
		$reconname = $reconrun['runname'];
		$reference_number = $reconrun['reference_number'];
		$path = $reconrun['path'];

		$stackid = $reconrun['REF|ApStackData|stack'];
		$stackcount = commafy($particle->getNumStackParticles($stackid));
		$stackmpix = $particle->getStackPixelSizeFromStackId($stackid);
		$stackparams = $particle->getStackParams($stackid);
		$stackapix = format_angstrom_number($stackmpix);
		$stackbox = (int) $stackparams['boxsize'];
		//print_r($stackparams);

		$modelid 	= $reconrun['REF|ApInitialModelData|initialModel'];
		$modelparams = $particle->getInitModelInfo($modelid);
		$symdata 	= $particle->getSymInfo($modelparams['REF|ApSymmetryData|symmetry']);
		$res 		= $particle->getHighestResForRecon($reconid);
		$avgmedjump = $particle->getAverageMedianJump($reconid);
		$iterinfo 	= $particle->getIterationInfo($reconid);
		
		// Find the total number of particles used for this refinement
		$lastiterinfo 	= $particle->getRefinementData( $reconid, $reconrun['num_iter'] );
		$lastiterid 	= $lastiterinfo[0]['DEF_id'];
		$numIterParts	= $particle->getNumParticlesFromRefineIter( $lastiterid );
		$numIterParts	= $numIterParts[0]['num_parts'];
		// to convert the string $stackcount to an integer, first remove any commas or conversion chokes
		$stackParts		= intval(ereg_replace("[^-0-9\.]","",$stackcount));
		$percentParts 	= floor(($numIterParts * 100) / $stackParts);
		
		// See if this has the same name as the previous one
		// Toggle the bg color each time a new set is displayed
		// Using the same color that appears in the appion menu.
		if ( $prevName != $reconname ) {
			$bgcoloron = !$bgcoloron;
		} 	
		$prevName = $reconname;
		$bgcolor = $bgcoloron ? "style='background-color:#EEE' " : "";
	
		
		// Add the final image
		$bestimages = glob($reconrun['path'].'/'.$iterinfo[0]['volumeDensity'].'.1.png');
		if ($bestimages)
			$bestimage = $bestimages[0];

		// recon info
		$html .= "<tr $bgcolor>\n";
		// image
		if (file_exists($bestimage)) 
			$html .= "<td><a href='loadimg.php?filename=$bestimage' target='snapshot'>"
				."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a></td>\n";
		else
			$html .= "<td></td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($reconid,$reconrun['description']) : $reconrun['description'];

		// recon info		
		$html .= "<td><font size='+1'><a href='reconreport.php?expId=$expId&reconId=$reconid'>$reconname</a></font>\n"
			." <br/><i>(ID: $reconid reference:$reference_number)</i>\n"
			." <br/><input class='edit' type='submit' name='hideItem".$reconid."' value='hide'>\n"
			."</td>\n";
		$html .= "<td><font size=-2>$descDiv</font></td>\n";
		$html .= "<td><font size=-2>$path</font></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// stack info
		$html .= "<td><a href='stackreport.php?expId=$expId&sId=$stackid'>".$stackparams['shownstackname']."</a>"
			." <br/><i>(ID: $stackid)</i></td>\n";
		$html .= "<td>$stackcount<br/><i>(used: $numIterParts, $percentParts%)</i></td>\n";
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
