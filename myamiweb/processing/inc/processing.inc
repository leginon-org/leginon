<?php

/**
 *	The Leginon software is Copyright 2006 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement see
 *	@licence http://ami.scripps.edu/software/leginon-license
 */
/**
 *	Query definition to access all leginon data 
 *	
 */

require_once "inc/ssh.inc";
require_once "inc/session.inc";

// --- add to config file later --- //
define(PROCESSING_HOST, 'garibaldi');

define(DONE_PIC,'img/green_circle.gif');
define(NONE_PIC,'img/red_circle.gif');
define(PROG_PIC,'img/blue_circle.gif');

define(NONE_COLOR,'#FFFFCC');
define(PROG_COLOR,'#CCFFFF');
define(DONE_COLOR,'#CCFFCC');


// start a php session
setsession();

// add commas to an int
function commafy($input) {
   if(strlen($input)<=3) { 
     return $input;
   }
   $length=substr($input,0,strlen($input)-3);
   $formatted_input = commafy($length).",".substr($input,-3);
   return $formatted_input;
}

function getHosts(){
	global $PROCESSING_HOSTS;
        if (is_array($PROCESSING_HOSTS)) return $PROCESSING_HOSTS;
	return array();
}

function writeTop($title,$heading=false,$headerstuff=false,$showloginerror=True){
  global $_GET;
  echo"<HTML>
  <HEAD>
  <title>$title</title>
  <link rel='stylesheet' type='text/css' href='../css/viewer.css'> 
  <link rel='stylesheet' type='text/css' href='../css/view.css'>
  <SCRIPT SRC='../js/viewer.js'>
  </SCRIPT>
  $headerstuff
  </HEAD>
  <BODY>
  <CENTER>
  <TABLE BORDER='0'>
  <TR>
  <TD ALIGN='LEFT'>\n";
  if ($heading) echo"<H3 ALIGN='CENTER'>$heading</H3>\n";
  if ($_SESSION['username']) {
    echo "<FONT CLASS='sf' ALIGN='right'><I>logged in as <B>$_SESSION[username]</B></I></FONT>\n";
    echo "<A CLASS='header' HREF='endsession.php?expId=$_GET[expId]'><FONT CLASS='sf'>[Log Out]</FONT></A>\n";
    $_SESSION['loggedin']=True;
  }
  elseif ($showloginerror==True) {
    echo "<FONT COLOR='red'><B>WARNING:</B> You cannot submit jobs without logging in</FONT> <A CLASS='header' HREF='login.php?expId=$_GET[expId]&prev=$_SERVER[PHP_SELF]'>[Log In]</A>\n";
  }
  echo"<HR>\n";
}

function writeBottom($showproclink=True, $nytimes=False){
  global $_GET;
  echo"
  </TD>
  </TR>
  </TABLE>\n";
#  if ($nytimes) echo "<table cellpadding='5' class='tableborder' border='1'><tr><td align='center'><a href='http://www.nytimes.com'>While waiting, enjoy <br /><img border='0' src='img/nytimes.gif' alt='New York Times'></A></td></tr></table><br />\n";
  if ($showproclink && $_GET['expId']) echo "<A HREF='processing.php?expId=$_GET[expId]' CLASS='header'>[Back to Processing Page]</A>\n";
  echo "
  </CENTER>
  </BODY>
  </HTML>\n";
}

function displayLogin($formAction) {
  echo "<FORM NAME='jobform' method='POST' ACTION='$formAction'>\n";
  echo "<TABLE CLASS='tableborder' BORDER='1' CELLSPACING='1' CELLPADDING='5'>\n";
  echo "<TR><TD>\n";
  echo "Username: <INPUT TYPE='text' name='username' value='$_POST[username]'>\n";
  echo "Password: <INPUT TYPE='password' name='password'><BR>\n";
  echo "<CENTER><INPUT TYPE='submit' NAME='login' VALUE='Log In'></CENTER>\n";
  echo "</TD></TR>\n";
  echo "</TABLE>\n";
  echo "</FORM>\n";  
}

