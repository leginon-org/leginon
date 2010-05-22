<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['count']) {
	runLoopAgain();
} elseif ($_GET['progrunid']) {
	createLoopAgainForm();
} else {
	selectLoopAgainForm();
}

function programTableRow($progrunid, $sessionname, $formAction) {
	$particle = new particledata();
	$currentuser = $_SESSION['username'];

	$html = "";
	$html .= "<tr>\n";
	$progrunparams = $particle->getProgramRunParams($progrunid);
	// skip run if its the same session
	$html .= "  <td>".$progrunid."</td>\n";
	$html .= "  <td>".$progrunparams['progname'].".py</td>\n";
	$html .= "  <td>".$progrunparams['runname']."</td>\n";
	if ($sessionname != $progrunparams['sessionname'])
		$html .= "  <td><font color='#339933'>".$progrunparams['sessionname']."</font></td>\n";
	else
		$html .= "  <td><font color='#993333'>".$progrunparams['sessionname']."</font></td>\n";
	if ($currentuser == $progrunparams['username'])
		$html .= "  <td><font color='#339933'>".$progrunparams['username']."</font></td>\n";
	else
		$html .= "  <td><font color='#993333'>".$progrunparams['username']."</font></td>\n";
	if ($_GET['progrunid']) {
		$html .= "  <td></td>\n";
	} elseif ($sessionname != $progrunparams['sessionname'])	{
		$html .= "  <td><a class='btp1' href='".$formAction."&progrunid=$progrunid'>"
			."Rerun this program on this session</a></span></td>\n";
	} else {
		$html .= "  <td><i>already done</i></td>\n";
	}
	$html .= "</tr>\n";
	return $html;
}

function selectLoopAgainForm($extra=false, $title='Loop Again Launcher', $heading='Loop Again Launcher') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	//echo "Project ID: ".$projectId." <br/>\n";
	$formAction = $_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	echo "<FORM NAME='selectLoopAgainForm' method='POST' ACTION='$formAction'>\n";

	// --- Get Session Name --- //
	$sessiondata = getSessionList($projectId,$expId);
	$sessioninfo = $sessiondata['info'];
	$sessionname = $sessioninfo['Name'];

	// --- Get Loop Data --- //
	$particle = new particledata();
	$loopruns = $particle->getLoopProgramRuns();
	//echo "LOOP RUNS: '";
	//print_r($loopruns);
	//echo ($loopruns);
	//echo "'";
	if (!$loopruns || count($loopruns) == 0) {
		echo "<b>Project does not appion loop runs.</b>\n";
		exit(1);
	}

	echo "<h2>Select an Appion Loop run</h2>\n";
	echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$display_keys = array ( 'id', 'program', 'runname', 'session', 'user', '',);
	echo "<tr>\n";
	foreach($display_keys as $key) {
		echo "  <td><span class='datafield0'>".$key."</span></td>\n";
	}
	echo "</tr>\n";

	$currentuser = $_SESSION['username'];
	foreach ($loopruns as $looprun) {
		$progrunid = $looprun['id'];
		echo programTableRow($progrunid, $sessionname, $formAction);
	}
	echo "</table>\n";

	echo appionRef();

	processing_footer();
	exit(1);
}

