<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

if ($_POST['checkjobs']) {
  checkJobs($showjobs=True);
}

checkJobs();

function checkJobs($showjobs=False,$extra=False) {
  $expId= $_GET['expId'];
  $particle = new particledata();
  $projectId=getProjectFromExpId($expId);

  $javafunc="  <SCRIPT LANGUAGE='JavaScript'>\n";
  $javafunc.="  function displayDMF(dmfdir,outdir,runid) {\n";
  $javafunc.="  newwindow=window.open('','name','height=150, width=900')\n";
  $javafunc.="  newwindow.document.write('<HTML><BODY>')\n";
  $javafunc.="    newwindow.document.write('dmf get '+dmfdir+'/model.tar.gz '+outdir+'/.<BR>')\n";
  $javafunc.="    newwindow.document.write('dmf get '+dmfdir+'/results.tar.gz '+outdir+'/.<BR>')\n";  
  $javafunc.="    newwindow.document.write('tar -xvf '+outdir+'/model.tar.gz -C '+outdir+'<BR>')\n";
  $javafunc.="    newwindow.document.write('tar -xvf '+outdir+'/results.tar.gz -C '+outdir+'<BR>')\n";  
  $javafunc.="    newwindow.document.write('rm -f '+outdir+'/model.tar<BR>')\n";
  $javafunc.="    newwindow.document.write('rm -f '+outdir+'/results.tar<BR>')\n";  
  $javafunc.="    newwindow.document.write('<P>&nbsp;<BR></BODY></HTML>')\n";
  $javafunc.="    newwindow.document.close()\n";
  $javafunc.="  }\n";
  $javafunc.="  </SCRIPT>\n";

  writeTop("Cluster Jobs","Cluster Jobs Awaiting Upload",$javafunc);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }

  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  $jobs = $particle->getJobIdsFromSession($expId);
  if ($_SESSION['loggedin']==True) {
    echo "<FORM NAME='jobform' method='POST' ACTION='$formAction'>\n";
    echo "<INPUT TYPE='SUBMIT' NAME='checkjobs' VALUE='Check Jobs in Queue'>\n";
    echo "</FORM>\n";
  }
  // if clicked button, list jobs in queue
  if ($showjobs) {
    $user = $_SESSION['username'];
    $pass = $_SESSION['password'];
    $queue = checkClusterJobs($user, $pass);
    if ($queue) {
      echo "<P>Jobs currently running on the cluster:<P>\n";
      $list = streamToArray($queue);
      $dispkeys = array('Job ID','User','Queue','Jobname','SessId','NDS','TSK','ReqMem','ReqTime','S','ElapTime');
      echo "<TABLE CLASS='tableborder' border=1 cellspacing=0, cellpadding=5>\n";
      echo "<TR>\n";
      foreach ($dispkeys as $key) {
	echo "<TD><SPAN CLASS='datafield0'>$key</SPAN></TD>";
      }
      echo "</TR>\n";
      foreach ($list as $line) {
	echo "<TR>\n";
	foreach ($line as $i) {echo "<TD>$i</TD>\n";}
	echo "</TR>\n";
      }
      echo "</TABLE>\n";
    }
    else {
      echo "no jobs on cluster\n";
    }	
    echo "<P>\n";	
  }
  foreach ($jobs as $job) {
    // get cluster job information
    $jobinfo = $particle->getJobInfoFromId($job['DEF_id']);
    $display_keys['name'] = $jobinfo['name'];
    $display_keys['appion path'] = $jobinfo['appath'];
    $display_keys['dmf path'] = $jobinfo['dmfpath'];
    $display_keys['cluster path'] = $jobinfo['clusterpath'];

    // find if job has been uploaded
    if ($particle->getReconIdFromClusterJobId($job['DEF_id'])) continue;

    // get stack id for job from job file
    $jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
    $f = file($jobfile);
    foreach ($f as $line) {
      if (preg_match('/^\#\sstackId:\s/',$line)) $stackid=ereg_replace('# stackId: ','',trim($line));
    }
    // get num of particles in stack
    $numinstack = $particle->getNumStackParticles($stackid);

    $dlbuttons = '';
    if ($jobinfo['status']=='Q') $status='Queued';
    elseif ($jobinfo['status']=='R') $status='Running';
    elseif ($jobinfo['status']=='D') {
      $dlbuttons = "<INPUT TYPE='BUTTON' onclick=\"displayDMF('$jobinfo[dmfpath]','$jobinfo[appath]')\" VALUE='get from DMF'> \n";
      $dlbuttons.= "<INPUT TYPE='BUTTON' onclick=\"parent.location=('uploadrecon.php?expId=$expId&jobId=$job[DEF_id]')\" VALUE='upload results'>\n";
      $status='Awaiting Upload';
    }
    if ($status) $display_keys['status'] = $status;

    echo divtitle("Job: <font class='aptitle'>$jobinfo[name]</font> (ID: <font class='aptitle'>$job[DEF_id]</font>)");
    echo "<TABLE BORDER='0' >\n";
    if ($dlbuttons) echo "<TR><TD COLSPAN='2'>$dlbuttons</TD></TR>\n";
    foreach($display_keys as $k=>$v) {
      echo formatHtmlRow($k,$v);
    }
    echo "</TABLE>\n";

    if ($showjobs && $status=='Running') {
      $stat = checkJobStatus($jobinfo['clusterpath'],$jobinfo['name'],$user,$pass);
      if (!empty($stat)) {
	$current=0;
	for ($i=0; $i<count($stat['refinelog']); $i++) {
	  // get last refine line
	  if ($stat['refinelog'][$i][0]=='refine' && preg_match('/\d+/',$stat['refinelog'][$i][1])) {
	    $current++;
	    $lastindx = $i;
	    $start=getlogdate($stat['refinelog'][$i-1]);
	    // find out how long last iteration took:
	    if ($laststart) {
	      $len=getduration($laststart['timestamp'],$start['timestamp']);
	      echo "<B>Iteration ".($current-1)." finished in $len</B><BR>\n";
	    }
	    $laststart = $start;
	  }	  
	}
	$numtot=count($stat['allref']);
	echo "<font class='aptitle'>Processing iteration $current of $numtot</font>\n";
	echo "<table class='tableborder' border='1' cellpadding='5' cellspacing='0'><tr>\n";
	$keys = array('reconstruction step', 'started', 'duration', 'status');
	$steps = array();
	foreach ($keys as $key) echo "<td><span class='datafield0'>$key</span></td>\n";
	echo "</tr>\n";
	// get key corresponding to where the last refinement run starts
	if (is_array($stat['refinelog'])) {
	  for ($i=$lastindx; $i<count($stat['refinelog']); $i++) {

	    if ($stat['refinelog'][$i][0] == 'project3d') {
	      $t = getlogdate($stat['refinelog'][$i]);
	      $steps['proj']['reconstruction step'] = "creating projections";
	      $steps['proj']['started'] = "$t[date]";
	      $steps['proj']['duration'] = getduration($t['timestamp'],time());
	      $steps['proj']['status'] = "<FONT CLASS='apcomment'>running</FONT>";
	      $lasttime=$t['timestamp'];
	    }

	    elseif ($stat['refinelog'][$i][0] == 'classesbymra') {
	      $steps['proj']['status'] = "<font class='green'> Done</font>";
	      $t = getlogdate($stat['refinelog'][$i]);
	      // set duration of previous run based on time stamp
	      $steps['proj']['duration'] = getduration($lasttime,$t['timestamp']);

	      // get the number of particles that have been classified
	      $cmd = "grep ' -> ' $jobinfo[clusterpath]/recon/refine$current.txt | wc -l";
	      $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
	      $r = trim($r);
	      // find out how much time is left for rest of particles
	      if ($r < $numinstack) {
		$left = gettimeleft($r,$numinstack,$t['timestamp']);
	      }
	      $p = "classifying particles ($r/$numinstack)";
	      $steps['clsbymra']['reconstruction step'] = $p;
	      $steps['clsbymra']['started'] = "$t[date]";
	      $steps['clsbymra']['duration'] = getduration($t['timestamp'],time());
	      $steps['clsbymra']['status'] = "<FONT CLASS='apcomment'><B>$left</B> remain</FONT>";
	      $lasttime=$t['timestamp'];
	    }

	    elseif ($stat['refinelog'][$i][0] == 'classalignall') {
	      $steps['clsbymra']['status'] = "<font class='green'> Done</font>";
	      $steps['clsbymra']['reconstruction step']='classifying particles';
	      $t = getlogdate($stat['refinelog'][$i]);
	      // set duration of previous run based on time stamp
	      $steps['clsbymra']['duration'] = getduration($lasttime,$t['timestamp']);

	      $steps['clsalign']['reconstruction step'] = "iterative class averaging";
	      $steps['clsalign']['started'] = "$t[date]";
	      $steps['clsalign']['duration'] = getduration($t['timestamp'],time());
	      $steps['clsalign']['status'] = "<FONT CLASS='apcomment'>running</FONT>";
	      $lasttime=$t['timestamp'];
	    }

	    elseif ($stat['refinelog'][$i][0] == 'make3d') {
	      $steps['clsalign']['status'] = "<font class='green'> Done</font>";
	      $t = getlogdate($stat['refinelog'][$i]);
	      $t = getlogdate($stat['refinelog'][$i]);
	      // set duration of previous run based on time stamp
	      $steps['clsalign']['duration'] = getduration($lasttime,$t['timestamp']);

	      $steps['make3d']['reconstruction step'] = "creating 3d model";
	      $steps['make3d']['started'] = "$t[date]";
	      $steps['make3d']['duration'] = getduration($t['timestamp'],time());
	      $steps['make3d']['status'] = "<FONT CLASS='apcomment'>running</FONT>";
	      $lasttime=$t['timestamp'];
	    } 

	    elseif ($stat['refinelog'][$i][1] == 'T-test') {
	      $steps['make3d']['status'] = "<font class='green'> Done</font>";
	      $t = getlogdate($stat['refinelog'][$i]);
	      $t = getlogdate($stat['refinelog'][$i]);
	      // set duration of previous run based on time stamp
	      $steps['make3d']['duration'] = getduration($lasttime,$t['timestamp']);

	      $steps['eotest']['reconstruction step'] = "performing even/odd test";
	      $steps['eotest']['started'] = "$t[date]";
	      $steps['eotest']['duration'] = getduration($t['timestamp'],time());
	      $steps['eotest']['status'] = "<FONT CLASS='apcomment'>running</FONT>";
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
	}
	if ($stat['errors']) echo "<P><FONT COLOR='RED'>There are errors in this job, you should resubmit</FONT><P>";
      }
    }
    echo "<P>\n";
  }
  writeBottom();
  exit;
}

function checkJobStatus($jobpath,$jobfile,$user,$pass) {
  $cmd = "grep refine $jobpath/$jobfile ";
  $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
  $allref = streamToArray($r);
  if (empty($allref)) return;
  foreach ($allref as $i){
    if ($i[0]=='refine' && preg_match('/\d+/',$i[1])) $stat['allref'][]=$i;
  }
  $cmd = "cat $jobpath/recon/refine.log";
  $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
  $curref = streamToArray($r);
  $stat['refinelog']=$curref;
  $cmd = "grep Alarm $jobpath/recon/refine.* ";
  $stat['errors'] = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);

  return $stat;
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