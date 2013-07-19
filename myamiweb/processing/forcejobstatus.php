<?php
require_once "inc/particledata.inc";
require_once "inc/util.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

if ($_POST['confirm'] == 'Force Status to Done') {
	doForceStatus();
} else {
	confirmForceStatus();
}


function confirmForceStatus() {
	$expId = $_GET['expId'];
	$jobid = $_GET['jobId'];
	$projectId = getProjectId();

	processing_header("Confirm Force Status", "Confirm Force Status", '');
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobid";

	// make sure we are logged in
	$user = $_SESSION['username'];
	if (!$user || is_null($user)) {
		echo "<font color='#cc3333' size='+2'>You cannot change job status if you are not logged in.</font>\n";
		exit;
	}

	$particle = new particledata();
	// find if job has been uploaded
	if ($particle->getReconIdFromAppionJobId($jobid)) {
		echo "<font color='#cc3333' size='+2'>Status Update Failed: This job has already been uploaded.</font>\n";
		exit;
	}

	echo "<form name='jobform' method='post' action='$formAction'>\n";

	$jobdata = $particle->getJobInfoFromId($jobid);
	echo displayJobInfo($jobdata);
		
	if ($jobdata['status'] == 'D') {
		echo "<font color='#cc3333' size='+2'>Job is already set to Done.</font>\n";
	} else {
		echo "<input type='submit' name='confirm' value='Force Status to Done'>\n";
		echo "<input type='button' value='Cancel' onClick='history.back()'>\n";
	}
	echo "</form><br/>\n";

	processing_footer();
};

function doForceStatus() {
	$expId = $_GET['expId'];
	$jobid = $_GET['jobId'];
	$projectId = getProjectId();

	processing_header("Force Job $jobid to Done", "Force Job $jobid to Done", '');
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobid";

	$user = $_SESSION['username'];
	if (!$user || is_null($user)) {
		echo "<font color='#cc3333' size='+2'>You cannot modify job status unless you are logged in</font>\n";
		exit;
	}

	$particle = new particledata();
	// find if job has been uploaded
	if ($particle->getReconIdFromAppionJobId($jobid)) {
		echo "<font color='#cc3333' size='+2'>Status Update Failed: This job has already been uploadedd</font>\n";
		exit;
	}

	$particle->updateClusterJobStatus($jobid, "D");

	echo "<font color='#cc3333' size='+2'>Updated status of Job Id $jobid to Done.</font><br/><br/>\n";

	$jobdata = $particle->getJobInfoFromId($jobid);
	echo displayJobInfo($jobdata);

	// Abort multiple attempts of the same job
	$aborted_similar_jobids = $particle->abortSimilarJobs($expId,$jobdata['name'],$jobdata['jobtype']);
	if (count($aborted_similar_jobids)) echo formatHtmlRow('____________','___');
	foreach($aborted_similar_jobids as $aborted_jobid) {
		echo formatHtmlRow('Abort attempt of the same job in jobid',$aborted_jobid);
	}

	processing_footer();
};

function displayJobInfo($jobdata)
{
	$jobid = $_GET['jobId'];
	
	// Display job info
	$display_keys['name'] = $jobdata['name'];
	$display_keys['appion path'] = $jobdata['appath'];
	$display_keys['cluster path'] = $jobdata['clusterpath'];
	$display_keys['cluster'] = $jobdata['cluster'];
	$display_keys['status'] = $jobdata['status'];
	$html = apdivtitle("Job: <font class='aptitle'>$jobdata[name]</font> (ID: <font class='aptitle'>$jobid</font>)");
	$html .= "<table border='0' >\n";
	foreach($display_keys as $k=>$v) {
		$html .= formatHtmlRow($k,$v);
	}
	$html .= "</table>\n";
	
	return $html;
};

?>