function createLoopAgainForm($extra=false, $title='Loop Again Launcher', $heading='Loop Again Launcher') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$progrunid = $_GET['progrunid'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&progrunid=$progrunid";

	$javascript.= editTextJava();

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	echo "<FORM NAME='createLoopAgainForm' method='POST' ACTION='$formAction'>\n";

	// --- Get Session Name --- //
	$sessiondata = getSessionList($projectId,$expId);
	$sessioninfo = $sessiondata['info'];
	$sessionname = $sessioninfo['Name'];

	// --- Get Stack Data --- //
	$particle = new particledata();

	echo "<h2>Edit and submit an Appion Loop run</h2>\n";


	echo "<h3>Old processing info</h3>\n";
	echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		echo programTableRow($progrunid, $sessionname, $formAction);
	echo "</table>\n";
	echo "<br/>\n";

	// ----- Create list of parameters ------ //

	echo "<h3>Processing parameter info</h3>\n";
	$params = $particle->getProgramCommands($progrunid);
	echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";

	$notdone = array();
	echo "<tr><td colspan='3'><h4>Special parameters</h4></td></tr>\n";
	foreach ($params as $param) {
		if ($param['name'] == 'sessionname') {
			echo "<tr>\n";
			echo "  <td>".$param['name']."</td>\n";
			echo "  <td colspan='2'>$sessionname\n";
			echo "    <input type='hidden' name='sessionname' value='$sessionname' />\n";
			echo "  </td>\n";
			echo "</tr>\n";
		} elseif ($param['name'] == 'runname') {
			echo "<tr>\n";
			echo "  <td>".$param['name']."</td>\n";
			if ( substr($param['value'], -4) != "copy" )
				$runname = $param['value']."copy";
			else
				$runname = $param['value'];
			echo "  <td colspan='2'>\n";
			echo "    <input type='text' name='runname' value='"
				.$runname."' size=".(strlen($runname))." />\n";
			echo "  </td>\n";
			echo "</tr>\n";
		} elseif ($param['name'] == 'rundir') {
			echo "<tr>\n";
			echo "  <td>outdir</td>\n";
			$newrundir = ereg_replace($param['sessionname'], $sessionname, $param['value']);
			$newoutdir = dirname($newrundir);
			echo "  <td colspan='2'>\n";
			echo "    <input type='text' name='outdir' value='"
				.$newoutdir."' size=".(strlen($newoutdir))." />\n";
			echo "  </td>\n";
			echo "</tr>\n";
		} elseif ($param['name'] == 'projectid') {
			"";
		} else {
			// skip for later
			$notdone[] = $param;
		}
	}
	echo "<tr><td colspan='3'><h4>Normal parameters</h4></td></tr>\n";
	$count = 0;
	foreach ($notdone as $param) {
		$count++;
		echo "<tr>\n";
		echo "  <td>".$param['name']."</td>\n";
		echo "  <td>".$param['value']."</td>\n";
		echo "  <td>\n";
		//echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
		echo "    <input type='text' name='param$count' value='"
			.$param['usage']."' size=".(strlen($param['usage']))." />\n";
		echo "  </td>\n";
		echo "</tr>\n";
	}
	echo "</table>\n";
	echo "<input type='hidden' name='count' value='$count' />\n";

	echo getSubmitForm("Run Loop Program Again");

	echo appionRef();

	processing_footer();
	exit;
}

function runLoopAgain() {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$progrunid = $_GET['progrunid'];
	$count = $_POST['count'];

	// --- Get Session Name --- //
	$sessiondata = getSessionList($projectId,$expId);
	$sessioninfo = $sessiondata['info'];
	$sessionname = $sessioninfo['Name'];

	if (!$runname) 
		createLoopAgainForm("<B>ERROR:</B> No runname selected");

	if (!$outdir) 
		createLoopAgainForm("<B>ERROR:</B> No outdir selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// --- Get Program Data --- //
	$particle = new particledata();
	$progrunparams = $particle->getProgramRunParams($progrunid);
	$command = $progrunparams['progname'].".py ";

	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	$command.="--session=$sessionname ";

	for($i = 1; $i<=$count; $i++) {
		$origarg = $_POST['param'.$i];
		$arg = trim($origarg);
		$arg = ereg_replace(";.*$", "", $arg);
		$arg = ereg_replace("^[^-]*-", "-", $arg);
		if ($arg)
			$command .= "$arg ";
		//echo "param$i: '$origarg' -> '$arg'<br/>\n";
	}

	// submit job to cluster
	if ($_POST['process']=="Run Loop Program Again") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password))
			createLoopAgainForm("<B>ERROR:</B> Enter a user name and password");
		$progname = strtolower($progrunparams['progname']);
		$sub = submitAppionJob($command,$outdir,$runname,$expId,$progname);
		// if errors:
		if ($sub)
			createLoopAgainForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Loop Again Launcher","Loop Again Launcher");

		echo appionRef();

		echo"
		<table width='600' class='tableborder' border='1'>
		<tr><td colspan='2'>
		<b>Loop Again Command:</b><br/>
			$command
		</td></tr>
		<tr><td>run id</td><td>$runname</td></tr>
		<tr><td>run dir</td><td>$rundir</td></tr>\n";
		echo "</table>\n";
		processing_footer();
	}
	exit;
}



?>
