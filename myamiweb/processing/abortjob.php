<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

if ($_POST['confirm'] == 'Abort Job') {
	doAbortJob();
} else {
	confirmAbortJob();
}


function confirmAbortJob() {
	$expId = $_GET['expId'];
	$jobid = $_GET['jobId'];
	$projectId = getProjectId();

	processing_header("Confirm Abort Job", "Confirm Abort Job", '');
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobid";

	// make sure we are logged in
	$user = $_SESSION['username'];
	if (!$user || is_null($user)) {
		echo "<font color='#cc3333' size='+2'>You cannot abort jobs unless you are logged in</font>\n";
		exit;
	}

	$particle = new particledata();
	// find if job has been uploaded
	if ($particle->getReconIdFromAppionJobId($jobid)) {
		echo "<font color='#cc3333' size='+2'>You cannot abort recon jobs that are uploaded</font>\n";
		exit;
	}

	echo "<form name='jobform' method='post' action='$formAction'>\n";

	// Display job info
	$jobdata = $particle->getJobInfoFromId($jobid);
	$display_keys['name'] = $jobdata['name'];
	$display_keys['appion path'] = $jobdata['appath'];
	$display_keys['dmf path'] = $jobdata['dmfpath'];
	$display_keys['cluster path'] = $jobdata['clusterpath'];
	$display_keys['cluster'] = $jobdata['cluster'];
	$display_keys['status'] = $jobdata['status'];
	echo apdivtitle("Job: <font class='aptitle'>$jobdata[name]</font> (ID: <font class='aptitle'>$jobid</font>)");
	echo "<table border='0' >\n";
	foreach($display_keys as $k=>$v) {
		echo formatHtmlRow($k,$v);
	}
	echo "</table>\n";

	if ($jobdata['status'] == 'A') {
		echo "<font color='#cc3333' size='+2'>Job is already aborted</font>\n";
	} else {
		echo "<input type='submit' name='confirm' value='Abort Job'>\n";
		echo "<input type='button' value='Cancel' onClick='history.back()'>\n";
	}
	echo "</form><br/>\n";

	processing_footer();
};

function doAbortJob() {
	$expId = $_GET['expId'];
	$jobid = $_GET['jobId'];
	$projectId = getProjectId();

	processing_header("Aborted Job $jobid", "Aborted Job $jobid", '');
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobid";

	$user = $_SESSION['username'];
	if (!$user || is_null($user)) {
		echo "<font color='#cc3333' size='+2'>You cannot abort jobs unless you are logged in</font>\n";
		exit;
	}

	$particle = new particledata();
	// find if job has been uploaded
	if ($particle->getReconIdFromAppionJobId($jobid)) {
		echo "<font color='#cc3333' size='+2'>You cannot abort recon jobs that are uploaded</font>\n";
		exit;
	}

	// get job data
	$jobdata = $particle->getJobInfoFromId($jobid);

	// abort the job
	$clusterjobid = $jobdata['clusterjobid'];
	$cmd = "qdel $clusterjobid";
	$pass = $_SESSION['password'];
	$host = $jobdata['cluster'];
	//echo "'$host', '$user', '$cmd'\n<br/>\n";
	// this is not working on garibaldi??
	$results = exec_over_ssh($host, $user, $pass, $cmd, True);

	$particle->abortClusterJob($jobid, $user);

	echo "<font color='#cc3333' size='+2'>Aborted Job Id $jobid, Cluster Id $clusterjobid</font><br/><br/>\n";

	// Display job info
	$jobdata = $particle->getJobInfoFromId($jobid);
	$display_keys['name'] = $jobdata['name'];
	$display_keys['appion path'] = $jobdata['appath'];
	$display_keys['dmf path'] = $jobdata['dmfpath'];
	$display_keys['cluster path'] = $jobdata['clusterpath'];
	$display_keys['cluster'] = $jobdata['cluster'];
	$display_keys['status'] = $jobdata['status'];
	echo apdivtitle("Job: <font class='aptitle'>$jobdata[name]</font> (ID: <font class='aptitle'>$jobid</font>)");
	echo "<table border='0' >\n";
	foreach($display_keys as $k=>$v) {
		echo formatHtmlRow($k,$v);
	}
	echo "</table>\n";

	processing_footer();
};
?>
