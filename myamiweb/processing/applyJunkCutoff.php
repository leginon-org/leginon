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
	runApplyJunkCutoff();
}

// Create the form page
else {
	createApplyJunkCutoffForm();
}

function createApplyJunkCutoffForm($extra=false, $title='sortJunkStack.py Launcher', $heading='Sort Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId=$_GET['stackId'];
	$partnum=$_GET['partnum'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&stackId=$stackId" : "";
	$formAction.=($partnum) ? "&partnum=$partnum" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$runid = ($_POST['runid']) ? $_POST['runid'] : 'sortjunksubstack'.$stackId;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$stackId) $stackId = $_POST['stackId'];

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
  
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	//query the database for parameters
	$particle = new particledata();
	
	# get stack name
	$stackp = $particle->getStackParams($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];
	echo "<input type='hidden' name='box' value='$boxsize'>\n";

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";
	echo"
					<b>Stack information:</b> <br />
					name & path: $filename <br />	
					ID: $stackId<br />
                                        <input type='hidden' name='stackId' value='$stackId'>
					<br />\n";
	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' value='$runid'><br />\n";
	echo "<b>Particle number:</b><br />\n";
	echo "<input type='text' name='partnum' value='$partnum' width='5'><br />\n";
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
	echo getSubmitForm("Apply Junk Cutoff");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runApplyJunkCutoff() {
	$expId = $_GET['expId'];

	$runid=$_POST['runid'];
	$partnum=$_POST['partnum'];
	$stackId=$_POST['stackId'];
	$outdir=$_POST['outdir'];
	$commit=$_POST['commit'];

	$command.="subStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runid) createApplyJunkCutoffForm("<b>ERROR:</b> Specify a runid");
	if (!$partnum) createApplyJunkCutoffForm("<b>ERROR:</b> Specify a particle number");
	if (!$description) createApplyJunkCutoffForm("<B>ERROR:</B> Enter a brief description");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;

	//putting together command
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="-n $runid ";
	$command.="--no-meanplot ";
	$command.="--sorted ";
	$command.="--last $partnum ";
	$command.="-s $stackId ";
	$command.="-d \"$description\" ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Apply Junk Cutoff") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createApplyJunkCutoffForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createApplyJunkCutoffForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Apply Junk Cutoff", "Apply Junk Cutoff");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>sortJunkStack.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>run id</td><td>$runid</td></tr>\n";
	echo "<tr><td>stack id</td><td>$stackId</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>outdir</td><td>$procdir</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
