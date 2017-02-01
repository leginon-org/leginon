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

if ($_POST['process']) {
	recalculateCriteria();
}
else {
	automatedCommonLinesSummary();
}

function automatedCommonLinesSummary($extra=False, $title='Common Lines Summary', $heading='Common Lines Summary', $results=False) {

	// show any errors
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$simpleId = $_GET['simpleId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&simpleId=$simpleId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=getProjectId();

	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript.= editTextJava();
	$javascript.= writeJavaPopupFunctions('appion');
	
	processing_header("SIMPLE Common Lines Summary","SIMPLE Common Lines Summary Page", $javascript, true);

	// edit description form
	echo "<form name='templateform' method='post' action='$formAction'>\n";

	// --- get run data
	$particle = new particledata();
	$simplerun = $particle->getSIMPLEOrigamiRunInfo($simpleId);

	if ($simplerun) {

		### get all data
		if ($simpleparamid = $simplerun['REF|ApSIMPLEOrigamiParamsData|simple_params']) {
			$simpleparams = $particle->getSIMPLEOrigamiParams($simpleparamid);
		}
		$simpleid = $simplerun['DEF_id'];
		$simplename = $simplerun['runname'];
		$description = $simplerun['description'];
		$path = $simplerun['path'];
		$box = $simplerun['box'];
		$apix = $simplerun['apix'];
		$nconformers = $simpleparams['tos'];
		$lp = $simpleparams['lp'];
		$hp = $simpleparams['hp'];
		$maxits = $simpleparams['maxits'];
		$msk = $simpleparams['msk'];
		$amsklp = $simpleparams['amsklp'];
		$edge = $simpleparams['edge'];
		$trs = $simpleparams['trs'];
		$mw = $simpleparams['mw'];

		### get all stack info	
		if ($clusterid = $simplerun['REF|ApClusteringStackData|clusteringstack']) {
			$clusterparams = $particle->getClusteringStackParams($clusterid);
			$clusterid = $clusterparams['DEF_id'];
			$clusterfile = $clusterparams['path']."/".$clusterparams['avg_imagicfile'];
			$nclasses = $clusterparams['num_classes'];
			$numparts = $clusterparams['num_particles'];
		}
		if ($stackid = $simplerun['REF|ApStackData|stack']) {
			$stackparams = $particle->getStackParams($stackid);
			$stackid = $stackparams['DEF_id'];
			$stackfile = $stackparams['path']."/".$stackparams['name'];
		}
		if ($alignstackid = $simplerun['REF|ApAlignStackData|alignstack']) {
			$alignstackparams = $particle->getAlignStackParams($alignstackid);	
			$alignstackid = $alignstackparams['DEF_id'];
			$alignstackfile = $alignstackparams['path']."/".$alignstackparams['imagicfile'];
		}		

		// add edit button to description if logged in
		$descDiv = ($_SESSION['username']) ? editButton($simpleid,$simplerun['description']) : $simplerun['description'];
		// hide simple
		if ($_POST['hideItem'.$simpleid]) {
			echo "Hiding SIMPLE $simpleid\n<br/>\n";
			$particle->updateHide('ApSIMPLEOrigamiRunData', $simpleid, '1');
			continue;
		}
		// update description
		if ($_POST['updateDesc'.$simpleid]) {
			updateDescription('ApSIMPLEOrigamiRunData', $simpleid, $_POST['newdescription'.$simpleid]);
			$simplerun['description']=$_POST['newdescription'.$simpleid];
		}
	
		// display all informationa
		$html = "";	
		$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr><td><font size='+1'>Runname</font></td><td><font size='+1'>$simplename</font></td></tr>\n";
		$html .= "<tr><td>ID</td><td>$simpleid</td></tr>\n";
		$html .= "<tr><td>Description</td><td>$descDiv</td></tr>\n";
		$html .= "<tr><td>Path</td><td>$path</td></tr>\n";
		$html .= "<tr><td>Pixel size</td><td>$apix</td></tr>\n";
		$html .= "<tr><td>Box size</td><td>$box</td></tr>\n";
		$html .= "<tr><td>Low-pass filter value</td><td>$lp</td></tr>\n";
		$html .= "<tr><td>High-pass filter value</td><td>$hp</td></tr>\n";
		$html .= "<tr><td>Maximum number of iterations run by Origami</td><td>$maxits</td></tr>\n";
		$html .= "<tr><td>Mask</td><td>$msk</td></tr>\n";
		$html .= "<tr><td>Auto-masking Low-pass filter value</td><td>$amsklp</td></tr>\n";
		$html .= "<tr><td>Edge softening parameter</td><td>$edge</td></tr>\n";
		$html .= "<tr><td>Translational search</td><td>$trs</td></tr>\n";
		$html .= "<tr><td>Molecular weight (kDa)</td><td>$mw</td></tr>\n";
		$html .= "<tr><td>Number of utilized classes</td><td>$nclasses</td></tr>\n";
		$html .= "<tr><td>Number of original particles</td><td>$numparts</td></tr>\n";
		if ($simplerun['REF|ApStackData|stack']) {
			$html .= "<br><tr><td>Raw Stack</td><td><a target=tsview href='viewstack.php?file=$stackfile&expId=$expId"
			."&stackid=$stackid'><b>View Stack (ID $stackid)</b></a></td></tr>";
		}
		if ($simplerun['REF|ApAlignStackData|alignstack']) {
			$html .= "<br><tr><td>Aligned Stack</td><td><a target=tsview href='viewstack.php?file=$alignstackfile&expId=$expId"
				."&alignid=$alignid'><b>View Aligned Stack (ID $alignstackid)</b></a></td></tr>";
		}
		if ($simplerun['REF|ApClusteringStackData|clusteringstack']) {
			$html .= "<br><tr><td>Clustering Stack</td><td><a target=tsview href='viewstack.php?file=$clusterfile&expId=$expId"
	                        ."&clusterid=$clusterid'><b>View Clustering Stack (ID $clusterid)</b></a></td></tr>";
		}
		$html .= "</table><br>\n";
	
		$html.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html.= "<TR>\n";
		$display_keys = array ( 'volnum', 'snapshots', 'volume name');
		foreach($display_keys as $key) {
			$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
		}
	
		for ($i = 1; $i <= $nconformers; $i++) {

			// volume number & snapshots
			$html .= "<tr>\n";
			$html .= "<td><font size='+1'><center><b>$i</b></center></font></td>\n";
			$volname = $nconformers."_states/recvol".$maxits."_state".$i.".mrc";
#			echo $volname;	
	
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
	
			// add downloader to volumes	
			$modellink = "&nbsp;(<font size='-2'><a href='download.php?expId=$expId&file=$path/$volname'>\n";
			$modellink .= "  <img style='vertical-align:middle' src='img/download_arrow.png' border='0' width='16' height='17' alt='download model'>";
			$modellink .= "  &nbsp;download model\n";
			$modellink .= "</a></font>)\n";

			// display relevant information
			$html.= "<td>$volname$modellink<br></td>\n";
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
?>
