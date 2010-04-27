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
$projectId = getProjectId();
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
				echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
				echo "<tr><td>\n";
				echo clustersummarytable($clusterrunid, true);
				echo "</td></tr>\n";
				echo "</table>\n";
				echo "<br/>\n";
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
