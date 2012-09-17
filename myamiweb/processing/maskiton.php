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
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

if ($_POST) {
	createMaskitonForm();
} else {
	createSelectStackForm();
}

function createMaskitonForm($extra=false, $title='Maskiton Launcher', $heading='Masks with Maskiton') {
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
	$stackval 	= $_POST['stackval'];

	processing_header($title,$heading,$javascript, $pleaseWait=false, $showmenu=true, $printDiv=false, 
						$guideURL="http://ami.scripps.edu/redmine/projects/appion/wiki/");
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	echo "<Iframe src='http://maskiton.scripps.edu/masking.html?projectid=$projectId&stackid=$stackval' width='800' height='800'></Iframe><br /><br />\n";

	processing_footer();
}


function createSelectStackForm($extra=false, $title='Appion: Select Maskiton Stack', $heading='Select Maskiton Stack') 
{
	// check if coming directly from a session
   $expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
		
	$particle = new particledata();
	
	// find each stack entry in database
	$stackIds = $particle->getStackIds($expId);
	
	// remove stacks with no particles
	$filteredStackIds = array();
	foreach ($stackIds as $stackId) {
		$numpart = $particle->getNumStackParticles($stackId['stackid']);
		if ($numpart != 0) { 
			$filteredStackIds[] = $stackId['stackid'];
		}
	}

	processing_header($title,$heading,$javafunc);

	echo "<form name='maskiton' method='POST' ACTION='$formAction'>";
	echo "<b>Select a stack:</b><br>";
	echo "<P><input type='SUBMIT' NAME='submitstack' VALUE='Use selected stack'>";

	echo "<br /><br />";
 
	echo "<table class='tableborder' border='1'>\n";
	foreach ($filteredStackIds as $stackId) {
		echo "<tr><td>\n";
		echo "<input type='radio' NAME='stackval' value='$stackId' ";		
		echo ">\n";
		echo "Use<br/>Stack\n";

		echo "</td><td>\n";	
		echo stacksummarytable( $stackId, True, False, False );
		echo "</td></tr>\n";
	}
	echo "</table>\n\n";	

	echo "<P><input type='SUBMIT' NAME='submitstack' VALUE='Use selected stack'>";
	echo "</form>";

	echo showReference( "appion" );
	processing_footer();
}


?>
