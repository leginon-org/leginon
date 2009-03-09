<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runMaxLikeAlign();
} else {
	createMaxLikeAlignForm();
}

function createMaxLikeAlignForm($extra=false, $title='uploadMaxlikeAlignment.py Launcher', $heading='Upload Maximum Likelihood Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectFromExpId($sessionId);
		$formAction=$_SERVER['PHP_SELF'];
	}

	$javascript .= writeJavaPopupFunctions('appion');	
	$javascript .= editTextJava();
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra)
		echo "<span style='font-size: larger; color:#bb3333;'>$extra</span><br />\n";

	// connect to particle database
	$particle = new particledata();
	$maxlikejobs = $particle->getFinishedMaxLikeJobs($projectId);

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	if (!$maxlikejobs) {
		echo "<font color='red'><B>No Maximum Likelihood Jobs for this Project</B></FONT>\n";
	} else {
		foreach ($maxlikejobs as $maxlikejob) {
			$jobid = $maxlikejob['DEF_id'];
			echo "<form name='viewerform' method='POST' action='$formAction&jobid=$jobid'>\n";

			if ($_POST['hideJob'.$jobid] == 'hide') {
				$particle->updateHide('ApMaxLikeJobData', $jobid, '1');
				$maxlikejob['hidden']='1';
			} elseif ($_POST['hideUndoJob'.$jobid] == 'unhide') {
				$particle->updateHide('ApMaxLikeJobData', $jobid, '0');
				$maxlikejob['hidden']='0';
			}

			echo openRoundBorder();
			echo "<table cellspacing='8' cellpading='2' border='0'>\n";

			echo "<tr><td colspan='5'>\n";
			$nameline = "<span style='font-size: larger; color:#111111;'>\n";
			$nameline .= "Job Id: $jobid &nbsp;\n";
			$nameline .= " ".$maxlikejob['runname'];
			$nameline .= "</span>\n";
			if ($maxlikejob['hidden'] == 1) {
				$nameline.= " <font color='#cc0000'>HIDDEN</font>\n";
				$nameline.= " <input class='edit' type='submit' name='hideUndoJob".$jobid."' value='unhide'>\n";
				$display_keys['hidden'] = "<font color='#cc0000'>HIDDEN</font>";
			} else $nameline.= " <input class='edit' type='submit' name='hideJob".$jobid."' value='hide'>\n";

			echo apdivtitle($nameline);
			echo "</td></tr>\n";

			$avgfile = $maxlikejob['path']."/average.mrc";
			if (file_exists($avgfile)) {
				echo "<tr><td align='left' rowspan='30' align='center' valign='top'>";
				echo "<img src='loadimg.php?filename=$avgfile&s=100' height='100'><br/>\n";
				echo "<i>final reference image</i>\n";
				echo "</td></tr>\n";
			}

			//echo "<tr><td colspan='2'>\n";
			//echo print_r($maxlikejob)."<br/><br/>";
			//echo "</td></tr>\n";

			$display_keys['date time'] = $maxlikejob['DEF_timestamp'];
			$display_keys['path'] = $maxlikejob['path'];
			echo "<input type='hidden' name='path".$jobid."' value='".$maxlikejob['path']."'>\n";
			$display_keys['file prefix'] = $maxlikejob['timestamp'];

			$refstackname = "part".$maxlikejob['timestamp']."_average.hed";
			$refstack = $maxlikejob['path']."/".$refstackname;
			if (file_exists($refstack))
				$display_keys['reference stack'] = "<a target='stackview' HREF='viewstack.php?"
					."file=$refstack&expId=$expId'>".$refstackname."</a>";

			echo "<input type='hidden' name='timestamp".$jobid."' value='".$maxlikejob['timestamp']."'>\n";
			foreach($display_keys as $k=>$v) {
				echo formatHtmlRow($k,$v);
			}

			echo "<tr><td colspan='2'>\n";
			echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
			echo docpop('commit','<B>Commit to Database</B>');
			echo "</td></tr>\n";

			echo "<tr><td colspan='2'>\n";
			echo getSubmitForm("Upload Job $jobid");
			echo "</td></tr>\n";

			echo "</table>\n";
			echo closeRoundBorder();
			echo "<br/>\n";
			echo "</form>\n";
		}
	}


	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}
	processing_footer();
	exit;
}

function runMaxLikeAlign() {
	$expId=$_GET['expId'];
	$jobid = $_GET['jobid'];
	$timestamp=$_POST['timestamp'.$jobid];
	$rundir=$_POST['path'.$jobid];
	$commit = ($_POST['commit']=="on") ? true : false;

	//make sure a stack was selected
	//if (!$rundir)
	//	createMaxLikeAlignForm("<B>ERROR:</B> Unknown output directory");

	// make sure outdir ends with '/' and append run name
	$outdir = dirname($rundir);
	$runname = basename($rundir);
	if (substr($outdir,-1,1)!='/') $outdir.='/';

	// setup command
	$command="uploadMaxlikeAlignment.py ";
	$command.="--rundir=$rundir ";
	if ($timestamp) $command.="-t $timestamp ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	$command.="--projectid=".$_SESSION['projectId']." ";

	// submit job to cluster
	if (substr($_POST['process'],0,11)=="Upload Job ") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMaxLikeAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'maxlikeali');
		// if errors:
		if ($sub) createMaxLikeAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Max Like Align Upload Params","Max Like Upload Params");
		echo "<table width='600' class='tableborder' border='1'>";
		echo "
			<tr><td colspan='2'>
			<b>MaxLike Alignment Command:</b><br />
			$command
			</td></tr>
			<tr><td>process</td><td>".substr($_POST['process'],0,11)."</td></tr>
			<tr><td>jobid</td><td>$_GET[jobid]</td></tr>
			<tr><td>timestamp</td><td>$timestamp</td></tr>
			<tr><td>run name</td><td>$runname</td></tr>
			<tr><td>run directory</td><td>$rundir</td></tr>
			<tr><td>commit</td><td>$commit</td></tr>
			</table>\n";
		processing_footer();
	}
}
?>
