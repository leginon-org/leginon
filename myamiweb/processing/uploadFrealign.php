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
require "inc/summarytables.inc";

$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

/*
******************************************
******************************************
******************************************
*/


if ($_POST['submitjob'])
	submitJob(); // submit job
else
	selectFrealignJob(); // select a prepared frealign job

/*
******************************************
******************************************
******************************************
*/

function selectFrealignJob($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectId = getProjectFromExpId($expId);
	processing_header("Frealign Job Launcher","Frealign Job Launcher", $javafunc);
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	$particle = new particledata();

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	// get prepared frealign jobs
	//$frealignjobs = $particle->getJobIdsFromSession($expId, $jobtype='prepfrealign', $status='D');
	$rawfrealignjobs = $particle->getPreparedFrealignJobs();

	// print jobs with radio button
	if (!$rawfrealignjobs) {
		echo "<font color='#CC3333' size='+2'>No prepared frealign jobs found</font>\n";
		exit;
	} 

	// check if jobs have associated cluster jobs
	$frealignjobs = array();
	foreach ($rawfrealignjobs as $frealignjob) {
		$frealignrun = $particle->getClusterJobByTypeAndPath('runfrealign', $frealignjob['path']);
		if (!$frealignrun)
			$frealignjobs[] = $frealignjob;
	}

	// print jobs with radio button
	if (!$frealignjobs) {
		echo "<font color='#CC3333' size='+2'>No prepared frealign jobs available</font>\n";
		exit;
	} 

	echo "<table class='tableborder' border='1'>\n";
	foreach ($frealignjobs as $frealignjob) {
		echo "<tr><td>\n";
		$id = $frealignjob['DEF_id'];
		echo "<input type='radio' NAME='jobid' value='$id' ";
		echo "><br/>\n";
		echo"Launch<br/>Job\n";

		echo "</td><td>\n";

		echo frealigntable($frealignjob);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='submitprepared' VALUE='Use this prepared job'></FORM>\n";

	processing_footer();
	exit;
};

/*
******************************************
******************************************
******************************************
*/

function frealigntable($data) {
	// initialization
	$table = "";

	$expId = $_GET['expId'];
	$particle = new particledata();

	// start table
	$name = $data['name'];
	$id = $data['DEF_id'];

	$table .= apdivtitle("Frealign Job: <span class='aptitle'>$name</span> (ID: $id) $j\n");
	$display_keys['date time'] = $data['DEF_timestamp'];
	$display_keys['path'] = $data['path'];
	$display_keys['model'] = modelsummarytable($data['REF|ApInitialModelData|model'], true);
	$display_keys['stack'] = stacksummarytable($data['REF|ApStackData|stack'], true);

	$table .= "<table border='0'>\n";
	// show data
	foreach($display_keys as $k=>$v) {
		$table .= formatHtmlRow($k,$v);
	}

	$table .= "</table>\n";
	return $table;
};

/*
******************************************
******************************************
******************************************
*/


?>
