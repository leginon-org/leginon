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
				echo "<tr><td>\n";
				$numclusters = count($particle->getClusteringStacks($expId, $projectId));
				echo apdivtitle("Clustering Info: ".$numclusters." clusters\n");

				foreach ($clusterruns as $clusterrun) {
					$clusterrunid = $clusterrun['clusterrunid'];
					if ($_GET['showHidden'])
						$clusterdatas = $particle->getClusteringStacksForClusteringRun($clusterrunid, true);
					else
						$clusterdatas = $particle->getClusteringStacksForClusteringRun($clusterrunid, false);
					if ($clusterdatas) {
						if ($clusterrun['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
							echo "<b>Cluster Run ".$clusterrunid."</b>"
								.", method='<i> Hierarchical Clustering (IMAGIC)"
								."</i>', factor list='<i>69 Eigen Images, (eigenimages.img)</i>'\n";
							echo "<ul>\n";
						} elseif ($clusterrun['REF|ApSpiderClusteringParamsData|spiderparams']) {
							echo "<b>Cluster Run ".$clusterrunid."</b>"
								.", method='<i>".$clusterrun['method']." (SPIDER) "
								."</i>', factor list='<i>".$clusterrun['factor_list']."</i>'\n";
							echo "<ul>\n";
						} elseif ($clusterrun['REF|ApKerDenSOMParamsData|kerdenparams']) {
							// KerDen only has one cluster data
							$clusterdata = $clusterdatas[0];
							$clusterid = $clusterdata['clusterid'];
							echo "<b>Cluster Run ".$clusterrunid.":</b>&nbsp;\n"
								."<i>KerDen Self-Organizing Map (Xmipp)</i><br/>\n";
							$montagefile = $clusterdata['path']."/"."montage.png";
							echo "<a href='loadimg.php?filename=$montagefile'>\n"
								."<img src='loadimg.php?h=80&filename=$montagefile' height='80'><br/>View Montage</a>\n";
							$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
							echo "&nbsp;<a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
								." View as Stack</a><br/>\n";
						}
						foreach ($clusterdatas as $clusterdata) {
							$clusterid = $clusterdata['clusterid'];
							$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
							$clustervarfile = $clusterdata['path']."/".$clusterdata['var_imagicfile'];
							if ($clusterdata['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
								echo "<li><span>"
									."<a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
									.$clusterdata['num_classes']." Class Averages</a>&nbsp;"
									."</span></li>\n";
							} elseif ($clusterdata['REF|ApSpiderClusteringParamsData|spiderparams']) {
								echo "<li><span>"
									."<a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
									.$clusterdata['num_classes']." Class Averages</a>&nbsp;"
									."<a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clustervarfile'>"
									."[variance]</a>&nbsp;(ID $clusterid) "
									."</span></li>\n";
							}
						}
						echo "</ul>\n";
					}
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
