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
	runUploadImage();
}

// Create the form page
else {
	createUploadImageForm();
}


function createUploadImageForm($extra=false, $title='UploadImage.py Launcher', $heading='Upload Images') {
	$particle = new particledata();
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$projectId = getProjectId();

	$formAction=$_SERVER['PHP_SELF'];
	if ($expId) $formAction.="?expId=$expId&projectId=$projectId";
	elseif ($projectId) $formAction.="?projectId=$projectId";

	$javafunctions .= writeJavaPopupFunctions('appion');
	$leginondata = new leginondata();

	processing_header($title,$heading,$javafunctions);
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	if ($expId) {
		$sessiondata = getSessionList($projectId, $expId);
		$sessioninfo = $sessiondata['info'];
		if (!empty($sessioninfo)) {
			$outdir=$sessioninfo['Image path'];
			$outdir=ereg_replace("leginon*","leginon",$outdir);
			$sessionname=$sessioninfo['Name'];
			$description=$sessioninfo['description'];
			$tem=$sessioninfo['InstrumentId'];
			$cam=$sessioninfo['CameraId'];
			echo "<input type='hidden' name='outdir' value='$outdir'>\n";
		}
	}
	// if no session name is set, set a default
	if (!$sessionname) {
		$prefix = strtolower(date('yMd'));
		for ($i=90; $i>=65; $i--) {
			$letter = strtolower(chr($i));
			$sessionname = $prefix.$letter;
			$testinfo = $leginondata->getSessionInfo($sessionname);
			//echo "<font size='+3'>$i:</font>\n";
			//print_r($testinfo);
			//echo "<br/><br/>\n";
			if (empty($testinfo))
				break;
		}
	}

	// Set any existing parameters in form
	$temval = ($_POST['tem']) ? $_POST['tem'] : $tem;
	$camval = ($_POST['cam']) ? $_POST['cam'] : $cam;
	$sessionname = ($_POST['sessionname']) ? $_POST['sessionname'] : $sessionname;
	$batch = ($_POST['batch']) ? $_POST['batch'] : $batch;
	$batch_check = ($_POST['batchcheck']=='off') ? '' : 'checked';
	$tiltgroup = ($_POST['tiltgroup']) ? $_POST['tiltgroup'] : 1;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$imgdir = ($_POST['imgdir']);
	$apix = ($_POST['apix']) ? $_POST['apix'] : "";;
	$binx = ($_POST['binx']) ? $_POST['binx'] : "1";
	$biny = ($_POST['biny']) ? $_POST['biny'] : "1";
	$kv = ($_POST['kv']) ? $_POST['kv'] : "";
	$mag = ($_POST['mag']) ? $_POST['mag'] : "";
	$df = ($_POST['df']) ? $_POST['df'] : "";
	$invert_check = ($_POST['invert_check']=='on') ? 'checked' : '';

	// Start Tables
	echo"<table class=tableborder>\n";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='15' cellspacing='5'>\n";
	echo"<tr><td valign='top'>\n";
	echo "<br/>\n";

	// Setup Project
	$projectdata = new project();
	if (!$expId && !$projectId) {
		echo "<b>Project:</b><br/>\n";
		echo "<select name='projectId'>";
		$projects=$projectdata->getProjects();
		foreach ($projects as $project) {
			$sel=($project['id']==$projectId) ? "selected" : "";
			echo "<option value='".$project['id']."' $sel >".$project['name']."</option>\n";
		}
		echo "</select>\n";
	} else {
		$projectinfo = $projectdata->getProjectInfo($projectId);
		echo "<font size='+1'><b>Project:</b>\n";
		echo $projectinfo['name']." <i>($projectId)</i></font>\n";
	}

	echo "<br/><br/>\n";

	// Setup Session Name
	echo docpop('uploadsession', 'Session Name:');
	echo "<br/>\n";
	echo "<input type='text' name='sessionname' value='$sessionname' size='15'>\n";

	echo "<br/><br/>\n";

	// Setup Session Name
	echo "<b>Session Description:</b><br/>";
	echo "<input type='text' name='description' size='46' value='$description'>";



	// Root directory
	/*	echo "<br/><br/>\n";

	echo "<b>Root directory to store images:</b>";
	echo "<br/>\n";
	echo "<input type='text' name='rootdir' size='55' value='$description'>";
	echo "<br/>\n";
	echo "<font size='-1'><i>(Session name will be appended to the end)</i></font>";*/

	echo "<br/><br/>\n";

	echo"</td></tr>\n";
	echo"<tr><td valign='top' class='tablebg'>\n";
	echo "<br/>\n";

	// Setup Instruments
	// Force to use the fake appion host to avoid accidental changing real calibration
	$instrumenthosts = array('appion');
	sort($instrumenthosts);
	$instrumenthostval = ($_POST[instrumenthost]) ? $_POST[instrumenthost] : $instrumenthosts[0];
	echo docpop('host', 'Host:');
	echo "<select name='instrumenthost' onchange=submit()>";
	foreach($instrumenthosts as $host) {
		$s = ($instrumenthostval==$host) ? 'selected' : 'not';
		echo "<option value=".$host." ".$s.">".$host."</option>\n";
	}
	echo"</select>";

	echo "<br/><br/>\n";

	// Setup Scopes
	$scopes = $leginondata->getScopes($instrumenthostval);
	$cameras = $leginondata->getCameras($instrumenthostval);
	echo docpop('scope', 'Scope:');
	echo "<select name='tem' onchange=submit()>";
	foreach($scopes as $sc) {
		$s = ($temval==$sc['id']) ? 'selected' : '';
		echo "<option value=".$sc['id']." ".$s." >".$sc['name']."</option>";
	}
	echo" </select>";

	// Setup Camera
	echo docpop('camera', 'Camera:');
	echo "
		<select name='cam' onchange=submit()>";
	foreach($cameras as $c) {
		echo $c['id'];
		$s = ($camval==$c['id']) ? 'selected' : 'not';
		echo "<option value=".$c['id']." ".$s." >".$c['name']."</option>";
	}
	echo"</select>";

	echo "<br/><br/>\n";

	// Setup Images in Group
	echo docpop('images_in_group', 'Number of images in each tilt series if any:');
	echo "<br/>\n<input type='text' name='tiltgroup' value='$tiltgroup' size='5'>\n";
	echo "<br/>\n";
	echo "<br/><input type='checkbox' name='invert_check' $invert_check>\n";
	echo "Invert image density\n";

	echo "<br/><br/>\n";
	echo "</td></tr>\n";
	echo "<tr><td>\n";

	echo "<hr/>\n";
	echo "<font size='+1'><b>Use one of two following options for upload:</b></font>\n";
	echo "<br/><br/>\n";

	// Setup batchfile
	echo "<font size='+1'>1. Specify a parameter file:</font><br/>\n";
	echo "&nbsp;\n";
	echo openRoundBorder();
	echo docpop('batchfile', 'Information file for the images (with full path):');
	echo "<br/>\n<input type='text' name='batch' value='$batch' size='45'>\n";
	echo "<br/>\n<input type='checkbox' NAME='batchcheck' $batch_check>\n";
	echo docpop('batchcheck','<B>Confirm existence and format of the information file</B>');

	echo "<br/><br/>\n";
	echo closeRoundBorder();
	echo "<br/>\n";

	// Enter parameters manually
	echo "<font size='+1'>2. Enter parameters manually:</font><br/>\n";
	echo "&nbsp;\n";
	echo openRoundBorder();
	echo "<table border='0'>\n";

	echo "<tr><td colspan='2'>\n";
		echo docpop('imgpath','Directory containing images');
		echo "<br/>\n";
		echo "<input type='text' name='imgdir' value='$imgdir' size='45'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('fileformat', 'file format:');
	echo "</td><td align='right'>\n";
		echo " <select name='fileformat'>\n";
		$filetypes = array("mrc","tif","dm3","dm2");
		foreach ($filetypes as $ftype) {
			$s = ($ftype==$_POST[fileformat]) ? ' selected' : '';
			echo "<option".$s.">$ftype</option>";
		}
		echo "</select>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('apix','pixel size (A):');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='apix' value='$apix' size='5' style='text-align:center'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('imgbin','binning in x:');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='binx' value='$binx' size='2' style='text-align:center'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('imgbin','binning in y:');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='biny' value='$biny' size='2' style='text-align:center'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('magnification', 'magnification:');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='mag' value='$mag' size='6' style='text-align:center'>\n";
	echo "</td></tr>\n";


	echo "<tr><td>\n";
		echo docpop('defocus', 'defocus (microns):');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='df' value='$df' size='4' style='text-align:center'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo docpop('kev','high tension (kV):');
	echo "</td><td align='right'>\n";
		echo "<input type='text' name='kv' value='$kv' size='3' style='text-align:center'>\n";
	echo "</td></tr>\n";

	echo "</table>\n";
	echo closeRoundBorder();

	echo"<tr><td align='center'>\n";

	// Launcher
	echo "<hr/><br/>\n";
	echo getSubmitForm("Upload Image");

	// End table
	echo"</td></tr>\n";
	echo"</table>\n";
	echo"</td></tr>\n";
	echo"</table>\n";
	echo"</form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runUploadImage() {
	/* *******************
	PART 1: Get variables
	******************** */
	// trim removes any white space from start and end of strings
	$sessionname = trim($_POST['sessionname']);
	$projectId = getProjectId();
	$batch = trim($_POST['batch']);
	$batch_check = trim($_POST['batchcheck']);
	$invert_check = trim($_POST['invert_check']);
	$tiltgroup = $_POST['tiltgroup']+0;
	$tem = $_POST['tem'];
	$cam = $_POST['cam'];
	$description=$_POST['description'];
	$_POST['runname'] = "imageloader";

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a session name was entered if upload an independent file
	if (!$sessionname) createUploadImageForm("<B>ERROR:</B> Enter a session name of the image");
	$leginon = new leginondata();
	$has_session = $leginon->getSessions('',false,$sessionname);
	$session_in_project = $leginon->getSessions('',$projectId,$sessionname);

	if ($has_session && !$session_in_project)
		createUploadImageForm("<B>ERROR:</B> You have entered an existing session not belonging to this project");

	if ($session_in_project)
		$warning = ("<B>Warning:</B>  Will append to an existing session with the original description");
	// add session to the command

	//make sure a description was provided
	if (!$description && !$session_in_project)
		createUploadImageForm("<B>ERROR:</B> Enter a brief description of the session");

	/* *******************
	PART 3: Create program command
	******************** */

	// start setting up the imageloader command
	$command = "imageloader.py ";
	$command.="--session=$sessionname ";

	// for inverting density
	if ($invert_check=='on') $command.="--invert ";

	//determine if a information batch file was provided
	if (!$batch) {
		$errormsg = "<b>ERROR:</b> If not specifying a parameter file, ";
		$imgdir = $_POST['imgdir'];
		if (!$imgdir)
			createUploadImageForm($errormsg."specify an image directory");
		$fileformat = $_POST['fileformat'];
		$apix = $_POST['apix'];
		if (!$apix)
			createUploadImageForm($errormsg."specify a pixel size");
		$binx = $_POST['binx'];
		$biny = $_POST['biny'];
		if (!($binx && $biny))
			createUploadImageForm($errormsg."specify both x and y binning");
		$mag = $_POST['mag'];
		if (!$mag)
			createUploadImageForm($errormsg."specify a magnification");
		$df = $_POST['df'];
		if (!$df)
			createUploadImageForm($errormsg."specify a defocus");
		if ($df > 0) $df = $df*-1;
		if ($df > -0.1)
			createUploadImageForm("<b>Error:</b> defocus must be in microns (i.e. -1.5)");
		$kv = $_POST['kv'];
		if (!$kv)
			createUploadImageForm($errormsg."specify the high tension");
		if ($kv > 1000)
			createUploadImageForm("<b>Error:</b> high tension must be in kilovolts (i.e. 120)");
		// add options to command
		$command.="--dir=$imgdir ";
		$command.="--filetype=$fileformat ";
		$command.="--apix=$apix ";
		$command.="--binx=$binx ";
		$command.="--biny=$biny ";
		$command.="--mag=$mag ";
		$command.="--df=$df ";
		$command.="--kv=$kv ";
	} elseif ($batch) {
		if ($batch_check && !file_exists($batch))
			createUploadImageForm("<B>ERROR:</B> Batch file does not exist");
		//make sure  the batch file contains 7 or 8 fields separated by tab at each line
		$bf = file($batch);
		foreach ($bf as $line) {
			$items = explode("\t",$line);
			if (count($items)!=7  && (count($items)!=8 && $tiltgroup > 1)) {
				$badbatch = true;
				break;
			}
		}
		// add batch file to command
		$command.="--batchparams=$batch ";
	}
	else {
		$badbatch = false;
	}
	if ($badbatch) createUploadImageForm("<B>ERROR:</B> Invalid format in the batch file");
	// make sure there are valid instrument
	if (!$tem) createUploadImageForm("<B>ERROR:</B> Choose a tem where the images are acquired");
	if (!$cam) createUploadImageForm("<B>ERROR:</B> Choose a camera where the images are acquired");

	// add rest of options to command
	$command.="--scopeid=$tem ";
	$command.="--cameraid=$cam ";
	$command.="--description=\"$description\" ";
	if ($tiltgroup >= 2)
		$command.="--tiltgroup=$tiltgroup ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadimage', 1);

	// if error display them
	if ($errors)
		createUploadImageForm($errors);
	exit;
}
?>
