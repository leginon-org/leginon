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
require_once "inc/login.inc";
require_once "inc/ssh.inc";
require_once "inc/session.inc";

define('DONE_PIC','img/green_circle.gif');
define('NONE_PIC','img/red_circle.gif');
define('PROG_PIC','img/blue_circle.gif');

define('NONE_COLOR','#FFFFCC');
define('PROG_COLOR','#CCFFFF');
define('DONE_COLOR','#CCFFCC');

// start a php session
setsession();

function getProjectFromExpId($expId) {
	// Determine projectId from the expId
  $projectdata = new project();
  $projectdb = $projectdata->checkDBConnection();
 
  if($projectdb) $projectinfo = $projectdata->getProjectfromSessionId($expId);
  $projectId=(int) $projectinfo['projectId'];
  return $projectId;
}

function getProjectId() {
	// Complicated way to get the project id
	if ($_GET['expId']) {
		$projectid = getProjectFromExpId($_GET['expId']);
		$_SESSION['projectId'] = $projectid;

	} elseif ($_POST['sessionId']) {
		$projectid = getProjectFromExpId($_POST['sessionId']);
		$_SESSION['projectId'] = $projectid;

	} elseif ($_GET['projectId']) {
		$projectid = trim($_GET['projectId']);
		$_SESSION['projectId'] = $projectid;

	} elseif ($_POST['projectId']) {
		$projectid = trim($_POST['projectId']);
		$_SESSION['projectId'] = $projectid;

	} elseif ($_SESSION['projectId']) {
		$projectid = trim($_SESSION['projectId']);
		$_SESSION['projectId'] = $projectid;
	}

	if ($projectid)
		$projectid = (int) $projectid;
	if (is_int($projectid))
		$_SESSION['projectId'] = $projectid;

	return $projectid;
};

