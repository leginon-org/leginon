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

processing_header("Aligned Stack Report","Aligned Stack Summary Page", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	echo "<h3><a href='alignsummary.php?expId=$expId'>Show Composite Page</a></h3>\n";
	foreach ($stackdatas as $stackdata) {
		$alignstackid = $stackdata['alignstackid'];
		$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, $projectId, False);
		if ($clusterruns) {
			foreach ($clusterruns as $clusterrun) {
				$clusterrunid = $clusterrun['clusterrunid'];
				$clusterdatas = $particle->getClusteringStacksForClusteringRun($clusterrunid, false);
				if ($clusterdatas) {
					echo openRoundBorder();
					echo "<table cellspacing='8' cellpading='5' border='0'>\n";
					echo "<tr><td>\n";
					if ($clusterrun['REF|ApImagicAlignAnalysisData|imagicMSArun']) {
						echo "<b>Cluster Run ".$clusterrunid."</b>"
							.", <br/>method='<i> Hierarchical Clustering (IMAGIC)"
							."</i>', <br/>factor list='<i>69 Eigen Images, (eigenimages.img)</i>'\n";
						echo "<ul>\n";
					} elseif ($clusterrun['REF|ApSpiderClusteringParamsData|spiderparams']) {
						echo "<b>Cluster Run ".$clusterrunid."</b>"
							.", <br/>method='<i>".$clusterrun['method']." (SPIDER) "
							."</i>', <br/>factor list='<i>".$clusterrun['factor_list']."</i>'\n";
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
					echo "</td></tr>\n";
					echo "</table>\n";
					echo closeRoundBorder();
					echo "<br/>\n";
				}
			}
		}
	}
	echo "<h3><a href='alignsummary.php?expId=$expId'>Show Composite Page</a></h3>\n";
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

processing_footer();
exit;

?>
