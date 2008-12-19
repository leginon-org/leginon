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
	createTiltPairSubStackForm();
}

function createTiltPairSubStackForm($extra=false, $title='norefTiltPairSubStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$norefClassId=$_GET['norefClass'];
	$norefId=$_GET['noref'];
	$exclude=$_GET['exclude'];
	$norefClassfile=$_GET['file'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	if (!$description) $description = $_POST['description'];
	$runid = ($_POST['runid']) ? $_POST['runid'] : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$norefClassId) $norefClassId = $_POST['norefClass'];
	if (!$norefId) $norefId = $_POST['noref'];
	if (!strlen($exclude)) $exclude = $_POST['exclude'];
	if (!$norefClassfile) $norefClassfile = $_POST['file'];

	

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
	

	# get stack name
	$noref = $particle->getNoRefParams($norefId);
	$stackId = $noref['REF|ApStackData|stack'];
	$stackp = $particle->getStackParams($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];
	

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";
	echo"
					<b>Original Stack Information:</b> <br />
					Name & Path: $filename <br />	
					Stack ID: $stackId<br />
                     <input type='hidden' name='stackId' value='$stackId'>
					<br />\n";

	echo"
					<b>Reference Free Class Information:</b> <br />
					Name & Path: $norefClassfile <br />
					Noref Class ID: $norefClassId<br />
							<input type='hidden' name='norefClassId' value='$norefClassId'>
					<br />\n";

	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' value='$runid'><br />\n";
	echo docpop('outdir','<b>Output Directory:</b> ');
	echo "<input type='text' name='outdir' value='$outdir' size='38'><br />\n";
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
	$stackId=$_POST['stackId'];
	$norefClassId=$_POST['norefClassId'];
	$norefId=$_POST['norefId'];
	$outdir=$_POST['outdir'];
	$commit=$_POST['commit'];
	$exclude=$_POST['exclude'];

	$command.="norefTiltPairSubStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runid) createTiltPairSubStackForm("<b>ERROR:</b> Specify a runid");
	if (!$description) createTiltPairSubStackForm("<B>ERROR:</B> Enter a brief description");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;

	//putting together command
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="-n $runid ";
	$command.="--norefclass=$norefClassId ";
	$command.="-d \"$description\" ";
	$command.="--exclude=$exclude ";
	if ($outdir) $command.="-o $procdir ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Create SubStack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTiltPairSubStackForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createTiltPairSubStackForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Creating a SubStack", "Creating a SubStack");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>norefTiltPairSubStack.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>run id</td><td>$runid</td></tr>\n";
	echo "<tr><td>norefclass id</td><td>$norefClassId</td></tr>\n";
	echo "<tr><td>stack id</td><td>$stackId</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>outdir</td><td>$procdir</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
