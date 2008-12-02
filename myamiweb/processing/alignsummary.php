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
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript.= editTextJava();

processing_header("Aligned Stack Report","Aligned Stack Summary Page", $javascript, True);

// --- Get Stack Data --- //
$particle = new particledata();

// find each stack entry in database
//$stackIds = $particle->getAlignStackIds($expId, True);
if (!$_GET['showHidden']) {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, False);
	$hidestackdatas = $particle->getAlignStackIds($expId, $projectId, True);
} else {
	$stackdatas = $particle->getAlignStackIds($expId, $projectId, True);
	print_r($stackdatas);
	$hidestackdatas = $stackdatas;
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden aligned stacks]</a><br/><br/>\n";
}

if ($stackdatas) {
	echo "<form name='stackform' method='post' action='$formAction'>\n";
	//echo print_r($stackdatas)."<br/>\n";
	foreach ($stackdatas as $stackdata) {
		$alignstackid = $stackdata['alignstackid'];
		echo alignstacksummarytable($alignstackid);
		echo "<a href='runCoranClassify.php?expId=6143&alignId=$alignstackid'>Run Coran On Align Stack Id $alignstackid</a><br/>\n";
	}
	echo "</form>\n";
} else {
	echo "<B>Session does not contain any aligned stacks.</B>\n";
}

if (count($stackdatas) != count($hidestackdatas) && !$_GET['showHidden']) {
	$numhidden = count($hidestackdatas) - count($stackdatas);
	echo "<br/><a href='".$formAction."&showHidden=True'>[Show ".$numhidden." hidden stacks]</a><br/>\n";
}

processing_footer();
exit;

?>
