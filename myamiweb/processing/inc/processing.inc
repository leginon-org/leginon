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
  if (is_array($PROCESSING_HOSTS))
		return $PROCESSING_HOSTS;
	return array();
}

function getHostForm() {
	$h=array();
	$current_host=$_SESSION['processinghost'];
	$proc_list = (array)getHosts();
	// only list hosts if there are more than 1
	if (count($proc_list) > 1){
		foreach ($proc_list as $host) {
			$s=($host==$current_host) ? "selected" : "";
			$h[]="<option $s >$host</option>\n";
  		}
		$html="<select name=\"processinghost\">\n";
		$html.=join("\n",$h);
		$html.="</select>";
	}
	else $html="<input type='hidden' name=\"processinghost\" value='$proc_list[0]'>\n";
	return $html;
}

function getSubmitForm($name="Run", $displayhost=true, $warning=false) {
	$html="<input type='submit' name='process' value='Just Show Command' onclick='pleasewait()'>\n";
	if ($displayhost && $_SESSION['username']) {
		$html.=getHostForm();
	}
	if ($_SESSION['loggedin']) {
		$html.="  <input type='submit' name='process' value='$name' onclick='pleasewait()'>\n";
	}
	if ($warning) {
		$html.="<br/><font class='apcomment'>Submission will NOT run, only output a command that you can copy and paste into a unix shell</font>";
	}
	return $html;
}

// write popup function 'a href'
function docpop($key,$text) {
	return "<a href='#' id='l".$key."' onMouseOver='popLayer(\"".$key."\",\"l".$key."\")' onMouseOut='hideLayer()'>$text</a>\n";
}

function getStackSize($stackdata) {
	if (substr($stackdata['name'], -4) == ".hed")
		$stackimgfile = $stackdata['path']."/".substr($stackdata['name'], 0, -4).".img";
	else
		$stackimgfile = $stackdata['path']."/".$stackdata['name'];
	if (file_exists($stackimgfile)) {
		if (filesize($stackimgfile) > 1073741824)
		  	$size = sprintf("%.2f GB", filesize($stackimgfile)/1073741824);
		else
			$size = sprintf("%.1f MB", filesize($stackimgfile)/1048576);
	}
	return $size;
}

function apdivtitle($title) {
	$htmlstr = '
	<div style="padding: 4px; border:1px solid black; background-color:#b5d0df; font-size:10pt;" >
	<b>'.$title.'</b> 
	</div>
	';
	return $htmlstr;
}

