<?php
require_once "inc/particledata.inc";
require_once "inc/util.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

checkJobs();

function checkJobs($showjob=False,$showall=False,$extra=False) {
	$expId= $_GET['expId'];
	$jobId= $_GET['jobId'];
	$particle = new particledata();

	processing_header("Appion Job","Appion Job Status",$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobId=$jobId";

	// For now, assume that logged in user,password
	// will work. Potential problem here if logged in
	// user,password not same as user,password who
	// started the job.	Maybe should verify this.
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// get cluster info for specified job
	$jobinfo = $particle->getJobInfoFromId($jobId);
	$display_keys['name'] = $jobinfo['name'];
	if ($user == $jobinfo['user'])
		$display_keys['user'] = "<font color='#339933'>".$jobinfo['user']."</font>";
	else
		$display_keys['user'] = "<font color='#993333'>".$jobinfo['user']."</font>";
	$display_keys['appion path'] = $jobinfo['appath'];
	$display_keys['submit time'] = $jobinfo['DEF_timestamp'];
	$clusterjobid = $jobinfo['clusterjobid'];
	$host = $jobinfo['cluster'];

	// kill the job if requested
	if ($_POST['killjob']) {
		$cmd = "qdel $clusterjobid";
		exec_over_ssh($host,$user,$pass,$cmd, True);
		if ($jobinfo['status'] == 'R') {
			$particle->updateClusterQueue($jobId,$clusterjobid,'D');
		} else {
			// only same user can abort job
			$particle->abortClusterJob($jobId,$user);
		}
		echo "<font class='apcomment'>Job \"$clusterjobid\" has been removed from the cluster</font><br />\n";
		// get updated job info
		$jobinfo = $particle->getJobInfoFromId($jobId);
	}
	
	// mark the job broken if requested
	if ($_POST['brokenjob']) {
		// only same user can abort job
		$particle->abortClusterJob($jobId,$user);
		echo "<font class='apcomment'>Broken job \"".$jobinfo['name']."\" has been marked as aborted</font><br />\n";
		// get updated job info
		$jobinfo = $particle->getJobInfoFromId($jobId);
	}
	
	// mark the job done if requested
	if ($_POST['donejob']) {
		// only same user can abort job
		$particle->markDoneAppionJob($jobId,$user);
		echo "<font class='apcomment'>Done job \"".$jobinfo['name']."\" has been marked as done</font><br />\n";
		// get updated job info
		$jobinfo = $particle->getJobInfoFromId($jobId);
	}

	// if clicked button, list job in queue
	$queue = checkClusterJobs($host,$user, $pass);
	if ($queue) {
		echo "<p>Jobs currently running on the <b>$c</b> cluster:<p>\n";
		$list = streamToArray($queue);
		$cluster = checkClusterType($user);
		if ($cluster == "sge") {
			$dispkeys = array('Job ID','Priority','Name','User','State','Submit/Start Date','Start time','Queue','Slots');
		}
		else {
			$dispkeys = array('Job ID','User','Queue','Jobname','SessId','NDS','TSK','ReqMem','ReqTime','S','ElapTime');
		}
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
	}
	else echo "no jobs currently running on cluster\n";
	echo "<p>\n";	

	// check job status
	if ($jobinfo['status']=='Q') $status='Queued';
	elseif ($jobinfo['status']=='R') $status='Running';
	elseif ($jobinfo['status']=='A') $status='Aborted';
	elseif ($jobinfo['status']=='D') $status='Done';

	if ($status) $display_keys['status'] = $status;

	echo apdivtitle("Job: <font class='aptitle'>$jobinfo[name]</font> (ID: <font class='aptitle'>$jobId</font>)");
	echo "<table BORDER='0' >\n";
	foreach($display_keys as $k=>$v) {
		echo formatHtmlRow($k,$v);
	}
	echo "</table>\n";

	// get log file from name of job
	$logfile = preg_replace("%.job%",".log", $jobinfo['name']);
	$logpath = $jobinfo['appath']."/".$logfile;
	if ($_SESSION['loggedin']==True || !function_exists(ssh2_connect)) {
		if (file_exists($logpath)) {
			$tail = ($_POST['tail']) ? $_POST['tail'] : '10';
			$statinfo=checkJobStatus($host,$jobinfo['appath'],$logfile,$user,$pass,$tail);
			if ($statinfo) {
				echo "<table border='0' width='600' CELLPADDING='5'>\n";
				echo "<tr><td>\n";
				echo "<form name='jobform' method='post' action='$formAction'>\n";
				echo "Show last <input type='text' name='tail' size='4' value='$tail'> lines of log file<br />\n";
				echo "<input type='submit' name='checkjob' value='Update Status'><br />\n";
				echo "$logfile:</td></tr>\n";
				echo "<tr><td bgcolor='#000000'>\n";
				echo "<pre>\n";
				echo "<font color='white' size='-1'>\n";
				foreach ($statinfo as $l) {
					$colored = convertToColors($l);
					echo "$colored\n";
				}
				echo "</font></pre>\n";
				echo "</td></tr></table>\n";
				if ($status=='Running'|| $status=='Queued') echo "<center><input type='submit' name='killjob' value='Kill this job'></center>\n";
				echo "</form>\n";
			}
		} else {
			if (!$queue) {
				echo "<form name='jobform' method='post' action='$formAction'>\n";
				if ($status=='Running') echo "<center><input type='submit' name='brokenjob' value='Mark this broken job as aborted'></center>\n";
				if ($status=='Running') echo "<center><input type='submit' name='donejob' value='Mark this finished job as completed'></center>\n";
				echo "</form>\n";
			}
		}
	}
	processing_footer();
	exit;
}

function checkJobStatus($host,$jobpath,$jobfile,$user,$pass,$tail) {
	$file = "$jobpath/$jobfile";
	if (file_exists($file)) {
		$r = tail_file($file, $tail);
		//echo "<!-- ".print_r($r)." -->";
		$allref = streamToArray($r);
	} else {
		$cmd = "tail -$tail $jobpath/$jobfile ";
		$r = exec_over_ssh($host,$user,$pass,$cmd, True);
		//echo "<!-- ".$r." -->";
		$allref = streamToArray($r);
	}
	return $allref;
}

function tail_file($file, $lines) {
	if (!$handle = fopen($file, "r")) {
		return "";
	}

	$linecounter = $lines;
	$pos = -2;
	$beginning = false;
	$text = array();
	while ($linecounter > 0) {
		$t = " ";
		while ($t != "\n") {
			if(fseek($handle, $pos, SEEK_END) == -1) {
				$beginning = true; 
				break; 
			}
			$t = fgetc($handle);
			$pos --;
		}
		$linecounter --;
		if ($beginning) {
			rewind($handle);
		}
		$text[$lines-$linecounter-1] = fgets($handle);
		if ($beginning) break;
	}
	fclose ($handle);
	$linearray = array_reverse($text);

	$cleanlines = "";
	foreach ($linearray as $line) {
		$line = trim($line);
		if (strlen($line) > 130)
			$line = substr($line,0,100)." ... ".substr($line, -25);
		$cleanlines .= $line."\n";
	}

	return $cleanlines;

}



function convertToColors($j) {
	foreach ($j as $i) {
		//$i = removebackspace($i);
		$i = trim($i);
		$i = preg_replace("%\033\[(1;)?31m%","<font style='color:red'>", $i);
		$i = preg_replace("%\033\[(1;)?32m%","<font style='color:green'>", $i);
		$i = preg_replace("%\033\[(1;)?33m%","<font style='color:yellow'>", $i);
		$i = preg_replace("%\033\[(1;)?34m%","<font style='color:blue'>", $i);
		$i = preg_replace("%\033\[(1;)?35m%","<font style='color:magenta'>", $i);
		$i = preg_replace("%\033\[(1;)?36m%","<font style='color:cyan'>", $i);
		$i = preg_replace("%\033\[(1;)?0m%","</font>", $i);
		$line .= "$i ";
		// make sure line doesn't get too long:
		$linelen = $linelen + strlen($i) + 1;
		if ($linelen > 100) {
			$linelen = 0;
			$line .= "\n";
		}		
	}
	return $line;
}

function removebackspace($s) {
	// modified from http://macgirvin.com/

	// Map the characters which sit underneath a backspace.
	// If you can come up with a regex to do all of the following
	// madness - be my guest.
	// It's not as simple as you think. We need to take something
	// that has been backspaced over an arbitrary number of times
	// and wrap a forward looking matching number of characters in
	// HTML, whilst deciding if it's intended as an underline or
	// strikeout sequence.

	// Essentially we produce a string of '1' and '0' characters
	// the same length as the source text.
	// Any position which is marked '1' has been backspaced over.

	$cursor = 0;
	$dst = $s;
	$bs_found = false;
	for($x = 0; $x < strlen($s); $x ++) {
		if( $s[$x] == "\010" && $cursor) {
			$bs_found = true;
			$cursor --;
			$dst[$cursor] = '0';
			$dst[$x] = '0';
			$continue;
		} else {
			if($bs_found) {
				$bs_found = false;
				$cursor = $x;
			}
			$dst[$cursor] = '1';
			$cursor ++;
		}

	}

	$hide = '';
	for($x = 0; $x < strlen($s); $x ++) {
		$chr = $s[$x];
		$hide .= sprintf("%03d ",ord($chr));
	}
	$add = "<!-- list ".$hide." -->";

	$out = '';
	for($x = 0; $x < strlen($s); $x++) {
		if($dst[$x] == '1') {
			$out .= $s[$x];
		} else {
			//$out .= $s[$x];
		}
	}

	return $add.str_replace("\010","",$out);
}


?>