function commafy($input) {
	// add commas to an integer
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
	$selected_host=$_POST['processinghost'];
	$proc_list = (array)getHosts();

	// only list hosts if there are more than 1
	if (count($proc_list) > 1){
		foreach ($proc_list as $host) {
			$s = ($host['host'] == $_POST['processinghost']) ? "selected" : "";
			$h[]="<option value='".$host['host']."' ".$s." >".$host['host']."</option>\n";
  		}
		$html="<select name=\"processinghost\">\n";
		$html.=join("\n",$h);
		$html.="</select>";
	}
	else $html="<input type='hidden' name=\"processinghost\" value='".$proc_list[0]['host']."'>\n";
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
		$fsize = (int) filesize($stackimgfile);
		if ($fsize > 1073741824)
		  	$size = sprintf("%.2f GB", $fsize/1073741824);
		else
			$size = sprintf("%.1f MB", $fsize/1048576);
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

function processing_header($title,$heading=false,$headerstuff=false,$pleaseWait=false,$showmenu=true) {
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	// check if logged in
	if ($_POST['login']) {
		$errors = checkLogin();
	}

	if (!is_numeric($expId) && !is_numeric($projectId)) {
		echo "<h3>cannot display Appion page</h3>";
		echo "<h4>you are missing the expId in the URL above, e.g., <i>myamiweb/processing/page.php?expId=###</i></h4>";
		exit;
	}

	$leginondata = new leginondata();
	$particle = new particledata();
	$projectdata = new project();
	checkExptAccessPrivilege($expId,'data');
	$_SESSION['projectId'] = $projectId;

	// Collect session info from database
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$sessions=$sessiondata['sessions'];
	$currentproject = $projectdata->getProjectInfo($projectId);

	// Show project & session pulldowns
	if (is_array($sessioninfo)) {
		$sessionDescr="<font size=+1><b>".$sessioninfo['Name']."</b></font> - ".$sessioninfo['Purpose'];
		$session_link= '<a class="header" target="viewer" href="../imageviewer.php?expId='.$expId.'">'.$sessionDescr.'</a>';
	}
	$proj_link= '<a class="header" target="project" href="'.PROJECT_URL."getproject.php?projectId=".$projectId.'">'
		.$currentproject['name'].' ('.$projectId.')</a>';
	$misc = $particle->getMiscInfoFromProject ($projectId);
	$proj_link.=($misc) ? "<a href='viewmisc.php?projectId=$projectId'>[Related Images, Movies, etc]</a>" : ""; 
	if ($expId) $expinfo = $leginondata->getSessionInfo($expId);

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
		if (privilege('data') > 1)
			$html.=displayLogin($formAction);
		if(!empty($errors)){
			$html.= "<font color='#EE82EE'>".$errors."</font>";
		}
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
	if ($session_link) $html.= "<li><b>Session:</b> ".$session_link."</li>\n";
	if ($expinfo) $html.= "<li><b>Image Path:</b> ".$expinfo['Image path']."</li>\n";

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
	if (($expId || $projectId) && $showmenu) {
		require "menuprocessing.php";
		$html.= $menujs;
		$html.= $menulink;
	}
	$html.= "<div id='content' style='padding-left: 5px'>\n";
	if (($expId || $projectId) && $showmenu) {
		$html.= "<div style='position: relative; float:left; margin-right:10px' id='leftcontent'>\n";
		$html.= "<div class='lvmenu'>";
		$html.= $menuprocesing;
		$html.= "</div>\n";
		$html.= "</div>\n";
	}
	$html.= "<table border='0' cellpadding='0' cellspacing='0'><tr><td>\n";
	$html.= "<div id='maincontent' style='z-index:0; width:auto; text-align:left; '>\n";

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
		if (!$_POST['username'] || !$_POST['password']) 
			return("Please enter your username and password to server " . $_SERVER['SERVER_ADDR']);
		// authenticate username & password
		if (!check_ssh($_SERVER['SERVER_ADDR'],$_POST['username'],$_POST['password'])) 
			return("Authentication failed to server " . $_SERVER['SERVER_ADDR']);
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
	if($projectdb)
		$projects = $projectdata->getProjects('all');
	return($projects);
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

function checkClusterJobs($processhost, $user, $pass) {
	$cmd = "qstat -au ".$user." | egrep '^[0-9]'";
	$subjobs = exec_over_ssh($processhost, $user, $pass, $cmd, true);
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
	$optionkeys = array ('updateheader', 'plist', 'stackinfoindex', 'pixelsize');
	$plist=false;
	$updateheader=false;
	$pixelsize=0;
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
	var pixelsize=\"$pixelsize\"
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
		scalebar = ($('scalebar').checked) ? 1 : 0
		info = ($('info').checked) ? 1 : 0
		t = $('quality').value
		var tileId = \"img\"+i
		var filename = 'getstackimg.php?'
				+'hed='+file_hed
				+'&img='+file_img
				+'&n='+i
				+'&t='+t
				+'&b='+binning
				+'&uh='+updateheader
				+'&ps='+pixelsize
				+'&di='+info
				+'&sb='+scalebar

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

function getNumberOfProcsPerNode($processingHost) {
	global $PROCESSING_HOSTS;

	foreach ($PROCESSING_HOSTS as $host){
		if ($host['host'] == $processingHost){
			$numOfNode = $host['nproc'];
			break;
		}
	}
	return $numOfNode;
}

function getNumberOfRequiredNodes($nproc, $ppn) {
	if ($nproc < $ppn)
		return array(1, $nproc);
	$nodes = (int) ceil($nproc/$ppn);
	$ppn = (int) ceil($nproc/$nodes);
	return array($nodes, $ppn);
}

/**************************************/
function showOrSubmitCommand($command, $headinfo, $jobtype, $nproc) {
	/*
		If user clicked run button it launches job on appion cluster
		Otherwise displays command to copy and paste into terminal

		Requirements:
			$_GET['expId']
			$_POST['runname']
			$_POST['outdir'] 
		need to be defined and correct
	*/

	// get required inputs
	$expId=$_GET['expId'];
	if (empty($expId))
		return "<B>ERROR:</B> undefined expId";
	$runname=$_POST['runname'];
	if (empty($runname))
		return "<B>ERROR:</B> undefined runname";
	$outdir=$_POST['outdir'];
	if (empty($outdir))
		return "<B>ERROR:</B> undefined outdir";
	$projectid = getProjectId();

	// set rundir from runname and outdir
	if (substr($outdir,-1,1)!='/')
		$outdir.='/';
	$rundir = $outdir.$runname;

	// add space to end, if necessary
	if (substr($command,-1,1)!=' ')
		$command.=' ';
	// in the future maybe remove if statements
	if (!preg_match("/--rundir=/", $command))
		$command .= "--rundir=$rundir ";
	if (!preg_match("/--runname=/", $command))
		$command .= "--runname=$runname ";
	if (!preg_match("/--projectid=/", $command))
		$command .= "--projectid=$projectid ";
	if (!preg_match("/--expid=/", $command))
		$command .= "--expId=$expId ";
	if (!preg_match("/--jobtype=/", $command))
		$command .= "--jobtype=$jobtype ";

	if ($_POST['process'] != "Just Show Command") {
		// Option 1: selected the run button
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			return "<B>ERROR:</B> Enter a user name and password";

		$errors = submitAppionJob($command, $outdir, $runname, $expId, $jobtype, False, False, False, $nproc);

		// if errors:
		if ($errors)
			return "<B>ERROR:</B> $errors";

		exit;
	} else {
		// Option 2: just show command
		$bits = split(" ", $command);
		$function = $bits[0];

		processing_header("Just Show $function Command", "Just Show $function Command");
		echo $headinfo;
		echo justShowCommandTable($command);
		processing_footer();
		exit;
	}
};

/**************************************/
function justShowCommandTable($command) {
	global $USE_APPION_WRAPPER, $APPION_WRAPPER_PATH;

	if ($USE_APPION_WRAPPER) {
		$command = $APPION_WRAPPER_PATH." ".$command;
	}

	$command = trim($command);
	$bits = split(" ", $command);
	$function = array_shift($bits);

	$commandtable = "<table class='tablebubble' border='0' width='800'>\n";
	$commandtable .= "<tr><td colspan='2'>\n";
	$commandtable .= "	Copy and paste this $function command into a terminal:<hr/>\n";
	$commandtable .= "</td></tr><tr><td colspan='2' style='padding-left:0.3in;text-indent:-0.3in'>\n";
	$commandtable .= "	<p>\n";
	$commandtable .= "		<font size='+1'>$command</font>\n";
	$commandtable .= "	</p>\n";
	$commandtable .= "</td></tr><tr><td colspan='2'><hr/>\n";
	sort($bits);
	foreach ($bits as $bit) {
		if (substr($bit, 0, 2) == "--") {
			if (preg_match("/^--([^=]*)=(.*)$/", $bit, $matches)) {
				// type 1: --param=value
				if (empty($matches[1]))
					continue;
				$commandtable .= "</td></tr><tr><td>\n";
				$commandtable .= "<b>".$matches[1]."</b>\n";
				$commandtable .= "</td><td>\n";
				$commandtable .= $matches[2]."\n";
			} elseif (preg_match("/^--([^=]*)$/", $bit, $matches)) {
				// type 2: --param, e.g., --no-commit
				if (empty($matches[1]))
					continue;
				$commandtable .= "</td></tr><tr><td>\n";
				$commandtable .= "--<b>".$matches[1]."</b>\n";
				$commandtable .= "</td><td>\n";
				$commandtable .= "<font color='#339933'><i>flag enabled</i></font>\n";
			}
		} elseif(!empty($bit)) {
			$commandtable .= "</td></tr><tr><td>\n";
			$commandtable .= "<font color='#cc3333'>Unknown flag:</font>\n";
			$commandtable .= "</td><td>\n";
			$commandtable .= "$bit\n";
		}
	}
	$commandtable .= "</td></tr>\n";
	$commandtable .= "</table>\n";
	return $commandtable;
};

/**************************************/
function submitAppionJob($command, $outdir, $runname, $expId, $jobtype, $testimg=False,
		 $xvfb=False, $xtra=False, $nproc=1, $ppn=0, $nodes=0, $walltime="240", $cputime="240") {
	global $DATA_DIRS;
	
	$particle=new particleData();

	if ($_POST['processinghost']) {
		$_SESSION['processinghost'] = $_POST['processinghost'];
	}
	$processhost = $_SESSION['processinghost'];
	$webserver = $_SERVER['SERVER_ADDR'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// check if database is configured on processing host
	$cmd = "echo 'hello'";
	$syscheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
	if (trim($syscheck)=='') return "could not connect to processing host: $processhost";
	$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"leginondata\")'";
	$dbcheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
	if (trim($dbcheck)=='') return "sinedon is not configured for leginondata, check your sinedon.cfg file";
	$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"appiondata\")'";
	$dbcheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
	if (trim($dbcheck)=='') return "sinedon is not configured for appiondata, check your sinedon.cfg file";

	//Check if filesystem is full
	$cmd = "df $outdir";
	$fscheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
	$fsbits = split(" ", trim($fscheck));
	foreach ($fsbits as $fsbit) {
		if (preg_match("/^[0-9]+%$/", $fsbit))
			$percent = (float) preg_replace("/%/", "", $fsbit);
	}
	if ($percent && $percent >= 98) {
		$error = "Filesystem is $percent% full, please change output directory<br/>\n";
		$error .= "<font size='-2'>$outdir</font>";
		return $error;
	}

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// check to make sure the rundir is a valid directory
	if ($DATA_DIRS) {
		$ingood = False;
		foreach ( $DATA_DIRS as $gooddisk)
			if (!$gooddisk) {
				$ingood = True;
			} else { 
				$ingood = (ereg($gooddisk,$rundir))? True: $ingood;
			}
		if (!$ingood) 
			return 'could not create directory '.$rundir.'<br/> try using '.implode(' or ',$DATA_DIRS);
	}

	// if more than one job running in the directory (like
	// classification of ref free)
	// is this used anymore? - neil
	if ($xtra) $runname = "$runname.$xtra";

	// set names of cluster job file and output log
	$jobfile = "$runname.appionsub.job";
	$logfile = "$runname.appionsub.log";

	if (is_array($command)) {
		$apcmd = array();
		foreach ($command as $cmd) {
			$filtcommand = ereg_replace("\'","", $cmd);;
			$apcmd[] = "webcaller.py '".$filtcommand."' $rundir/$logfile"."\n";
		}
	} else {
		// create appion command
		$filtcommand = ereg_replace("\'","", $command);
		//$filtcommand = preg_replace("/[\n\r]/", " -- ", $filtcommand);
		$apcmd = "webcaller.py '".$filtcommand."' $rundir/$logfile";
	}

	// create run directory and wait a few seconds to make sure it happened
	$cmd = "mkdir -p $rundir;";
	$temp = exec_over_ssh($webserver, $user, $pass, $cmd, True);
	$temp = exec_over_ssh($processhost, $user, $pass, $cmd, True);
	$checkcount = 0;
	while (!file_exists($rundir) && $checkcount < 7) {
		// sometime NFS cache is slow to update new changes
		sleep(1);
		$checkcount++;
	}
	if (!file_exists($rundir))
		return "could not create directory '$rundir'<br/>check folder permissions";

	if ($testimg) {
		//submit directly to head node on cluster if testing 1 image
		$cmd .= "cd $rundir; $apcmd; exit;";
		$jobnum = exec_over_ssh($processhost, $user, $pass, $cmd, True);
		return;
	}

	// get proper node numbers
	if ($ppn < 1)
		$ppn = getNumberOfProcsPerNode($processhost);
	if ($nodes < 1)
		list($nodes, $ppn) = getNumberOfRequiredNodes($nproc, $ppn);
	if ($ppn < 1)
		$ppn = 1;
	// Torque PBS: the cput needs to be nproc*walltime
	// PBS Pro: cput = walltime
	$cput = $walltime*$nproc;

	// insert cluster job data and set job as queued
	$jobid=$particle->insertClusterJobData($processhost,$rundir,'',$rundir,$jobfile,$expId,$jobtype,$user);

	$jobtext = "#PBS -l nodes=$nodes:ppn=$ppn\n";
	// AMI guppy specific to get small jobs to run on 4 proc nodes
	/*if ($nproc < 5) {
		$jobtext = "#PBS -l nodes=1:ppn=4:fourProc\n";
	} else {
		$jobtext = "#PBS -l nodes=$nodes:ppn=$ppn\n";
	}*/

	// create job file
	$jobtext .= "#PBS -l walltime=$walltime:00:00\n";
	$jobtext .= "#PBS -l cput=$cputime:00:00\n";
	$jobtext .= "#PBS -j oe\n";
	$jobtext .= "#PBS -r n\n\n";
	$projectid = getProjectId();

	// we should get rid of this and let python do it
	$jobtext .= "updateAppionDB.py $jobid R $projectid\n\n";

	if (is_array($command)) {
		foreach ($apcmd as $iteration) {
			$jobtext .= "$iteration\n";
		}
	} else
		$jobtext .= "$apcmd\n";

	// we should get rid of this and let python do it
	$jobtext .= "\nupdateAppionDB.py $jobid D $projectid\n\n";

	$jobtext .= "exit\n"; 

	// this next part is why users have to be able to login to web server
	// write jobfile to tmp dir on cronus3
	$randstr = randomString(16);
	$tmpfile = "/tmp/$randstr.txt";
	$f = fopen($tmpfile,'w');
	fwrite($f,$jobtext);
	fclose($f);
	// copy file to run directory on the web server
	$cmd .= "cp $tmpfile $rundir/$jobfile;\n";
	exec_over_ssh($webserver, $user, $pass, $cmd, True);

	// write output page
	processing_header("Appion Job Submission","Appion Job Submission");
	echo "<table width='600'>\n";
	echo "<tr><td>Appion Directory</td><td>$rundir</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobfile</td></tr>\n";
	echo "<tr><td>Hostname</td><td>$processhost</td></tr>\n";
	echo "<tr><td>Username</td><td>$user</td></tr>\n";
	echo "<tr><td>Local server ip</td><td>$webserver</td></tr>\n";
	echo "<tr><td>Project Id</td><td>$projectid</td></tr>\n";
	$cmd = "cd $rundir; qsub $jobfile;\n";

	// submit job to cluster
	$jobdata = exec_over_ssh($processhost, $user, $pass, $cmd, True);

	// retrieve job id
	ereg("([0-9]{1,})", $jobdata, $regs);
	$jobnum = $regs[1];
	if (!is_numeric($jobnum)) {
		echo "</table><p>\n";
		echo "ERROR in job submission. Check the cluster\n".$jobdata."\n".$regs."\n";
		processing_footer();
		exit;
	}

	// insert cluster job id into row that was just created
	$particle->updateClusterQueue($jobid,$jobnum,'Q');

	echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
	echo "<tr><td>Command</td><td><font size='-3'>$filtcommand</font></td></tr>\n";
	echo "</table>\n";

	// check jobs that are running on the cluster
	echo "<p>Jobs currently running on the cluster:\n";
	$subjobs = checkClusterJobs($processhost, $user, $pass);
	if ($subjobs) {
		echo "<pre>$subjobs</pre>\n";
	} else {
		echo "<font color='red'>No Jobs on the cluster, check your settings</font>\n";
	}
	echo "<p><a href='checkAppionJob.php?expId=$expId&jobId=$jobid'>[Check status of this job]</a><p>\n";
	echo "<p><font color='#990000'>Do not hit 'reload' - it will re-submit job</font><p>\n";
	processing_footer();
	exit;
}

/**************************************/
function writeTestResults($jpg,$ccclist,$bin){
	if (!file_exists($jpg)) {
		$base = basename($jpg);
		$dir = dirname($jpg);
		return "<font color='#990000' size='+2'>An Error occurred - the image $base was not found in folder $dir</font><br />\n";
	}
	$html = "<center>\n";
	$html.= "<a href='loadimg.php?filename=$jpg' target='blank'>\n";
	$html.= "<img src='loadimg.php?filename=$jpg&h=256'></a>\n";
	if (count($ccclist)>1)
		$html.= "<br />\n";
	foreach ($ccclist as $ccc) {
		$html.= "<a href='loadimg.php?filename=$ccc' target='blank'>\n";
		$html.= "<img src='loadimg.php?filename=$ccc&h=256'></a>\n";
	}
	$html.= "</center>\n";
	return $html;
}

/**************************************/
function randomString($length) {
	$s = md5(time());
	$i = 32-$length;
	$randstring=substr($s,rand(0,$i),$length);
	return $randstring;
}

/**************************************/
function getTimestring() {
	$today = getdate();
	$timestring = substr($today['year'],2,2)
		.strtolower(substr($today['month'],0,3))
		.sprintf("%02u", $today['mday'])
		.sprintf("%c", $today['hours']+97)
		.sprintf("%02u", $today['minutes']);
	return $timestring;
}

/**************************************/
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

/**************************************/
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

/**************************************/
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

/**************************************/
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

/**************************************/
function updateDescription($table, $editid, $text) {
	$particle=new particledata();

	# convert html back to single quotes
	$desc = html_entity_decode($text, ENT_QUOTES);
	$desc = trim($desc);
	$particle->updateDescription($table, $editid, $desc);
}

/**************************************/
function pleaseWaitJava() {
	$java = "<script type=\"text/javascript\" >\n";
	$java.= "function pleasewait() {\n";
	$java.= "	pleasewaitScreen=$('pleasewaitScreen');\n";
	$java.= "	pleasewaitScreen.style.visibility='visible';\n";
	$java.= "}\n"; 
	$java.= "</script>\n";
	return $java;
}

/**************************************/
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

/**************************************/
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

/**************************************/
function openRoundBorder() {
	$text = "<div id='roundbox'>\n";
	$text .= "<b class='xtop'><b class='xb1'></b><b class='xb2'></b><b class='xb3'></b><b class='xb4'></b></b>\n";
	$text .= "<div class='roundboxcontent'>\n";
	$text .= "<p>\n";
	return ($text);
}

/**************************************/
function closeRoundBorder() {
	$text = "</p>\n";
	$text .= "</div><!--/roundboxcontent-->\n";
	$text .= "<b class='xbottom'><b class='xb4'></b><b class='xb3'></b><b class='xb2'></b><b class='xb1'></b></b>\n";
	$text .= "</div><!--/roundbox-->\n";
	return ($text);
}

/**************************************/
function getPngList($dir) {
	$pngimages=array();
	$pngimages['pngfiles']=array();
	$pngimages['eulerfiles']=array();

	//get pngs
	//echo "GLOB: ".$dir."/".'*\.png';
	$pngfiles1 = glob($dir."/*\.png");
	$pngfiles2 = glob($dir."/*/*\.png");
	$pngfiles3 = glob($dir."/*/*/*\.png");
	$pngfiles = array_merge($pngfiles1, $pngfiles2, $pngfiles3);
	//print_r($pngfiles)."<br/>";
	if (count($pngfiles) < 2)
		return $pngimages;

	//sort pngs
	$eulerstr = 'euler.*\.png$';
	foreach ($pngfiles as $pngfile) {
		if (eregi($eulerstr, $pngfile))
			$pngimages['eulerfiles'][] = $pngfile;
		else
			$pngimages['pngfiles'][] = $pngfile;
	}
	sort($pngimages['pngfiles']);
	sort($pngimages['eulerfiles']);
	//print_r($pngimages)."<br/>";
	return $pngimages;
}

/**************************************/
function emanRef() {
	return referenceBox("EMAN: semiautomated software for high-resolution single-particle reconstructions.", 1999, "Ludtke SJ, Baldwin PR, Chiu W.", "J Struct Biol.", 128, 1, 10600563, false, false, "img/eman_logo.png");
}

/**************************************/
function spiderRef() {
	return referenceBox("SPIDER and WEB: processing and visualization of images in 3D electron microscopy and related fields.", 1996, "Frank J, Radermacher M, Penczek P, Zhu J, Li Y, Ladjadj M, Leith A.", "J Struct Biol.", 116, 1, 8742743, false, false, "img/spider_logo.png");
}

/**************************************/
function imagicRef() {
	return referenceBox("A New Generation of the IMAGIC Image Processing System.", 1996, 
		"van Heel M., Harauz G., Orlova E. V., Schmidt R. & Schatz M", "J Struct Biol", 116, 1, 8742718, false, false, "img/imagic_logo.png");
}

/**************************************/
function appionRef() {
	return referenceBox("Appion: an integrated, database-driven pipeline to facilitate EM image processing.", 2009, "Lander GC, Stagg SM, Voss NR, <i>et&nbsp;al.</i>", "J Struct Biol.", 166, 1, 19263523, 2775544, "10.1016/j.jsb.2009.01.002", "img/topbarbackgrnd.jpg");
}

/**************************************/
function frealignRef() {
	return referenceBox("FREALIGN: high-resolution refinement of single particle structures.", 2007, "Grigorieff, N.", "J Struct Biol.", 157, 1, 16828314, false, "10.1016/j.jsb.2006.05.004", "img/grigorieff_lab.png");
}

/**************************************/
function initModelRef() {
	return referenceBox("A toolbox for ab initio 3-D reconstructions in single-particle electron microscopy.", 2010, "Voss NR, Lyumkis D, Cheng A, <i>et&nbsp;al.</i>", "J Struct Biol.", 169, 3, 20018246, false, false, "img/topbarbackgrnd.jpg");
}

/**************************************/
function referenceBox($title, $year, $authorlist, $journal, $volume=false, $issue=false, $pmid=false, $pmcid=false, $doi=false, $logo=false) {
	$refbox = "<br/>";
	$refbox .= "<table class='tablebubble' border='0'><tr><td>\n";
	if ($logo)
		$refbox .= "<img height='80' src='$logo'>";
	$refbox .= "</td><td width='480'>\n";
	$refbox .= "<h4>If you find this software useful please cite:</h4>\n";
	$refbox .= "\n";
	// add period at end of certain fields
	if (substr($title,-1,1)!='.')
		$title.='.';
	if (substr($authorlist,-1,1)!='.')
		$authorlist.='.';
	if (substr($journal,-1,1)!='.')
		$journal.='.';

	$refbox .= "<i>\"$title\"</i>&nbsp;($year)\n";
	$refbox .= "$authorlist\n";
	$refbox .= "$journal";
	if ($volume)
		$refbox .= " v$volume";
	if ($issue)
		$refbox .= "<i>($issue)</i>";
	$refbox .= ".&nbsp;\n";
	if ($pmid)
		$refbox .= "PMID:&nbsp;<a href='http://www.ncbi.nlm.nih.gov/pubmed/$pmid'>$pmid</a>&nbsp;\n";
	if ($pmcid)
		$refbox .= "Free text:&nbsp;<a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC$pmcid'>PMC$pmcid</a>&nbsp;\n";
	if ($doi)
		$refbox .= "DOI:&nbsp;<a href='http://dx.doi.org/$doi'>$doi</a>&nbsp;\n";
	$refbox .= "\n";
	$refbox .= "</td></tr></table><br/>\n";
	return ($refbox);
	//echo referenceBox(title, year, authorlist, journal, volume, issue, pmid, pmc, doi, logo);

}



?>
