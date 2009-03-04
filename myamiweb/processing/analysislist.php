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
		$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, False);
		foreach ($analysisdatas as $analysisdata) {
			$analysisid = $analysisdata['analysisid'];
			echo openRoundBorder();
			echo "<table cellspacing='8' cellpading='5' border='0'>\n";
			echo "<tr><td>\n";
			echo analysissummarytable($analysisid, true);
			if ($analysisdata['REF|ApCoranRunData|coranrun'] != false) {
				echo "<a class='btp1blue' href='runClusterCoran.php?expId=$expId"
					."&analysisId=$analysisid&alignId=$alignstackid'>"
					."Run Another Particle Clustering On Analysis Id $analysisid</a><br/>\n";
			} elseif ($analysisdata['REF|ApImagicAlignAnalysisData|imagicMSArun'] != false) {
				echo "<a class='btp1blue' href='imagicMSAcluster.php?expId=$expId"
					."&analysisId=$analysisid&alignId=$alignstackid'>"
					."Run Another Particle Clustering On Analysis Id $analysisid</a>&nbsp;<br/>\n";
			} else {
				echo "<a href='clusterlist.php?expId=$expId'>See clustering page for more information</a>\n";
			}
			echo "</td></tr>\n";
			echo "</table>\n";
			echo closeRoundBorder();
			echo "<br/>\n";
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
