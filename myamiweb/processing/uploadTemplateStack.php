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
	$alignId = $_GET['alignId'];
	$refs = $_GET['refs'];
	$exclude = $_GET['exclude'];
	$include = $_GET['include'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	processing_header($title,$heading,$javafunc);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","templatestacks",$outdir);

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
	
	echo"<INPUT TYPE='hidden' NAME='projectId' VALUE='$projectId'>\n";
	if ($clusterId) echo "<INPUT TYPE='hidden' NAME='clusterId' VALUE='$clusterId'>\n";
	elseif ($alignId) echo "<INPUT TYPE='hidden' NAME='alignId' VALUE='$alignId'>\n";
	if ($refs) echo "<INPUT TYPE='hidden' NAME='refs' VALUE='$refs'>\n";

	//query the database for parameters
	$particle = new particledata();
	$templateruns = 1;

	// set any default parameters
	$template_stack = ($_POST['template_stack']) ? $_POST['template_stack'] : '';
	$apix = ($_POST['apix']) ? $_POST['apix'] : '';
	$description = ($_POST['description']) ? $_POST['description'] : '';
	while (file_exists($outdir."/templatestack".($templateruns)))
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
	echo "<i>Output Directory: </i>".$outdir;
	echo "<br>";

	echo "<br/>\n";
	echo docpop('descr', '<b>Template Stack Description:<br></b>');
	echo "<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>";
	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	//if uploading a new template stack that does not yet exist in the database 
	if (!$clusterId && !$alignId) {
		echo "<br>\n";
		echo docpop('oldtemplatename', "<b>Template Stack Name with path: </b><br> \n");
		echo "<INPUT TYPE='text' NAME='template_stack' VALUE='$template_stack' SIZE='55'/>\n";
		echo "<br><br>\n";
		echo docpop('apix', "<b>&Aring;ngstroms per pixel </b><br>\n");
		echo "<INPUT TYPE='text' NAME='apix' VALUE='$apix' SIZE='5'/>\n";
		echo "<br><br>";			
	}	
	elseif ($clusterId || $alignId) {
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
	if (!$clusterId && !$alignId) {
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
	echo appionRef();
	processing_footer();
	exit;
}

function runUploadTemplateStack() {
	/* *******************
	PART 1: Get variables
	******************** */
	$clusterId = $_POST['clusterId'];
	$alignId = $_POST['alignId'];
	$refs = $_POST['refs'];
	$exclude = $_POST['exclude'];
	$include = $_POST['include'];
	$template_stack = $_POST['template_stack'];
	$stacktype = $_POST['stack_type'];
	$apix = $_POST['apix'];
	$description = $_POST['description'];
	$session = $_POST['sessionname'];
	$commit = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a description is provided
	if (!$description) 
		createUploadTemplateStackForm("<B>ERROR:</B> Enter a brief description of the template");

	//make sure angstroms per pixel is specified, or is retrieved from the database
	if ((!$apix && !$clusterId) && (!$apix && !$alignId)) 
		createUploadTemplateStackForm("<B>ERROR:</B> Enter a value for angstroms per pixel");

	//make sure template type is specified
	if ((!$stacktype && !$clusterId) && (!$stacktype && !$alignId)) 
		createUploadTemplateStackForm("<B>ERROR:</B> Enter the type of stack (i.e. class averages or forward projections)");

	// make sure that a template stack is specified, if there is no $clusterId or $alignId
	if ((!$clusterId && !$alignId) && (!$template_stack))
		createUploadTemplateStackForm("<B>ERROR:</B> Make sure the path to the template stack was specified");

	//make sure a session was selected
	if (!$session) createUploadTemplateStackForm("<B>ERROR:</B> Select an experiment session");

	//check if the template is an existing file 
	if ($clusterId == False && !file_exists($template_stack))
		$template_warning="File ".$template_stack." does not exist. "; 

	elseif (!$clusterId && !$alignId) $template_warning="File ".$template_stack." exists. Make sure that this is the file that you want!";
	

	/* *******************
	PART 3: Create program command
	******************** */

	//putting together command
	$command = "uploadTemplateStack.py ";
	if ($template_stack) {
		$command.="--templatestack=$template_stack ";
		$command.="--templatetype=$stacktype ";
		$command.="--apix=$apix ";
	}
	elseif ($clusterId || $alignId) {
		if ($clusterId)
			$command.="--clusterId=$clusterId ";
		else {
			if ($refs) $command.="--alignId=$alignId --references ";
			else $command.="--alignId=$alignId ";
		}
		$command.="--templatetype=clsavg ";
		if ($exclude) {
			$command.="--exclude=$exclude ";
		}
		elseif ($include) {
			$command.="--include=$include ";
		}
	}
	$command.="--session=$session ";
	$command.="--description=\"$description\" ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'templatestack', 1);

	// if error display them
	if ($errors)
		createUploadTemplateStackForm($errors);
	exit;
}

?>