function checkLogin() {
  // if everything is cool, then return nothing
  if (!$_SESSION['username']) {
    if (!$_POST['username'] || !$_POST['password']) return("ERROR: enter your user name and password");
    // authenticate username & password
    if (!check_ssh($_SERVER['HTTP_HOST'],$_POST['username'],$_POST['password'])) return("ERROR: authentication failed");
    ## save username and password to the session
    $_SESSION['username']=$_POST['username'];
    $_SESSION['password']=$_POST['password'];
    unset($_POST['username']);
    unset($_POST['password']);
  }
  return;
}

function getProjectList() {
  $projectdata = new project();
  $projectdb = $projectdata->checkDBConnection();
 
  if($projectdb) $projects = $projectdata->getProjects('all');
    
  return($projects);
}

function getProjectFromExpId($expId) {
  $projectdata = new project();
  $projectdb = $projectdata->checkDBConnection();
 
  if($projectdb) $projectinfo = $projectdata->getProjectfromSessionId($expId);
  $projectId=$projectinfo['projectId'];
  return $projectId;
}

// --- Set sessionId
function getSessionList($projectId,$sessionId){
	$projectdata = new project();
	$leginondata = new leginondata();

	if(!$sessions) $sessiondata['sessions'] = $leginondata->getSessions('description', $projectId);

	$sessiondata['info']=$leginondata->getSessionInfo($sessionId);
	$sessiondata['presets']=$leginondata->getTruePresets($sessionId);
	$sessiondata['currentproject']=$projectdata->getProjectFromSession($sessiondata['info']['Name']);

	return $sessiondata;
}

// --- Display forms to get a project & session
function displayExperimentForm($projectId,$sessionId,$expId){
	global $PROJECT_URL;
	// Collect session info from database
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessions=$sessiondata['sessions'];
	$currentproject=$sessiondata['currentproject'];

	if ($expId){
		$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL
			."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
		$sessionDescr=$sessiondata['info']['Purpose'];
		$session_link="<a class='header' target='project' href='../3wviewer.php?expId=$expId'>$sessionDescr</a>";
		echo "Project: $proj_link<BR>\nSession: $session_link\n";

	} else {

		echo"
		<b>Select Session:</b><br />
		<select name='projectId' onchange='newexp()'>\n";
		$projects=getProjectList();
		foreach ($projects as $k=>$project) {
			$sel = ($project['id']==$projectId) ? "selected" : '';
			echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
		}
		echo"
		</select>
		<br />
		<select name='sessionId' onchange='newexp()'>
		<option value=''>all sessions</option>\n";
		foreach ($sessions as $k=>$session) {
			$sel = ($session['id']==$sessionId) ? 'selected' : '';
			$shortname=substr($session['name'],0,90);
			echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>\n";
		}
		echo"</select>\n";
	}
	return $sessiondata;
}

function checkClusterJobs($host, $user, $pass, $cmd='qstat -a | grep $user') {
  $subjobs = exec_over_ssh($host,$user,$pass,$cmd,True);
  return $subjobs;
}

function checkRequiredFileError($path,$filename) {
	if (substr($path,-1,1)!='/') $path.='/';
	$file = $path.$filename;
	if (file_exists($file)) {
		if (filesize($file) > 0) {
			return false;
		} else {
			return '<B>ERROR:</B> empty '.$filename;
		}
	} else {
		return '<B>ERROR:</B> '.$filename.' not exist';
	}
}

function streamToArray($stream) {
  // turns a stream into an array of arrays
  $lines=explode("\n", $stream);
  foreach($lines as $line) {
    if (!$line=trim($line))
      continue;
    $fields=explode(" ",$line);
    $row=array();
    foreach($fields as $f) {
      if (!trim($f))
	continue;
      $row[]=$f;
    }
    $rows[]=$row;
  }
  return $rows;
}

