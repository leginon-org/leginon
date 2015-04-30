<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
// This file should display a list of each testsuite run for this session.
//
// Information on writing appion tests is available at:
// http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Testing
//--------------------------------------------------------------------------------------

require_once "inc/basicreport.inc";

$expId = $_GET['expId'];

try {
	// Create an instance of the BasicReport class to display all the testsuite runs from this session.
	// The testsuite run data is stored in the ApTestRunData table. 
	$testSuiteReport = new BasicReport( $expId, "testsuite", "ApTestRunData");
	
	if ($testSuiteReport->hasRunData()) {
		$runDatas = $testSuiteReport->getRunDatas(True);
		
		// For each testsuite run, set the URL for it's report page and display it's summary info.
		foreach ($runDatas as $runData) {
			$runReportPageLink = 'testsuiterunreport.php?expId='.$expId.'&rId='.$runData['DEF_id'];
			$summaryTable .= $testSuiteReport->displaySummaryTable($runData, $runReportPageLink);
		}
			
	} else {
		$summaryTable = "<font color='#cc3333' size='+2'>No Test Run information available</font>\n<hr/>\n";
	}

} catch (Exception $e) {
	$message = $e->getMessage();
    $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
} 

// Display the standard Appion interface header
processing_header("Test Suite Results", "Test Suite Results");

// Display the table built by the BasicReport class or errors
echo $summaryTable;

// Display the standard Appion interface footer
processing_footer();
?>
