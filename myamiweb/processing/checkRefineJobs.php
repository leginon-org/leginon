<?php
// compress this file if the browser accepts it.
if (substr_count($_SERVER['HTTP_ACCEPT_ENCODING'], 'gzip')) ob_start("ob_gzhandler"); else ob_start();

require_once "inc/particledata.inc";
require_once "inc/util.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require_once "inc/refineJobsSingleModel.inc";
require_once "inc/refineJobsMultiModel.inc";


if ($_POST['checkjobs']) {
	checkJobs($showjobs=True);
} else {
	checkJobs();
}

function checkJobs($showjobs=False, $showall=False, $extra=False) {
	$expId= $_GET['expId'];
	$particle = new particledata();
	$projectId=getProjectId();

	processing_header("Cluster Jobs", "Cluster Job Status", $javafunc);
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
	

	$type = $_GET['type'];
	if ( $type == "multi" ) 
	{
		$refineJobs = new RefineJobsMultiModel($expId);
	} else {
		$refineJobs = new RefineJobsSingleModel($expId);
	}
	$jobs = $refineJobs->getUnfinishedRefineJobs($showall);
	
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
				if ($jobinfo['jobtype'] == 'emanrecon') {
					// if recon is of type EMAN
					//showEMANJobInfo($jobinfo);
				} elseif ($jobinfo['jobtype'] == 'frealignrecon') {
					// if recon is of type FREALIGN
					//showFrealignJobInfo($jobinfo);
				} elseif ($jobinfo['jobtype'] == 'xmipprecon') {
					// if recon is of type XMIPP
					//showXmippJobInfo($jobinfo);	
				} else {
					print_r($jobinfo);
				}
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
		$has_coran = checkCoranTarGz($jobinfo);
		if ($jobinfo['jobtype'] == 'emanrecon') {
			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
				."uploadrecon.php?expId=$expId&jobId=$jobid')\" value='Upload EMAN results'>&nbsp;\n";
		} elseif ($jobinfo['jobtype'] == 'frealignrecon') {
			$dlbuttons .= "<input type='button' onclick=\"parent.location=('"
				."uploadrecon.php?expId=$expId&jobId=$jobid')\" value='Upload FREALIGN results'>&nbsp;\n";
//			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
//				."uploadFrealign.php?expId=$expId&jobId=$jobid')\" value='Upload FREALIGN results'>&nbsp;\n";
		} elseif ($jobinfo['jobtype'] == 'xmipprecon') {
			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
				."uploadrecon.php?expId=$expId&jobId=$jobid')\" value='Upload Xmipp results'>&nbsp;\n";
		} elseif ($jobinfo['jobtype'] == 'xmippml3d') {
			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
				."uploadrecon.php?expId=$expId&jobId=$jobid')\" value='Upload Xmippml3d results'>&nbsp;\n";
		} elseif ($jobinfo['jobtype'] == 'relionrecon') {
			$dlbuttons = "<input type='button' onclick=\"parent.location=('"
				."uploadrecon.php?expId=$expId&jobId=$jobid')\" value='Upload Relion results'>&nbsp;\n";
		}
		if ($user == $job['user'] || is_null($job['user'])) {
			$dlbuttons .= "&nbsp;<input type='BUTTON' onclick=\"parent.location="
				."('abortjob.php?expId=$expId&jobId=$jobid')\" value='Hide job'>\n";
		}
		$status='Awaiting Upload';
	}
	return array($status,$dlbuttons);
}

/******************************
******************************/
function showFrealignJobInfo($jobinfo) {
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$cluster = $jobinfo['cluster'];
	$particle = new particledata();
	$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];

	
	$refinelogfile = $jobinfo['clusterpath']."/recon/refine.log";
	$cmd = "cat $refinelogfile | tail -n 2";
	$refinelog = exec_over_ssh($cluster, $user, $pass, $cmd, True);
	$refinelog = trim($refinelog);
	

	$resolutionfile = $jobinfo['clusterpath']."/recon/resolution.txt";
	$cmd = "cat $resolutionfile | cut -c-19 | sed 's/$/ \&Aring\;/'";
	$resolutiondata = exec_over_ssh($cluster, $user, $pass, $cmd, True);
	$resolutiondata = trim($resolutiondata);

	if ($resolutiondata) {
		echo "<table class='tablebg'><tr><td><pre>\n";
			echo $resolutiondata."\n";
			echo $refinelog."\n";
		echo "</pre></td></tr></table>\n";
	} else {
		$refinelogfile = $jobinfo['clusterpath']."/recon/refine.log";
		$cmd = "cat $refinelogfile | tail -n 2";
		$refinelog = exec_over_ssh($cluster, $user, $pass, $cmd, True);
		$refinelog = trim($refinelog);
		// there are no results, just say downloading
		if ($refinelog) {
			echo "<table class='tablebubble'><tr><td><pre>\n";
				//echo $refinelog."\n";
				echo $refinelog."\n";
			echo "</pre></td></tr></table>\n";
		} else {
			echo "<p><font size='+2'>downloading files...</font></p>\n";
		}
	}
};

