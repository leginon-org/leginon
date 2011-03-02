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
require_once "inc/project.inc";
require_once "inc/processing.inc";
require "inc/summarytables.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runDeleteStack();
}

// Create the form page
else {
	createDeleteStackForm();
}

function createDeleteStackForm($extra=false, $title='Delete Stack', $heading='Delete Stack Page') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$stackid=$_GET['sId'];

	$javascript = "<script type='text/javascript'>\n";
	$javascript.= "function doubleCheck(parts) {\n";
	$javascript.= "  return confirm(\"Are you sure you want to delete this stack of \"+parts+\" particles?\");\n";
	$javascript.= "}\n";
	$javascript.= "</script>\n";

	processing_header($title,$heading, $javascript, False);

	if (!$stackid) {
		echo "<B>No Stack Selected for deletion</B>\n";
		processing_footer();
		exit;
	}

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&sId=$stackid";

	// --- Get Stack Data --- //
	$particle = new particledata();

	echo "<font color='#990000' size='+2'>WARNING: This stack will be deleted, along with all associated metadata.<br />\n";
	echo "This action cannot be undone!<br /></font>\n";
	echo stacksummarytable($stackid, $mini=False,$tiny=False,$showOptions=False);
	$numpart = $particle->getNumStackParticles($stackid);
	$numpart = commafy($numpart);
	echo "<hr />\n";
	echo "<center>\n";
	echo "<form name='viewerform' method='post' action='$formAction' onSubmit='return doubleCheck(\"$numpart\")'>\n";
	echo "<input type='submit' name='process' value='Delete Stack'>\n";
	echo "</form>\n";
	echo "</center>\n";
	processing_footer();
	exit;
}

function runDeleteStack() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$stackid=$_GET['sId'];

	/* *******************
	PART 2: Get stack info, then remove it from database 
	******************** */
	$particle = new particledata();
	$stackdata = $particle->getStackParams($stackid);
	$deleteInfo = $particle->removeStackById($stackid);
	
	/* *******************
	PART 3: Show Additional Commands
	******************** */

	processing_header("Delete Stack","Delete Stack Page", $javascript, False);
	echo "<h3>Database deletion status:</h3>\n";
	echo $deleteInfo;
	echo "<hr>\n";
	echo "<h1>YOU ARE NOT DONE YET!!</h1>\n";
	echo "<h3>You must now remove the stack directory manually:</h3>\n";
	echo "rm -rf ".$stackdata['path'];
	echo "<br>\n";
	processing_footer();	
	exit;

}
?>
