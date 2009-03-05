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
if ($_GET['showHidden'])
	$formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Aligned Stack List","Aligned Stack List", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
if (!$_GET['showHidden']) {
	$stackdatas = $particle->getAlignStackIds($expId, False);
	$hidestackdatas = $particle->getAlignStackIds($expId, True);
} else {
	$stackdatas = $particle->getAlignStackIds($expId, True);
	$hidestackdatas = $stackdatas;
}

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	echo "<h2>Alignment Stack List</h2>\n";
	echo "<h4><a href='alignsummary.php?expId=$expId'>Show Composite Page</a></h4>\n";
	//echo print_r($stackdatas)."<br/>\n";
	foreach ($stackdatas as $stackdata) {
		echo "<table cellspacing='8' cellpading='5' class='tablebubble' border='0'>\n";
		$alignstackid = $stackdata['alignstackid'];
		echo "<tr><td>\n";
		echo alignstacksummarytable($alignstackid, true);
		$analysisdatas = $particle->getAnalysisRunForAlignStack($alignstackid, $projectId, true);
		if ($analysisdatas) {
			echo count($analysisdatas)." feature analysis runs completed on this align run, "
				."<a href='analysislist.php?expId=$expId'>view feature analysis runs</a><br/><br/>\n";
			echo "<a class='btp1' href='selectFeatureAnalysis.php?expId=$expId&alignId=$alignstackid'>"
				."Run Another Feature Analysis On Align Stack Id $alignstackid</a><br/>\n";
		} else {
			echo "<a class='btp1' href='selectFeatureAnalysis.php?expId=$expId&alignId=$alignstackid'>"
				."Run Feature Analysis On Align Stack Id $alignstackid</a><br/>\n";
		}
		$clusterruns = $particle->getClusteringRunsForAlignStack($alignstackid, false);
		if ($clusterruns) {
			echo "<br/>".count($clusterruns)." cluster runs completed on this feature analysis run, "
				."<a href='clusterlist.php?expId=$expId'>view particle clusters</a>\n";
		}
		echo "</td></tr>\n";
		echo "</table>\n";
		echo "<br/>\n";
	}
	echo "<h4><a href='alignsummary.php?expId=$expId'>Show Composite Page</a></h4>\n";
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
