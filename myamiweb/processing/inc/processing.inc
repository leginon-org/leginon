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
  if (is_array($PROCESSING_HOSTS))
		return $PROCESSING_HOSTS;
	return array();
}

// write popup function 'a href'
function docpop($key,$text) {
	return "<a href='#' id='l".$key."' onMouseOver='popLayer(\"".$key."\",\"l".$key."\")' onMouseOut='hideLayer()'>$text</a>\n";
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
	$expId = $_GET['expId'];

	// check if logged in
	if ($_POST['login']) {
		$errors = checkLogin();
	}
	
	$leginondata = new leginondata();
	$particle = new particledata();
	$projectId=getProjectFromExpId($expId);

	// Collect session info from database
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessions=$sessiondata['sessions'];
	$currentproject=$sessiondata['currentproject'];

	// Show project & session pulldowns
	$sessionDescr=$sessioninfo['Name']." - ".$sessioninfo['Purpose'];
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
	$html.="<script src='../js/lvmenu.js'></script>\n";
	$html.= "</head>
<body onload='initmenu()'>
<div id='apheader'>
  <div class='aptopbar'> </div>
  <hr />
  <div class='middlebar'>
<div style='float: right; padding:10px'>\n";
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
<li><b>Project:</font></b> '.$proj_link.'</li>
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
	</div>
	</body>
</html>';
	echo $html;
}

