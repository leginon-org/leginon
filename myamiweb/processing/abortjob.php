<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

if ($_POST['modify']) {
	echo print_r($_POST);
  abortJob($showjobs=True);
}

abortJob($showjobs=True);

function abortJob($showjobs=False,$extra=False) {
  $expId= $_GET['expId'];
  $jobId= $_GET['jobId'];
  $particle = new particledata();
  $projectId=getProjectId();

  processing_header("Cluster Job To Be Aborted","Aborting Job",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
  }

  $formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobId";
  if ($_SESSION['loggedin']==True) {
    echo "<form name='jobform' method='post' action='$formAction'>\n";
    echo "<input type='submit' name='checkjobs' value='Check Jobs in Queue'>\n";
    echo "</form>\n";
  }
	$jobs = array($particle->getJobInfoFromId($jobId));
	$qdeljob = False;
  // if clicked button, list jobs in queue
  if ($showjobs) {
    // first find out which clusters have jobs on them
    $clusters=array();
    foreach ($jobs as $job) {
      if (!in_array($job['cluster'],$clusters)) $clusters[]=$job['cluster'];
    }
    $user = $_SESSION['username'];
    $pass = $_SESSION['password'];
    if ($clusters[0]) foreach ($clusters as $c) {
      $queue = checkClusterJobs($c,$user, $pass);
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
				$queuejobid = substr($queue,0,strpos($queue,substr($user,0,6))-1);
				$queuejobnum = substr($queuejobid,0,strpos($queuejobid,substr($c,0,6))-1);
				if ($queuejobnum == $job[clusterjobid]) {
					echo "<td><tr>deleting ".$queuejobid." on the cluster</tr></td>";
					// delete queued job on host
					$cmd = "qdel ".$queuejobnum.".".$c.";\n";
					$host =  $job['cluster'];
					$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
					$qdeljob = True; 
				} else {
					echo "<td><tr>".$job[clusterjobid]." Not Runing</tr></td>";
				}
	  echo "</tr>\n";
        }
        echo "</table>\n";
      }
    }
    else {
      echo "no jobs on cluster\n";
    }	
    echo "<p>\n";	
  }
  foreach ($jobs as $job) {
    // get cluster job information
    $jobinfo = $particle->getJobInfoFromId($job['DEF_id']);
    $display_keys['name'] = $jobinfo['name'];
    $display_keys['appion path'] = $jobinfo['appath'];
    $display_keys['dmf path'] = $jobinfo['dmfpath'];
    $display_keys['cluster path'] = $jobinfo['clusterpath'];
    $display_keys['cluster'] = $jobinfo['cluster'];

    // find if job has been uploaded
    if ($particle->getReconIdFromClusterJobId($job['DEF_id'])) continue;

    // get stack id for job from job file
    $jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
    if (!file_exists($jobfile)) {
			continue;
		}
		$f = file($jobfile);
    foreach ($f as $line) {
      if (preg_match('/^\#\sstackId:\s/',$line)) $stackid=ereg_replace('# stackId: ','',trim($line));
    }
    // get num of particles in stack
    $numinstack = $particle->getNumStackParticles($stackid);

    $dlbuttons = '';
    if ($jobinfo['status']=='Q') {
      $dlbuttons.= "<input type='BUTTON' onclick=\"$particle->abortClusterJob($job[DEF_id])\" value='abort job'>\n";
			$status='Queued';
		}
    elseif ($jobinfo['status']=='R') {
      $dlbuttons.= "<input type='BUTTON' onclick=\"parent.location=('abortrecon.php?expId=$expId&jobId=$job[DEF_id]')\" value='abort job'>\n";
			$status='Running';
		}
		elseif ($jobinfo['status']=='A') $status='Aborted';
    elseif ($jobinfo['status']=='D') {
      $status='Awaiting Upload';
    }
    if ($status) $display_keys['status'] = $status;

    echo apdivtitle("Job: <font class='aptitle'>$jobinfo[name]</font> (ID: <font class='aptitle'>$job[DEF_id]</font>)");
    echo "<table BORDER='0' >\n";
    if ($dlbuttons) echo "<tr><td colspan='2'>$dlbuttons</td></tr>\n";
    foreach($display_keys as $k=>$v) {
      echo formatHtmlRow($k,$v);
    }
    echo "</table>\n";
	}

  processing_footer();
	if (!is_null($jobinfo['user'])) {
		#allow only the user created the job to abort it
		$particle->abortClusterJob($jobId,$user);
	} else {
		#old jobs has no user field in db.  Therefore, anyone can set status to abort
		$particle->abortClusterJob($jobId);
	}
	echo '<script type="text/javascript">history.go(-1);</script>';
  exit;
}

function getlogdate($emanline) {
  for ($i=4; $i>0; $i--) $emantime[] = $emanline[count($emanline)-$i];
  $time = implode(' ',$emantime);
  $tmstmp['timestamp'] = strtotime($time);
  $tmstmp['date'] = date('M d, Y H:i:s',$tmstmp['timestamp']);
  return $tmstmp;
}

function getduration($start, $stop) {
  $len = $stop - $start;
  return formatTime($len);
}

function gettimeleft($p, $tot, $start) {
  $now = time();
  $len = $now - $start;
  $perparticle = $len/$p;
  $all = $perparticle*$tot;
  $rem = $all - $len;
  return formatTime($rem);
}

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
