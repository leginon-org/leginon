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
require_once "html_elements.inc";
require_once "publication.inc";

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

// consider making this a static function in cluster.inc
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
	$hostArray = $proc_list[0];

	// only show host selection if there are more than 1
	if (count($proc_list) > 1){
		foreach ($proc_list as $host) {
			if ($host['host'] == $_POST['processinghost']) {
				$hostArray = $host;
			}
			$s = ($host['host'] == $_POST['processinghost']) ? "selected" : "";
			$h[]="<option value='".$host['host']."' ".$s." >".$host['host']."</option>\n";
		}
		$html="<select name=\"processinghost\" onchange='this.form.submit()'>\n";
		$html.=join("\n",$h);
		$html.="</select>";
	} else {
		$html="<b>".$hostArray['host'].":</b>\n";
		$html.="<input type='hidden' name=\"processinghost\" value='".$proc_list[0]['host']."'>\n";
	}
	
	// TODO: would be nice to change the javascript so that the entire page is not reloaded when new 
	// host selected.
	// Add queues
	if ($hostArray['queues']) {
		$queues = $hostArray['queues'];
		$selectedQueue = $_POST['queue'];
		$q = array(); //the list of queue options in the select field
		
		if ( count($queues) > 1 ) {
			foreach ($queues as $queue) {
				$s = ($queue == $selectedQueue) ? "selected" : "";
				$q[] = "<option value='".$queue."' ".$s." >".$queue."</option>\n";
			}
			$html.="<select name=\"queue\">\n";
			$html.=join("\n",$q);
			$html.="</select>";
		} else {
			$html.="<input type='hidden' name=\"queue\" value='".$queues[0]."'>\n";
		}
	}
	
	return $html;
}

function getSubmitForm($name="Run", $displayhost=true, $warning=false, $button="On") {
	if ($button == "On") {
		if ( $_POST['testimage'] )
			# Refresh Test Results avoids resubmit to cluster that would rerun the test
			$html = "<input type='submit' name='process' value='Refresh Test Results' onclick='pleasewait()'>\n";
		$html.="<input type='submit' name='process' value='Just Show Command' onclick='pleasewait()'>\n";
	}
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
	if (file_exists($stackimgfile))
		return (displayFileSize((int) filesize($stackimgfile)));
}

