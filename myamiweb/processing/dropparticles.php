<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runDeleteParticles();
}

// Create the form page
else {
	createDeleteParticlesForm();
}

function createDeleteParticlesForm($extra=false, $title='Delete Particles Run', $heading='Delete Particles Run Page') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$partId=$_GET['partId'];

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&partId=$partId";

	$javascript = "<script type='text/javascript'>\n";
	$javascript.= "function doubleCheck(particles) {\n";
	$javascript.= "  return confirm(\"Are you sure you want to delete this Selection run containing \"+particles+\" particle picks?\");\n";
	$javascript.= "}\n";
	$javascript.= "</script>\n";

	processing_header($title,$heading, $javascript, False);

	if (!$partId) {
		echo "<B>No Particle Selection Run Selected for deletion</B>\n";
		processing_footer();
		exit;
	}

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	// --- Get Stack Data --- //
	$particle = new particledata();
	$display_keys = array ( 'preset','totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev');

	echo "<font color='#990000' size='+2'>WARNING: This Particle Selection run will be deleted, along with all associated metadata.<br />\n";
	echo "This action cannot be undone!<br /></font>\n";
	echo openRoundBorder();
	echo "<table cellspacing='3'>";
	echo "<tr>";
	echo "<td>\n";
	echo pickingsummarytable($partId, true, false);
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>";
	echo closeRoundBorder();

	$stats = $particle->getStats($partId);
	$numparts = $stats['totparticles'];
	echo "<hr />\n";
	echo "<center>\n";
	echo "<form name='viewerform' method='post' action='$formAction' onSubmit='return doubleCheck(\"$numparts\")'>\n";
	echo "<input type='submit' name='process' value='Delete $type'>\n";
	echo "</form>\n";
	echo "</center>\n";
	processing_footer();
	exit;
}

function runDeleteParticles() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$partId=$_GET['partId'];

	/* *******************
	PART 2: Remove CTF run from database 
	******************** */
	$particle = new particledata();
	$selectiondata= $particle->getSelectionParams($partId);
	$deleteInfo = $particle->removeSelectionRunById($partId);
	
	/* *******************
	PART 3: Show Additional Commands
	******************** */

	processing_header("Delete Selection Run","Delete Selection Run", $javascript, False);
	echo "<h3>Database deletion status:</h3>\n";
	echo $deleteInfo;
	echo "<hr>\n";
	echo "<h1>YOU ARE NOT DONE YET!!</h1>\n";
	echo "<h3>You must now remove the Particle Selection directory manually:</h3>\n";
	echo "rm -rf ".$selectiondata[0]['path'];
	echo "<br>\n";
	processing_footer();	
	exit;

}
?>
