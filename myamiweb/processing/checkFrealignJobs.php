<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

if ($_POST['checkjobs']) {
	checkJobs($showjobs=True);
} else {
	checkJobs();
}

/******************************
******************************/
function checkJobs($showjobs=False,$showall=False,$extra=False) {
	$expId= $_GET['expId'];
	$particle = new particledata();
	$projectId=getProjectId();

	processing_header("Frealign Job Status","Frealign Job Status",$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$jobs = $particle->getJobIdsFromSession($expId, 'runfrealign');
	if ($_SESSION['loggedin'] == true) {
		echo "<form name='jobform' method='post' action='$formAction'>\n";
		echo "<input type='submit' name='checkjobs' value='Check Jobs in Queue'>\n";
		echo "</form>\n";
	}
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// if clicked button, list jobs in queue
	if ($showjobs) {
		// first find out which clusters have jobs on them
		$clusters=array();
		foreach ($jobs as $job) {
		  	if (!in_array($job['cluster'], $clusters)) $clusters[]=$job['cluster'];
		}
		if ($clusters[0]) {
			foreach ($clusters as $c) {
				$queue = checkClusterJobs($c, $user, $pass);
				if ($queue) {
					echo "<p>Jobs currently running on the <b>$c</b> cluster:<p>\n";
					$list = streamToArray($queue);
					$dispkeys = array('Job ID','User','Queue','Jobname','SessId','NDS','TSK','ReqMem','ReqTime','S','ElapTime');
					echo "<table class='tableborder' border=1 cellspacing=0, cellpadding=5>\n";
					echo "<tr>\n";
					foreach ($dispkeys as $key) {
					  echo "<td><span class='datafield0'>$key</span></td>";
					}
					echo "</tr>\n";
					foreach ($list as $line) {
						echo "<tr>\n";
						foreach ($line as $i) {echo "<td>$i</td>\n";}
						echo "</tr>\n";
					}
					echo "</table>\n";
				} else echo "no queue on $c cluster<br/>\n";
			}
		}
		else echo "no jobs found\n";
		echo "<p>\n";	
	}

	foreach ($jobs as $job) {
		// get cluster job information
		$jobinfo = $particle->getJobInfoFromId($job['DEF_id']);

		// skip if job has been uploaded
		if ($particle->getReconIdFromClusterJobId($job['DEF_id']))
			continue;

		// skip if jobs was aborted
		if ($showall != True && $jobinfo['status'] == 'A')
			continue;

		// check if job file exists on local filesystem
		$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
		if (!file_exists($jobfile)) {
			echo apdivtitle("Frealign Job: <font class='aptitle'>$jobinfo[name]</font> "
				."(ID: <font class='aptitle'>$jobinfo[DEF_id]</font> -- "
				."Date: <font size='-2'>". substr($jobinfo['DEF_timestamp'], 0, 10) ."</font>)");
			echo $job['DEF_id'].": ".$jobinfo['name'].": <i>missing job file: $jobfile</i><br/>\n";
			continue;
		}

		// display relevant info
		$display_keys['name'] = $jobinfo['name'];
		$display_keys['appion path'] = $jobinfo['appath'];
		if ($jobinfo['dmfpath'])
			$display_keys['dmf path'] = $jobinfo['dmfpath'];
		$display_keys['cluster path'] = $jobinfo['clusterpath'];
		$display_keys['cluster'] = $jobinfo['cluster'];

		// get job status
		list($status, $dlbuttons) = showStatus($jobinfo);
		if ($status) $display_keys['status'] = $status;

		// print header
		echo apdivtitle("Frealign Job: <font class='aptitle'>$jobinfo[name]</font> "
			."(ID: <font class='aptitle'>$jobinfo[DEF_id]</font> -- "
			."Date: <font size='-2'>". substr($jobinfo['DEF_timestamp'], 0, 10) ."</font>)");
		echo "<table BORDER='0' >\n";
		if ($dlbuttons) echo "<tr><td colspan='2'>$dlbuttons</td></tr>\n";
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k, $v);
		}
		echo "</table>\n";
		echo "<br/><br/>\n";
	}
	processing_footer();
	exit;
}

