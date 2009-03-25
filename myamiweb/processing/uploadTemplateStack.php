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
	$javafunc .= writeJavaPopupFunctions('appion');

        // check if coming directly from a session
	$expId=$_GET['expId'];
	$clusterId = $_GET['clusterId'];
	$exclude = $_GET['exclude'];
	$include = $_GET['include'];

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	processing_header($title,$heading,$javafunc);
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
	if ($clusterId) echo "<INPUT TYPE='hidden' NAME='clusterId' VALUE='$clusterId'>\n";

	//query the database for parameters
	$particle = new particledata();
	$templateruns = 1;

	// set any default parameters
	$template_stack = ($_POST['template_stack']) ? $_POST['template_stack'] : '';
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$description = ($_POST['description']) ? $_POST['description'] : '';
	while (file_exists($rundir."/templatestack".($templateruns)))
		$templateruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'templatestack'.$templateruns;
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";

	echo "<br>\n";
	echo docpop('runid','<b>Runname (New Name for Template Stack, no spaces)<br></b>');
	echo "<input type='text' name='runname' value='$runname' SIZE='50'/>\n";
	echo "<br>\n";

	echo "<br>";
	echo "<i>Output Directory: </i>".$rundir;
	echo "<br>";

	echo "<br/>\n";
	echo docpop('descr', '<b>Template Stack Description:<br></b>');
	echo "<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>";
	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	//if uploading a new template stack that does not yet exist in the database 
	if (!$clusterId) {
		echo "<br>\n";
		echo docpop('oldtemplatename', "<b>Template Stack Name with path: </b><br> \n");
		echo "<INPUT TYPE='text' NAME='template_stack' VALUE='$template_stack' SIZE='55'/>\n";
		echo "<br><br>\n";
		echo docpop('apix', "<b>&Aring;ngstroms per pixel </b><br>\n");
		echo "<INPUT TYPE='text' NAME='apix' VALUE='$apix' SIZE='5'/>\n";
		echo "<br><br>";			
	}
	
	elseif ($clusterId) {
		echo "<br>";
		if ($exclude) {
			echo docpop('excludeClassum', '<b>Excluded Class Averages: </b><br>');
			echo "<TEXTAREA NAME='exclude' ROWS='3' COLS='70'>$exclude</TEXTAREA>";
			echo "<br><br>";
		}
		elseif ($include) {
			echo docpop('includeClassum', '<b>Included Class Averages: </b><br>');
			echo "<TEXTAREA NAME='include' ROWS='3' COLS='70'>$include</TEXTAREA>";
			echo "<br><br>";
		}
	}
	
	// give option of choosing the type of images if not coming directly from clustering stack
	if (!$clusterId) {
		echo "<INPUT TYPE='radio' NAME='stack_type' VALUE='clsavg'/>";
		echo docpop('templatetype', '<b> Class Averages </b>');
		echo "<br/>";

		echo "<INPUT TYPE='radio' NAME='stack_type' VALUE='forward_proj'/>";
		echo docpop('templatetype', '<b> Forward Projections </b>');
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
	$clusterId = $_POST['clusterId'];
	$exclude = $_POST['exclude'];
	$include = $_POST['include'];
	$template_stack = $_POST['template_stack'];
	$stacktype = $_POST['stack_type'];
	$apix = $_POST['apix'];
	$runname = $_POST['runname'];
	$description = $_POST['description'];
	$session = $_POST['sessionname'];
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	//make sure new name does not have spaces
	if (!$runname) createUploadTemplateStackForm("<B>ERROR:</B> Enter a new name for the template stack, as it will be stored in templatestacks directory");
	if (ereg(" ", $runname)) {
		$runname = ereg_replace(" ", "_", $runname);
	}

	//make sure a description is provided
	if (!$description) createUploadTemplateStackForm("<B>ERROR:</B> Enter a brief description of the template");

	//make sure angstroms per pixel is specified, or is retrieved from the database
	if (!$apix && !$clusterId) createUploadTemplateStackForm("<B>ERROR:</B> Enter a value for angstroms per pixel");

        //make sure template type is specified
        if (!$stacktype && !$clusterId) createUploadTemplateStackForm("<B>ERROR:</B> Enter the type of stack (i.e. class averages or forward projections)");

	//make sure a session was selected
	if (!$session) createUploadTemplateStackForm("<B>ERROR:</B> Select an experiment session");

	//check if the template is an existing file 
	if (!file_exists($template_stack) && !$clusterId) {
		$template_warning="File ".$template_stack." does not exist. "; 
	}
	elseif (!$clusterId) $template_warning="File ".$template_stack." exists. Make sure that this is the file that you want!";
	

	// set runname as time
//	$runname = "templatestack".getTimestring();

	//putting together command
	$command = "uploadTemplateStack.py ";
	if ($template_stack) {
		$command.="--templatestack=$template_stack ";
		$command.="--templatetype=$stacktype ";
		$command.="--apix=$apix ";
	}
	elseif ($clusterId) {
		$command.="--clusterId=$clusterId ";
		$command.="--templatetype=clsavg ";
		if ($exclude) {
			$command.="--exclude=$exclude ";
		}
		elseif ($include) {
			$command.="--include=$include ";
		}
	}
	
	$command.="--projectid=$projectId ";
	$command.="--session=$session ";
	$command.="--runname=$runname ";
	$command.="--description=\"$description\" ";
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

		$sub = submitAppionJob($command,$rundir,$runname,$expId,'templatestack',True);
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
