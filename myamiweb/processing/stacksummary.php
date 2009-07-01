<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */
$expId = $_GET['expId'];

require "inc/particledata.inc";
require "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require "inc/summarytables.inc";
  
$projectId = (int) getProjectFromExpId($expId);
//echo "Project ID: ".$projectId." <br/>\n";
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";
if ($_GET['syntheticOnly']) $formAction.="&syntheticOnly=True";

$javascript.= editTextJava();

processing_header("Stack Report","Stack Summary Page", $javascript, False);

// --- Get Stack Data --- //
$particle = new particledata();

if ($_GET['syntheticOnly']) {
	if (!$_GET['showHidden']) {
		$stackdatas = $particle->getStackIds($expId, False, True);
		$hidestackdatas = $particle->getStackIds($expId, True, True);
	}
	else {
		$stackdatas = $particle->getStackIds($expId, True, True);
		$hidestackdatas = $stackdatas;
	}
}
else {
	if (!$_GET['showHidden']) {
		$stackdatas = $particle->getStackIds($expId, False, False);
		$hidestackdatas = $particle->getStackIds($expId, True, False);
	}
	else {
		$stackdatas = $particle->getStackIds($expId, True, False);
		$hidestackdatas = $stackdatas;
	}
}
	
if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden stacks]</a><br/><br/>\n";
}

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	foreach ($stackdatas as $stackdata) {
		$stackid = $stackdata['stackid'];
		echo stacksummarytable($stackid);
	}
	echo "</form>";
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
