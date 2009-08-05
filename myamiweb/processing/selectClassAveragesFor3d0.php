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

processing_header("Class Average List","Class Average List", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each template stack entry in database
$tsdatas = $particle->getTemplateStacksFromSession($expId, False, "cls_avgs");
	
// find each stack entry in database
$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);

if ($tsdatas || $stackdatas) echo "<form name='stackform' method='post' action='$formAction'>\n";

if ($tsdatas) {
	echo "<h2>Template Stack List</h2>\n";
	foreach ($tsdatas as $tsdata) {
		echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
		echo "<tr><td>\n";
		echo templateStackEntry($tsdata, False, $mini=True);
		echo "</td></tr>\n";
		echo "</table>\n";
		echo "<br/>\n";
	}
}		
	
if ($stackdatas) {
	echo "<h2>Cluster Stack List</h2>\n";
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
}

if ($tsdatas || $stackdatas) echo "</form>\n";
else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

processing_footer();
exit;

?>
