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
	runDeleteCtf();
}

// Create the form page
else {
	createDeleteCtfForm();
}

function createDeleteCtfForm($extra=false, $title='DumimgsCTF Run', $heading='Delete CTF Run Page') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$ctfId=$_GET['ctfId'];

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&ctfId=$ctfId";

	$javascript = "<script type='text/javascript'>\n";
	$javascript.= "function doubleCheck(imgs) {\n";
	$javascript.= "  return confirm(\"Are you sure you want to delete this CTF run containing \"+imgs+\" values?\");\n";
	$javascript.= "}\n";
	$javascript.= "</script>\n";

	processing_header($title,$heading, $javascript, False);

	if (!$ctfId) {
		echo "<B>No CTF Run Selected for deletion</B>\n";
		processing_footer();
		exit;
	}

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	// --- Get Stack Data --- //
	$particle = new particledata();
	$ctfdata= $particle->getAceParams($ctfId);

	if ($ctfdata['stig']!=1 && $ctfdata!=0) {
		$fields = array('defocus1', 'confidence', 'confidence_d', 'amplitude_contrast');
	}
	else {
		$fields = array('defocus1', 'defocus2', 'confidence', 'angle_astigmatism', 'amplitude_contrast');
	}
	$stats = $particle->getCTFStats($fields, $expId, $ctfId);
	$display_keys = array ( 'nb', 'min', 'max', 'avg', 'stddev');
	
	echo "<font color='#990000' size='+2'>WARNING: This CTF run will be deleted, along with all associated metadata.<br />\n";
	echo "This action cannot be undone!<br /></font>\n";
	echo openRoundBorder();
	echo "<table cellspacing='3'>";
	echo "<tr>";
	echo "<td>\n";
	echo apdivtitle("Ctf Run: ".$ctfrunid." ".$popupstr."<b>".$rName."</b></a>\n");	
	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr bgcolor='#ffffff'>\n";
	echo "<td>Path:&nbsp;<i>".$ctfdata['path']."</i></td>\n";
	echo "</tr>\n";
	echo "<tr><td colspan='10'>\n";
	echo displayCTFstats($stats, $display_keys);
	echo "</td></tr>\n";
	echo "</table>";
	echo closeRoundBorder();

	$numimgs = $stats[$fields[0]][0]['nb'];
	echo "<hr />\n";
	echo "<center>\n";
	echo "<form name='viewerform' method='post' action='$formAction' onSubmit='return doubleCheck(\"$numimgs\")'>\n";
	echo "<input type='submit' name='process' value='Delete $type'>\n";
	echo "</form>\n";
	echo "</center>\n";
	processing_footer();
	exit;
}

function runDeleteCtf() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$ctfId=$_GET['ctfId'];

	/* *******************
	PART 2: Remove CTF run from database 
	******************** */
	$particle = new particledata();
	$ctfdata= $particle->getAceParams($ctfId);
	$deleteInfo = $particle->removeCtfRunById($ctfId);
	
	/* *******************
	PART 3: Show Additional Commands
	******************** */

	processing_header("Delete CTF Run","Delete CTF Run", $javascript, False);
	echo "<h3>Database deletion status:</h3>\n";
	echo $deleteInfo;
	echo "<hr>\n";
	echo "<h1>YOU ARE NOT DONE YET!!</h1>\n";
	echo "<h3>You must now remove the CTF directory manually:</h3>\n";
	echo "rm -rf ".$ctfdata['path'];
	echo "<br>\n";
	processing_footer();	
	exit;

}
?>
