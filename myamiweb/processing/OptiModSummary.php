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

processing_header("OptiMod Summary","OptiMod Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

// --- Get Reconstruction Data
$aclRunsTs = $particle->getAutomatedCommonLinesRunsTs($sessionId);
$aclRunsCs = $particle->getAutomatedCommonLinesRunsCs($sessionId);
$aclRuns = array_merge((array)$aclRunsTs, (array)$aclRunsCs);
//print_r($aclRuns);

if ($aclRuns) {

	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'best image', 'best volumes', 'combined score', 'OptiMod runname', 'description', 'path', '',
		'stack info', 'num parts', 'box size', 'pixel size');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	foreach ($aclRuns as $aclrun) {
		$aclid = $aclrun['DEF_id'];

//		print_r($aclRun);

		// update description
		if ($_POST['updateDesc'.$aclid]) {
			updateDescription('ApAutomatedCommonLinesRunData', $aclid, $_POST['newdescription'.$aclid]);
			$aclrun['description']=$_POST['newdescription'.$aclid];

		}

		// hide acl
		if ($_POST['hideItem'.$aclid]) {
			echo "Hiding Recon $aclid\n<br/>\n";
			$particle->updateHide('ApRefineRunData', $aclid, '1');
			continue;
		}

		// GET INFO
		$aclname = $aclrun['runname'];
		$path = $aclrun['path'];

		if ($aclrun['REF|ApClusteringStackData|clusterid']) {
			$stackid = $aclrun['REF|ApClusteringStackData|clusterid'];
			$stackcount = '';
			$stackmpix = '';
			$stackapix = '';
			$stackbox = '';
		}
		elseif ($aclrun['REF|ApTemplateStackData|templatestackid']) {
			$stackid = $aclrun['REF|ApTemplateStackData|templatestackid'];
			$stackmpix = $particle->getStackPixelSizeFromStackId($stackid);
			$stackparams = $particle->getStackParams($stackid);
			$stackapix = format_angstrom_number($stackmpix);
			$stackbox = (int) $stackparams['boxsize'];
		}

		$statfile = $path."/"."final_model_stats_sorted_by_Rcrit.dat";
		if (file_exists($statfile)) { 
			$statarray = file($statfile);
			$volumes = array();
			$Rcrits = array();
			for ($i = 1; $i <= 5; $i++) {
				$row = ltrim(rtrim($statarray[$i]));
				$row2 = preg_replace( '/\s+/', ' ', $row);
				$keydata = explode(' ', $row2);
				$volume = $keydata[0];
				$volumes[$i] = $volume;
				$Rcrit = $keydata[1];
				$Rcrits[$i] = $Rcrit;
			}
//		print_r($volumes);
//		print_r($Rcrits);
		}


		//print_r($aclrun);
		$pathtoimage = $aclrun['path'].'/snapshots/'.$volumes[0].'.slice.png';
		$bestimages = glob($aclrun['path'].'/snapshots/'.$volumes[0].'*.png');
		if ($bestimages)
			$bestimage = $bestimages[0];
		else $bestimage = "";

		// acl info
		$html .= "<tr>\n";
		// image
		if (file_exists($bestimage)) 
			$html .= "<td><a href='loadimg.php?filename=$bestimage' target='snapshot'>"
				."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a></td>\n";
		else
			$html .= "<td>no snapshot available</td>\n";

		# add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($aclid,$aclrun['description']) : $aclrun['description'];

		// best volumes & combined scores
		$html .= "<td>";
		for ($i = 1; $i <= 5; $i++) {
			$html .= $volumes[$i]."<br>";
		}
		$html .= "</td>\n";
		$html .= "<td>";
		for ($i = 1; $i <= 5; $i++) {
			$html .= $Rcrits[$i]."<br>";
		}
		$html .= "</td>\n";
		

		// acl info		
		$html .= "<td><font size='+1'><a href='OptiModReport.php?expId=$expId&aclId=$aclid'>$aclname</a></font>\n"
			." <br/><i>(ID: $aclid)</i>\n"
			." <br/><input class='edit' type='submit' name='hideItem".$aclid."' value='hide'>\n"
			."</td>\n";
		$html .= "<td><font size=-2>$descDiv</font></td>\n";
		$html .= "<td><font size=-2>$path</font></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";

		// class average info
//		print_r($particle->getClusteringStackParams(1));
		if ($aclrun['REF|ApClusteringStackData|clusterid']) {
			$csdata = $particle->getClusteringStackParams($aclrun['REF|ApClusteringStackData|clusterid']);
			$csfile = $csdata['path']."/".$csdata['avg_imagicfile'];
			$csid = $csdata['DEF_id'];
			$apix = $csdata['pixelsize'];
			$box = $csdata['boxsize'];
			$numparts = $csdata['num_classes'];
			$html.="<td><a target=tsview href='viewstack.php?file=$csfile&expId=$expId"
				."&clusterId=$csid'><b>View Clustering Stack (ID: $csid)</b></a></td>\n";
			$html .= "<td bgcolor='#dddddd'></td>\n";
		}
		elseif ($aclrun['REF|ApTemplateStackData|templatestackid']) {
			$tsdata = $particle->getTemplateStackParams($aclrun['REF|ApTemplateStackData|templatestackid']);
			$tsfile = $tsdata['path']."/".$tsdata['templatename'];
			$tsid = $tsdata['DEF_id'];
			$apix = $tsdata['apix'];
			$box = $tsdata['boxsize'];
			$numparts = $tsdata['numimages'];
			$html.="<td><a target=tsview href='viewstack.php?file=$tsfile&expId=$expId"
				."&templateStackId=$tsid'><b>View Template Stack (ID: $tsid)</b></a></td>\n";
		} 

		// rest
		$html .= "<td>$numparts</td>\n";
		$html .= "<td>$box</td>\n";
		$html .= "<td>$apix</td>\n";

		$html .= "</tr>\n";
	}

	$html .= "</table>\n";
	echo $html;
} else {
	echo "no common lines reconstruction information available";
}

processing_footer();

?>
