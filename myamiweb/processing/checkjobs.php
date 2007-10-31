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
    $jobinfo = $particle->getJobInfoFromId($job['DEF_id']);

    // find if job has been uploaded
    $recon = $particle->getReconIdFromClusterJobId($job['DEF_id']);
    $display_keys['name'] = $jobinfo['name'];
    $display_keys['appion path'] = $jobinfo['appath'];
    $display_keys['dmf path'] = $jobinfo['dmfpath'];
    $display_keys['cluster path'] = $jobinfo['clusterpath'];

    // get stack id for job from job file
    $jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
    $f = file($jobfile);
    foreach ($f as $line) {
      if (preg_match('/^\#\sstackId:\s/',$line)) $stackid=ereg_replace('# stackId: ','',trim($line));
    }
    // get num of particles in stack
    $numinstack = $particle->getNumStackParticles($stackid);

    if ($recon) $status="<A HREF='reconreport.php?reconId=$recon[DEF_id]'>Uploaded</A>\n";
    elseif ($jobinfo['status']=='Q') $status='Queued';
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
	echo "<B>Current Status:</B>\n";
	$current=0;
	foreach ($stat['refinelog'] as $i){
	  // get last refine line
	  if ($i[0]=='refine' && preg_match('/\d+/',$i[1])) {
	    $current++;
	    $lastindx = $i;
	  }
	}
	$numtot=count($stat['allref']);
	echo "<table class='tableborder' cellpadding=5 ><tr><td>\n";
	echo "<font class='aptitle'>Processing iteration $current of $numtot</font>\n";
	echo "</td></tr>\n";
	echo "<tr><td>\n";
	echo "<table border='0' cellpadding='5' cellspacing='0'>\n";
	echo "<tr><td><span class='datafield0'>step</span></td>\n";
	echo "<td><span class='datafield0'>started</span></td>\n";
	echo "<td><span class='datafield0'>status</span></td></tr>\n";
	echo "<tr><td>\n";
	// get key corresponding to where the last refinement run starts
	$lastkey = array_search($lastindx, $stat['refinelog']);
	for ($i=$lastkey; $i<count($stat['refinelog']); $i++) {
	  if ($stat['refinelog'][$i][0] == 'project3d') {
	    $d = getlogdate($stat['refinelog'][$i]);
	    $progress[] = "creating projections</td><td>$d";
	  }
	  elseif ($stat['refinelog'][$i][0] == 'classesbymra') {
	    // get the number of particles that have been classified
	    $d = getlogdate($stat['refinelog'][$i]);
	    $cmd = "grep ' -> ' $jobinfo[clusterpath]/recon/refine$current.txt | wc -l";
	    $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
	    $r = trim($r);
	    $progress[] = "classifying particles ($r/$numinstack)</td><td>$d\n";
	  }
	  elseif ($stat['refinelog'][$i][0] == 'classalignall') {
	    $d = getlogdate($stat['refinelog'][$i]);
	    $progress[] = "iterative class averaging</td><td>$d\n";
	  }
	  elseif ($stat['refinelog'][$i][0] == 'make3d') {
	    $d = getlogdate($stat['refinelog'][$i]);
	    $progress[] = "creating 3d model</td><td>$d\n";
	  }
	  elseif ($stat['refinelog'][$i][0] == 'eotest') {
	    $d = getlogdate($stat['refinelog'][$i]);
	    $progress[] = "performing even/odd test</td><td>$d\n"; 
	    break;
	  }
	}
	echo implode("</td><td><font class='green'> Done</font></td></tr>\n<tr><td>",$progress);
	echo "</td><td>running</td></tr></table>\n";
	echo "</TD></TR></TABLE>\n";
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
  for ($i=4; $i>0; $i--) {
    $emantime[] = $emanline[count($emanline)-$i];
  }
  $time = implode(' ',$emantime);
  $tmstmp = strtotime($time);
  return date('M d,Y H:i:s',$tmstmp);
}