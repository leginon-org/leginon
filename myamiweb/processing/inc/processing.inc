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
require_once "inc/project.inc";
require_once "inc/cluster.inc";

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

function getProcessString() 
{
	return $_POST['process'];
}

function getHosts(){
	global $PROCESSING_HOSTS;
	if (is_array($PROCESSING_HOSTS))
	return $PROCESSING_HOSTS;
	return array();
}

function getSelectedProcessingHost() 
{
	if ($_POST['processinghost']) {
		$_SESSION['processinghost'] = $_POST['processinghost'];
	}
	return $_SESSION['processinghost'];
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
	if ($warning) {
		$html.="<br/><font class='apcomment'>Submission will NOT run, only output a command that you can copy and paste into a unix shell</font>";
	}
	else if ($_SESSION['loggedin']) {
		$html.="  <input type='submit' name='process' value='$name' onclick='pleasewait()'>\n";
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

function processing_header($title,$heading=false,$headerstuff=false,$pleaseWait=false,$showmenu=true,$printDiv=false) {
	$expId = $_GET['expId'];
	if (!is_numeric($expId) || $expId == 0) {
		// special case for uploading images to a new session coming from a known project
		$projectId = $_GET['projectId'];
		checkProjectAccessPrivilege($projectId); 
	} else {
		checkExptAccessPrivilege($expId,'data');
		$projectId = getProjectId();
	}
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
	//if ($expId) $expinfo = $leginondata->getSessionInfo($expId);
	$expId = $sessioninfo;
	$html="<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN'  'http://www.w3.org/TR/html4/strict.dtd'>
<html>
<head>
<title>".$title."</title>
<link rel='stylesheet' type='text/css' href='../css/viewer.css'>
<link rel='stylesheet' type='text/css' href='css/proc.css'>
<link rel='stylesheet' type='text/css' href='../css/lvmenu.css'>\n";
	// javascript for please wait div to show up on submit
	if ($pleaseWait) $html.= pleaseWaitJava();
	if ($printDiv) $html.= printDivJava();
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
		if (!empty($_GET['expId']))
			$html.='<a class="header" href="endsession.php?expId='.$_GET['expId'].'">[Log Out]</a>'."\n";
		else
			$html.='<a class="header" href="endsession.php?projectId='.$_GET['projectId'].'">[Log Out]</a>'."\n";
		$_SESSION['loggedin']=true;
	}
	else {
		$expId=$_GET['expId'];
		$projectId=getProjectId();
		// retain the original formAction if expId is not specified as in the case of uploadimage
		if (!empty($expId))
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
		return("Please enter your username and password to server ");
		// Do not authenticate username & password on webserver, this assumes
		//the user has access to the webserver.  Until we fix this properly 
		//just ensure that a username and password have been provided.
		//if (!check_ssh($_SERVER['SERVER_ADDR'],$_POST['username'],$_POST['password']))
		//return("Authentication failed to server " . $_SERVER['SERVER_ADDR']);
		
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

	if(!$sessionId) $sessiondata['sessions'] = $leginondata->getSessions('description', $projectId);

	$sessiondata['info']=$leginondata->getSessionInfo($sessionId);
	$sessiondata['presets']=$leginondata->getTruePresets($sessionId);
	if ($leginondata->hasManualImages($sessionId)) $sessiondata['presets'][] = 'manual';
	$sessiondata['currentproject']=$projectdata->getProjectFromSession($sessiondata['info']['Name']);

	return $sessiondata;
}

// TODO: what if the cluster does not use qstat? Moab uses mstat or some thing like that.
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

function getNumberOfRequiredNodes($nproc, $ppn) 
{
	if ($nproc < $ppn) {
		return array(1, $nproc);
	}
	
	if ( $ppn ) {
		$nodes = (int) ceil($nproc/$ppn);
	}
	
	if ( $nodes ) {
		$ppn = (int) ceil($nproc/$nodes);
	}
	
	return array($nodes, $ppn);
}

//*****************************************************************************
//
// Add the Appion wrapper to a command to allow multiple installations of
// Appion on a single machine.
//
//*****************************************************************************
function addAppionWrapper($command, $processhost=false) 
{
	if ( USE_APPION_WRAPPER ) {
		if ($processhost === false) {
			$processhost = getSelectedProcessingHost();
		}
		$cluster = new Cluster( $processhost );
		$wrapper = $cluster->getWrapperPath();
		$wrapper = $wrapper ? $wrapper : APPION_WRAPPER_PATH;
		$command = $wrapper." ".$command;
	}
	return $command;
}


/**************************************/
function showOrSubmitCommand($command, $headinfo, $jobtype, $nproc, $testimg=False) 
{
	/*
		If user clicked run button it launches job on appion cluster
		Otherwise displays command to copy and paste into terminal

		Requirements:
		$_GET['expId']
		$_POST['runname']
		$_POST['outdir']
		need to be defined and correct
		*/
	$expId=$_GET['expId'];
	// uploadimage jobtype need to be handled differently since it has none of these
	if ($jobtype != 'uploadimage' && $jobtype != 'etomorecon') {
		// get required inputs
		if (!is_numeric($expId) || $expId == 0) 
			return "<B>ERROR:</B> undefined expId";
		$allow_processing = checkExptAdminPrivilege($expId,'data');
		$runname=$_POST['runname'];
		if (empty($runname))
			return "<B>ERROR:</B> undefined runname";
		$outdir=$_POST['outdir'];
		if (empty($outdir))
			return "<B>ERROR:</B> undefined outdir";
			
		// set rundir from runname and outdir
		if (substr($outdir,-1,1)!='/')
			$outdir.='/';
		$rundir = $outdir.$runname;
		
		// set remoterundir from runname and remoteoutdir
		$remoteoutdir = $_POST['remoteoutdir'];
		if ( !empty($remoteoutdir) ) {
			if (substr($remoteoutdir,-1,1)!='/')
				$remoteoutdir.='/';
			$remoterundir = $remoteoutdir.$runname;
		}
	} else {
		if (!is_numeric($expId) || $expId == 0) {
			// special case for uploading images to a new session coming from a known project
			$projectId = $_GET['projectId'];
			$allow_processing = checkProjectExptAdminPrivilege($projectId);
		} else {
			$allow_processing = checkExptAdminPrivilege($expId,'data');
		}
	}
	if (!$allow_processing)
		redirect(BASE_URL.'accessdeny.php?text=You do not have permission to process this data set');
	$projectid = getProjectId();

	// add space to end, if necessary
	if (substr($command,-1,1)!=' ')
	$command.=' ';
	// in the future maybe remove if statements
	if (!preg_match("/--rundir=/", $command) && !empty($rundir))
	$command .= "--rundir=$rundir ";
	if (!preg_match("/--remoterundir=/", $command) && !empty($remoterundir))
	$command .= "--remoterundir=$remoterundir ";
	if (!preg_match("/--runname=/", $command) && !empty($runname))
	$command .= "--runname=$runname ";
	if (!preg_match("/--projectid=/", $command))
	$command .= "--projectid=$projectid ";
	if (!preg_match("/--expid=/", $command) && !empty($expId))
	$command .= "--expId=$expId ";
	if (!preg_match("/--jobtype=/", $command))
	$command .= "--jobtype=$jobtype ";
	
	// Get the processing host
	$processhost = getSelectedProcessingHost();

	// until uploadimage works with appionJob submission, it is not allowed to do so
	if ($_POST['process'] != "Just Show Command" && $jobtype != 'uploadimage') {
		// Option 1: selected the run button
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) {
			return "<B>ERROR:</B> Enter a user name and password";
		}

		$errors = submitAppionJob($command, $outdir, $runname, $expId, $jobtype, $testimg, False, False, $nproc);
		
		// if errors:
		if ($errors) {
			return "<B>ERROR:</B> $errors";
		} else if ($testimg) {
			return;
		}

		exit;
	} elseif ($_POST['process'] != "Just Show Command" && $jobtype == 'uploadimage') {
		$user = $_SESSION['username'];
		$pass = $_SESSION['password'];

		// Add the Appion wrapper to support muliple installations of Appion
		$wrappedcommand =  addAppionWrapper($command, $processhost);
		// uploadimage is run directly through ssh, not webcaller.py and qsub
		exec_over_ssh($processhost, $user, $pass, $wrappedcommand, TRUE);
		processing_header("Upload image to project", "Upload image to project");
		echo $headinfo;
		echo "<B>uploadimage job submitted to ".$processhost." through ssh.</B>";
		echo "<p></p>\n";
		echo justShowCommandTable($command, $processhost, true);
		processing_footer();
		exit;
		
	} elseif ($_POST['process'] == "Just Show Command" && $testimg) {		
		// if we are testing an image with just show command, return to the parameter page 
		return;
		
	} else {
		// Option 2: just show command
		$bits = split(" ", $command);
		$function = $bits[0];

		processing_header("Just Show $function Command", "Just Show $function Command");
		echo $headinfo;
		echo justShowCommandTable($command, $processhost);		
		processing_footer();
		exit;
	}
};

/**************************************/
function justShowCommandTable($command, $processhost, $skip_command=false) {

	// Keep this section before adding the wrapper
	// to get the proper values. Trim the whitespace from the ends,
	// split the components into an array, and pop the first element
	// which should be the function.
	$command = trim($command);
	
	// tokenize the command on spaces, without splitting quoted tokens.
	// The first call to strtok gets the first token, following calls will return the next token. 
	$token = strtok($command,' ');
	while ($token) {
		// find double quoted tokens, the second expression looks for the case of a single word description
		// in which case both the begin and end quote is in a single token
		if ( preg_match('/([^"]*)"([^"]*)/', $token) && !(preg_match('/([^"]*)"([^"]*)"/', $token)) ) { 
			$token .= ' '.strtok('"').'"'; 
		}
		// find single quoted tokens, the second expression looks for the case of a single word description
		if ( preg_match("/([^']*)'([^']*)/", $token) && !(preg_match("/([^']*)'([^']*)'/", $token)) ) { 
			$token .= ' '.strtok("'")."'"; 
		}
		
		$tokens[] = $token;
		$token = strtok(' ');
	} 
	
	// remove the first token, which should be the file name
	$function = array_shift($tokens);	
	
	// Add the Appion wrapper to support muliple installations of Appion
	$command =  addAppionWrapper($command, $processhost);

	$commandtable = "<table class='tablebubble' border='0' width='800'>\n";
	if (!$skip_command) {
		$commandtable .= "<tr><td colspan='2'>\n";
		$commandtable .= "	Copy and paste this ".$function." command into a terminal:<hr/>\n";
		$commandtable .= "</td></tr><tr><td colspan='2' style='padding-left:0.3in;text-indent:-0.3in'>\n";
		$commandtable .= "	<p>\n";
		$commandtable .= "		<font size='+1'>$command</font>\n";
		$commandtable .= "	</p>\n";
	}
	$commandtable .= "</td></tr><tr><td colspan='2'><hr/>\n";
	sort($tokens);
	foreach ($tokens as $token) {
		if (substr($token, 0, 2) == "--") {
			if (preg_match("/^--([^=]*)=(.*)$/", $token, $matches)) {
				// type 1: --param=value
				if (empty($matches[1]))
				continue;
				$commandtable .= "</td></tr><tr><td>\n";
				$commandtable .= "<b>".$matches[1]."</b>\n";
				$commandtable .= "</td><td>\n";
				$commandtable .= $matches[2]."\n";
			} elseif (preg_match("/^--([^=]*)$/", $token, $matches)) {
				// type 2: --param, e.g., --no-commit
				if (empty($matches[1]))
				continue;
				$commandtable .= "</td></tr><tr><td>\n";
				$commandtable .= "--<b>".$matches[1]."</b>\n";
				$commandtable .= "</td><td>\n";
				$commandtable .= "<font color='#339933'><i>flag enabled</i></font>\n";
			}
		} elseif(!empty($token)) {
			$commandtable .= "</td></tr><tr><td>\n";
			$commandtable .= "<font color='#cc3333'>Unknown flag:</font>\n";
			$commandtable .= "</td><td>\n";
			$commandtable .= "$token\n";
		}
	}
	$commandtable .= "</td></tr>\n";
	$commandtable .= "</table>\n";
	return $commandtable;
};

function addProcessingHostParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime )
{
	if ($ppn < 1 && !preg_match("/--ppn=/", $command) ) {
		$ppn = getNumberOfProcsPerNode($processhost);
	}
	if ($nodes < 1 && !preg_match("/--nodes=/", $command) ) {
		list($nodes, $ppn) = getNumberOfRequiredNodes($nproc, $ppn);
	}
	if ($ppn < 1) {
		$ppn = 1;
	}
	// Torque PBS: the cput needs to be nproc*walltime
	// PBS Pro: cput = walltime
	// This was not being using in current job files, should it be?
	$cput = $walltime * $nproc;
	
	if (!preg_match("/--ppn=/", $command))
		$command .= " --ppn=$ppn ";
	if (!preg_match("/--nodes=/", $command))
		$command .= " --nodes=$nodes ";
	if (!preg_match("/--walltime=/", $command))
		$command .= " --walltime=$walltime ";
	if (!preg_match("/--cput=/", $command) && $cputime)
		$command .= " --cput=$cputime ";
		
	return $command;		
}

