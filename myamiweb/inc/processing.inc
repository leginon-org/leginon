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
  <link rel='stylesheet' type='text/css' href='css/viewer.css'> 
  <link rel='stylesheet' type='text/css' href='css/view.css'>
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