function stackViewer($file_hed,$file_img,$n_images,$updateheader,$plist=False) {
	$javascript = "
	<style>
	input, select {
		border: 1px solid #AABDCC;
	}
	img.imgtile {
		border: 1px solid #000000;
	}

	div.scrollpane {
		height: 600px;
		overflow: auto;
		border: 1px solid #666;
		background-color: #ccc;
		padding: 8px;
	}
	</style>
	<script src=\"../js/prototype.js\"></script>
	<script>

	var file_hed=\"$file_hed\"
	var file_img=\"$file_img\"
	var n_images=\"$n_images\"
	var updateheader=\"$updateheader\"\n";
	if (is_array($plist)) {
		$javascript.="imgArray = new Array()\n";
		foreach ($plist as $p) {
			$javascript.="imgArray.push(\"$p[p]\");";
		}
		$javascript.="
		function displaystack(imgArray, startImg, endImg, force) {
			var wholemap = $('wholemap')
			var i=0
			for(i = startImg; i <= endImg; i++) {
				var tileId = addTile(wholemap, imgArray[i], force)
			}
		}\n";
  	}

	else {
		$javascript.="
		function displaystack(startImg, endImg, force) {
			var wholemap = $('wholemap')
			var i=0
			for(i = startImg; i <= endImg; i++) {
				var tileId = addTile(wholemap, i, force)
			}
		}\n";
	}

	$javascript.= "
	function addTile(wholemap, i, force) {
		binning = $('binning').value
		t = $('quality').value
		var tileId = \"img\"+i
		var filename = 'getstackimg.php?'
				+'hed='+file_hed
				+'&img='+file_img
				+'&n='+i
				+'&t='+t
				+'&b='+binning
				+'&uh='+updateheader

		var img = $(tileId)
		if(!img || force){
			img = document.createElement(\"img\")
			img.src = filename
			img.setAttribute(\"id\", tileId)
			img.setAttribute(\"class\", \"imgtile\")
			wholemap.appendChild(img)
		}

		return tileId
	}

	function load() {
		clean()
		startImg=parseInt($('startimg').value)
		endImg=parseInt($('endimg').value)
		if (endImg > n_images-1) {
			endImg=n_images-1
		}
		force=1
		displaystack(\n";
		if (is_array($plist)) $javascript.="imgArray, ";
		$javascript.="startImg, endImg, force) 
	}

	function clean() {
		var wholemap = $('wholemap')
		var allTiles = wholemap.getElementsByTagName('img')
		for(i = 0; i < allTiles.length; i++) {
			var id = allTiles[i].getAttribute('id')
			wholemap.removeChild(allTiles[i])
			i-- 
		}
	}

	function setImage() {
		window.document.myf.submit(); 
	}

	</script>\n";
	return $javascript; 
}

function submitJob($command,$outdir,$jobfile,$expId,$testimg=False) {
	$particle=new particleData();

	$host = 'guppy';
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	if ($testimg){
		//submit directly to head node on cluster if testing 1 image
		$cmd = "mkdir -p $outdir; cd $outdir; $command; exit;";
		$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
		return;
	}

	else {
		// create job file
		$jobid=$particle->insertClusterJobData($host,$outdir,'',$outdir,$jobfile,$expId,$user);
		$jobtext .= "#PBS -l nodes=1:ppn=1\n";
		$jobtext .= "#PBS -r n\n\n";
		$jobtext .= "updateAppionDB.py $jobid R\n\n";
		$jobtext .= "$command\n";
		$jobtext .= "updateAppionDB.py $jobid D\n\n";
		$jobtext .= "exit\n"; 
	
		// write jobfile to tmp dir on cronus3
		$randstr = randomString(16);
		$tmpfile = "/tmp/$randstr.txt";
		$f = fopen($tmpfile,'w');
		fwrite($f,$jobtext);
		fclose($f);

		// copy file to run directory
		$cmd = "mkdir -p $outdir; cp $tmpfile $outdir/$jobfile;\n";
		exec_over_ssh($_SERVER['HTTP_HOST'],$user,$pass,$cmd, True);
	
		writeTop("Appion Job Submission","Appion Job Submission");
		echo "<table width='600'>\n";
		echo "<tr><td>Appion Directory</td><td>$outdir</td></tr>\n";
		echo "<tr><td>Job File Name</td><td>$jobfile</td></tr>\n";
		$cmd = "cd $outdir; qsub $jobfile;\n";
		// submit job on cluster
		$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
		$jobnum=trim($jobnum);
		$jobnum = ereg_replace('\.'.$host.'.*','',$jobnum);
		if (!is_numeric($jobnum)) {
			echo "</table><p>\n";
			echo "ERROR in job submission.  Check the cluster\n";
			writeBottom();
			exit;
		}
		// insert cluster job id into row that was just created
		$particle->updateClusterQueue($jobid,$jobnum);

		echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
		echo "</table>\n";

		// check jobs that are running on the cluster
		echo "<p>Jobs currently running on the cluster:\n";
		$subjobs = checkClusterJobs($host,$user,$pass);
		if ($subjobs) {echo "<pre>$subjobs</pre>\n";}
		else {echo "<font color='red'>No Jobs on the cluster, check your settings</font>\n";}
#	echo "<p><a href='checkappionjobs.php?expId=$expId'>[Check Status of Jobs Associated with this Experiment]</a><p>\n";
		echo "<p><font color='red'>Do not hit 'reload' - it will re-submit job</font><p>\n";
		writeBottom(True, True);
		exit;
	}
}

function writeTestResults($jpg,$ccclist,$bin){
        echo"<center>\n";
        echo"<a href='loadimg.php?filename=$jpg' target='blank'>\n";
        echo"<img src='loadimg.php?filename=$jpg&s=256'></a>\n";
        if (count($ccclist)>1) echo "<BR>\n";
        foreach ($ccclist as $ccc){
                echo"<a href='loadimg.php?filename=$ccc' target='blank'>\n";
                echo"<img src='loadimg.php?filename=$ccc&s=256'></a>\n";
        }
        echo"</center>\n";
}

function randomString($length) {
	$s = md5(time());
	$i = 32-$length;
	$randstring=substr($s,rand(0,$i),$length);
	return $randstring;
}

function bashcolor2html($str) {
	$chr27=chr(27);
	$str=trim($str);
	$str=preg_replace("/$chr27/", 'e',$str);
	$str=preg_replace('/;/', 'me[',$str);
	preg_match_all('/(e\[[0-9]{1,2}m)/', $str, $matches);
	$htmlstyles=array();
	foreach ((array)$matches[1] as $code) {
		if (!empty($code)) {
			$codeescaped=preg_replace('/\[/','\\[',$code);
			$str=preg_replace("/$codeescaped/", '',$str);
			$htmlstyles[]=getHtmlStyle($code);
		}
	}
	$style='style="'.implode(';', $htmlstyles).'"';
	$html='<font '.$style.'>'.$str.'</font>';
	return $html;
}

function getHtmlStyle($code) {
	$codes['e[1m']='font-weight:bold';
	$codes['e[0m']='';
	$codes['e[4m']='text-decoration: underline';
	$codes['e[7m']='';
	$codes['e[30m']='color:black';
	$codes['e[31m']='color:red';
	$codes['e[32m']='color:green';
	$codes['e[33m']='color:yellow';
	$codes['e[34m']='color:blue';
	$codes['e[35m']='color:magenta';
	$codes['e[36m']='color:cyan';
	$codes['e[37m']='color:white';
	$codes['e[40m']='background-color:black';
	$codes['e[41m']='background-color:red';
	$codes['e[42m']='background-color:green';
	$codes['e[43m']='background-color:yellow';
	$codes['e[44m']='background-color:blue';
	$codes['e[45m']='background-color:magenta';
	$codes['e[46m']='background-color:cyan';
	$codes['e[47m']='background-color:white';
	return $codes[$code];
}
?>