// Put the command into format:
// <wrapper> runjob.py <wrapper> somejob.py --param1=x -- param2=y
// for generic jobs or
// <wrapper> runjob.py --appionwrapper=<wrapper> --param1=x -- param2=y
// for jobs that need to create a type specific job file.
function addJobSubmitParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime )
{
	// Add the Appion wrapper to support muliple installations of Appion
	$command = addAppionWrapper($command, $processhost);
	
	// if there is no python file in the command, turn the wrapper into a flag
	if (!preg_match("/.py /", $command)) {
		$command = "--appionwrapper=".$command;
	}
	
	// Funnel all jobs through the cluster agent, runjob.py.
	// Jobs to be run on remote clusters are built by job specific classes.
	// All others are built by apGenericJob.py.
	if (!preg_match("/runJob.py/", $command)) {
		$command = "runJob.py ".$command;

		// Add the Appion wrapper to support muliple installations of Appion
		// Makes sure we use the right version of runjob.py and subsequent scripts.
		$command = addAppionWrapper($command, $processhost);
	}
	
	// Add processing host parameters to the command
	// TODO: when is the command ever an array??? should it always be an array that sometimes has len=1??
	// Commenting this out for now, if no problems it can be removed
//	if (is_array($command)) {
//		foreach ($command as $cmd) {
//			$cmd = addProcessingHostParams($cmd, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime);
//		}
//	} else {
		$command = addProcessingHostParams($command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime);
//	}
	
	return $command;
}