function processing_header($title,$heading=false,$headerstuff=false,$pleaseWait=false) {
	global $PROJECT_URL;
	$expId = $_GET['expId'];

	// check if logged in
	if ($_POST['login']) {
		$errors = checkLogin();
	}
	
	$leginondata = new leginondata();
	$particle = new particledata();
	$projectdata = new project();
	$projectId=getProjectFromExpId($expId);
	if ($_POST['projectId'] && empty($expId)) {
		$projectId = $_POST['projectId'];
	}
	$_SESSION['projectId'] = $projectId;

	// Collect session info from database
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessions=$sessiondata['sessions'];
	$currentproject = $projectdata->getProjectInfo($projectId);

	// Show project & session pulldowns
	$sessionDescr="<font size=+1><b>".$sessioninfo['Name']."</b></font> - ".$sessioninfo['Purpose'];
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$projectId.'">'.$currentproject['name'].'</a>';
	$session_link= '<a class="header" target="viewer" href="../imageviewer.php?expId='.$expId.'">'.$sessionDescr.'</a>';
	$misc = $particle->getMiscInfoFromProject ($projectId);
	$proj_link.=($misc) ? "<a href='viewmisc.php?projId=$projectId'>[Related Images, Movies, etc]</a>" : ""; 
	$expinfo = $leginondata->getSessionInfo($expId);

	$html="<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN'  'http://www.w3.org/TR/html4/strict.dtd'>
<html>
<head>
<title>".$title."</title>
<link rel='stylesheet' type='text/css' href='../css/viewer.css'>
<link rel='stylesheet' type='text/css' href='css/proc.css'>
<link rel='stylesheet' type='text/css' href='../css/lvmenu.css'>\n";
	// javascript for please wait div to show up on submit
	if ($pleaseWait) $html.= pleaseWaitJava();
	$html.= $headerstuff;
	$html.= "<script src='../js/lvmenu.js'></script>\n";
	$html.= "</head>\n";
	$html.= "<body onload='initmenu()'>\n";
	$html.= "<div id='apheader'>\n"; // open apheader div
	$html.= "<div class='aptopbar'>\n"; // open topbar div
	$html.= "</div>\n"; // close topbar div
	$html.= "<hr />\n";
	$html.= "<div class='middlebar'>\n"; // open middlebar div
	$html.= "<div style='float: right; padding:10px'>\n"; // open
							      // login div
	if ($_SESSION['username']) {
		$html.='<i>logged in as <b>'.$_SESSION['username'].'</b></i>'."\n";
		$html.='<a class="header" href="endsession.php?expId='.$_GET['expId'].'">[Log Out]</a>'."\n";
		$_SESSION['loggedin']=true;
	}
	else {
		$expId=$_GET['expId'];
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
		$html.=displayLogin($formAction);
	}

	$html.= "</div>\n"; // close login div
	$html.= "<div style='padding:5px; padding-left:20px; font-size: 15pt'>\n"; // open title div
	$html.= "<img style='vertical-align:middle' src='img/topbarbackgrnd.jpg'>\n";
	$html.= "<font color='#fff'>".$heading."</font>\n";
	$html.= "</div>\n"; // close title div
	$html.= "</div>\n"; // close middlebar div
	$html.= "<hr />\n";
	$html.= "<div class='apbottombar'>\n";  // open bottombar div
	$html.= "<div class='apbottomcontent'>\n"; // open
						   // bottomcontent div
	$html.= "<ul>\n";
	$html.= "<div style='float: right; padding-right:10px;'>\n";
	$html.= "<a href='procsummary.php?expId=$expId'>[Appion Stats]</a>\n";
	$html.= "</div>\n";
	$html.= "<li><b>Project:</font></b> ".$proj_link."</li>\n";
	$html.= "<li><b>Session:</b> ".$session_link."</li>\n";
	$html.= "<li><b>Image Path:</b> ".$expinfo['Image path']."</li>\n";

	$html.= "</ul>\n";
	$html.= "</div>\n"; // close bottomcontent div
	$html.= "<div style='float: right'>\n"; // open right content div
	$html.= "</div>\n"; // close right content div
	$html.= "</div>\n"; // close bottombar div
	$html.= "<hr />\n";
	$html.= "<div class='apshadow'>\n"; // open shadow div
	$html.= "&nbsp;\n";
	$html.= "</div>\n"; // close shadow div
	$html.= "</div>\n"; // close apheader div

	// --- for help popup documentation --- //
	$helpdiv = "<div id='dhelp' class='aphelpdoc' onmouseover='overdiv=1;' onmouseout='overdiv=0;'></div>\n";
	$html.=$helpdiv;

	require "menuprocessing.php";
	$html.= $menujs;
	$html.= $menulink;
	$html.='
<div id="content" style="padding-left: 5px">

<div style="position: relative; float:left; margin-right:10px" id="leftcontent">
    <div class="lvmenu">'
		.$menuprocesing
		.'</div>
</div>
<table border="0" cellpadding="0" cellspacing="0"><tr><td>
<div id="maincontent" style="z-index:0; width:auto; text-align:left; ">';

	// div for the 'please wait' box to show when processing
	if ($pleaseWait) {
		$html.= "<div id='pleasewaitScreen' style='position:absolute;z-index:5;top:30%;left:35%;visibility:hidden;'>\n";
		$html.= "<table border='1' bordercolor='#000000' cellpadding='0' cellspacing='0' height='200' width='300'>\n";
		$html.= "<tr><td width='100%' height='100%' bgcolor='#ffffff' align='center' valign='middle'>\n";
		$html.= "<b>Processing, Please wait...</b>\n";
		$html.= "<br />\n";
		$html.= "<img src='img/ajax-loader.gif' border='0'>\n";
		$html.= "</td></tr>\n";
		$html.= "</table>\n";
		$html.= "</div>\n";
	}
	echo $html;

	// return all the menu data
	return $data;
}

function processing_footer() {
	$html='<p>
		</div>
		</td></tr></table>
	</div>
	</body>
</html>';
	echo $html;
}