/******************************
******************************/
function showEMANJobInfo($jobinfo) {
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$particle = new particledata();
	$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];

	// get stack id from job file: ugly, ugly, ugly
	$f = file($jobfile);
	foreach ($f as $line) {
		if (preg_match('/^\#\sstackId:\s/',$line))
			$stackid = preg_replace('%# stackId: %', '', trim($line));
	}
	// get num of particles in stack
	$numinstack = $particle->getNumStackParticles($stackid);

	$previters=array();
	$stat = checkEMANJobStatus($jobinfo['cluster'], $jobinfo['clusterpath'], $jobinfo['name'], $user, $pass);
	if (!empty($stat)) {
		$current=0;
		$laststart=0;
		for ($i=0; $i<count($stat['refinelog']); $i++) {
			// get last refine line
			if ($stat['refinelog'][$i][0]=='refine' && preg_match('/\d+/',$stat['refinelog'][$i][1])) {
				$current++;
				$lastindx = $i;
				$start=getlogdate($stat['refinelog'][$i-1]);
				// find out how long last iteration took:
				if ($laststart) {
					$len=getduration($laststart['timestamp'],$start['timestamp']);
					$previters[$current-1]="<B>Iteration ".($current-1)." finished in $len</B>";
				}
				$laststart = $start;
			}
			// get final resolutions of previous iterations
			elseif($stat['refinelog'][$i][0]=='RESOLUTIONS') {
				for ($j=$i+1;$j<count($stat['refinelog']);$j++) {
					$iternum = preg_replace('%:%','', $stat['refinelog'][$j][1]);
					$iterres = $stat['refinelog'][$j][2];
					$previters[$iternum].=", resolution: ".round($iterres,2)." &Aring;";
				}
			}
		}
		// format the last iteration if it is finished with resolution output
		if ($iternum == $current) {
			$previters[$current]="<B>Iteration ".($current)." finished </B>".$previters[$current];
		}

		foreach ($previters as $previter) echo "$previter <br />\n";
		$numtot=count($stat['allref']);
		if ($jobinfo['status'] == "R")
			echo "<br/>\n<font class='aptitle'>Processing iteration $current of $numtot</font>\n";
		// get key corresponding to where the last refinement run starts
		if ($jobinfo['status'] == "R" && is_array($stat['refinelog'])) {
			echo "<table class='tableborder' border='1' cellpadding='5' cellspacing='0'><tr>\n";
			$keys = array('reconstruction step', 'started', 'duration', 'status');
			$steps = array();
			foreach ($keys as $key) echo "<td><span class='datafield0'>$key</span></td>\n";
			echo "</tr>\n";
			$reconpath=$jobinfo['clusterpath']."/recon";
			for ($i=$lastindx; $i<count($stat['refinelog']); $i++) {
				if ($stat['refinelog'][$i][0] == 'project3d') {
					$t = getlogdate($stat['refinelog'][$i]);
					$steps['proj']['reconstruction step'] = "creating projections";
					$steps['proj']['started'] = "$t[date]";
					$steps['proj']['duration'] = getduration($t['timestamp'],time());
					$steps['proj']['status'] = "<font class='apcomment'>running</font>";
					$lasttime=$t['timestamp'];
				}

				elseif ($stat['refinelog'][$i][0] == 'classesbymra') {
					$steps['proj']['status'] = "<font class='green'> Done</font>";
					$t = getlogdate($stat['refinelog'][$i]);
					// set duration of previous run based on time stamp
					$steps['proj']['duration'] = getduration($lasttime,$t['timestamp']);

					// get the number of particles that have been classified
					$cmd = "grep ' -> ' $reconpath/refine$current.txt | wc -l";
					$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$r = trim($r);
					// find out how much time is left for rest of particles
					if ($r < $numinstack && $r > 0) {
						$left = gettimeleft($r,$numinstack,$t['timestamp']);
					}
					$p = "classifying particles ($r/$numinstack)";
					$steps['clsbymra']['reconstruction step'] = $p;
					$steps['clsbymra']['started'] = "$t[date]";
					$steps['clsbymra']['duration'] = getduration($t['timestamp'],time());
					$steps['clsbymra']['status'] = "<font class='apcomment'>running</font>";
					if ($left) $steps['clsbymra']['status'] = "<font class='apcomment'><B>$left</B> remain</font>";
					$lasttime=$t['timestamp'];
				}

				elseif ($stat['refinelog'][$i][0] == 'classalignall') {
					$steps['clsbymra']['status'] = "<font class='green'> Done</font>";
					$steps['clsbymra']['reconstruction step']='classifying particles';
					$t = getlogdate($stat['refinelog'][$i]);
					// set duration of previous run based on time stamp
					$steps['clsbymra']['duration'] = getduration($lasttime,$t['timestamp']);

					// get the number of classes
					$cmd = "ls $reconpath/cls*.lst | wc -l";
					$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$cls = trim($cls);
					// get the number of classes that have been aligned
					$cmd = "egrep '^Final' $reconpath/refine$current.txt | wc -l";
					$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$r = trim($r);
					// find out how much time is left for rest of particles
					if ($r < $cls && $r > 0) {
						$left = gettimeleft($r,$cls,$t['timestamp']);
					}
					$p = "iterative class averaging ($r/$cls)";
					$steps['clsalign']['reconstruction stsp'] = $p;
					$steps['clsalign']['started'] = "$t[date]";
					$steps['clsalign']['duration'] = getduration($t['timestamp'],time());
					$steps['clsalign']['status'] = "<font class='apcomment'>running</font>";
					if ($left) $steps['clsalign']['status'] = "<font class='apcomment'><b>$left</b> remain</font>";
					$lasttime=$t['timestamp'];
				}

				elseif ($stat['refinelog'][$i][0] == 'make3d') {
					if ($steps['make3d']['status'] == "<font class='green'> Done</font>") continue;
					$steps['clsalign']['status'] = "<font class='green'> Done</font>";
					$steps['clsalign']['reconstruction step'] = 'iterative class averaging';
					$t = getlogdate($stat['refinelog'][$i]);
					// set duration of previous run based on time stamp
					$steps['clsalign']['duration'] = getduration($lasttime,$t['timestamp']);

					$steps['make3d']['reconstruction step'] = "creating 3d model";
					$steps['make3d']['started'] = "$t[date]";
					$steps['make3d']['duration'] = getduration($t['timestamp'],time());
					$steps['make3d']['status'] = "<font class='apcomment'>running</font>";
					$lasttime=$t['timestamp'];
				}

				// if running coran:
				elseif (preg_match('%coran%',$stat['refinelog'][$i][0])) {
					$steps['make3d']['status'] = "<font class='green'> Done</font>";
					$t = getlogdate($stat['refinelog'][$i]);
					// set duration of previous run based on time stamp
					$steps['make3d']['duration'] = getduration($lasttime,$t['timestamp']);

					// get progress of coran
					$cmd = "ls $reconpath/coran$current/cls*.lst | wc -l";
					$tot = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$tot = trim($tot);
					$cmd = "ls $reconpath/coran$current/cls*.dir/classes_avg.spi | wc -l";
					$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$r = trim($r);
					// determine how much time left to finish coran
					$left='';
					if ($r > 0) $left = gettimeleft($r,$tot,$t['timestamp']);
					if ($r == $tot) {
						$cmd = "iminfo $reconpath/coran$current/goodavgs.hed | grep goodavgs.hed | awk '{print $3}'";
						$avgs = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
						$avgs = trim($avgs);
						$left = $avgs;
						if ($avgs > 0 && $avgs < $tot*2) $left = gettimeleft($avgs,$tot,$t['timestamp']);
					}
					$steps['coran']['reconstruction step'] = "performing SPIDER subclass ($r/$tot)";
					$steps['coran']['started'] = "$t[date]";
					$steps['coran']['duration'] = getduration($t['timestamp'],time());
					$steps['coran']['status'] = "<font class='apcomment'>running</font>";
					if ($left) $steps['coran']['status'] = "<font class='apcomment'><b>$left</b> remain</font>";
				}

				elseif ($stat['refinelog'][$i][1] == 'T-test') {
					$steps['make3d']['status'] = "<font class='green'> Done</font>";
					$t = getlogdate($stat['refinelog'][$i]);
					$t = getlogdate($stat['refinelog'][$i]);
					// set duration of previous run based on time stamp
					$steps['make3d']['duration'] = getduration($lasttime,$t['timestamp']);

					// see if making model
					$cmd = "egrep '^Run .classalignall' $reconpath/eotest$current.txt | wc -l";
					$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
					$r = trim($r);
					if ($r < 2) {
						// get the number of e/o classes
						$cmd = "ls $reconpath/cls*.lst | wc -l";
						$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
						$cls = trim($cls);
						// get the number of classes that have been aligned
						$cmd = "egrep '^Final' $reconpath/eotest$current.txt | wc -l";
						$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
						$r = trim($r);
						// find out how much time is left for rest of particles
						$left = gettimeleft($r,$cls,$t['timestamp']);
						$p = "creating e/o classes ($r/$cls)";
						$steps['eotest']['status'] = "<font class='apcomment'>$left remain</font>";
					}
					else {
						// see if transforming
						$cmd = "egrep '^[0-9]+/[0-9]+([0-9]+)' $reconpath/eotest$current.txt | wc -l";
						$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
						$r = trim($r);
						if ($r > 0) {
							// get the number of classes
							$cmd = "ls $reconpath/cls[0-9]*[0-9].lst | wc -l";
							$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
							$cls = trim($cls);
							// find number of times cycled
							// At certain point of the refinement cycle cls returns zero. 
							// This next line  avoids division error
							if (!is_numeric($cls) or $cls==0) $cls=1;
							$numt = floor($r/$cls);
							$m = $r%$cls;
							$tran = "transforming slice: $m/$cls";
							if ($numt) $tran = "(completed $numt rounds)";
							$steps['eotest']['status'] = "<font class='apcomment'>$tran</font>";
						}
						else $steps['eotest']['status'] = "<font class='apcomment'>running</font>";
						$p = "creating e/o 3d models";
					}
					$steps['eotest']['reconstruction step'] = "$p";
					$steps['eotest']['started'] = "$t[date]";
					$steps['eotest']['duration'] = getduration($t['timestamp'],time());
					break;
				}
			}
			foreach ($steps as $step) {
				echo "<tr>\n";
				foreach ($keys as $key) {
					if (is_array($step[$key])) $step[$key]=implode($step[$key]);
					echo "<td>$step[$key]</td>\n";
				}
				echo "</tr>\n";
			}
			echo "</table>\n";
		} elseif ($jobinfo['status'] == "R") {
			// there are no results, just say downloading
			echo "<p><font size='+2'>downloading files...</font></p>\n";
		}
		// we have errors!!!
		if ($stat['errors']) {
			if ($stat['alarm'])
				echo "<p><font color='#cc3333' size='+2'><b>There are EMAN Alarm errors (in refine*.txt) "
					." for this job, you should resubmit</b></font><p>";
			else
				echo "<p><font color='#cc3333' size='+2'><b>There are unknown errors (in refine*.txt) "
					."for this job, you should resubmit</b></font><p>";
		}
	}
};
/******************************
******************************/
function showXmippJobInfo($jobinfo) {
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	$particle = new particledata();
	$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];

	// get stack id from job file: ugly, ugly, ugly
	$f = file($jobfile);
	foreach ($f as $line) {
		if (preg_match('/^\#\sstackId:\s/',$line))
			$stackid = preg_replace('%# stackId: %', '', trim($line));
	}
	// get num of particles in stack
	$numinstack = $particle->getNumStackParticles($stackid);

};