function displayFileSize($fsize) {
	if ($fsize > 1073741824)
	$size = sprintf("%.2f GB", $fsize/1073741824);
	else
	$size = sprintf("%.1f MB", $fsize/1048576);
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

function processing_header($title,$heading=false,$headerstuff=false,$pleaseWait=false,$showmenu=true,$printDiv=false, 
							$guideURL="http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing") 
{
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

	// If the user is logged in, note if this is an advanced user
	$_SESSION['advanced_user'] = isAdvancedUser();

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
	$expinfo = $sessioninfo;
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
	//next line is for hiding advanced features
	$html.= "
	<script type='text/javascript'>
	function toggle(divID) {
		var ele = document.getElementById(divID);
		var text = document.getElementById(divID+'_toggle');
		if(ele.style.display == 'block') {
		   ele.style.display = 'none';
		   text.innerHTML = 'Show '+divID;
		   text.style.color = 'blue';
		} else {
		   ele.style.display = 'block';
		   text.innerHTML = 'Hide '+divID;
		   text.style.color = 'red';
		}
	}
	</script>
	";
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
		if (!empty($expId)) {
			// Some forms need the class name to be specified in the url.
			if (!empty($_GET['form'])) {
				$form = $_GET['form'];
				$formAction=$_SERVER['PHP_SELF']."?expId=$expId&form=$form";
			} else { 
				$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
			}
		}
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
	$html.= "<li><a href='procsummary.php?expId=$expId'>[Appion Stats]</a></li>\n";
	$html.= "<li><font size=+1><b><a target='_blank' href='$guideURL'>[User Guide]</a></b></font></li>\n";
	$html.= "</div>\n";
	$html.= "<li><b>Project:</font></b> ".$proj_link."</li>\n";
	if ($session_link) $html.= "<li><b>Session:</b> ".$session_link."</li>\n";
	if ($expinfo) $html.= "<li><b>Image Path:</b> ".$expinfo['Image path']."</li>\n";
	
	// To display a notice to users on the processing header, add the following line to the myami/config.php file:
	// define('STARTUP_MESSAGE', "Your Message here");
	if (defined('STARTUP_MESSAGE') && STARTUP_MESSAGE != '') {
		$html.= "<li><b>Important Notice:</b> ".STARTUP_MESSAGE."</li>\n";
	}

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
		require_once "menuprocessing.php";
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
	$cluster = checkClusterType($user);
	if ($cluster == 'sge') {
		$cmd = "qstat -u ".$user." | egrep '^[0-9]'";
		$subjobs = exec_over_ssh($processhost, $user, $pass, $cmd, true, $port=22, $max_time=10);
#		print_r($subjobs);
	}
	else {
		$cmd = "qstat -au ".$user." | egrep '^[0-9]'";
		$subjobs = exec_over_ssh($processhost, $user, $pass, $cmd, true, $port=22, $max_time=10);
	}
	return $subjobs;
}

function checkClusterType($user) {
	$appioncfg = "~".$user."/.appion.cfg";
#	$appioncfg = "/data2/log-l/.appion.cfg";
//	echo $appioncfg;
	if (file_exists($appioncfg)) {
		$contents = file_get_contents($appioncfg);
		$contents = explode("\n", $contents);
		foreach($contents as $line) {
			if (strpos($line,'ProcessingHostType')!== false) {
				$str = explode("=", $line);
				$cluster = $str[1];
			}
		}
	}
	return strtolower($cluster);
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


function getNumberOfProcsPerNode( $processingHost ) 
{
	$cluster = new Cluster( $processingHost );
	$ppn = $cluster->getPpnDef();
	
	return $ppn;
}

function getMaxNumberOfProcsPerNode( $processingHost ) 
{
	$cluster = new Cluster( $processingHost );
	$ppn = $cluster->getPpnMax();
	
	return $ppn;
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
		$wrapper = getAppionWrapper($processhost);
		if ($wrapper) $command = $wrapper." ".$command;
		return $command;
}

function getAppionWrapper($processhost=false) 
{
	if ( USE_APPION_WRAPPER ) {
		if ($processhost === false) {
			$processhost = getSelectedProcessingHost();
		}
		$cluster = new Cluster( $processhost );
		$wrapper = $cluster->getWrapperPath();
		$wrapper = $wrapper ? $wrapper : APPION_WRAPPER_PATH;
	}
	return $wrapper;
}


/**************************************/
function showOrSubmitCommand($command, $headinfo, $jobtype, $nproc, $testimg=False, $nodes=0, $ppn=0) 
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
		//Only allow alphanumeric _- characters in runname
		if ($runname != preg_replace("/[^A-Za-z0-9_-]/", "", $runname))
			return "<b>ERROR:</b> Only alphanumeric characters in runname";
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
	$command .= "--expid=$expId ";
	if (!preg_match("/--jobtype=/", $command))
	$command .= "--jobtype=$jobtype ";
		
	// Get the processing host
	$processhost = getSelectedProcessingHost();

	if ($_POST['process'] == "Refresh Test Results" && $testimg) {		
		// if we are testing an image, return to the parameter page 
		return;
	}	

	// until uploadimage works with appionJob submission, it is not allowed to do so
	if ($_POST['process'] != "Just Show Command" && $jobtype != 'uploadimage') {
		// Option 1: selected the run button
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) {
			return "<B>ERROR:</B> Enter a user name and password";
		}

		$errors = submitAppionJob($command, $outdir, $runname, $expId, $jobtype, $testimg, False, False, $nproc, $ppn, $nodes);
		
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
		$bits = preg_split("% %", $command);
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

function addProcessingHostParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime, $queue )
{
	if (!preg_match("/--ppn=/", $command) ) {
		if ($ppn < 1) {
			// set to use default ppn if 0
			$ppn = getNumberOfProcsPerNode($processhost);
		}
		$ppnmax = getMaxNumberOfProcsPerNode($processhost);
		if ($ppn >  $ppnmax) {
			// set to use max ppn if very large
			$ppn = $ppnmax;
		}
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
	if (!preg_match("/--queue=/", $command) && $queue)
		$command .= " --queue=$queue ";
		
	return $command;		
}

// Put the command into format:
// <wrapper> runjob.py <wrapper> somejob.py --param1=x -- param2=y
// for generic jobs or
// <wrapper> runjob.py --appionwrapper=<wrapper> --param1=x -- param2=y
// for jobs that need to create a type specific job file.
function addJobSubmitParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime, $queue )
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
	$command = addProcessingHostParams($command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime, $queue);
	
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
	$queue = $_POST['queue'];

	// Add parameters that are only needed if submitting the job from the web server
	$command = addJobSubmitParams( $command, $processhost, $nproc, $ppn, $nodes, $walltime, $cputime, $queue );
	
	//Check if filesystem is full
	$cmd = "df $outdir";
	$fscheck = exec_over_ssh($processhost,$user,$pass,$cmd,True);
	if ($fscheck === false ){
		$errMsg = "Could not determine if filesystem space is available for $outdir from $processhost: ";
		$errMsg .= pconnError();
		return $errMsg;
	}
	$fsbits = preg_split("% %", trim($fscheck));
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
			$ingood = (preg_match('%'.$gooddisk.'%',$rundir))? True: $ingood;
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
	$rvalue = exec_over_ssh($processhost, $user, $pass, $cmd, False);
	if ($rvalue === false ){
		$errMsg = "Could not create run directory on $processhost: ";
		$errMsg .= pconnError();
		return $errMsg;
	}
	// check that the directory was created successfully
	$fileExists = file_exists($rundir);
  	if ($fileExists===false) {
  		$errMsg = "Warning: The output directory (<font color=black>$rundir</font>) may not have been created on $processhost.  <br>";
  		// Don't return yet, perhaps we don't have access to the dir from the web server.
  		// This message will be prepended to a later occuring error.
  	}
	
	if ($testimg) {
		//submit directly to head node on cluster if testing 1 image
		$cmd = "cd $rundir; $command; exit;";
		$jobdata = exec_over_ssh($processhost, $user, $pass, $cmd, True, $port=22, $max_time=160);
		if ( empty($jobdata) ) {		
			$errMsg .= "Job submission to $processhost failed for command:<br> <font color=black size='-1'>$command</font> <br> ";
			$errMsg .= pconnError();
			return $errMsg;
		} else {
			return;
		}
	}


	// Set names of cluster job file and output log
	// These should match the names being assigned on the python side where the files are created
	$jobfile = "$runname.appionsub.job";
	$logfile = "$runname.appionsub.log";
	
	// insert cluster job data and set job as queued
	$particle = new particleData();
	$jobid = $particle->insertClusterJobData($processhost, $rundir, '', $rundir, $jobfile, $expId, $jobtype, $user);
	
	// Add the job id to the command string
	$command .= "--jobid=$jobid ";
		
	$apcmd = $command;
	//$cmd = "cd $rundir; $apcmd;\n";
	$cmd = $apcmd;
	
	// write output page
	$checkUrl = "checkAppionJob.php?expId=$expId&jobId=$jobid";
	//$autoRedirect = '';
	$autoRedirect = " <meta http-equiv='refresh' content='10;url=$checkUrl'>\n";

	// I find that the redirection here does not give me enough time to view any errors. Removing for now.
	//processing_header("Appion Job Submission","Appion Job Submission", $autoRedirect);
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
	$jobdata = exec_over_ssh($processhost, $user, $pass, $cmd, True, $port=22, $max_time=20);
	if ( empty($jobdata) ) {		
		$errMsg .= "Error: Job submission to $processhost failed. <br>  ";
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
		echo "ERROR in job submission. Check ".$rundir." to ensure you have write access to this directory. You can also copy the command from above into ".$processhost." terminal for more info. </br></br>Note for systems administrators: ensure the ,.appio.cfg configuration file is correct (http://emg.nysbc.org/redmine/projects/appion/wiki/Configure_appioncfg)\n".$jobdata."\n".$matches[0][0]."\n";
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
	echo "<p><a href='$checkUrl'>[Check status of this job]</a><p>\n";
	echo "<p><font color='#990000'>do NOT hit 'reload' -- it will re-submit job</font><p>\n";
	processing_footer();
	exit;
}

/**************************************/
function writeTestResults($jpg,$ccclist,$bin,$process_str='')
{
	// First, see if we are just showing the command or refreshing the results
	if ($process_str === '') {
		$process_str = getProcessString();
	}
	$showcmd = preg_match('/[Ss]how/',$process_str);
	if ( !$showcmd )	{
		$showcmd = preg_match('/[Rr]efresh/',$process_str);
	}

	// Remove any white space in the image name
	$jpg = preg_replace('/\s+/','',$jpg);
	
	clearstatcache(); // clear cache
	$fileExists = is_file($jpg);
  	if ( ($fileExists===false) && $showcmd ) {
		return "<font color='#990000'>The test results ($jpg) are not ready for display. Use <b>Refresh Test Results</b> button below to display it after the command is run successfully. </font><br />\n";
  	}
	
	
	// refs #1706. Give the test command a chance to complete. For some reason,
	// the file_exists() function does not seem to detect the existance of the file
	// in a timely manner. This will often loop for 30 seconds, even if the file 
	// existed 7 seconds into the loop. Not sure why.
	$start_time 	= time();
  	$max_time 		= 60; // constant, max time in seconds that we will wait for processing to complete 
  	$curr_wait_time = 0; // the number of seconds this function has waited for the processing to complete
	$mod_time 		= 0; // seconds since an existing file was modified 
	// $max_mod_time : constant, if the file was modified within this many seconds of the current time, 
	// assume it is new and not the result of a previous run. In my testing, the actual time got up to 24 seconds.
	$max_mod_time	= 35;  
  	
  	// Make sure we don't show the user a previous test result, and processing has completed.
	// Wait for 1. the file to exist, 2. an existing file to be modified, or 3. timer to run out
	if (!$showcmd) {
		do {
  		clearstatcache(); // filemtime() and file_exists() results are cached, clear it.
			$fileExists = is_file($jpg);
  		if ($fileExists) {
				$file_time = filemtime($jpg);
				$mod_time = abs($start_time - $file_time);
  		}
			$curr_wait_time = time() - $start_time;	
			if ($curr_wait_time > $max_time) break;
		} while ( (($fileExists===false) && ($curr_wait_time < $max_time )) || (($fileExists===true) && ($mod_time > $max_mod_time)) );
	}
  
	clearstatcache(); // filetime() and file_exists() results are cached, clear it.
  	$fileExists = is_file($jpg);
  	if ($fileExists===false) {
		$base = basename($jpg);
		$dir = dirname($jpg);
		return "<font color='#990000' >The image $base was not found in folder $dir.<br /> Processing may be taking longer than expected. Click <b>Refresh Test Results</b> when the image is available to display.</font><br />\n";
	}

	// The results are ready, display them.
	$html = "<center>\n";
	$html.= "<a href='loadimg.php?filename=$jpg&coff=1' target='blank'>\n";
	$html.= "<img src='loadimg.php?filename=$jpg&h=256&coff=1'></a>\n";
	if (count($ccclist)>1)
	$html.= "<br />\n";
	foreach ($ccclist as $ccc) {
		$html.= "<a href='loadimg.php?filename=$ccc&coff=1' target='blank'>\n";
		$html.= "<img src='loadimg.php?filename=$ccc&h=256&coff=1'></a>\n";
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

function hasPatternInArrayKeys($post_array,$pattern='/updateDesc/') {
	$has_pattern = false;
	if (is_array($post_array) && count($post_array)) {
		$keys = array_keys($post_array);
		foreach ($keys as $k) if (preg_match($pattern,$k)) { $has_pattern=true; break; };
	}
	return $has_pattern;
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
		helpstr=eval('help.'+a)
		if(!helpstr){helpstr=eval('$helpsection'+a)}
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
		if (preg_match('%'.$eulerstr.'%', $pngfile))
		$pngimages['eulerfiles'][] = $pngfile;
		else
		$pngimages['pngfiles'][] = $pngfile;
	}
	sort($pngimages['pngfiles']);
	sort($pngimages['eulerfiles']);
	//print_r($pngimages)."<br/>";
	return $pngimages;
}

// These functions return html reference citation boxes
function emanRef() { return showReference("eman"); }
function spiderRef() { return showReference("spider"); }
function imagicRef() { return showReference("imagic"); }
function appionRef() { return showReference("appion"); }
function frealignRef() { return showReference("frealign"); }
function initModelRef() { return showReference("initmodel"); }
function imodWeightedBackProjRef() { return showReference("imodweightedbackproj"); }
function protomoRef() { return showReference("protomo"); }
function imodRef() { return showReference("imod"); }
function xmippRef() { return showReference("xmipp"); }

// TODO: This should be revisited. 
function showReference( $method )
{
	$pub = new Publication($method);
	return $pub->getHtmlTable();
}

/**************************************/
// Moved this function to html_elements class. 
// TODO: Since this function is called from everywhere, will wait to 
// remove this wrapper until after 2.2 release.
function referenceBox($title, $year, $authorlist, $journal, $volume=false, $issue=false, $pmid=false, $pmcid=false, $doi=false, $logo=false) 
{
	return html_elements::referenceBox($title, $year, $authorlist, $journal, $volume, $issue, $pmid, $pmcid, $doi, $logo);
}

?>