function writeTop($title,$heading=false,$headerstuff=false) {
	global $PROJECT_URL;
	$expId = $_GET['expId'];
	$leginondata = new leginondata();
	$particle = new particledata();
	$projectId=getProjectFromExpId($expId);

	// Collect session info from database
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessions=$sessiondata['sessions'];
	$currentproject=$sessiondata['currentproject'];

	// Show project & session pulldowns
	$sessionDescr="<font size=+1><b>".$sessioninfo['Name']."</b></font> - ".$sessioninfo['Purpose'];
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$projectId.'">'.$currentproject['name'].'</a>';
	$session_link= '<a class="header" target="viewer" href="../imageviewer.php?expId='.$expId.'">'.$sessionDescr.'</a>';
	$misc = $particle->getMiscInfoFromProject ($projectId);
	$proj_link.=($misc) ? "<a href='viewmisc.php?projId=$projectId'>[Related Images, Movies, etc]</a>" : ""; 
	$expinfo = $leginondata->getSessionInfo($expId);

$html='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"  "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<title>'.$title.'</title>
<link rel="stylesheet" type="text/css" href="../css/viewer.css">
<link rel="stylesheet" type="text/css" href="../css/view.css">
<link rel="stylesheet" type="text/css" href="css/proc.css">
<link rel="stylesheet" type="text/css" href="../css/lvmenu.css">
<script src="../js/lvmenu.js"></script>
'.$headerstuff.'
</head>
<style>
	ul {
      margin:     0;
      padding:    0;
      list-style: none inside;
   }
	input {
		border: 1px solid #aabbcc;
	}

</style>
<body>
<div id="apheader">
  <div class="aptopbar"> </div>
  <hr />
  <div class="middlebar">
<div style="float: right; padding:10px">';
if ($_SESSION['username']) {
		$html.="      <i>logged in as <b>$_SESSION[username]</b></i>\n";
		$html.="      <a class='header' href='endsession.php?expId=$_GET[expId]'>[Log Out]</a>\n";
		$_SESSION['loggedin']=True;
} else {
	$expId=$_GET['expId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$html.=displayLogin($formAction);
}

$html.='
    </div>
<div style="padding:5px; padding-left:20px; font-size: 15pt">
	<img style="vertical-align:middle" src="img/topbarbackgrnd.jpg">
	<font color="#fff">'.$heading.'</font>
</div>
  </div>
  <hr />
  <div class="apbottombar">
<div class="apbottomcontent">
<ul>
<li><b>Project:</b> '.$proj_link.'</li>
<li><b>Session:</b> '.$session_link.'</li>
<li><b>Image Path:</b> '.$expinfo['Image path'].'</li>
</ul>
	</div>
	<div style="float: right"> 
   </div>
</div>

<hr />
  <div class="apshadow">
    &nbsp;
  </div>
</div>';
	// for help popup documentation
	$helpdiv = "<div id='dhelp' class='aphelpdoc' onmouseover='overdiv=1;' onmouseout='overdiv=0;'></div>\n";
	$html.=$helpdiv;
	echo $html;

}

function writeTop_org($title,$heading=false,$headerstuff=false) {
	global $PROJECT_URL;
	global $_GET;
	$expId = $_GET['expId'];
	$leginondata = new leginondata();
	$particle = new particledata();
	$projectId=getProjectFromExpId($expId);

	// Collect session info from database
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessions=$sessiondata['sessions'];
	$currentproject=$sessiondata['currentproject'];

	// Show project & session pulldowns
	$sessionDescr="<font size=+1><b>".$sessioninfo['Name']."</b></font> - ".$sessioninfo['Purpose'];
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$projectId.'">'.$currentproject['name'].'</a>';
	$session_link= '<a class="header" target="viewer" href="../imageviewer.php?expId='.$expId.'">'.$sessionDescr.'</a>';
	$misc = $particle->getMiscInfoFromProject ($projectId);

	
  	echo "<html>\n";
	echo "<head>\n";
	echo "<title>$title</title>\n";
	echo "<link rel='stylesheet' type='text/css' href='../css/viewer.css'> \n";
	echo "<link rel='stylesheet' type='text/css' href='../css/view.css'>\n";
	echo "<link rel='stylesheet' type='text/css' href='css/proc.css'>\n";
	echo "<script src='../js/viewer.js'>\n";
	echo "</script>\n";
	echo "$headerstuff\n";
	echo "</head>\n";
	echo "<body>\n";
	echo "<center>\n";
	echo "<!-- header -->\n";
	echo "<div id='apheader'>\n";
	echo "  <div class='aptopbar'>\n";

	if ($_SESSION['username']) {
		echo "    <div class='aplogged'>\n";
		echo "      <i>logged in as <b>".$_SESSION['username']."</b></i>\n";
		echo "    </div>\n";
		echo "    <div class='aplogout'>\n";
		echo "      <a class='header' href='endsession.php?expId=$_GET[expId]'>[Log Out]</a>\n";
		$_SESSION['loggedin']=True;
	}
	else {
		$expId=$_GET['expId'];
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
		echo "    <div class='aplogin'>\n";
		displayLogin($formAction);
	}
	echo "    </div>\n";
	echo "  </div>\n";
	echo "  <hr />\n";
	echo "  <div class='middlebar'>\n";
	echo "    <div class='aptitle'>\n";
	echo "      <table border='0' cellpadding='5' cellspacing='0'>\n";
	echo "      <tr><td valign='middle'><img src='img/topbarbackgrnd.jpg'></td>\n";
	echo "	    <td valign='middle'>$heading</td></tr>\n";
	echo "      </table>\n";
	echo "    </div>\n";
	echo "  </div>\n";
	echo "  <hr />\n";
	echo "  <div class='apbottombar'>\n";
	echo "    <div class='apbottomcontent'>\n";
	// --- display Project / Session / Path table info --- //
	$ptable[]=array(
			'c1'=>'<b>Project:</b>',
			'c2'=>$proj_link,
			'c3'=>($misc) ? "<a href='viewmisc.php?projId=$projectId'>[Related Images, Movies, etc]</a>" : "" 
				); 
	$ptable[]=array(
			'c1'=>'<b>Session:</b>',
			'c2'=>$session_link
			);

	// get experiment information
	if ($expinfo = $leginondata->getSessionInfo($expId)) {
		$ptable[]=array(
				'c1'=>'<b>Image Path:</b>',
				'c2'=>$expinfo['Image path']
				);
	}
	echo "<div class='aplogged'>".array2table($ptable, array(), false, "");
	echo "</div>";
		echo "<div class='aplogout'>      <a class='header' href='endsession.php?expId=$_GET[expId]'>[Log Out]</a></div>\n";
	echo "    </div>\n";
	echo "  </div>\n";
	echo "  <hr />\n";
	echo "  <div class='apshadow'>\n";
	echo "    &nbsp;\n";
	echo "  </div>\n";
	echo "</div>\n";
	// for help popup documentation
	$helpdiv = "<div id='dhelp' class='aphelpdoc' onmouseover='overdiv=1;' onmouseout='overdiv=0;'></div>\n";
	echo $helpdiv;

}

function writeBottom($showproclink=True){
	global $_GET;
	echo "<p>\n";
	if ($showproclink && $_GET['expId']) {
		echo "<table border='0' cellpadding='0' cellspacing='0'>\n";
		echo "<tr>\n";
		echo "<td valign='center'>\n";
		echo "<a href='index.php?expId=$_GET[expId]' class='header'>\n";
		echo "<img border='0' src='img/leftendButton.gif'>\n";
		echo "</a>\n";
		echo "</td>\n";
		echo "<td align='center' valign='center' background='img/middleButton.gif'>\n";
		echo "<a href='index.php?expId=$_GET[expId]' class='header'><font size='-2'>Back to Processing Page</font></a>\n";
		echo "</td>\n";
		echo "<td valign='top'>\n";
		echo "<img border='0' src='img/rightendButton.gif'>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "</table>\n";
	}
	echo "</center>\n";
	echo "</body>\n";
	echo "</html>\n";
}

function displayLogin($formAction) {
	$html='<form name="loginform" method="post" action="'.$formAction.'">
Username: <input type="text" name="username" value="'.$_POST['username'].'">
Password: <input type="password" name="password">
<input type="submit" name="login" value="Log In">
</form>';  
	return $html;
}

function checkLogin() {
  // if everything is cool, then return nothing
  if (!$_SESSION['username']) {
    if (!$_POST['username'] || !$_POST['password']) return("ERROR: enter your user name and password");
    // authenticate username & password
    if (!check_ssh($_SERVER['SERVER_ADDR'],$_POST['username'],$_POST['password'])) return("ERROR: authentication failed");
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
	echo "Retired function, displayExperimentForm() ---- You should redirect this call to getSessionList(projectId,sessionId)!!!!!";
	global $PROJECT_URL;
	// Collect session info from database
	$sessiondata=getSessionList($projectId,$sessionId);
// 	$sessions=$sessiondata['sessions'];
// 	$currentproject=$sessiondata['currentproject'];

// 	if ($expId){
// 		$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL
// 			."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
// 		$sessionDescr=$sessiondata['info']['Purpose'];
// 		$session_link="<a class='header' target='project' href='../3wviewer.php?expId=$expId'>$sessionDescr</a>";
// 		echo "Project: $proj_link<br />\nSession: $session_link\n";

// 	} else {

// 		echo"
// 		<b>Select Session:</b><br />
// 		<select name='projectId' onchange='newexp()'>\n";
// 		$projects=getProjectList();
// 		foreach ($projects as $k=>$project) {
// 			$sel = ($project['id']==$projectId) ? "selected" : '';
// 			echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
// 		}
// 		echo"
// 		</select>
// 		<br />
// 		<select name='sessionId' onchange='newexp()'>
// 		<option value=''>all sessions</option>\n";
// 		foreach ($sessions as $k=>$session) {
// 			$sel = ($session['id']==$sessionId) ? 'selected' : '';
// 			$shortname=substr($session['name'],0,90);
// 			echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>\n";
// 		}
// 		echo"</select>\n";
// 	}
	return $sessiondata;
}

function checkClusterJobs($host, $user, $pass) {
	$cmd='qstat -a | grep '.$user;
	$subjobs = exec_over_ssh($host,$user,$pass,$cmd,true);
	return $subjobs;
}

function checkRequiredFileError($path,$filename) {
	if (substr($path,-1,1)!='/') $path.='/';
	$file = $path.$filename;
	if (file_exists($file)) {
		if (filesize($file) > 0) {
			return false;
		} else {
			return '<B>ERROR:</B> empty '.$file;
		}
	} else {
		return '<B>ERROR:</B> '.$file.' not exist';
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

function stackViewer($file_hed,$file_img,$n_images,$stackoptions=array()) {
	$optionkeys = array ('updateheader', 'plist', 'stackinfoindex');
	$plist=false;
	$updateheader=false;
	$stackinfoindex=0;
	foreach ((array)$stackoptions as $k=>$v) {
		if (in_array($k, $optionkeys)) {
			$$k = $v;
		}
	}
	$javascript = "
  <style type='text/css'>
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
	var updateheader=\"$updateheader\"
	var stackinfoindex=\"$stackinfoindex\"
	var excludeimages=Array()
	var selectimages=Array()
	var n_tiles=0
	var lastselectedimage\n";
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
			n_tiles=i
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
			n_tiles=i
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

		if (typeof stackinfo == 'object' && stackinfo[i]) {
			filename +='&i='+stackinfo[i]
		}

		if (stackinfoindex) {
			filename +='&k='+stackinfoindex
		}

		var img = $(tileId)
		if(!img || force){
			img = document.createElement(\"img\")
			img.src = filename
			img.setAttribute(\"id\", tileId)
			img.setAttribute(\"class\", \"imgtile\")
			img.setAttribute(\"onclick\", \"setSelection(\"+i+\",\"+tileId+\")\")
      wholemap.appendChild(img)
   }

		return tileId
	}

	function setSelection(id, img) {
		if (mode=='exclude') {
			c=excludeImage(id)
			if(c!=-1) { 
				img.style.border='1px solid #f00'
				img.style.opacity=0.5
			} else {
				img.style.border=''
				img.style.opacity=''
			}
			if (typeof addexcludefn== 'function') {
				addexcludefn()
			}
		}
		if (mode=='select') {
			c=selectImage(id)
			img.style.border=(c!=-1) ? '1px solid #0f0' : ''
			if (typeof addselectfn== 'function') {
				addselectfn()
			}
		}
		if (o=$('excludedIndex')) {
			o.value=getExcludeImages()
		}
		if (o=$('selectedIndex')) {
			o.value=getSelectImages()
		}
	}

	function selectImage(id) {
		var cindex=selectimages.length
		for(var i=0; i<selectimages.length; i++) {
			if (selectimages[i]==id) {
				cindex=i
				id=-1
				break
			}
		}
		selectimages[cindex]=id
		return id
	}

	function select2exclude() {
		var selected=false
		for(var j=0; j<n_tiles; j++) {
			selected=false
			for(var i=0; i<selectimages.length; i++) {
				if (selectimages[i]==j) {
					selected=true
				}
			}
			excludeimages[j]=(selected) ? -1 : j
		}
	}

	function getSelectImages() {
		var a=Array();
		for(var i=0; i<selectimages.length; i++) {
			if (selectimages[i]!=-1) {
				a[a.length]=selectimages[i]
			}
		}
		if (a.length) {
			lastselectedimage=a[a.length-1]
		}
		return a.toString()
	}

	function getLastSelectedImage() {
		return lastselectedimage
	}

	function getExcludeImages() {
		var a=Array();
		for(var i=0; i<excludeimages.length; i++) {
			if (excludeimages[i]!=-1) {
				a[a.length]=excludeimages[i]
			}
		}
		return a.toString()
	}

	function excludeImage(id) {
		var cindex=excludeimages.length
		for(var i=0; i<excludeimages.length; i++) {
			if (excludeimages[i]==id) {
				cindex=i
				id=-1
				break
			}
		}
		excludeimages[cindex]=id
		return id
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

	function resetSelection() {
		selectimages=Array()
		excludeimages=Array()
		for(var id=0; id<n_tiles; id++) {
			var img = $('img'+id)
			if(s=img.style) {
				s.border=''
				s.opacity=''
			}
		}
	}

	var mode='exclude'
	function setMode(){
		resetSelection()
		if (o=$('mode')) {
			if (mode=='select') {
				o.style.border='1px solid #F00'
				mode='exclude'
			} else {
				o.style.border='1px solid #0F0'
				mode='select'
			}
			o.value=mode
		}
	}

	</script>\n";
	return $javascript; 
}

function getNumberOfProcsPerNode() {
	return 8;
}

function getNumberOfRequiredNodes($nproc, $ppn) {
	if ($nproc < $ppn)
		return array(1, $nproc);
	$nodes = (int) ceil($nproc/$ppn);
	$ppn = (int) ceil($nproc/$nodes);
	return array($nodes, $ppn);
}

function submitAppionJob($command, $outdir, $runname, $expId, $jobtype,
		$testimg=False, $xvfb=False, $xtra=False, $nproc=1, $ppn=0, $nodes=0) {
	$particle=new particleData();

	if ($_POST['processinghost']) {
		$_SESSION['processinghost']=$_POST['processinghost'];
	}
	$host = $_SESSION['processinghost'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// check if database is configured on processing host
	$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"leginondata\")'";
	$dbcheck = exec_over_ssh($host,$user,$pass,$cmd,True);
	if (trim($dbcheck)=='') return "sinedon is not configure for leginondata";
	$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"appionData\")'";
	$dbcheck = exec_over_ssh($host,$user,$pass,$cmd,True);
	if (trim($dbcheck)=='') return "sinedon is not configure for appionData";

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runname;

	// AMI SPECIFIC
	// if not data00 or data16, write to data00
	if (!ereg("/ami/data(00|16)",$procdir)) {
		return "could not create directory '$procdir'<br/> try using data00 or data16";
		$procdir = ereg_replace("/ami/data..","/ami/data00",$procdir);
	}

	// if more than one job running in the directory (like
	// classification of ref free)
	if ($xtra) $runname = "$runname.$xtra";

	// set names of cluster job file and output log
	$jobfile = "$runname.appionsub.job";
	$logfile = "$runname.appionsub.log";

	if (is_array($command)) {
		$apcmd = array();
		foreach ($command as $cmd) {
			$filtcommand = ereg_replace("\'","", $cmd);;
			$apcmd[] = "webcaller.py '".$filtcommand."' $procdir/$logfile"."\n";
		}
	}
	else {
		// create appion command
		$filtcommand = ereg_replace("\'","", $command);
		//$filtcommand = preg_replace("/[\n\r]/", " -- ", $filtcommand);
		$apcmd = "webcaller.py '".$filtcommand."' $procdir/$logfile";
	}

	$cmd = "mkdir -p $procdir;";
	//$temp = exec_over_ssh($host, $user, $pass, $cmd, True);
	$temp = exec_over_ssh($_SERVER['SERVER_ADDR'], $user, $pass, $cmd, True);
	//mkdir($procdir, 0777, true); //gives permissions to apache :(
	$checkcount = 0;
	while (!file_exists($procdir) && $checkcount < 5) {
		sleep(1);
		$checkcount++;
	}
	if (!file_exists($procdir))
		return "could not create directory '$procdir'<br/>check folder permissions";
	if ($testimg){
		//submit directly to head node on cluster if testing 1 image
		$cmd .= "cd $procdir; $apcmd; exit;";
		// this shouldn't be necessary -- neil, it is done in python
		//if ($xvfb) $cmd = "Xvfb :25 -ac -pn -screen 0 800x800x8  -fp /usr/share/X11/fonts/misc -sp /usr/lib64/xserver/SecurityPolicy -co /usr/share/X11/rgb &; $cmd; kill %1;";
		$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
		return;
	} else {
		// get proper node numbers
		if ($ppn < 1)
			$ppn = getNumberOfProcsPerNode();
		if ($nodes < 1)
			list($nodes, $ppn) = getNumberOfRequiredNodes($nproc, $ppn);

		// create job file
		$jobid=$particle->insertClusterJobData($host,$procdir,'',$procdir,$jobfile,$expId,$jobtype,$user);
		$jobtext .= "#PBS -l nodes=$nodes:ppn=$ppn\n";
		$jobtext .= "#PBS -l walltime=120:00:00\n";
		$jobtext .= "#PBS -l cput=960:00:00\n";
		$jobtext .= "#PBS -j oe\n";
		$jobtext .= "#PBS -r n\n\n";
		$dbprojectid = getProjectFromExpId($expId);
		$projectid = $_SESSION['projectId'] ? $_SESSION['projectId'] : "";
		if ($dbprojectid != $projectid)
			return "project id from expId ($expId -> $dbprojectid) does not match project id from web browser ($projectid)";
		$jobtext .= "updateAppionDB.py $jobid R $projectid\n\n";

		// create virtual window for matlab images
		// this shouldn't be necessary -- neil, it is done in python
		//if ($xvfb) $jobtext .= "Xvfb :25 -ac -pn -screen 0 800x800x8  -fp /usr/share/X11/fonts/misc -sp /usr/lib64/xserver/SecurityPolicy -co /usr/share/X11/rgb &\n";
		if (is_array($command)) {
			foreach ($apcmd as $iteration) {
				$jobtext .= "$iteration\n";
			}
		}
		else $jobtext .= "$apcmd\n";
		$jobtext .= "\nupdateAppionDB.py $jobid D $projectid\n\n";
		$jobtext .= "exit\n"; 
	
		// write jobfile to tmp dir on cronus3
		$randstr = randomString(16);
		$tmpfile = "/tmp/$randstr.txt";
		$f = fopen($tmpfile,'w');
		fwrite($f,$jobtext);
		fclose($f);

		// copy file to run directory
		$cmd .= "cp $tmpfile $procdir/$jobfile;\n";
		exec_over_ssh($_SERVER['SERVER_ADDR'], $user, $pass, $cmd, True);

		processing_header("Appion Job Submission","Appion Job Submission");
		echo "<table width='600'>\n";
		echo "<tr><td>Appion Directory</td><td>$procdir</td></tr>\n";
		echo "<tr><td>Job File Name</td><td>$jobfile</td></tr>\n";
		echo "<tr><td>Hostname</td><td>$host</td></tr>\n";
		echo "<tr><td>Username</td><td>$user</td></tr>\n";
		echo "<tr><td>Local server ip</td><td>".$_SERVER['SERVER_ADDR']."</td></tr>\n";
		echo "<tr><td>Project Id</td><td>".$_SESSION['projectId']."</td></tr>\n";
		$cmd = "cd $procdir; qsub $jobfile;\n";

		// submit job on cluster
		$jobdata = exec_over_ssh($host, $user, $pass, $cmd, True);

		ereg("([0-9]{1,})", $jobdata, $regs);
		$jobnum = $regs[1];
		if (!is_numeric($jobnum)) {
			echo "</table><p>\n";
			echo "ERROR in job submission. Check the cluster\n".$jobdata."\n".$regs."\n";
			writeBottom();
			exit;
		}
		// insert cluster job id into row that was just created
		$particle->updateClusterQueue($jobid,$jobnum,'Q');

		echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
		echo "<tr><td>Command</td><td><font size='-3'>$filtcommand</font></td></tr>\n";
		echo "</table>\n";

		// check jobs that are running on the cluster
		echo "<p>Jobs currently running on the cluster:\n";
		$subjobs = checkClusterJobs($host,$user,$pass);
		if ($subjobs) {echo "<pre>$subjobs</pre>\n";}
		else {echo "<font color='red'>No Jobs on the cluster, check your settings</font>\n";}
		echo "<p><a href='checkAppionJob.php?expId=$expId&jobId=$jobid'>[Check status of this job]</a><p>\n";
		echo "<p><font color='red'>Do not hit 'reload' - it will re-submit job</font><p>\n";
		processing_footer();
		exit;
	}
}

function writeTestResults($jpg,$ccclist,$bin){
	if (!file_exists($jpg)) return "<font class='apcomment'>An Error occurred - No image was created</font><br />\n";
        $html = "<center>\n";
        $html.= "<a href='loadimg.php?filename=$jpg' target='blank'>\n";
        $html.= "<img src='loadimg.php?filename=$jpg&s=256'></a>\n";
        if (count($ccclist)>1) $html.=  "<br />\n";
        foreach ($ccclist as $ccc){
                $html.= "<a href='loadimg.php?filename=$ccc' target='blank'>\n";
                $html.= "<img src='loadimg.php?filename=$ccc&s=256'></a>\n";
        }
        $html.= "</center>\n";
	return $html;
}

function randomString($length) {
	$s = md5(time());
	$i = 32-$length;
	$randstring=substr($s,rand(0,$i),$length);
	return $randstring;
}

function getTimestring() {
	$today = getdate();
	$timestring = substr($today['year'],2,2)
		.strtolower(substr($today['month'],0,3))
		.sprintf("%02u", $today['mday'])
		.sprintf("%c", $today['hours']+97)
		.sprintf("%02u", $today['minutes']);
	return $timestring;
}

function bashcolor2html($str) {
	$chr27=chr(27);
	$str=trim($str);
	$str=preg_replace("/$chr27/", 'e',$str);
#	$str=preg_replace('/;/', 'me[',$str);
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

function editTextJava() {
	// javascript for hiding/showing edit text & form
	$javascript = "<script language='javascript' type='text/javascript'>\n";
	$javascript.= "function hideEditForm(stackid, text,cols,rows) {\n";
	$javascript.= "  var descText='descText'+stackid;\n";
	$javascript.= "  var textarea=\"<textarea name='newdescription\"+stackid+\"' cols='\"+cols+\"' rows='\"+rows+\"'>\"+text+\"</textarea><input class='edit' type='submit' name='updateDesc\"+stackid+\"' value='Update'>\";\n";
	$javascript.= "  if (document.getElementById) { // DOM3 = IE5, NS6\n";
	$javascript.= "    document.getElementById(descText).innerHTML=textarea;\n";
	$javascript.= "  }\n"; 
	$javascript.= "}\n";
	$javascript.= "</script>\n";
	return $javascript;
}

function eulerImgJava() {
	// javascript to switch the euler image
	$javascript = "<script language='javascript' type='text/javascript'>\n";
	$javascript.="	function switchEulerImg(i,img) {\n";
	$javascript.="		var eulerimage = 'eulerimg'+i;\n";
	$javascript.="		var eulerlink = 'loadimg.php?scale=.125&filename='+img;\n";
	$javascript.="		var eulerbiglink = 'loadimg.php?filename='+img;\n";
	$javascript.="		document['eulerimg'+i].src = eulerlink;\n";
	$javascript.="		document.getElementById('eulerlink'+i).href = eulerbiglink;\n";
	$javascript.="	}\n";
	$javascript.="</script>\n";
	return $javascript;
}

function editButton($editid,$text) {
	$len=(strlen($text)==0) ? 15 : strlen($text);
	$cols = ($len > 50) ? 50 : $len;
	$rows = ($cols==50) ? ceil($len/50) : 1;

	// create textarea input
	//$textbox="<textarea name=\"newdescription".$editid."\" cols=\"$cols\" rows=\"$rows\">";
	# convert single quotes to html
	$textbox.=htmlentities($text, ENT_QUOTES);

	# add edit button to description
	$editButton="<div id='descText".$editid."' style='position:relative;'>";
	$editButton.=$text;
	$editButton.=" <input class='edit' type='button' name='editdesc' value='edit' onclick=\"javascript:hideEditForm('$editid','$textbox','$cols','$rows')\">";
	$editButton.="</div>\n";
	//	$editButton.="<div id='descForm".$editid."' style='visibility:hidden; z=index:1'>";
	//	$editButton.=" <input class='edit' type='submit' name='updateDesc".$editid."' value='Update'>";
	//	$editButton.="</div>\n";
	return $editButton;
}

function updateDescription($table, $editid, $text) {
	$particle=new particledata();

	# convert html back to single quotes
	$desc = html_entity_decode($text, ENT_QUOTES);
	$desc = trim($desc);
	$particle->updateDescription($table, $editid, $desc);
}

function pleaseWaitJava() {
	$java = "<script type=\"text/javascript\" >\n";
	$java.= "function pleasewait() {\n";
	$java.= "	pleasewaitScreen=$('pleasewaitScreen');\n";
	$java.= "	pleasewaitScreen.style.visibility='visible';\n";
	$java.= "}\n"; 
	$java.= "</script>\n";
	return $java;
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

function writeJavaPopupFunctions ($help) {
	$javafunc = "
  <style type='text/css'>
    input { border-style: solid; border-color: #9dae9b; }
    select { border-style: solid; border-color: #9dae9b; }

		span.info {
			width: 100px;
		}
  </style>\n";

	$javafunc .= "
  <script type='text/javascript' src='js/help.js'></script>
  <script type='text/javascript' src='../js/prototype.js'></script>
  <script type='text/javascript' src='../js/draglayer.js'></script>
  <script type='text/javascript'>

	overdiv='0'
	var ie = (document.all)? true:false

// create the popups 
	function popLayer(a, id) {
		dhelp=$('dhelp')
		helpstr=eval('help.$help.'+a)
		if(!helpstr){helpstr='<font color=red>Missing help info</font>'}

		desc = '<div style=\'position: relative; width: 300px; padding: 1em\'>'+helpstr+'</div>'
		dhelp.innerHTML=desc;

		if (o=$(id)) {
			wh = ie ? window.document.body.clientHeight : window.innerHeight
			ww = ie ? window.document.body.clientWidth : window.innerWidth
			wwo = ie ? window.document.body.scrollLeft : window.pageXOffset

			oleft=getAbsLeft(o)
			otop=getAbsTop(o)
			if (ww+wwo-oleft<350)
				oleft -= 300
			dhelp.style.left = oleft+ 'px'
			dhelp.style.bottom= wh-otop+20 + 'px'
		}

		dhelp.style.visibility='visible'
	}

	function hideLayer(){
		dhelp=$('dhelp')
		if (overdiv == '0') {
			dhelp.innerHTML=''
			dhelp.style.visibility='hidden';
		}
	}

</script>\n";
	return $javafunc;
};

function openRoundBorder() {
	$text = "<div id='roundbox'>\n";
	$text .= "<b class='xtop'><b class='xb1'></b><b class='xb2'></b><b class='xb3'></b><b class='xb4'></b></b>\n";
	$text .= "<div class='roundboxcontent'>\n";
	$text .= "<p>\n";
	return ($text);
}

function closeRoundBorder() {
	$text = "</p>\n";
	$text .= "</div><!--/roundboxcontent-->\n";
	$text .= "<b class='xbottom'><b class='xb4'></b><b class='xb3'></b><b class='xb2'></b><b class='xb1'></b></b>\n";
	$text .= "</div><!--/roundbox-->\n";
	return ($text);
}

function showStackInfo($stackId, $stackparams, $apix, $expId, $particle) {
	$title = "stack info";
	$stackparticles = $particle->getNumStackParticles($stackId);
	$apixstr=format_angstrom_number($apix/1e10)."/pixel";
	//print_r($stackparams);
	$stackinfo = array(
	'id'=>"<a href='stackreport.php?expId=$expId&sId=$stackId'>$stackId</A>",
	'runid'=>$stackparams['stackRunName'],
	'description'=>$stackparams['description'],
	'name'=>"<a target='stackview' href='viewstack.php?expId=$expId&stackId=$stackId&file=$stackfile'>$stackparams[name]</A>",
	'path'=>$stackparams['path'],
	'num part'=>commafy($stackparticles),
	'pixel/box size'=>$apixstr."; ".$stackparams['boxSize']." pixels"
	);
	$particle->displayParameters($title,$stackinfo,array(),$expId);
	return $stackparticles;
}

function showModelInfo($model, $expId, $particle) {
	$title = "initial model info";
	//print_r($model);
	$symdata=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
	$modelname=$model['name'];
	$modelinfo = array(
	'id'=>"<a href='viewmodels.php?expId=$expId'>$model[DEF_id]</A>",
	'description'=>$model['description'],
	'path'=>$model['path']."/".$modelname,
	'symmetry'=>$symdata['symmetry'].", ".$symdata['description'],
	'pixel/box size'=>format_angstrom_number($model['pixelsize']/1e10)."/pixel; ".$model['boxsize']." pixels",
	);
	$particle->displayParameters($title,$modelinfo,array(),$expId);
	return $modelname;
}

function getPngList($dir) {
	$pngimages=array();
	$pngimages['pngfiles']=array();
	$pngimages['eulerfiles']=array();
	$eulerstr = 'euler.*\.png$';
	$refinedir = opendir($dir);
	while ($f = readdir($refinedir)) {
		if (eregi($eulerstr, $f)) $pngimages['eulerfiles'][] = $f;
		elseif (eregi('\.png$',$f)) $pngimages['pngfiles'][] = $f;
	}
	sort($pngimages['pngfiles']);
	sort($pngimages['eulerfiles']);
	return $pngimages;
}

?>
