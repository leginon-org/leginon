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

if ($_POST['process']) {
	recalculateCriteria();
}
else {
	OptiModSummary();
}

function OptiModSummary($extra=False, $title='Common Lines Summary', $heading='Common Lines Summary', $results=False) {

	// show any errors
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$aclId = $_GET['aclId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&aclId=$aclId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=getProjectId();

	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript.= editTextJava();
	$javascript.= writeJavaPopupFunctions('appion');
	
	processing_header("OptiMod Report","OptiMod Report Page", $javascript, true);

	// edit description form
	echo "<form name='templateform' method='post' action='$formAction'>\n";

	// --- get data
	$particle = new particledata();
	$aclrun = $particle->getAutomatedCommonLinesRunInfo($aclId);

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
			$particle->updateHide('ApAutomatedCommonLinesRunData', $aclid, '1');
			continue;
		}
		// update description
		if ($_POST['updateDesc'.$aclid]) {
			updateDescription('ApAutomatedCommonLinesRunData', $aclid, $_POST['newdescription'.$aclid]);
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
	
		// add button to recalculate statistics
		$ccpr_val = ($_POST['ccpr']) ? $_POST['ccpr'] : 1;
		$ej_val = ($_POST['ej']) ? $_POST['ej'] : 0;
		$fsc_val = ($_POST['fsc']) ? $_POST['ccpr'] : 0;
		$html .= "<br>\n";
		$html .= "<b><font size +1>Recalculate Combined Model Statistics</font></b><br>\n";
		$html .= "<input type='text' name='ccpr' value='$ccpr_val' size='4'>\n";
		$html .= docpop('ccpr_weight', 'CCPR weight');
		$html = addspace($html, 5);
		$html .= "<input type='text' name='ej' value='$ej_val' size='4'>\n";
		$html .= docpop('ej_weight', 'EJ weight');
		$html = addspace($html, 5);
		$html .= "<input type='text' name='fsc' value='$fsc_val' size='4'>\n";
		$html .= docpop('fsc_weight', 'FSC weight');
		$html .= "<input type='hidden' name='path' value='$path'>\n";
		$html .= "<br>\n";	
		$html .= getSubmitForm("Recalculate Statistics");
		$html .= "<br><br><br>\n";

		if ($results) {
			$html .= "<b><font size='+1'>$results<font></b><br><br><br>\n";
		}
	
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
		$display_keys = array ( 'volnum', 'snapshots', 'volume name', 'combined score', '# averaged volumes', 'CCPR', 'EJ', 'FSC (0.5)');
		foreach($display_keys as $key) {
			$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
		}
	
		for ($i = 1; $i <= $length; $i++) {

			// volume number & snapshots
			$html .= "<tr>\n";
			$html .= "<td><font size='+1'><center><b>$i</b></center></font></td>\n";
	
			$pathtoimage = $aclrun['path'].'/snapshots/'.$statdata_sorted[$i][0].'.slice.png';
			$bestimages = glob($aclrun['path'].'/snapshots/'.$statdata_sorted[$i][0].'*.png');
			$html .= "<td>";
			if ($bestimages) {
				for ($j = 0 ; $j <= 4 ; $j++) {
					if (file_exists($bestimages[$j])) {
						$bestimage = $bestimages[$j];
						$html .= "<a href='loadimg.php?filename=$bestimage' target='snapshot'>"
							."<img src='loadimg.php?filename=$bestimage&h=64' height='64'></a>\n";
					}
				}
			} else {
				$html .= "<font size='+1'>no snapshots available</font>\n";
			}
			$html .= "</td>";

			// volume name & statistics
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

			$volnum_temp1 = explode(".", $volname);
			$volnum_temp2 = explode("_", $volnum_temp1[0]);
			$volnum = $volnum_temp2[0];
			$reprojlink = "<a target=tsview href='viewstack.php?file=$path/refinement/refine_$volnum/3d$volnum"
					."_refined_projections.hed&expId=$expId'>reprojections stack</a>\n"; 
			$clsavg_reprojlink = "<a target=tsview href='viewstack.php?file=$path/refinement/refine_$volnum"
					."/clsavg_reprojection_comparison.hed&expId=$expId'>clsavg/reproj comparison</a>\n";
		
			// display relevant information
			$html.= "<td>$volname$modellink<br>$reprojlink<br>$clsavg_reprojlink</td>\n";
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
	exit;
}

function recalculateCriteria() {
	$infile = $_POST['path']."/final_model_stats.dat";
	$outfile = $_POST['path']."/final_model_stats_sorted_by_Rcrit.dat";
	$ccpr = $_POST['ccpr'];
	$ej = $_POST['ej'];
	$fsc = $_POST['fsc'];
	
	// error handling
	if (!$ccpr && !$ej && !$fsc) OptiModSummary("please specify at least one criteria");
	
	// command 
	$command = "combineQualityMetrics.py --infile=$infile --outfile=$outfile ";
	$command .= "--metrics='";
	if ($ccpr) $command .= "CCPR,1,$ccpr ";
	if ($ej) $command .= "EJ,-1,$ej ";
	if ($fsc) $command .= "FSC,-1,$fsc ";
	$command .= "'";

//	$errors = showOrSubmitCommand($command, "", 'Metric Combiner', 1, false);
	if ($_POST['process'] != "Just Show Command") {
		$error = processBasic($command);
		OptiModSummary($error, $title='Common Lines Summary', $heading='Common Lines Summary', false);
	} else {
		$processhost = getSelectedProcessingHost();
		$results = addAppionWrapper($command, $processhost);
		OptiModSummary($error, $title='Common Lines Summary', $heading='Common Lines Summary', $results);
	}
}

function processBasic($command) {
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	if (!($user && $pass)) {
		return "<B>ERROR:</B> Enter a user name and password";
	}
	$processhost = getSelectedProcessingHost();
	$wrappedcommand =  addAppionWrapper($command, $processhost);
	exec_over_ssh($processhost, $user, $pass, $wrappedcommand, TRUE);
	return;
}

function addspace($text, $n) {
	for ($i=1 ; $i <= $n ; $i++) $text.="&nbsp";
	return $text;
}

?>
