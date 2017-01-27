<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

// Currently, maskiton cannot connect to our DB, so skip selecting a stack in the gui, the user will need to upload it to the maskiton server.
if (True /*$_POST*/) {
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
						$guideURL="http://emg.nysbc.org/redmine/projects/appion/wiki/Maskiton");
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	// This stopped working. Users need to upload a stack to the maskiton server to work with it.
	//echo "<Iframe src='http://maskiton.nysbc.org/masking.html?projectid=$projectId&stackid=$stackval' width='800' height='800'></Iframe><br /><br />\n";
	echo "<Iframe src='http://maskiton.nysbc.org/' width='800' height='800'></Iframe><br /><br />\n";
	
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
