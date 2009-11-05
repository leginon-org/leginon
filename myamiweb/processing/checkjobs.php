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

function checkJobs($showjobs=False,$showall=False,$extra=False) {
	$expId= $_GET['expId'];
	$particle = new particledata();
	$projectId=getProjectFromExpId($expId);

	$javafunc="  <script language='JavaScript'>\n";
	$javafunc.="  function displayDMF(dmfdir,outdir,runid) {\n";
	$javafunc.="  newwindow=window.open('','name','height=150, width=900')\n";
	$javafunc.="  newwindow.document.write('<html><body>')\n";
	$javafunc.="    newwindow.document.write('dmf get '+dmfdir+'/model.tar.gz '+outdir+'/.<br />')\n";
	$javafunc.="    newwindow.document.write('dmf get '+dmfdir+'/results.tar.gz '+outdir+'/.<br />')\n";
	$javafunc.="    newwindow.document.write('dmf get '+dmfdir+'/coran.tar.gz '+outdir+'/.<br />')\n";
	$javafunc.="    newwindow.document.write('tar -xvf '+outdir+'/model.tar.gz -C '+outdir+'<br />')\n";
	$javafunc.="    newwindow.document.write('tar -xvf '+outdir+'/results.tar.gz -C '+outdir+'<br />')\n";
	$javafunc.="    newwindow.document.write('tar -xvf '+outdir+'/coran.tar.gz -C '+outdir+'<br />')\n";
	$javafunc.="    newwindow.document.write('rm -vf '+outdir+'/model.tar*<br />')\n";
	$javafunc.="    newwindow.document.write('rm -vf '+outdir+'/results.tar*<br />')\n";  
	$javafunc.="    newwindow.document.write('rm -vf '+outdir+'/coran.tar*<br />')\n";  
	$javafunc.="    newwindow.document.write('echo done<br />')\n";  
	$javafunc.="    newwindow.document.write('<p>&nbsp;<br /></body></html>')\n";
	$javafunc.="    newwindow.document.close()\n";
	$javafunc.="  }\n";
	$javafunc.="  </script>\n";

	processing_header("Cluster Jobs","Cluster Job Status",$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='RED'>$extra</font>\n<HR>\n";
	}
	
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$jobs = $particle->getJobIdsFromSession($expId, 'recon');
	if ($_SESSION['loggedin']==True) {
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
		//echo "<br/><br/>\n";
		// get cluster job information
		$jobinfo = $particle->getJobInfoFromId($job['DEF_id']);
		$display_keys['name'] = $jobinfo['name'];
		$display_keys['appion path'] = $jobinfo['appath'];
		$display_keys['dmf path'] = $jobinfo['dmfpath'];
		$display_keys['cluster path'] = $jobinfo['clusterpath'];
		$display_keys['cluster'] = $jobinfo['cluster'];
		
		// find if job has been uploaded
		//echo $job['DEF_id']."<br/>\n";
		if ($particle->getReconIdFromClusterJobId($job['DEF_id'])) continue;
		//echo $jobinfo['status']."<br/>\n";
		if ($showall != True && $jobinfo['status'] == 'A') continue;
		// get stack id for job from job file
		$jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
		if (!file_exists($jobfile)) {
			echo $job['DEF_id'].": ".$jobinfo['name'].": <i>missing job file: $jobfile</i><br/>\n";
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
			if ($user == $job['user'] || is_null($job['user']))
				//$dlbuttons.= "<input type='BUTTON' onclick=\"parent.location=('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='abort job'>\n";
			$status='Queued';
		}
		elseif ($jobinfo['status']=='R') {
			if ($user == $job['user'] || is_null($job['user']))
				//$dlbuttons.= "<input type='BUTTON' onclick=\"parent.location=('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='abort job'>\n";
			$status='Running';
		}
		elseif ($jobinfo['status']=='A') $status='Aborted';

		elseif ($jobinfo['status']=='D') {
			$dlbuttons = "<input type='BUTTON' onclick=\"displayDMF('$jobinfo[dmfpath]','$jobinfo[appath]')\" value='get from DMF'> \n";
			$dlbuttons.= "<input type='BUTTON' onclick=\"parent.location=('uploadrecon.php?expId=$expId&jobId=$job[DEF_id]')\" value='upload results'>\n";
			if ($user == $job['user'] || is_null($job['user']))
				//$dlbuttons.= "<input type='BUTTON' onclick=\"parent.location=('abortjob.php?expId=$expId&jobId=$job[DEF_id]')\" value='ignore job'>\n";
			$status='Awaiting Upload';
		}
		if ($status) $display_keys['status'] = $status;

		echo apdivtitle("Job: <font class='aptitle'>$jobinfo[name]</font> "
			."(ID: <font class='aptitle'>$job[DEF_id]</font> -- "
			."Date: <font size='-2'>". substr($jobinfo['DEF_timestamp'], 0, 10) ."</font>)");
		echo "<table BORDER='0' >\n";
		if ($dlbuttons) echo "<tr><td colspan='2'>$dlbuttons</td></tr>\n";
		foreach($display_keys as $k=>$v) {
			echo formatHtmlRow($k,$v);
		}
		echo "</table>\n";

		if ($showjobs && ($status=='Running' || $status='Awaiting Upload')) {
			$previters=array();
			$stat = checkJobStatus($jobinfo['cluster'],$jobinfo['clusterpath'],$jobinfo['name'],$user,$pass);
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
							$iternum = ereg_replace(':','', $stat['refinelog'][$j][1]);
							$iterres = $stat['refinelog'][$j][2];
							$previters[$iternum].=", resolution: ".round($iterres,2)." &Aring;";
						}
					}
				}

				foreach ($previters as $previter) echo "$previter <br />\n";
				$numtot=count($stat['allref']);
				if ($status=='Running')
					echo "<br/>\n<font class='aptitle'>Processing iteration $current of $numtot</font>\n";
				// get key corresponding to where the last refinement run starts
				if ($status=='Running' && is_array($stat['refinelog'])) {
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
							$cmd = "cd $reconpath; ls cls*.lst | wc -l";
							$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
							$cls = trim($cls);
							// get the number of classes that have been aligned
							$cmd = "grep Final $reconpath/refine$current.txt | wc -l";
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
						elseif (ereg('coran',$stat['refinelog'][$i][0])) {
							$steps['make3d']['status'] = "<font class='green'> Done</font>";
							$t = getlogdate($stat['refinelog'][$i]);
							// set duration of previous run based on time stamp
							$steps['make3d']['duration'] = getduration($lasttime,$t['timestamp']);
							
							// get progress of coran
							$cmd = "cd $reconpath/coran$current; ls cls*.lst | wc -l";
							$tot = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
							$tot = trim($tot);
							$cmd = "cd $reconpath/coran$current; ls cls*.dir/classes_avg.spi | wc -l";
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
							$cmd = "grep classalignall $reconpath/eotest$current.txt | wc -l";
							$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
							$r = trim($r);
							if ($r < 2) {
								// get the number of e/o classes
								$cmd = "cd $reconpath; ls cls*.lst | wc -l";
								$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
								$cls = trim($cls);
								// get the number of classes that have been aligned
								$cmd = "grep Final $reconpath/eotest$current.txt | wc -l";
								$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
								$r = trim($r);
								// find out how much time is left for rest of particles
								$left = gettimeleft($r,$cls,$t['timestamp']);
								$p = "creating e/o classes ($r/$cls)";
								$steps['eotest']['status'] = "<font class='apcomment'>$left remain</font>";
							}
							else {
								// see if transforming
								$cmd = "grep '[0-9]*/[0-9]*([0-9]*)' $reconpath/eotest$current.txt | wc -l";
								$r = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
								$r = trim($r);
								if ($r > 0) {
									// get the number of classes
									$cmd = "cd $reconpath; ls cls*.lst | grep 'cls[0-9]*.lst' | wc -l";
									$cls = exec_over_ssh($jobinfo['cluster'],$user,$pass,$cmd, True);
									$cls = trim($cls);
									// find number of times cycled
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
				}
				elseif ($status=='Running') echo "<p>getting files from DMF...</p>\n";
				if ($stat['errors']) {
					if ($stat['alarm']) echo "<p><font color='red'><b>There are EMAN Alarm errors (in refine*.txt) for this job, you should resubmit</b></font><p>";
					else echo "<p><font color='red'><b>There are unknown errors (refine*.txt) for this job, you should resubmit</b></font><p>";
				}
				
			}
		}
		echo "<p>\n";
	}
	processing_footer();
	exit;
}

function checkJobStatus($host,$jobpath,$jobfile,$user,$pass) {
	$cmd = "grep refine $jobpath/$jobfile ";
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
