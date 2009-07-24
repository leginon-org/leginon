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

//echo $particle->mysql->getDBInfo();

// find each stack entry in database
//$stackIds = $particle->getAlignStackIds($expId, True);
if ($_GET['cluster']) {
	$stackdatas = $particle->getAlignStackIdsWithCluster($expId, $projectId);
	$hidestackdatas = $stackdatas;
} elseif ($_GET['analysis']) {
	$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);
	$hidestackdatas = $stackdatas;
} elseif (!$_GET['showHidden']) {
	$stackdatas = $particle->getAlignStackIds($expId, False);
	$hidestackdatas = $particle->getAlignStackIds($expId, True);
} else {
	$stackdatas = $particle->getAlignStackIds($expId, True);
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
		echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
		$alignstackid = $stackdata['alignstackid'];
		if ($_GET['showHidden'])
			$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, true);
		else
			$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, false);
		if ($analysisdatas) {
			if ($_GET['showHidden'])
				$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, true);
			else
				$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, false);
			if ($clusterruns) {
				// --------------------------
				// Stack with analysis and clustering
				// --------------------------
				echo "<tr><td>\n";
				echo alignstacksummarytable($alignstackid, true);
				echo "<a class='btp1' href='selectFeatureAnalysis.php?expId=$expId&alignId=$alignstackid'>"
					."Run Another Feature Analysis On Align Stack Id $alignstackid</a></span><br/>\n";	
				echo "</td></tr>\n";

				// START ANALYSIS
				if ($analysisdatas)
					echo "<tr><td><hr/>Feature Analysis<hr/></td></tr>\n";

				foreach ($analysisdatas as $analysisdata) {
					echo "<tr><td>\n";
					//echo print_r($analysisdata)."<br/>\n";;
					$analysisid = $analysisdata['analysisid'];
					echo analysissummarytable($analysisid, true);
					if ($analysisdata['REF|ApCoranRunData|coranrun'] != false) {
						echo "<a class='btp1' href='runClusterCoran.php?expId=$expId"
							."&analysisId=$analysisid&alignId=$alignstackid'>"
							."Run Another Particle Clustering On Analysis Id $analysisid</a><br/>\n";
						echo "</td></tr>\n";
					}
					elseif ($analysisdata['REF|ApImagicAlignAnalysisData|imagicMSArun'] != false) {
						echo "<a class='btp1' href='imagicMSAcluster.php?expId=$expId"
							."&analysisId=$analysisid&alignId=$alignstackid'>"
							."Run Another Particle Clustering On Analysis Id $analysisid</a>&nbsp;<br/>\n";
						echo "</td></tr>\n";
					}
				}

				// START CLUSTERING
				if ($clusterruns)
					echo "<tr><td><hr/>Particle Clusters<hr/></td></tr>\n";
				echo "<tr><td>\n";

				foreach ($clusterruns as $clusterrun) {
					$clusterrunid = $clusterrun['clusterrunid'];
					$clusterrunid = $clusterrun['clusterrunid'];
					echo clustersummarytable($clusterrunid, true);
				}
				echo "</td></tr>\n";
			} else {
				// --------------------------
				// Stack with analysis
				// --------------------------
				echo "<tr><td>\n";
				echo alignstacksummarytable($alignstackid, true);
				echo "<a class='btp1' href='selectFeatureAnalysis.php?expId=$expId&alignId=$alignstackid'>"
					."Run Another Feature Analysis On Align Stack Id $alignstackid</a><br/>\n";	
				echo "</td></tr>\n";

				// START ANALYSIS
				if ($analysisdatas)
					echo "<tr><td><hr/>Feature Analysis<hr/></td></tr>\n";

				foreach ($analysisdatas as $analysisdata) {
					echo "<tr><td>\n";
					$analysisid = $analysisdata['DEF_id'];
					echo analysissummarytable($analysisid);
					if ($analysisdata['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
						echo "<a class='btp1' href='imagicMSAcluster.php?expId=$expId&analysisId=$analysisid&alignId=$alignstackid'>"
							."Run IMAGIC Particle Clustering On Analysis Id $analysisid</a><br/>\n";
						echo "</td></tr>\n";
					}
					else {
						echo "<a class='btp1' href='runClusterCoran.php?expId=$expId&analysisId=$analysisid&alignId=$alignstackid'>"
							."Run Particle Clustering On Analysis Id $analysisid</a><br/>\n";
						echo "</td></tr>\n";
					}
				}
			}
		} else {
			// --------------------------
			// Just a stack with nothing
			// --------------------------
			echo "<tr><td>\n";
			echo alignstacksummarytable($alignstackid);
			echo "<a class='btp1' href='selectFeatureAnalysis.php?expId=$expId&alignId=$alignstackid'>"
				."Run Feature Analysis On Align Stack Id $alignstackid</a><br/>\n";
			echo "</td></tr>\n";
		}
		echo "</table>\n";
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
