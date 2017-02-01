<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/basicreport.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

try {
    // Create an instance of the BasicReport class to display all the completed particle polishing runs from this session.
    $report = new BasicReport( $expId, "particlepolishing", "ApAppionJobData", True);

    if ($report->hasRunData($expId)) {
        $runDatas =$report->getRunDatas(True);

        // For each run, set the URL for its report page and display it's summary info.
        foreach ($runDatas as $runData) {
            $runReportPageLink = ''; // Don't have further info yet
	    if($runData['jobtype']==='particlepolishing' &&  ($runData['status']==='D'))
		{
		
            $summaryTable .=  $report->displaySummaryTable($runData, $runReportPageLink, True, True );
        	}
	}

    } else {
        $summaryTable = "<font color='#cc3333' size='+2'>No particle polishing information available</font>\n<hr/>\n";
    }

} catch (Exception $e) {
    $message = $e->getMessage();
    $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
} 

// Display the standard Appion interface header
$javascript.= editTextJava();
processing_header("Raw Frame Stack Creation Results", "Particle Polishing Results", $javascript, False);

// Display the table built by the BasicReport class or errors
echo $summaryTable;

// Display the standard Appion interface footer
processing_footer();
?>
