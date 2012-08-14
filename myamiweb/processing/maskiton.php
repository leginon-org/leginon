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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
 
createForm();

function createForm($extra=false, $title='Maskiton Launcher', $heading='Masks with Maskiton') {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ( $expId ) {
		$sessionId	= $expId;
		$formAction	= $_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId 	= $_POST['sessionId'];
		$formAction = $_SERVER['PHP_SELF'];	
	}
	$projectId = getProjectId();

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo "<Iframe src='http://ami.scripps.edu/group/forum/index.php?view=1' width='600' height='600'></Iframe><br /><br />\n";

	processing_footer();
}


?>
