<?php
// compress this file if the browser accepts it.
if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip')) ob_start("ob_gzhandler"); else ob_start();

require_once "inc/particledata.inc";
require_once "inc/util.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require_once "inc/alignJobs.inc";


if ($_POST['checkjobs']) {
	checkJobs($showjobs=True);
} else {
	checkJobs();
}

function checkJobs($showjobs=False, $showall=False, $extra=False) {
	$expId= $_GET['expId'];
	$particle = new particledata();
	$projectId=getProjectId();

	processing_header("Align Jobs", "Align Job Status", $javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// display button to show jobs
	if ($_SESSION['loggedin'] == true) {
		echo "<form name='jobform' method='post' action='$formAction'>\n";
		echo "<input type='submit' name='checkjobs' value='Check Jobs in Queue'>\n";
		echo "</form><br/>\n";
	}

	$alignJobs = new AlignJobs($expId);
	$jobs = $alignJobs->getUnfinishedRefineJobs($showall);
	
	// if clicked button, list jobs in queue
	if ($showjobs && $_SESSION['loggedin'] == true) {
		showClusterJobTables($jobs);
	}
	
	// loop over jobs and show info
	foreach ($jobs as $job) {	
		$jobid = $job['DEF_id'];
		$jobinfo = $particle->getJobInfoFromId($jobid);
		
		// check if job has an associated jobfile
		// works only if the file is already send to local appath
		$jobfile = $job['appath'].'/'.$job['name'];
		if (!file_exists($jobfile)) {
			// multiple qsub refinement does not generate .job but would generate .commands
			$commandfile = substr($jobfile,0,-3).'commands';
			if (!file_exists($commandfile)) {
				echo divisionHeader($jobinfo);
				echo "<i>missing job or commands file: $jobfile</i><br/><br/>\n";
				continue;
			}
		}
		
		// display relevant info

		$display_keys['job name'] = $jobinfo['name'];
		$display_keys['local path'] = $jobinfo['appath'];
		$display_keys['cluster name'] = $jobinfo['cluster'];
		$display_keys['cluster path'] = $jobinfo['clusterpath'];
		if ($jobinfo['dmfpath'])
			$display_keys['dmf path'] = $jobinfo['dmfpath'];

		// get job status
		list($status, $dlbuttons) = showStatus($jobinfo);
		if ($status) $display_keys['status'] = $status;

		// print header
		echo divisionHeader($jobinfo);

		// any download buttons
		if ($dlbuttons)
			echo "$dlbuttons<br/>\n";

		// fill table
		echo "<table border='0'>\n";
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
		echo "</table>\n";
		
		echo "<a href='checkAppionJob.php?expId=$expId&jobId=$jobid'>[check logfile]</a><br />\n";
		
		if ($_SESSION['loggedin'] == true && $showjobs) {
			if ($jobinfo['status']=='R' || $jobinfo['status']=='D') {
				print_r($jobinfo);
			}
		}
		echo "<br/><br/>\n\n";
	}
	
	processing_footer();
	exit;
}

/******************************
******************************/
function divisionHeader($jobinfo) {
	return apdivtitle("Job: <font class='aptitle'>$jobinfo[name]</font> "
		."(ID: <font class='aptitle'>$jobinfo[DEF_id]</font> -- "
		."Date: <font size='-2'>". substr($jobinfo['DEF_timestamp'], 0, 10) ."</font>)\n");
};

/******************************
******************************/
function showClusterJobTables($jobs) {
	// first find out which clusters have jobs on them
	$clusters = array();
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	foreach ($jobs as $job) {
		if (!in_array($job['cluster'], $clusters))
			$clusters[] = $job['cluster'];
	}
	
	// compare this list with what we find in the config file
	// and query each host for jobs belonging to the user.
	global $PROCESSING_HOSTS;
	
	if (!$clusters[0]) {
		echo "<i>No jobs found on any cluster.</i><br/><br/>\n";
	} else {
		foreach ($PROCESSING_HOSTS as $host) {
			$hostname = $host['host'];
			
			if ( in_array($hostname, $clusters) ) {
				$jobs = checkClusterJobs($hostname, $user, $pass);
				
				if ($jobs) {
					echo "";
					// START TABLE
					echo "<table class='tableborder' border=1 cellspacing=0, cellpadding=5>\n";
	
					// TABLE HEADER
					echo "<tr><td colspan='15'><font size='+1'>Jobs currently running on the "
						."<font color='#339933'><b>$hostname</b></font>"
						." cluster</font></td></tr>";
	
					// LABEL FIELDS
					echo "<tr>\n";
					$dispkeys = array('Job ID','User','Queue','Jobname','SessId','NDS','TSK','ReqMem','ReqTime','S','ElapTime');
					foreach ($dispkeys as $key) {
						echo "<td><span class='datafield0'>$key</span></td>";
					}
					echo "</tr>\n";
	
					// SHOW DATA
					$list = streamToArray($jobs);
					foreach ($list as $line) {
						echo "<tr>\n";
						foreach ($line as $i) {echo "<td>$i</td>\n";}
						echo "</tr>\n";
					}
					// CLOSE TABLE
					echo "</table><br/><br/>\n";
				} else {
					echo "<i>No jobs found on $hostname cluster for user $user.</i><br/><br/>\n";
				}								
			}
		}
	}
			
	echo "\n";
};

/******************************
******************************/
function showStatus($jobinfo) {
	//$user = $_SESSION['username'];
	$dlbuttons = '';
	$status='Unknown';
	$jobid = $jobinfo['DEF_id'];
	$expId = $_GET['expId'];

	if ($jobinfo['status']=='Q') {
		if ($user == $job['user'] || is_null($job['user']))
			$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
				."('abortjob.php?expId=$expId&jobId=$jobid')\" value='Abort job'>\n";
			$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
				."('forcejobstatus.php?expId=$expId&jobId=$jobid')\" value='Force Status to Done'>\n";
				$status='Queued';
	} elseif ($jobinfo['status']=='R') {
		if ($user == $job['user'] || is_null($job['user']))
			$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
				."('abortjob.php?expId=$expId&jobId=$jobid')\" value='Abort job'>\n";
		$status='Running';
	} elseif ($jobinfo['status']=='A') {
		$status='Aborted';
	} elseif ($jobinfo['status']=='E') {
		$status='Error';
	} elseif ($jobinfo['status']=='D') {
		if ($jobinfo['jobtype'] == 'sparxisac') {
			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
				."runUploadIsac.php?expId=$expId&jobId=$jobid')\" value='Upload ISAC results'>&nbsp;\n";
		} elseif ($jobinfo['jobtype'] == 'maxlikealignment') {
			$dlbuttons .= "<input type='button' onclick=\"parent.location=('"
				."runUploadMaxLike.php?expId=$expId&jobId=$jobid')\" value='Upload MaxLike results'>&nbsp;\n";
		} 
		
		if ($user == $job['user'] || is_null($job['user'])) {
			$dlbuttons .= "&nbsp;<input type='BUTTON' onclick=\"parent.location="
				."('abortjob.php?expId=$expId&jobId=$jobid')\" value='Hide job'>\n";
		}
		$status='Awaiting Upload';
	}
	return array($status,$dlbuttons);
}

?>