function writeTop($title,$heading=false,$headerstuff=false) {
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
	$sessionDescr=$sessioninfo['Name']." - ".$sessioninfo['Purpose'];
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
	$sessionDescr=$sessioninfo['Name']." - ".$sessioninfo['Purpose'];
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
		echo "      <i>logged in as <b>$_SESSION[username]</b></i>\n";
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

function submitAppionJob($command,$outdir,$runid,$expId,$jobtype,$testimg=False,$xvfb=False,$xtra=False) {
	$particle=new particleData();

	$host = 'guppy';
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// first check that the user has sinedon.cfg & leginon.cfg
	// files in their guppy home directory
	$filecheck = exec_over_ssh($host,$user,$pass,'ls leginon.cfg',True);
	if (trim($filecheck)!='leginon.cfg') return "You are missing the leginon.cfg file on the cluster";
	$filecheck = exec_over_ssh($host,$user,$pass,'ls sinedon.cfg',True);
	if (trim($filecheck)!='sinedon.cfg') return "You are missing the sinedon.cfg file on the cluster";

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;

	// if more than one job running in the directory (like
	// classification of ref free)
	if ($xtra) $runid = "$runid.$xtra";

	// set names of cluster job file and output log
	$jobfile = "$runid.appionsub.job";
	$logfile = "$runid.appionsub.log";

	// create appion command
	$apcmd = "webcaller.py '$command' $procdir/$logfile";

	$cmd = "mkdir -p $procdir;";
	if ($testimg){
		//submit directly to head node on cluster if testing 1 image
		$cmd .= "cd $procdir; $apcmd; exit;";
		if ($xvfb) $cmd = "Xvfb :25 -ac -pn -screen 0 800x800x8  -fp /usr/share/X11/fonts/misc -sp /usr/lib64/xserver/SecurityPolicy -co /usr/share/X11/rgb &; $cmd; kill %1;";
		$jobnum = exec_over_ssh($host, $user, $pass, $cmd, True);
		return;
	}

	else {
		// create job file
		$jobid=$particle->insertClusterJobData($host,$procdir,'',$procdir,$jobfile,$expId,$jobtype,$user);
		$jobtext .= "#PBS -l nodes=1:ppn=1\n";
		$jobtext .= "#PBS -l walltime=240:00:00\n";
		$jobtext .= "#PBS -l cput=240:00:00\n";
		$jobtext .= "#PBS -r n\n\n";
		$jobtext .= "updateAppionDB.py $jobid R\n\n";

		// create virtual window for matlab images
		if ($xvfb) $jobtext .= "Xvfb :25 -ac -pn -screen 0 800x800x8  -fp /usr/share/X11/fonts/misc -sp /usr/lib64/xserver/SecurityPolicy -co /usr/share/X11/rgb &\n";
		$jobtext .= "$apcmd\n";
		$jobtext .= "updateAppionDB.py $jobid D\n\n";
		$jobtext .= "exit\n"; 
	
		// write jobfile to tmp dir on cronus3
		$randstr = randomString(16);
		$tmpfile = "/tmp/$randstr.txt";
		$f = fopen($tmpfile,'w');
		fwrite($f,$jobtext);
		fclose($f);

		// copy file to run directory
		$cmd .= "cp $tmpfile $procdir/$jobfile;\n";
		exec_over_ssh($_SERVER['HTTP_HOST'],$user,$pass,$cmd, True);
	
		processing_header("Appion Job Submission","Appion Job Submission");
		echo "<table width='600'>\n";
		echo "<tr><td>Appion Directory</td><td>$procdir</td></tr>\n";
		echo "<tr><td>Job File Name</td><td>$jobfile</td></tr>\n";
		$cmd = "cd $procdir; qsub $jobfile;\n";

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
		$particle->updateClusterQueue($jobid,$jobnum,'Q');

		echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
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
	$javascript.= "function hideEditForm(stackid) {\n";
	$javascript.= "  var descText='descText'+stackid;\n";
	$javascript.= "  var descForm='descForm'+stackid;\n";
	$javascript.= "  if (document.getElementById) { // DOM3 = IE5, NS6\n";
	$javascript.= "    document.getElementById(descText).style.visibility = 'hidden';\n"; 
	$javascript.= "    document.getElementById(descForm).style.visibility = 'visible';\n"; 
	$javascript.= "  }\n"; 
	$javascript.= "  else {\n"; 
	$javascript.= "    if (document.layers) { // Netscape 4\n"; 
	$javascript.= "      document.descText.visibility = 'hidden';\n"; 
	$javascript.= "      document.descForm.visibility = 'visible';\n"; 
	$javascript.= "    }\n"; 
	$javascript.= "    else { // IE 4\n"; 
	$javascript.= "      document.all.descText.style.visibility = 'hidden';\n"; 
	$javascript.= "      document.all.descForm.style.visibility = 'visible';\n"; 
	$javascript.= "    }\n"; 
	$javascript.= "  }\n"; 
	$javascript.= "}\n";
	$javascript.= "</script>\n";
	return $javascript;
}

function editButton($editid,$text) {
	# add edit button to description
	$editButton="<div id='descText".$editid."' style='position:relative'>";
	$editButton.=$text;
	$editButton.=" <input class='edit' type='button' name='editdesc' value='edit' onclick=\"javascript:hideEditForm('$editid')\">";
	$editButton.="</div>\n";
	$editButton.="<div id='descForm".$editid."' style='visibility:hidden;'>";
	//	$editButton.="<textarea name='newdescription".$editid."' size='".strlen($text)."' value='";
	$len=(strlen($text)==0) ? 15 : strlen($text);
	$cols = ($len > 40) ? 40 : $len;
	$rows = ($cols==40) ? ceil($len/40) : 1;
	$editButton.="<textarea name='newdescription".$editid."' cols='$cols' rows='$rows'>";
	# convert single quotes to html
	$editButton.=htmlentities($text, ENT_QUOTES);
	$editButton.="</textarea>";
	$editButton.=" <input class='edit' type='submit' name='updateDesc".$editid."' value='Update'>";
	$editButton.="</div>\n";
	return $editButton;
}

function updateDescription($table, $editid, $text) {
	$particle=new particledata();

	# convert html back to single quotes
	$desc = html_entity_decode($text, ENT_QUOTES);
	$particle->updateDescription($table, $editid, $desc);
}

function pleaseWaitJava() {
	$java = "<script language='Javascript'>";
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
?>
