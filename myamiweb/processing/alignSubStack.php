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
	createNorefSubStackForm();
}

function createNorefSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$clusterId=$_GET['clusterId'];
	$alignId=$_GET['alignId'];
	
	$classfile=$_GET['file'];
	
	$exclude=$_GET['exclude'];
	
	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	$runid = ($_POST['runid']) ? $_POST['runid'] : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$clusterId) $clusterId = $_POST['clusterId'];
	if (!$alignId) $alignId = $_POST['alignId'];
	if (!strlen($exclude)) $exclude = $_POST['exclude'];

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
	
	//query the database for parameters
	$particle = new particledata();
	
	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";

	if ($clusterId) {
		echo"
					<b>Clustering Run Information:</b> <br />
					Name & Path: $classfile <br />
					Cluster Stack ID: $clusterId<br />
							<input type='hidden' name='clusterId' value='$clusterId'>
					<br />\n";
	}
	
	if ($alignId) {
		echo"
					<b>Clustering Run Information:</b> <br />
					Name & Path: $classfile <br />
					Align Stack ID: $alignId<br />
							<input type='hidden' name='alignId' value='$alignId'>
					<br />\n";
	}
	
	
	
	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' value='$runid'><br />\n";
	echo docpop('test','<b>Excluded Classes:</b> ');
	echo "<input type='text' name='exclude' value='$exclude' size='38'><br />\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='3'cols='70'>$description</textarea>\n";
	echo "<br />\n";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br />\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
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

	$runid=$_POST['runid'];
	$clusterId=$_POST['clusterId'];
	$alignId=$_POST['alignId'];
	$commit=$_POST['commit'];
	$exclude=$_POST['exclude'];

	$command.="alignSubStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runid) createNorefSubStackForm("<b>ERROR:</b> Specify a runid");
	if (!$description) createNorefSubStackForm("<B>ERROR:</B> Enter a brief description");

	//putting together command
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="-n $runid ";
	$command.="-d \"$description\" ";
	$command.="--class-list-drop=$exclude ";
	if ($clusterId) {
		$command.="--cluster-id=$clusterId ";
	} elseif ($alignId) {
		$command.="--align-id=$alignId ";
	} else {
		createNorefSubStackForm("<b>ERROR:</b> You need either a cluster Id or align ID");
	}
	
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Create SubStack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createNorefSubStackForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createNorefSubStackForm("<b>ERROR:</b> $sub");
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
	echo "<tr><td>run id</td><td>$runid</td></tr>\n";
	echo "<tr><td>cluster id</td><td>$clusterId</td></tr>\n";
	echo "<tr><td>align id</td><td>$alignId</td></tr>\n";
	echo "<tr><td>excluded classes</td><td>$exclude</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>commit</td><td>$commit</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
