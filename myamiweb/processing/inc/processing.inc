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
  $path = "/var/lib/wwwrun/.ssh/";
  $known_hosts = $path."known_hosts";
  $hosts = file($known_hosts);
  $result=array();
  foreach($hosts as $host) {
    list($str) = split(" ", $host);
    list($str) = split(",", $str);
    $hosts_select[]=$str;
  }	
  return $hosts_select;
}

function writeTop($title,$heading,$headerstuff=false){
  echo"<HTML>
  <HEAD>
  <title>$title</title>
  <link rel='stylesheet' type='text/css' href='../css/viewer.css'> 
  <link rel='stylesheet' type='text/css' href='../css/view.css'>
  $headerstuff
  </HEAD>
  <BODY>
  <CENTER>
  <TABLE BORDER='0'>
  <TR>
  <TD ALIGN='LEFT'>\n";
  if ($heading) echo"<H3 ALIGN='CENTER'>$heading</H3>\n";
  echo"<HR>\n";
}

function writeBottom(){
  echo"
  </TD>
  </TR>
  </TABLE>
  </CENTER>
  </BODY>
  </HTML>\n";
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
		$session_link="<a class='header' target='project' href='3wviewer.php?expId=$expId'>$sessionDescr</a>";
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