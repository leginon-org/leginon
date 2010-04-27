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

processing_header("Class Average List","Class Average List", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each template stack entry in database
$tsdatas = $particle->getTemplateStacksFromSession($expId, False, "cls_avgs");
	
// find each stack entry in database
$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);

if ($tsdatas || $stackdatas) echo "<form name='stackform' method='post' action='$formAction'>\n";

// information table

echo "<table border='1' class='tableborder' width='640'>";
	echo "<tr><td width='100' align='center'>\n";
	echo "  <h3>Angular Reconstitution</h3>";
	echo " <b> Angular reconstitution is a method for determining the euler angles of input 2-D images and "
		."is generally only used with class averages whose signal-to-noise ratio is high. "
		."The 3d0 model generator at hand will perform this euler search on an input stack of class averages, "
		."followed by a 3-D reconstruction & automasking procedure. It is advised to either (1) select "
		."the best class averages to create a \"template stack\" for 3d0 generation or (2) proceed directly "
		."with any of the class averages coming from the Alignment and Classification pipeline. </b>"
		."<br/><br/>";
	echo "</td></tr>";
echo "</table>";


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
else echo "<br><br><B>Session does not contain any template stacks.</B>\n";		
	
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
else echo "<br><br><B>Session does not contain any aligned stacks.</B>\n";

processing_footer();
exit;

?>
