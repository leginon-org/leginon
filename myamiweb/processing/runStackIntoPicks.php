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
if ($_POST) {
	runStackIntoPicks();
} else {
	createStackIntoPicksForm();
}

function createStackIntoPicksForm($extra=false, $title='Run Stack Into Picks', $heading='Run Stack Into Picks') {
	$expId = $_GET['expId'];
	$projectId = (int) getProjectFromExpId($expId);
	//echo "Project ID: ".$projectId." <br/>\n";
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#dd0000'>$extra</FONT><br />\n";

	// --- Get Stack Data --- //
	$particle = new particledata();
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","extract/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	//$stackids = $particle->getStackIdsForProject($projectId, False);
	$stackids = $particle->getStackIds($expId, False);
	$lastprtlruns = count($particle->getParticleRunIds($sessionId, True));
	while (file_exists($sessionpath.'stackrun'.($lastprtlruns+1)))
		$lastprtlruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'stackrun'.($lastprtlruns+1);
	$description = $_POST['description'];
	$stackparam = $particle->getStackParams($stackids[0]['stackid']);
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;

	if ($stackids) {
		echo "<form name='stackform' method='post' action='$formAction'>\n";
		echo "<table border='1'>";
		echo "<tr><td colspan='4'><h2>New stack info:</h2>\n";
		echo docpop('runname','<b>Stack picking name:</b>');
		echo "<br/>\n";
		echo "<input type='text' name='runname' value='$runname'>\n";
		echo "<br/>\n";
		echo "<br/>\n";
		echo docpop('outdir','<b>Output Directory:</b>');
		echo "<br />\n";
		echo "<input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br />\n";
		echo "<br />\n";
		echo getSubmitForm("Run Stack Into Picks");
		echo "</td></tr>\n";
		echo "<tr><td colspan='4'><h2>Select stack to convert into picks:</h2>\n";
		foreach ($stackids as $stackdata) {
			$stackid = $stackdata['stackid'];
			echo "<tr><td>\n<input type='radio' name='stackid' value='$stackid'";
			if ($_POST['stack'.$stackid]) echo " checked";
			echo ">convert<br/>stack id $stackid\n</td><td>\n";
			echo ministacksummarytable($stackid);
			echo "</td></tr>\n";
		}
		echo "</table>";
		echo "</form>";
	} else {
		echo "<B>Project does not contain any stacks.</B>\n";
	}

	processing_footer();
	exit;
}

function runStackIntoPicks() {
	$expId = $_GET['expId'];
	$projectId = (int) getProjectFromExpId($expId);
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackid=$_POST['stackid'];

	if (!$stackid) 
		createStackIntoPicksForm("<B>ERROR:</B> No stack selected");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	$command ="stackIntoPicks.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	$command.="--stackid=$stackid ";
	$command.="--commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Stack Into Picks") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password))
			createStackIntoPicksForm("<B>ERROR:</B> Enter a user name and password");
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'makestack');
		// if errors:
		if ($sub)
			createStackIntoPicksForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Run Stack Into Picks","Run Stack Into Picks");
		echo"
		<table width='600' class='tableborder' border='1'>
		<tr><td colspan='2'>
		<b>Run Stack Into Picks:</b><br />
		$command
		</td></tr>
		<tr><td>run id</td><td>$runname</td></tr>
		<tr><td>stack id</td><td>$stackid</td></tr>
		<tr><td>out dir</td><td>$rundir</td></tr>
		<tr><td>commit</td><td>$commit</td></tr>
		</table>\n";
		processing_footer();
	}
	exit;
}



?>
