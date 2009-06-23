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
	runSubStack();
}

// Create the form page
else {
	createSubStackForm();
}

function createSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$reconId = $_GET['reconId'];
	if (!$reconId) $reconId = $_POST['reconId'];

	//query the database for parameters
	$particle = new particledata();
	$numrecons = count($particle->getReconIdsFromSession($expId, true));
	$reconIds = $particle->getReconIdsFromSession($expId, false);

	if ($reconId) {
		$defrunname = 'squatstack'.$reconId;
		$formAction .= "&reconId=$reconId";
	} else {
		$defrunname = 'squatstack'.$numrecons;
	}

	// Set any existing parameters in form
	$description = ($_POST['description']) ? $_POST['description'] : '';
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	$maxjump = ($_POST['maxjump']) ? $_POST['maxjump'] : 20;

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","stacks",$outdir);

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr />\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";

	$basename = basename($classfile);
	if ($reconId) {
		$reconlink = "reconreport.php?expId=$expId&reconId=$reconId";
		$recondata = $particle->getReconInfoFromRefinementId($reconId);
		$stackId = $particle->getStackIdFromReconId($reconId);
		echo"<b>Reconstruction Run Information:</b> <ul>\n"
			."<li>Recon ID/Name: [ $reconId ] <a href='$reconlink'>$recondata[name]</a>\n"
			."<li>Recon Description: $recondata[description]\n"
			."<li>Stack ID: $stackId\n"
			."<input type='hidden' name='reconId' value='$reconId'>\n"
			."</ul>\n";
	} else if($reconIds) {
		echo"
		Select Reconstruction Run:<br>
		<select name='reconId''>\n";
		foreach ($reconIds as $reconrunarray) {
			$localreconId = $reconrunarray['DEF_id'];
			$reconname=$reconrunarray['name'];
			$stackId = $particle->getStackIdFromReconId($localreconId);
			$totprtls=commafy($particle->getNumStackParticles($stackId));
			echo "<OPTION VALUE='$localreconId'";
			// select previously set prtl on resubmit
			echo ">$localreconId: $reconname ($totprtls particles)";
			echo "</OPTION>\n";
		}
		echo "</SELECT>\n";
		echo "<br/><br/>\n";
	} else {
		echo"<font color='red'><b>No reconstructions for this session</b></font>\n";
	}

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname' size='15'><br/><br/>\n";

	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	echo "Output directory:<i>$outdir</i><br/>\n";
	echo "<br/>\n";

	// Maximum Median Euler Jump
	echo '<b>Maximum Median Euler Jump value:</b> ';
	echo "<br/>\n<input type='text' name='maxjump' value='$maxjump' size='5'><br/>\n";

	if ($reconId) {
		echo "<img src='eulergraph.php?expId=$expId&hg=1&recon=$reconId'>";
		echo "<br/>\n";
	}
	echo "<br/>\n";

	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='2' cols='60'>$description</textarea>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br/>\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo "<br/>\n";
	echo getSubmitForm("Create SubStack");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runSubStack() {
	$expId = $_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];

	$reconId=$_POST['reconId'];
	$maxjump=$_POST['maxjump'];
	$commit=$_POST['commit'];

	$command.="jumperSubStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runname) createSubStackForm("<b>ERROR:</b> Specify a runname");
	if (!$description) createSubStackForm("<B>ERROR:</B> Enter a brief description");
	if (!$maxjump) createSubStackForm("<B>ERROR:</B> You must specify a maximum jump cutoff");
	if (!$reconId) createSubStackForm("<B>ERROR:</B> You must specify a reconId");

	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	//putting together command
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	$command.="--description=\"$description\" ";
	$command.="--max-jump=$maxjump ";
	$command.="--refinerunid=$reconId ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Create SubStack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createSubStackForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'makestack');
		// if errors:
		if ($sub) createSubStackForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Creating a SubStack", "Creating a SubStack");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>alignSubStack.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>run id</td><td>$runname</td></tr>\n";
	echo "<tr><td>cluster id</td><td>$clusterId</td></tr>\n";
	echo "<tr><td>align id</td><td>$alignId</td></tr>\n";
	echo "<tr><td>excluded classes</td><td>$exclude</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>commit</td><td>$commit</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
