<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/basicreport.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

try {
    // Create an instance of the BasicReport class to display all the make raw frame stack runs from this session.
    $report = new BasicReport( $expId, "makeddrawframestack", "ApDDStackRunData", True);

    if ($report->hasRunData($expId)) {
        $runDatas =$report->getRunDatas(True);

        // For each run, set the URL for it's report page and display it's summary info.
        foreach ($runDatas as $runData) {
            $runReportPageLink = ''; // Don't have further info yet
            $summaryTable .=  $report->displaySummaryTable($runData, $runReportPageLink, True, True );
        }

    } else {
        $summaryTable = "<font color='#cc3333' size='+2'>No raw frame stack information available</font>\n<hr/>\n";
    }

} catch (Exception $e) {
    $message = $e->getMessage();
    $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
} 

// Display the standard Appion interface header
$javascript.= editTextJava();
processing_header("Raw Frame Stack Creation Results", "Raw Frame Stack Creation Results", $javascript, False);

// Display the table built by the BasicReport class or errors
echo $summaryTable;

// Display the standard Appion interface footer
processing_footer();
?>
