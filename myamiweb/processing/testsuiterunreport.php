<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
// This file should display a summary of each of the jobs that were run during a single test suite run.
// Each job summary should include a link to display a detailed summary page of the job.
//
// Information on writing appion tests is available at:
// http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Testing
//--------------------------------------------------------------------------------------

require_once "inc/basicreport.inc";
require_once "inc/particledata.inc";

$expId = $_GET['expId'];
$runId = $_GET['rId'];

$particle = new particledata();

try {
	// Create an instance of the BasicReport class and set the test suite database table name
	$testSuiteReport = new BasicReport( $expId, "testsuite", "ApTestRunData");
	
	// Get the run data for the specific test run we are reporting on
	$runData = $testSuiteReport->getRunData($runId);
	
	// Use the append_timestamp field of the testsuite run to find the jobs that it started. 
	// The job names all have this common timestamp appented to the program name and it is unique to each testsuite run.
	// The ScriptProgramRun database table holds run data including the 'runname' of every job started for this session.
	$runDatas = $testSuiteReport->getAllEntriesLike("ScriptProgramRun", "runname", $runData['append_timestamp'] );
	
	// Display a summary report of each job. The getAppionJobData() function returns the job data found in the
	// ApAppionJobData DB table corresponding to the given entry in the ScriptProgramRun table.
	foreach ($runDatas as $runData) {
		$jobData = $testSuiteReport->getAppionJobData("ScriptProgramRun", $runData['DEF_id']);
		$jobRunId = $particle->getJobRunIdFromRunname( $jobData['name'] );
		$jobReportPageLink = buildJobReportPageLink( $jobData['jobtype'], $expId, $jobRunId );
		
		$summaryTable .= $testSuiteReport->displaySummaryTable($jobData, $jobReportPageLink, False);
	}

} catch (Exception $e) {
	$message = $e->getMessage();
    $summaryTable = "<font color='#cc3333' size='+2'>Error creating report page: $message </font>\n";
} 

// Display the standard Appion interface header
processing_header("Test Suite Run Report","Test Suite Run Report for $runData[name]");
// Display the table built by the BasicReport class or errors
echo $summaryTable;
// Display the standard Appion interface footer
processing_footer();

// This function would need to be updated if a new jobtype is added to the test scripts
// TODO: figure out what the report page is for all the jobtypes. Add this to DB?
function buildJobReportPageLink( $jobtype, $expId, $jobRunId ) {
	
	$jobReportUrls=array(
		'stackId'=>"stackreport.php?expId=$expId&sId=$jobRunId"
		,'stackfilter'=>"stackreport.php?expId=$expId&sId=$jobRunId"
		,'substack'=>"stackreport.php?expId=$expId&sId=$jobRunId"
		,'makestack2'=>"stackreport.php?expId=$expId&sId=$jobRunId"
		,'particleSelection'=>"particlerunreport.php?expId=$expId&rId=$jobRunId"
		,'objectTracing'=>"particlerunreport.php?expId=$expId&rId=$jobRunId"
		,'templatecorrelator'=>"particlerunreport.php?expId=$expId&rId=$jobRunId"
		,'aligner'=>"tomoalignercyclereport.php?expId=$expId&aId=$jobRunId"
		,'sizingreport'=>"sizingreport.php?expId=$expId&sizingId=$jobRunId"
		,'dogpicker'=>"particlerunreport.php?expId=$expId&rId=$jobRunId"
		,'pyace'=>"ctfreport.php?expId=$expId"
		,'pyace2'=>"ctfreport.php?expId=$expId"
		,'ctfestimate'=>"ctfreport.php?expId=$expId"
		,'testsuite'=>"testsuiterunreport.php?expId=$expId&rId=$jobRunId"
		,'partalign'=>"alignlist.php?expId=$expId"
		,'maxlikealignment'=>"alignlist.php?expId=$expId"
		,'alignanalysis'=>"ctfreport.php?expId=$expId"
		,'tomomaker'=>"ctfreport.php?expId=$expId"
		,'uploadtomo'=>"ctfreport.php?expId=$expId"
		,'imageloader'=>"ctfreport.php?expId=$expId"
		,'uploadtemplate'=>"ctfreport.php?expId=$expId"
		,'manualpicker'=>"ctfreport.php?expId=$expId"
		,'tomotableupdate'=>"ctfreport.php?expId=$expId"
		,'emanrecon'=>"ctfreport.php?expId=$expId"
		,'uploadrecon'=>"ctfreport.php?expId=$expId"
		,'manualmask'=>"ctfreport.php?expId=$expId"
		,'spidernorefalign'=>"ctfreport.php?expId=$expId"
		,'partcluster'=>"ctfreport.php?expId=$expId"
		,'postproc'=>"ctfreport.php?expId=$expId"
		,'aligndefocalpairs'=>"ctfreport.php?expId=$expId"
		,'tiltaligner'=>"ctfreport.php?expId=$expId"
		,'uploadrecon'=>"ctfreport.php?expId=$expId"
		,'modelfromemdb'=>"ctfreport.php?expId=$expId"
		,'createtestsession'=>"ctfreport.php?expId=$expId"
	);	
	
	$jobReportUrl = $jobReportUrls[$jobtype];
	return $jobReportUrl;
}

?>
