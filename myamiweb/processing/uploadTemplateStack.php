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
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadTemplateStack();
}

// Create the form page
else {
	createUploadTemplateStackForm();
}

function createUploadTemplateStackForm($extra=false, $title='UploadTemplate.py Launcher', $heading='Upload a template') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$clusterId = $_GET['clusterId'];

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// set any default parameters
	$template_stack = ($_POST['template_stack']) ? $_POST['template_stack'] : '';
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$description = ($_POST['description']) ? $_POST['description'] : '';	
	$newname = ($_POST['newname']) ? $_POST['newname'] : '';
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$rundir=$sessioninfo['Image path'];
	$rundir=ereg_replace("leginon","appion",$rundir);
	$rundir=ereg_replace("rawdata","templatestacks",$rundir);

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
		echo "<input type='hidden' name='rundir' value='$rundir'>\n";
	}
	
	echo"<INPUT TYPE='hidden' NAME='projectId' VALUE='$projectId'>\n";
	
	//query the database for parameters
	$particle = new particledata();

	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";

	//if uploading a new template stack that does not yet exist in the database 
	if (!$clusterId) {
		echo "<br>\n";
		echo "Template Stack Name with path: <br> \n";
		echo "<INPUT TYPE='text' NAME='template_stack' VALUE='$template_stack' SIZE='55'/>\n";
		echo "<br><br>\n";
		echo "&Aring;ngstroms per pixel <br>\n";
		echo "<INPUT TYPE='text' NAME='apix' VALUE='$apix' SIZE='5'/>\n";
		echo "<br>";			
	}

	echo "<br>";
	echo "New Name for Template Stack (no spaces)<br>";
	echo "<INPUT TYPE='text' NAME='newname' VALUE='$newname' SIZE='50'/>\n";
	echo "<br>";

	echo "<br/>\n";
	echo "Template Stack Description:<br>";
	echo "<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>";
	echo "</TD></tr><TR><TD VALIGN='TOP'>";
	
	// give option of choosing the type of images if not coming directly from clustering stack
	if (!$clusterId) {
		echo "<label><INPUT TYPE='radio' NAME='stack_type' VALUE='clsavg'/></label> Class Averages";
		echo "<br/>";

		echo "<label><INPUT TYPE='radio' NAME='stack_type' VALUE='forward_proj'/></label> Forward Projections";
	        echo "<br/><br/>";
	}
	
	echo "<INPUT TYPE='checkbox' NAME='commit' $commit>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br/>\n";


	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'><hr/>";
	echo getSubmitForm("Upload Template Stack");
	echo "</td></tr></table></form>\n";
	processing_footer();
	exit;
}

function runUploadTemplateStack() {
	$expId = $_GET['expId'];
	$rundir = $_POST['rundir'];
	$projectId = $_POST['projectId'];
	$template_stack = $_POST['template_stack'];
	$stacktype = $_POST['stack_type'];
	$apix = $_POST['apix'];
	$newname = $_POST['newname'];
	$description = $_POST['description'];
	$session = $_POST['sessionname'];
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	//make sure new name does not have spaces
	if (!$newname) createUploadTemplateStackForm("<B>ERROR:</B> Enter a new name for the template stack, as it will be stored in templatestacks directory");
	if (ereg(" ", $newname)) {
		$newname = ereg_replace(" ", "_", $newname);
	}

	//make sure a description is provided
	if (!$description) createUploadTemplateStackForm("<B>ERROR:</B> Enter a brief description of the template");

	//make sure angstroms per pixel is specified, or is retrieved from the database
	if (!$apix) createUploadTemplateStackForm("<B>ERROR:</B> Enter a value for angstroms per pixel");

        //make sure template type is specified
        if (!$stacktype) createUploadTemplateStackForm("<B>ERROR:</B> Enter the type of stack (i.e. class averages or forward projections)");

	//make sure a session was selected
	if (!$session) createUploadTemplateStackForm("<B>ERROR:</B> Select an experiment session");

	//check if the template is an existing file 
	if (!file_exists($template_stack)) {
		$template_warning="File ".$template_stack." does not exist. "; 
	}
	else $template_warning="File ".$template_stack." exists. Make sure that this is the file that you want!";
	

	// set runname as time
	$runname = "templatestack".getTimestring();

	//putting together command
	$command = "uploadTemplateStack.py ";
	if ($template_stack) {
		$command.="--templatestack=$template_stack ";
		$command.="--templatetype=$stacktype ";
		$command.="--newname=$newname ";
		$command.="--apix=$apix ";
	}
	
	$command.="--projectid=$projectId ";
	$command.="--session=$session ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";


	// submit job to cluster
	if ($_POST['process']=="Upload Template Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadTemplateStackForm("<B>ERROR:</B> You must be logged in to submit");

		if (!file_exists($template_stack)) {
        		createUploadTemplateStackForm("File ".$template_stack." does not exist. ");
		 }

		$sub = submitAppionJob($command,$rundir,$runname,$expId,'runUploadTemplateStack',True);
		// if errors:
		if ($sub) createUploadTemplateStackForm("<b>ERROR:</b> $sub");

		$status = "template stack uploaded to the database";
		// check that upload finished properly
		$jobf = $rundir.'/'.$runname.'/'.$runname.'.appionsub.log';
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i]) || ereg("command not found",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Template Stack Upload", "Template Stack Upload");
		echo "$status\n";
	}
	else {
		processing_header("Upload Template Stack Command", "Upload Template Stack Command");
		if ($template_warning) echo"$template_warning<br />";
	}
	//rest of the page
	echo"
	<br/>
	<table class='tableborder' width='600' border='1'>
	<tr><td colspan='2'>
	$command
	<br/><br/>
	</TD></tr>
	<TR><td>template stack name</TD><td>$template_stack</TD></tr>
	<TR><td>session</TD><td>$session</TD></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	<TR><td>description</TD><td>$description</TD></tr>";

	echo"
	</table>\n";
	processing_footer();
}

?>