/**************************************/
function submitAppionJob($command, $outdir, $runname, $expId, $jobtype, $testimg=False,
$xvfb=False, $xtra=False, $nproc=1, $ppn=0, $nodes=0, $walltime="240", $cputime=False) {
	global $DATA_DIRS;

	$allow_processing = checkExptAdminPrivilege($expId,'data');
	if (!$allow_processing) return "processing not allowed by this user for experiment id: $expId";

	$processhost = getSelectedProcessingHost();
	$webserver = $_SERVER['SERVER_ADDR'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	// Add parameters that are only needed if submitting the job from the web server
	$command = addJobSubmitParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime );
	
	// check if database is configured on processing host
//	$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"leginondata\")'";	
//	$dbcheck = exec_over_ssh($processhost, $user, $pass, $cmd, True);
//	if ($dbcheck === false){
//		//Return a more accurate error message		
//		$errMsg = "Could not connect to $processhost: ";
//		$errMsg .= pconnError();
//		return $errMsg;
//	}	
//
//	if (trim($dbcheck)=='') return "sinedon is not configured for leginondata, check your sinedon.cfg file";
//	
//	if($expId != 000){
//		$cmd = "python -c 'import sinedon; print sinedon.getConfig(\"appiondata\")'";
//		$dbcheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
//		if (trim($dbcheck) == '') return "sinedon is not configured for appiondata, check your sinedon.cfg file";
//	}
	
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

	// create run directory on processing host only.  Do not do anything on
	// the webserver, doing so requires making poor assumptions. 
	$cmd = "mkdir -p $rundir;";
	$rvalue = exec_over_ssh($processhost, $user, $pass, $cmd, True);
	if ($rvalue === false ){
		$errMsg = "Could not create run directory on $processhost: ";
		$errMsg .= pconnError();
		return $errMsg;
	}
	
	if ($testimg) {
		//submit directly to head node on cluster if testing 1 image
		$cmd = "cd $rundir; $command; exit;";
		$jobdata = exec_over_ssh($processhost, $user, $pass, $cmd, True);
		if ( empty($jobdata) ) {		
			$errMsg = "Job submission to $processhost failed for command: $command Message: ";
			$errMsg .= pconnError();
			return $errMsg;
		} else {
			return;
		}
	}

	// set names of cluster job file and output log
	// Changing this, not sure why appionsub is being added to the name...AH
	// May need to change back in case of Armageddon
	$jobfile = "$runname.appionsub.job";
	$logfile = "$runname.appionsub.log";
	// These should match the names being assigned on the python side where the files are created
	//$jobfile = "$runname.job";
	//$logfile = "$runname.log";
	
	// insert cluster job data and set job as queued
	$particle = new particleData();
	$jobid = $particle->insertClusterJobData($processhost, $rundir, '', $rundir, $jobfile, $expId, $jobtype, $user);
	
	// Add the job id to the command string
	$command .= "--jobid=$jobid ";
		
	$apcmd = $command;
	//$cmd = "cd $rundir; $apcmd;\n";
	$cmd = $apcmd;
	
	// write output page
	processing_header("Appion Job Submission","Appion Job Submission");
	echo "<table width='800'>\n";
	echo "<tr><td>Appion Directory</td><td>$rundir</td></tr>\n";
	echo "<tr><td>Job File Name</td><td>$jobfile</td></tr>\n";
	echo "<tr><td>Hostname</td><td>$processhost</td></tr>\n";
	echo "<tr><td>Username</td><td>$user</td></tr>\n";
	echo "<tr><td>Local server ip</td><td>$webserver</td></tr>\n";
	echo "<tr><td>Project Id</td><td>$projectid</td></tr>\n";
	echo "<tr><td>Command</td><td><font size='-2'>$cmd</font></td></tr>\n";
	
	// submit job to cluster
	$jobdata = exec_over_ssh($processhost, $user, $pass, $cmd, True);
	if ( empty($jobdata) ) {		
		$errMsg = "Error: Job submission to $processhost failed:  ";
		$errMsg .= pconnError();
		echo "</table><p>\n";
		echo "<hr>\n<font color='#CC3333' size='+1'>$errMsg</font>\n";
		exit;
	}
	// retrieve job id
	// TODO: may want to clean this up so the number is not returned twice.
	// we want to match the last numeric value at the end of the $jobdata string
	// this currently returns it twice, hence the 2D array result requiring $matches[0][0] to access.
	preg_match_all("/([0-9]+)$/", $jobdata, $matches );
	$jobnum = $matches[0][0];
	if (!is_numeric($jobnum)) {
		echo "</table><p>\n";
		echo "ERROR in job submission. Check the cluster.\n".$jobdata."\n".$matches[0][0]."\n";
		processing_footer();
		exit;
	}
	
	// We need to check the status of the job so that we do not overwrite it in the following updateClusterQueue refs #706
	$jobinfo = $particle->getJobInfoFromId($jobid);
	
	// This could still overwrite the status if the job file is executed after the if and before updateClusterQueue below
	if ( $jobinfo['status'] ) {
		$status = $jobinfo['status'];
	} else {
		$status = 'Q';
	}

	// insert cluster job id into row that was just created
	$particle->updateClusterQueue($jobid, $jobnum, $status);

	echo "<tr><td>Job number</td><td>$jobnum</td></tr>\n";
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
function writeTestResults($jpg,$ccclist,$bin,$process_str=''){
	if (!file_exists($jpg)) {
		$base = basename($jpg);
		$dir = dirname($jpg);
		if ($process_str === '') {
			$process_str = getProcessString();
		}
		if (preg_match('/[Ss]how/',$process_str)) {
			return "<font color='#990000'>The test results are not ready for display. Refresh the page after the command is run successfully. </font><br />\n";
		} else {
			return "<font color='#990000' size='+2'>An Error occurred - the image $base was not found in folder $dir</font><br />\n";
		}
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

// TODO: is this used anywhere???
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

function printDivJava() {
	# used for printing a sub division of the page
	# put the desired content in a division with id 'divforprint'
	# and use the following input in the form before the division
	#		<input type="button" value=" Print " onclick="printdivision();return false;" />
	$java = "<script language='javascript' type=\"text/javascript\" >\n";
	$java.= "	function printdivision() {\n";
	$java.= "		var head = \"<html><head></head><body>\";\n";
	$java.= "		var body = document.getElementById('divforprint');\n";
  $java.= "		var foot = \"</body></html>\";\n";
  $java.= "		newwindow = window.open(\"\");\n";
  $java.= "		newwindow.document.write(head + body.innerHTML + foot,'','');\n";
  $java.= "		newwindow.print();\n";
  $java.= "		newwindow.close();\n";
	$java.= "	}\n";
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
function writeJavaPopupFunctions($help='') 
{
	$helpsection = ($help === '' ) ? "help." : "help.".$help.".";

	$javafunc = "
  <style type='text/css'>
    input { border-style: solid; border-color: #9dae9b; }
    select { border-style: solid; border-color: #9dae9b; }

		span.info {
			width: 100px;
		}
  </style>\n";

	$javafunc .= "<script type='text/javascript' src='js/help.js'></script>\n";
	// TODO: prototype.js is a huge amount of javascript to include in every page. Can we reduce it?
	// Not sure which portion is actually used, but not including it breaks help popups.
	$javafunc .= "<script type='text/javascript' src='../js/prototype.js'></script>\n";
	$javafunc .= "<script type='text/javascript' src='../js/draglayer.js'></script>
  <script type='text/javascript'>

	overdiv='0'
	var ie = (document.all)? true:false\n";
// create the popups
	$javafunc .="
	function popLayer(a, id) {
		dhelp=$('dhelp')
		helpstr=eval('$helpsection'+a)
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

function imodWeightedBackProjRef() {
	return referenceBox("Dual-axis tomography: an approach with alignment methods that preserve resolution.", 1997, "D.N. Mastronarde", "J. Struct. Biol.", 120,3, 9441937, false, "doi:10.1006/jsbi.1997.3919", false);
}

function protomoRef() {
	return referenceBox("Accurate marker-free alignment with simultaneous geometry determination and reconstruction of tilt series in electron tomography.", 2006, "Winkler H, Taylor KA", "Ultramicroscopy.", 106, 3, 16137829, false, "doi:10.1016/j.ultramic.2005.07.007", false);
}

function imodRef() {
	return referenceBox("Computer visualization of three-dimensional image data using IMOD", 1996, "Kremer J.R., D.N. Mastronarde and J.R. McIntosh", "J. Struct. Biol.", 116, 1, 8742726, false, "doi:10.1006/jsbi.1996.0013", false);
}

function xmippRef() 
{
	return referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.", "J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");
}

// TODO: This should be revisited. 
function showReference( $method )
{
	switch ( $method ){
		case "eman":
			return emanRef();
			break;
		case "xmipp":
			return xmippRef();
			break;
		case "frealign":
			return frealignRef();
			break;
		case "imagic":
			return imagicRef();
			break;
		case "spider":
			return spiderRef();
			break;
		default:
			return appionRef();
	}
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
