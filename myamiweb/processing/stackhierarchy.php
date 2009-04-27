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

$particle = new particledata();
$expId = $_GET['expId'];
$projectId = (int) getProjectFromExpId($expId);

function showStack($stackdata) {
	global $particle;
	global $expId;
	$stackid = $stackdata['stackid'];
	$allsubstackdatas = $particle->getSubStackIds($expId, $stackid, true);
	$substackdatas = $particle->getSubStackIds($expId, $stackid);
	if ($stackdata['hidden'] != 1 || $_POST['unhideStack'.$stackid] == 'unhide')
		echo stacksummarytable($stackid);
	else
		echo stacksummarytable($stackid, true, true);
	if ($allsubstackdatas) {
		echo "</td></tr><tr><td valign='center'>substack<br/>&ndash;&ndash;&gt;</td><td>";
		echo "<table class='tablebubble'><tr><td colspan='2'>\n";
		foreach ($allsubstackdatas as $substackdata) {
			showStack($substackdata);
		}
		echo "</td></tr></table>\n";
	}
};

//echo "Project ID: ".$projectId." <br/>\n";
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

$javascript.= editTextJava();

processing_header("Hierarchical Stack Summary","Hierarchical Stack Summary Page", $javascript, False);

// --- Get Stack Data --- //

$allstackdatas = $particle->getPrimaryStackIds($expId);

echo "<a href='stacksummary.php?expId=$expId'>[Show original stack summary page]</a><br/><br/>\n";
if ($allstackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	foreach ($allstackdatas as $stackdata) {
		echo "<table class='tablebubble'><tr><td colspan='2'>\n";
		showStack($stackdata);
		echo "</td></tr></table>\n";
	}
	echo "</form>";
} else {
	echo "<B><font size='+1'>Session does not contain any stacks.<br/>Create one here: <a href='runMakeStack2.php?expId=$expId'>make stack</a></font></B>\n";
}

echo "<a href='stacksummary.php?expId=$expId'>[Show original stack summary page]</a><br/><br/>\n";

processing_footer();
exit;

?>
