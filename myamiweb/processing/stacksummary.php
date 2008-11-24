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
echo "Project ID: ".$projectId." <br/>\n";
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Aligned Stack Report","Aligned Stack Summary Page", $javascript, False);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
//$stackIds = $particle->getAlignStackIds($expId, True);
if (!$_GET['showHidden']) {
	$stackdatas = $particle->getStackIdsWithProjectId($expId, $projectId, False);
	$hidestackdatas = $particle->getStackIdsWithProjectId($expId, $projectId, True);
} else {
	$stackdatas = $particle->getStackIdsWithProjectId($expId, $projectId, True);
	$hidestackdatas = $stackdatas;
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden stacks]</a><br/><br/>\n";
}

if ($stackdatas) {
	foreach ($stackdatas as $stackdata) {
		$stackid = $stackdata['stackid'];
		echo stacksummarytable($stackid);
	}
} else {
	echo "<B>Session does not contain any stacks.</B>\n";
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<br/><a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden stacks]</a><br/>\n";
}

processing_footer();
exit;

?>
