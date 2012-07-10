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

processing_header("Automated Common Lines Summary","Automated Common Lines Summary Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

// --- Get Stack Data
$particle = new particledata();

$aclId = $_GET['aclId'];

// --- Get Data
$aclrun = $particle->getAutomatedCommonLinesRunInfo($aclId);
//print_r($aclrun);

if ($aclrun) {

	// get run info
	$aclname = $aclrun['runname'];
	$path = $aclrun['path'];
	$aclid = $aclrun['DEF_id'];
	$description = $aclrun['description'];
	if ($aclrun['REF|ApClusteringStackData|clusterid']) {
		$csdata = $particle->getClusteringStackParams($aclrun['REF|ApClusteringStackData|clusterid']);
		$csfile = $csdata['path']."/".$csdata['avg_imagicfile'];
		$csid = $csdata['DEF_id'];
		$apix = $csdata['pixelsize'];
		$box = $csdata['boxsize'];
		$numparts = $csdata['num_classes'];
		$html.="<td>Cluster Stack ID: $csid<br>\n";
		$html.="<a target=tsview href='viewstack.php?file=$csfile&expId=$expId"
			."&clusterId=$csid'><b>View Clustering Stack</b></a></td>\n";
		$html .= "<td bgcolor='#dddddd'></td>\n";
	}
	elseif ($aclrun['REF|ApTemplateStackData|templatestackid']) {
		$tsdata = $particle->getTemplateStackParams($aclrun['REF|ApTemplateStackData|templatestackid']);
		$tsfile = $tsdata['path']."/".$tsdata['templatename'];
		$tsid = $tsdata['DEF_id'];
		$apix = $tsdata['apix'];
		$box = $tsdata['boxsize'];
		$numparts = $tsdata['numimages'];
		$html.="<td>Template Stack ID: $tsid<br>\n";
		$html.="<a target=tsview href='viewstack.php?file=$tsfile&expId=$expId"
			."&templateStackId=$tsid'><b>View Template Stack</b></a></td>\n";
	} 
	// add edit button to description if logged in
	$descDiv = ($_SESSION['username']) ? editButton($aclid,$aclrun['description']) : $aclrun['description'];
	// hide acl
	if ($_POST['hideItem'.$aclid]) {
		echo "Hiding Recon $aclid\n<br/>\n";
		$particle->updateHide('ApRefineRunData', $aclid, '1');
		continue;
	}
	// update description
	if ($_POST['updateDesc'.$aclid]) {
		updateDescription('ApRefineRunData', $aclid, $_POST['newdescription'.$aclid]);
		$aclrun['description']=$_POST['newdescription'.$aclid];

	}

	// display all informationa
	$html = "";	
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<tr><td><font size='+1'>Runname</font></td><td><font size='+1'>$aclname</font></td></tr>\n";
	$html .= "<tr><td>ID</td><td>$aclid</td></tr>\n";
	$html .= "<tr><td>Description</td><td>$descDiv</td></tr>\n";
	$html .= "<tr><td>Path</td><td>$path</td></tr>\n";
	$html .= "<tr><td>Pixel size</td><td>$apix</td></tr>\n";
	$html .= "<tr><td>Box size</td><td>$box</td></tr>\n";
	$html .= "<tr><td>Number of utilized classes</td><td>$numparts</td></tr>\n";
	if ($aclrun['REF|ApClusteringStackData|clusterid']) {
		$html .= "<br><tr><td>Clustering Stack</td><td><a target=tsview href='viewstack.php?file=$csfile&expId=$expId"
                        ."&templateStackId=$csid'><b>View Clustering Stack (ID $csid)</b></a></td></tr>";
	} else {
		$html .= "<br><tr><td>Template Stack</td><td><a target=tsview href='viewstack.php?file=$tsfile&expId=$expId"
			."&templateStackId=$tsid'><b>View Template Stack (ID $tsid)</b></a></td></tr>";
	}
	$html .= "</table><br>\n";

//	// add button to recalculate statistics
//	$html .= "<br>\n";
//	$html .= "<b><font size +1>Recalculate Combined Model Statistics</font></b><br>\n";


	// statistics files	
	$statfile = $path."/"."final_model_stats.dat";
	if (file_exists($statfile)) {
		$statarray = file($statfile);
		$length = count($statarray)-1;
		$statdata = array();
		for ($i = 1 ; $i <= $length ; $i++) {
			$row = ltrim(rtrim($statarray[$i]));
			$row2 = preg_replace( '/\s+/', ' ', $row);
			$keydata = explode(' ', $row2);
			$volname = $keydata[0];
			$statdata[$volname] = array($keydata[1], $keydata[2], $keydata[3], $keydata[6]);
		}
		
	}
	$statfile_sorted = $path."/"."final_model_stats_sorted_by_Rcrit.dat";
	if (file_exists($statfile_sorted)) { 
		$statarray = file($statfile_sorted);
		$statdata_sorted = array();
		$length = count($statarray)-1; 
		for ($i = 1; $i <= $length; $i++) {
			$row = ltrim(rtrim($statarray[$i]));
			$row2 = preg_replace( '/\s+/', ' ', $row);
			$keydata = explode(' ', $row2);
			$volume = $keydata[0];
			$Rcrit = $keydata[1];
			$num = $statdata[$volume][0];
			$ccpr = $statdata[$volume][1];
			$ej = $statdata[$volume][2];
			$fsc = $statdata[$volume][3];
			$statdata_sorted[$i] = array($volume, $Rcrit, $num, $ccpr, $ej, $fsc);
		}
	}

	$html.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html.= "<TR>\n";
	$display_keys = array ( 'snapshot', 'volume name', 'combined score', '# averaged volumes', 'CCPR', 'EJ', 'FSC (0.5)');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}

	for ($i = 1; $i <= $length; $i++) {

		// display volume & information
		$html.= "<tr>\n";

		$pathtoimage = $aclrun['path'].'/snapshots/'.$statdata_sorted[$i][0].'.slice.png';
		$bestimages = glob($aclrun['path'].'/snapshots/'.$statdata_sorted[$i][0].'*.png');
		if ($bestimages)
			$bestimage = $bestimages[0];
		else $bestimage = "";
		// image
		if (file_exists($bestimage)){
			$html .= "<td><a href='loadimg.php?filename=$bestimage' target='snapshot'>"
				."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a></td>\n";
		} else{
			$html .= "<td>no snapshot available</td>\n";
		}
		// volume name
		$volname = $statdata_sorted[$i][0];
		$Rcrit = $statdata_sorted[$i][1];
		$num = $statdata_sorted[$i][2];
		$ccpr = $statdata_sorted[$i][3];
		$ej = $statdata_sorted[$i][4];
		$fsc = $statdata_sorted[$i][5];

		// add downloader to volumes	
		$modellink = "&nbsp;(<font size='-2'><a href='download.php?expId=$expId&file=$path/$volname'>\n";
		$modellink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download model'>";
		$modellink .= "  &nbsp;download model\n";
		$modellink .= "</a></font>)\n";
	
		$html.= "<td>$volname$modellink</td>\n";
		$html.= "<td>$Rcrit</td>\n";
		$html.= "<td>$num</td>\n";
		$html.= "<td>$ccpr</td>\n";
		$html.= "<td>$ej</td>\n";
		$html.= "<td>$fsc</td>\n";
		$html.= "</tr>";
	}
	$html .= "</table>\n";
	echo $html;

} else {
	echo "no common lines reconstruction information available";
}

processing_footer();

?>
