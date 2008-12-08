<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";
  
$expId = $_GET['expId'];
$projectId = (int) getProjectFromExpId($expId);
//echo "Project ID: ".$projectId." <br/>\n";
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if($_GET['analysis'])
	$formAction.="&analysis=1";
if ($_GET['showHidden'])
	$formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Aligned Stack Report","Aligned Stack Summary Page", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
//$stackIds = $particle->getAlignStackIds($expId, True);
if ($_GET['cluster']) {
	$stackdatas = $particle->getAlignStackIdsWithCluster($expId, $projectId);
	$hidestackdatas = $stackdatas;
} elseif ($_GET['analysis']) {
	$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);
	$hidestackdatas = $stackdatas;
} elseif (!$_GET['showHidden']) {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, False);
	$hidestackdatas = $particle->getAlignStackIds($expId, $projectId, True);
} else {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, True);
	$hidestackdatas = $stackdatas;
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden aligned stacks]</a><br/><br/>\n";
}

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	//echo print_r($stackdatas)."<br/>\n";
	foreach ($stackdatas as $stackdata) {
		echo openRoundBorder();
		echo "<table cellspacing='8' cellpading='5' border='0'>\n";
		$alignstackid = $stackdata['alignstackid'];
		if ($_GET['showHidden'])
			$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, true);
		else
			$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, false);
		if ($analysisdatas) {
			if ($_GET['showHidden'])
				$clusterdatas = $particle->getClusteringStacksForAlignStack($alignstackid, $projectId, true);
			else
				$clusterdatas = $particle->getClusteringStacksForAlignStack($alignstackid, $projectId, false);
			if ($clusterdatas) {
				// Stack with analysis and clustering
				echo "<tr><td>\n";
				echo alignstacksummarytable($alignstackid, true);
				echo "<span style='border: 1px'>&nbsp;"
					."<a href='runCoranClassify.php?expId=$expId&alignId=$alignstackid'>"
					."Run Another Coran Classify On Align Stack Id $alignstackid</a>&nbsp;</span><br/>\n";	
				echo "</td></tr>\n";
				foreach ($analysisdatas as $analysisdata) {
					echo "<tr><td>\n";
					//echo print_r($analysisdata)."<br/>\n";;
					$analysisid = $analysisdata['analysisid'];
					echo analysissummarytable($analysisid, true);
					echo "<span style='font-size: larger; background-color:#eeccee;'>&nbsp;"
						."<a href='runClusterCoran.php?expId=$expId&analysisId=$analysisid&alignId=$alignstackid'>"
						."Run Particle Clustering On Analysis Id $analysisid</a>&nbsp;</span><br/>\n";
					echo "</td></tr>\n";
				}
				foreach ($clusterdatas as $clusterdata) {
					echo "<tr><td>\n";
					//echo print_r($analysisdata)."<br/>\n";;
					$clusterid = $clusterdata['clusterid'];
					$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
					$clustervarfile = $clusterdata['path']."/".$clusterdata['var_imagicfile'];
					echo "<span style='font-size: larger; background-color:#eeccee;'>&nbsp;"
						."<a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
						."View Class Average $clusterid with ".$clusterdata['num_classes']."</a>&nbsp;</span><br/>\n";
					echo "</td></tr>\n";
				}
			} else {
				// Stack with analysis
				echo "<tr><td>\n";
				echo alignstacksummarytable($alignstackid, true);
				echo "<span style='border: 1px'>&nbsp;"
					."<a href='runCoranClassify.php?expId=$expId&alignId=$alignstackid'>"
					."Run Another Coran Classify On Align Stack Id $alignstackid</a>&nbsp;</span><br/>\n";	
				echo "</td></tr>\n";
				//print_r($analysisdatas);
				foreach ($analysisdatas as $analysisdata) {
					echo "<tr><td>\n";
					//echo print_r($analysisdata)."<br/>\n";;
					$analysisid = $analysisdata['DEF_id'];
					echo analysissummarytable($analysisid);
					echo "<span style='font-size: larger; background-color:#eeccee;'>&nbsp;"
						."<a href='runClusterCoran.php?expId=$expId&analysisId=$analysisid&alignId=$alignstackid'>"
						."Run Particle Clustering On Analysis Id $analysisid</a>&nbsp;</span><br/>\n";
					echo "</td></tr>\n";
				}
			}
		} else {
				// Stack with nothing
			echo "<tr><td>\n";
			echo alignstacksummarytable($alignstackid);
			echo "<span style='font-size: larger; background-color:#eeccee;'>&nbsp;"
				."<a href='runCoranClassify.php?expId=$expId&alignId=$alignstackid'>"
				."Run Coran Classify On Align Stack Id $alignstackid</a>&nbsp;</span><br/>\n";
			echo "</td></tr>\n";
		}
		echo "</table>\n";
		echo closeRoundBorder();
		echo "<br/>\n";
	}
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden aligned stacks]</a><br/><br/>\n";
}

processing_footer();
exit;

?>
