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

function writeBottom($showproclink=True){
  global $_GET;
  echo"
  </TD>
  </TR>
  </TABLE>\n";
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

function checkClusterJobs($user,$pass) {
  $cmd = 'qstat -a | grep $user';
  $subjobs = exec_over_ssh('garibaldi',$user,$pass,$cmd,True);
  return $subjobs;
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
