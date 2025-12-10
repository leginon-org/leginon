basicReport.inc is a class that can be used to quickly display run information as well as parameters and results. It creates html tables by reading database tables.
The only input it needs is the expId, jobtype and a database table name. BasicReport is used for reporting results from [automated testing](/appion/Developers_guide/Appion_Testing).

This is a sample file using the class to display a list of all the makestack runs that have occured for the session:

    <?php
    require_once "inc/basicreport.inc";

    $expId = $_GET['expId'];

    try {
            // Create an instance of the BasicReport class to display all the makestack runs from this session.
        $testSuiteReport = new BasicReport( $expId, "makestack2", "ApStackRunData");

        if ($testSuiteReport->hasRunData()) {
            $runDatas =$testSuiteReport->getRunDatas(True);

            // For each testsuite run, set the URL for it's report page and display it's summary info.
            foreach ($runDatas as $runData) {
                $runReportPageLink = 'testsuiterunreport.php?expId='.$expId.'&rId='.$runData['DEF_id'];
                $summaryTable .=  $testSuiteReport->displaySummaryTable($runData, $runReportPageLink);
            }

        } else {
            $summaryTable = "<font color='#cc3333' size='+2'>No Test Run information available</font>\n<hr/>\n";
        }

    } catch (Exception $e) {
        $message = $e->getMessage();
        $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
    } 

    // Display the standard Appion interface header
    processing_header("Test Suite Results", "Test Suite Results", $javascript, False);

    // Display the table built by the BasicReport class or errors
    echo $summaryTable;

    // Display the standard Appion interface footer
    processing_footer();
    ?>

Here is a sample file using the class to display all the information from a single makestack run:

    <?php

    require_once "inc/basicreport.inc";

    $expId = $_GET['expId'];
    $runId = $_GET['rId'];

    try {
        // Create an instance of the BasicReport class using the makeStack jobtype and DB table
        $testSuiteReport = new BasicReport( $expId, "makestack2", "ApStackRunData");

        // Get the run data for the specific test run we are reporting on
        $runData =$testSuiteReport->getRunData($runId);

        // The jobReportLink provides a link to another page for further information. 
        // If there is no more data to display, this should link back to the current page.
        // If the 3rd param to displaySummaryTable() is True, sub tables will be parsed and displayed.
        $jobReportLink = 'testsuiterunreport.php?expId='.$expId.'&rId='.$runData['DEF_id'];
        $summaryTable =  $testSuiteReport->displaySummaryTable($runData, $jobReportLink, True);

    } catch (Exception $e) {
        $message = $e->getMessage();
        $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
    } 

    // Display the standard Appion interface header
    processing_header("MakeStack Run Report","MakeStack Run Report for $runData[stackRunName]");

    // Display the table built by the BasicReport class or errors
    echo $summaryTable;

    // Display the standard Appion interface footer
    processing_footer();

    ?>
