<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

jobForm();

function jobForm($extra=false) {
	$expId = $_GET['expId'];
	processing_header("Eman Job Generator","EMAN Job Generator",$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
	echo "<form name='imagicjob' method='post' action='$formaction'><br />\n";
	echo "</form>\n";
	processing_footer();
	exit;
}

