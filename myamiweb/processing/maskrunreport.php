<?php
require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/basicreport.inc";

$expId= $_GET['expId'];
$runId = $_GET['rId'];
$particle = new particledata();


try {
	// Create an instance of the BasicReport class and set the test suite database table name
	$testSuiteReport = new BasicReport( $expId, "maskmaker ", "ApMaskMakerRunData");
	
	// Get the run data for the specific test run we are reporting on
	$runData = $testSuiteReport->getRunData($runId);		
	$summaryTable .= $testSuiteReport->displaySummaryTable($runData, "multiimgassessor.php?expId=$expId&maskId=$runId", True, False);

} catch (Exception $e) {
	$message = $e->getMessage();
    $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
} 

// Display the standard Appion interface header
processing_header('Mask Maker Run Report',"Mask Maker Run Report for $runData[name]");
// Display the table built by the BasicReport class or errors
echo $summaryTable;
// Display the standard Appion interface footer
processing_footer();

?>
