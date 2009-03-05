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

$javascript.= editTextJava();

processing_header("Cluster Stack List","Cluster Stack List", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	echo "<h2>Cluster Stack List</h2>\n";
	echo "<h4><a href='alignsummary.php?expId=$expId&cluster=1'>Show Composite Page</a></h4>\n";
	foreach ($stackdatas as $stackdata) {
		$alignstackid = $stackdata['alignstackid'];
		$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, $projectId, False);
		if ($clusterruns) {
			foreach ($clusterruns as $clusterrun) {
				$clusterrunid = $clusterrun['clusterrunid'];
				$clusterrunname = $clusterrun['runname'];
				$clusterdatas = $particle->getClusteringStacksForClusteringRun($clusterrunid, false);
				if ($clusterdatas) {
					echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
					echo "<tr><td>\n";
					echo apdivtitle("Clustering Info: <span class='aptitle'>$clusterrunname</span>"
						." (ID: $clusterrunid) with ".count($clusterdatas)." clusters\n");
					echo "<br/>";
					if ($clusterrun['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
						echo "<b>Type:</b> <i>Imagic MSA</i><br/>\n";
						echo "<ul>\n";
					} elseif ($clusterrun['REF|ApSpiderClusteringParamsData|spiderparams']) {
						echo "<b>Type:</b> <i>SPIDER Coran</i><br/>\n";
						echo "<b>Method:</b> <i>".$clusterrun['method']."</i><br/>\n";
						echo "<b>Factor list:</b> <i>".$clusterrun['factor_list']."</i>\n";
						echo "<ul>\n";
					} elseif ($clusterrun['REF|ApKerDenSOMParamsData|kerdenparams']) {
						// KerDen only has one cluster data
						$clusterdata = $clusterdatas[0];
						$clusterid = $clusterdata['clusterid'];
						echo "<b>Type:</b> <i>Xmipp KerDen SOM</i><br/><br/>\n";

						$montagefile = $clusterdata['path']."/"."montage.png";
						echo "<a href='loadimg.php?filename=$montagefile'>\n"
							."<img src='loadimg.php?h=120&filename=$montagefile' height='120'></a><br/>";

						echo "<ul>\n";
						echo "<li><a href='loadimg.php?filename=$montagefile'>View montage of self-organizing map</a>\n";
						$clusteravgfile = $clusterdata['path']."/".$clusterdata['avg_imagicfile'];
						echo "<li><a href='viewstack.php?expId=$expId&clusterId=$clusterid&file=$clusteravgfile'>"
							."View montage as a stack for further processing</a><br/>\n";
						echo "</ul>\n";
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
					echo "</td></tr>\n";
					echo "</table>\n";
					echo "<br/>\n";
				}
			}
		}
	}
	echo "<h4><a href='alignsummary.php?expId=$expId&cluster=1'>Show Composite Page</a></h4>\n";
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

processing_footer();
exit;

?>
