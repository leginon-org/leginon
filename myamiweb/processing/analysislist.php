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

processing_header("Feature Analysis List","Feature Analysis List", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
$stackdatas = $particle->getAlignStackIdsWithAnalysis($expId, $projectId);

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	echo "<h2>Feature Analysis List</h2>\n";
	echo "<h4><a href='alignsummary.php?expId=$expId&analysis=1'>Show Composite Page</a></h4>\n";
	foreach ($stackdatas as $stackdata) {
		$alignstackid = $stackdata['alignstackid'];
		$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, False);
		foreach ($analysisdatas as $analysisdata) {
			$analysisid = $analysisdata['analysisid'];
			echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
			echo "<tr><td>\n";
			echo analysissummarytable($analysisid, false);
			$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, false);
			$another='';
			if ($clusterruns) {
				echo count($clusterruns)." cluster runs completed on this feature analysis run, "
					."<a href='clusterlist.php?expId=$expId'>view particle clusters</a><br/><br/>\n";
				$another="Another";
			}
			if ($analysisdata['REF|ApCoranRunData|coranrun'] != false) {
				echo "<a class='btp1' href='runClusterCoran.php?expId=$expId"
					."&analysisId=$analysisid&alignId=$alignstackid'>"
					."Run $another Particle Clustering On Analysis Id $analysisid</a><br/>\n";
			} elseif ($analysisdata['REF|ApImagicAlignAnalysisData|imagicMSArun'] != false) {
				echo "<a class='btp1' href='imagicMSAcluster.php?expId=$expId"
					."&analysisId=$analysisid&alignId=$alignstackid'>"
					."Run $another Particle Clustering On Analysis Id $analysisid</a>&nbsp;<br/>\n";
			} 
			echo "</td></tr>\n";
			echo "</table>\n";
			echo "<br/>\n";
		}
	}
	echo "<h4><a href='alignsummary.php?expId=$expId&analysis=1'>Show Composite Page</a></h4>\n";
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

processing_footer();
exit;

?>
