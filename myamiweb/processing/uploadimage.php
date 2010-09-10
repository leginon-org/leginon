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
#require "inc/viewer.inc";
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
	$utypeval = ($_POST['uploadtype']) ? $_POST['uploadtype'] : 'normal';
	$sessionname = ($_POST['sessionname']) ? $_POST['sessionname'] : $sessionname;
	$batch = ($_POST['batch']) ? $_POST['batch'] : $batch;
	$batch_check = ($_POST['batchcheck']=='off') ? '' : 'checked';
	$imagegroup = ($_POST['imagegroup']) ? $_POST['imagegroup'] : 1;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$imgdir = ($_POST['imgdir']);
	$apix = ($_POST['apix']) ? $_POST['apix'] : "";;
	$binx = ($_POST['binx']) ? $_POST['binx'] : "1";
	$biny = ($_POST['biny']) ? $_POST['biny'] : "1";
	$kv = ($_POST['kv']) ? $_POST['kv'] : "";
	$mag = ($_POST['mag']) ? $_POST['mag'] : "";
	$df = ($_POST['df']) ? $_POST['df'] : "";
	$dflist = ($_POST['dflist']) ? $_POST['dflist'] : "";
	$tiltlist = ($_POST['tiltlist']) ? $_POST['tiltlist'] : "";
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

	// Choose Upload Type
	$uploadtypes = array('normal'=>'None','tiltseries'=>'Tilt Series');
	if (!$expId)
		$uploadtypes['defocalseries'] = 'Defocal Series';
	echo docpop('uploadtype', 'Images grouped by :');
	echo "<select name='uploadtype' onchange=submit()>";
	foreach($uploadtypes as $utype=>$udisplay) {
		$u = ($utypeval == $utype) ? 'selected' :'';
		echo "<option value='".$utype."' $u >".$udisplay."</option>";
	}
	echo " </select>";
	echo "<br/><br/>\n";

	// Setup Session Name
	echo docpop('uploadsession', 'Session Name:');
	echo "<br/>\n";
	if ($utypeval != 'defocalseries' && !($utypeval == 'tiltseries' && $imgdir)) {
		echo "<input type='text' name='sessionname' value='$sessionname' size='15'>\n";
	} else {
		echo "    Determined automatically";
	}
	echo "<br/><br/>\n";

	// Setup Session Description
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

	if ($utypeval != 'normal') {
		// Setup Images in Group
		echo docpop('images_in_group', 'Number of images in each tilt series:');
		echo "<br/>\n<input type='text' name='imagegroup' value='$imagegroup' size='5'>\n";
		echo "<br/>\n";
	}
	// invert images on upload if needed
	echo "<br/><input type='checkbox' name='invert_check' $invert_check>\n";
	echo "Invert image density\n";

		echo "<br/><br/>\n";
	echo "</td></tr>\n";
	echo "<tr><td>\n";

	echo "<hr/>\n";
	// Upload parameter options are determined by the upload type and whether a choice has been made previously
	// Currently defocal series can only be uploaded by uploadImages.py which could not be used 
	// for adding more images, for example
	$paramtypes = array(($utypeval != 'defocalseries' && !$imgdir),(!$batch && !($utypeval == 'tiltseries' && $expId)));
	if ($paramtypes[0] && $paramtypes[1]) {
		echo "<font size='+1'><b>Use one of two following options for upload:</b></font>\n";
		echo "<br/><br/>\n";
	}
	if ($paramtypes[0]) {
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
	}
	// Title choices
	if ($paramtypes[0] && $paramtypes[1]) {
			echo "<font size='+1'>2. Enter parameters manually:</font><br/>\n";
	} elseif ($paramtypes[1]) {
		echo "<font size='+1'>Upload all images in the directory using these parameters:</font><br/>\n";
	}
	if ($paramtypes[1]) {
		// Enter parameters manually
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
		if ($utypeval == 'normal')
			$filetypes = array("mrc","tif","dm3","dm2");
		else
			$filetypes = array("mrc");
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
		echo docpop('kev','high tension (kV):');
		echo "</td><td align='right'>\n";
		echo "<input type='text' name='kv' value='$kv' size='3' style='text-align:center'>\n";
		echo "</td></tr>\n";

		if ($utypeval == 'defocalseries') {
			echo "<tr><td>\n";
			echo docpop('defociilist', 'defocii list (microns):');
			echo "</td><td align='right'>\n";
			echo "<input type='text' name='dflist' value='$dflist' size='30' style='text-align:center'>\n";
			echo "</td></tr>\n";
		} else {
			echo "<tr><td>\n";
			echo docpop('defocus', 'defocus (microns):');
			echo "</td><td align='right'>\n";
			echo "<input type='text' name='df' value='$df' size='4' style='text-align:center'>\n";
			echo "</td></tr>\n";
		}

		if ($utypeval == 'tiltseries') {
			echo "<tr><td>\n";
			echo docpop('tiltlist', 'tilt angle list (degrees):');
			echo "</td><td align='right'>\n";
			echo "<input type='text' name='tiltlist' value='$tiltlist' size='30' style='text-align:center'>\n";
			echo "</td></tr>\n";
		}

		echo "</table>\n";
		echo closeRoundBorder();
	}
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
	$projectId = getProjectId();
	// trim removes any white space from start and end of strings
	$sessionname = trim($_POST['sessionname']);
	$batch = trim($_POST['batch']);
	$batch_check = trim($_POST['batchcheck']);
	$invert_check = trim($_POST['invert_check']);
	$imagegroup = $_POST['imagegroup']+0;
	$tem = $_POST['tem'];
	$cam = $_POST['cam'];
	$uploadtype = $_POST['uploadtype'];
	$tiltlist = $_POST['tiltlist'];

	$outdir = $_POST['outdir'];

	// determine which upload script to use
	if (!$batch)
		$uploadscript = ($uploadtype == 'normal') ? 'imageloader': 'uploadImages';
	else
		$uploadscript = 'imageloader';
	// start setting up the imageloader command
	$command = $uploadscript.".py ";
	$command.="--projectid=".$projectId." ";

	$leginon = new leginondata();

	if ($uploadscript == 'imageloader') {
		//make sure a session name was entered if upload an independent file
		if (!$sessionname) createUploadImageForm("<B>ERROR:</B> Enter a session name of the image");
		$has_session = $leginon->getSessions('',false,$sessionname);
		$session_in_project = $leginon->getSessions('',$projectId,$sessionname);

		if ($has_session) {
			if (!$leginon->onlyUploadedImagesInSession($has_session[0]['id'])) {
				createUploadImageForm($errormsg."Session contains images not from  'appion' Host is not available for uploading more images");
			}
			if ($uploadtype == 'defocalseries')
				createUploadImageForm("<B>ERROR:</B> Defocal series can not be uploaded to an existing session");
		}
		if ($has_session && !$session_in_project)
			createUploadImageForm("<B>ERROR:</B> You have entered an existing session not belonging to this project");

		if ($session_in_project)
			$warning = ("<B>Warning:</B>  Will append to an existing session with the original description");
		// add session to the command
		$command.="--session=$sessionname ";
	}

	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description && !$session_in_project)
		createUploadImageForm("<B>ERROR:</B> Enter a brief description of the session");

	// for inverting density
	if ($invert_check=='on') $command.="--invert ";

	//determine if a information batch file was provided
	if (!$batch) {
		$errormsg = "<b>ERROR:</b> ";
		$imgdir = $_POST['imgdir'];
		if (!$imgdir)
			createUploadImageForm($errormsg."Specify an image directory");
		$fileformat = $_POST['fileformat'];
		$apix = $_POST['apix'];
		if (!$apix)
			createUploadImageForm($errormsg."Specify a pixel size");
		$binx = $_POST['binx'];
		$biny = $_POST['biny'];
		if (!($binx && $biny))
			createUploadImageForm($errormsg."Specify both x and y binning");
		$mag = $_POST['mag'];
		if (!$mag)
			createUploadImageForm($errormsg."Specify a magnification");
		if ($uploadtype != 'defocalseries') {
			$df = $_POST['df'];
			if (!$df)
				createUploadImageForm($errormsg."Specify a defocus");
			$dfarray = array($df);
		} else {
			$dflist = $_POST['dflist'];
			if (!$dflist) 
				createUploadImageForm($errormsg."Specify a defocii list");
			$dfarray = explode(',',trim($dflist));
			if (count($dfarray) != $imagegroup)
				createUploadImageForm($errormsg."Specify matched image-per-group and defocii list");
		}
		$tiltanglearray = array();
		if ($uploadtype == 'tiltseries') {
			$tiltlist = $_POST['tiltlist'];
			if (!$tiltlist) 
				createUploadImageForm($errormsg."Specify a tilt angle list");
			$tiltanglearray = explode(',',trim($tiltlist));
			if (count($tiltanglearray) != $imagegroup)
				createUploadImageForm($errormsg."Specify matched image-per-group and tilt-angle list");
			$rtiltarray = array();
			foreach($tiltanglearray as $ta)
				$rtiltarray[] = sprintf('%.5f', $ta * 3.14159 / 180.0);
			$tiltanglearray = $rtiltarray;
		}
		$mdfarray = array();
		foreach($dfarray as $df) {
			if ($df > 0) $df = $df*-1;
			if ($df > -0.1)
				createUploadImageForm("<b>Error:</b> defocus must be in microns (i.e. -1.5)");
			$mdfarray[] = $df * 1e-10;
		}
		$kv = $_POST['kv'];
		if (!$kv)
			createUploadImageForm($errormsg."specify the high tension");
		if ($kv > 1000)
			createUploadImageForm("<b>Error:</b> high tension must be in kilovolts (i.e. 120)");
		// add options to command
		if ($uploadscript == 'imageloader') {
			// imageloader.py
			$command.="--dir=$imgdir ";
			$command.="--filetype=$fileformat ";
			$command.="--apix=$apix ";
			$command.="--binx=$binx ";
			$command.="--biny=$biny ";
			$command.="--df=$df ";
			if ($imagegroup >= 2)
				$command.="--tiltgroup=$imagegroup ";
		} else {
			// uploadImages.py
			$command.="--image-dir=$imgdir ";
			$mpix = $apix*1e-10;
			$command.="--mpix=$mpix ";
			$command.="--type=$uploadtype ";
			$command.="--images-per-series=$imagegroup ";
			if (count($mdfarray) > 1) 
				$command.="--defocus-list=".implode(',',$mdfarray)." ";
			else
				$command.="--defocus=".$mdfarray[0]." ";
			if ($uploadtype == 'tiltseries')
				$command.="--angle-list=".implode(',',$tiltanglearray)." ";
		}
		$command.="--mag=$mag ";
		$command.="--kv=$kv ";

	} elseif ($batch) {
		if ($batch_check && !file_exists($batch))
			createUploadImageForm("<B>ERROR:</B> Batch file does not exist");
		//make sure  the batch file contains 7 or 8 fields separated by tab at each line
		$bf = file($batch);
		foreach ($bf as $line) {
			$items = explode("\t",$line);
			if (count($items)!=7  && (count($items)!=8 && $imagegroup > 1)) {
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
	$scopes = $leginon->getScopes('appion');
	$cameras = $leginon->getCameras('appion');
	$tem = $scopes[0]['id'];
	$cam = $cameras[0]['id'];
	if (!$tem || !$cam) createUploadImageForm("<B>ERROR:</B> Database does not contain instruments for appion image upload");

	// add rest of options to command
	if ($uploadscript == 'imageloader') {
		$command.="--scopeid=$tem ";
		$command.="--cameraid=$cam ";
	}
	$command.="--description=\"$description\" ";
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef(); // main appion ref
	/* *******************
	PART 5: Show or Run Command
	******************** */
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadimage', 1);

	// if error display them
	if ($errors)
		createuploadImageForm($errors);
	exit;
}
?>