/******************************
******************************/
function checkEMANJobStatus($host,$jobpath,$jobfile,$user,$pass) {
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
		$cmd = "echo 'RESOLUTIONS'; cat $jobpath/recon/resolution.txt";
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
};

function checkCoranTarGz($jobinfo) {
	// transfer coran results only if tar.gz exists
	
	// This function is obsolete. Replace it with a check to the log file after logging results during the run.
	// Comment this out for now.
//	$user = $_SESSION['username'];
//	$pass = $_SESSION['password'];
//	$cluster = $jobinfo['cluster'];
//	$coranfile = $jobinfo['dmfpath'].'/coran.tar.gz';
//	$cmd = "dmf ls $coranfile";
//	$lscoran = exec_over_ssh($cluster, $user, $pass, $cmd, True);
//	$has_coran = ($lscoran) ? 1:0;
//	return $has_coran;
	return false;
}

/******************************
******************************/
function getlogdate($emanline) {
	for ($i=4; $i>0; $i--) $emantime[] = $emanline[count($emanline)-$i];
	$time = implode(' ',$emantime);
	$tmstmp['timestamp'] = strtotime($time);
	$tmstmp['date'] = date('M d, Y H:i:s',$tmstmp['timestamp']);
	return $tmstmp;
};

/******************************
******************************/
function getduration($start, $stop) {
	$len = $stop - $start;
	return formatTime($len);
};

/******************************
******************************/
function gettimeleft($p, $tot, $start) {
	$now = time();
	$len = $now - $start;
	$perparticle = $len/$p;
	$all = $perparticle*$tot;
	$rem = $all - $len;
	return formatTime($rem);
};

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
};
?>