/******************************
******************************/
function showStatus($jobinfo) {
	$dlbuttons = '';
	$status='Unknown';
	if ($jobinfo['status']=='Q') {
		//if ($user == $job['user'] || is_null($job['user']))
		//	$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
		//		."('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='abort job'>\n";
		$status='Queued';
	} elseif ($jobinfo['status']=='R') {
		//if ($user == $job['user'] || is_null($job['user']))
		//	$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
		//		."('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='abort job'>\n";
		$status='Running';
	} elseif ($jobinfo['status']=='A') {
		$status='Aborted';
	} elseif ($jobinfo['status']=='D') {
		$dlbuttons = "<input type='BUTTON' onclick=\"displayDMF('$jobinfo[dmfpath]','$jobinfo[appath]')\" value='get from DMF'> \n";
		$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location=('uploadrecon.php?expId=$expId&jobId=$job[DEF_id]')\" value='upload results'>\n";
		//if ($user == $job['user'] || is_null($job['user']))
		//	$dlbuttons .= "<input type='BUTTON' onclick=\"parent.location="
		//		."('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='ignore job'>\n";
		$status='Awaiting Upload';
	}
	return array($status,$dlbuttons);
}

/******************************
******************************/
function checkJobStatus($host, $jobpath, $jobfile, $user, $pass) {
	$cmd = "egrep '^refine ' $jobpath/$jobfile ";
	$r = exec_over_ssh($host,$user,$pass,$cmd, True);
	$allref = streamToArray($r);
	if (empty($allref)) return;
	foreach ($allref as $i){
		if (preg_match('/refine/',$i[0]) && preg_match('/\d+/',$i[1])) $stat['allref'][]=$i;
	}
	$cmd = "cat $jobpath/recon/refine.log";
	$r = exec_over_ssh($host,$user,$pass,$cmd, True);
	if ($r) {
		$cmd = "echo 'RESOLUTIONS';cat $jobpath/recon/resolution.txt";
		$r .= exec_over_ssh($host,$user,$pass,$cmd, True);
	}
	$curref = streamToArray($r);
	$stat['refinelog']=$curref;
	
	// check for errors:
	$cmd = "grep Alarm $jobpath/recon/refine*.txt ";
	$stat['errors'] = exec_over_ssh($host,$user,$pass,$cmd, True);
	if (!$stat['errors']) {
		$cmd = "grep Error $jobpath/recon/refine*.txt ";
		$stat['errors'] = exec_over_ssh($host,$user,$pass,$cmd, True);
	}
	else {
		$stat['alarm'] = True;
	}
	return $stat;
}

/******************************
******************************/
function getlogdate($emanline) {
	for ($i=4; $i>0; $i--) $emantime[] = $emanline[count($emanline)-$i];
	$time = implode(' ',$emantime);
	$tmstmp['timestamp'] = strtotime($time);
	$tmstmp['date'] = date('M d, Y H:i:s',$tmstmp['timestamp']);
	return $tmstmp;
}

/******************************
******************************/
function getduration($start, $stop) {
	$len = $stop - $start;
	return formatTime($len);
}

/******************************
******************************/
function gettimeleft($p, $tot, $start) {
	$now = time();
	$len = $now - $start;
	$perparticle = $len/$p;
	$all = $perparticle*$tot;
	$rem = $all - $len;
	return formatTime($rem);
}

/******************************
******************************/
function formatTime($t) {
	if ($t > 24*3600) {
		$days=floor($t/(24*3600));
		$t=$t-($days*24*3600);
		$ft[] = ($days > 1) ? $days." days" : $days." day";
	}
	if ($t > 3600) {
		$hours=floor($t/3600);
		$t=$t-($hours*3600);
		$ft[] = ($hours > 1) ? $hours." hrs" : $hours." hr";
	}
	if ($t > 60) {
		$min=floor($t/60);
		$ft[] = $min." min";
	}
	// if only seconds, just display seconds
	if (!$days && !$hours && !$min) $ft = floor($t)." sec";
	if (is_array($ft)) $ft = implode(' ',$ft);
	return $ft;  
}
?>
