<?php
/**
 *      The Leginon software is Copyright under
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
#require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/html_elements.inc";

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

	$html_elements = new html_elements();
	$formAction=$_SERVER['PHP_SELF'];
	if ($expId) $formAction.="?expId=$expId&projectId=$projectId";
	elseif ($projectId) $formAction.="?projectId=$projectId";

	$javafunctions .= writeJavaPopupFunctions('appion');
	$leginondata = new leginondata();

	if ($extra) {
		$extrainput = "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	if ($expId) {
		$from_existing_session = true;
		$sessiondata = getSessionList($projectId, $expId);
		$sessioninfo = $sessiondata['info'];
		if (!empty($sessioninfo)) {
			$outdir=$sessioninfo['Image path'];
			$outdir=preg_replace("%/rawdata%","",$outdir);
			$sessionname=$sessioninfo['Name'];
			$description=$sessioninfo['Purpose'];
			$outdirinput = "<input type='hidden' name='outdir' value='".$outdir."'>\n";
		}
	}
	// if no session name is set, set a default
	if (!$sessionname) {
		$prefix = strtolower(date('yMd'));
		for ($i=90; $i>=65; $i--) {
			$letter = strtolower(chr($i));
			$sessionname = $prefix.$letter;
			$has_session = $leginondata->checkSessionNameExistance($sessionname,false);
			$session_is_reserved = $leginondata->checkSessionReservation($sessionname);
			if (!$has_session && !$session_is_reserved)
				break;
		}
	}

	// Set any existing parameters in form
	$utypeval = ($_POST['uploadtype']) ? $_POST['uploadtype'] : 'normal';
	$sessionname = ($_POST['sessionname']) ? $_POST['sessionname'] : $sessionname;
	$batch = ($_POST['batch']) ? $_POST['batch'] : $batch;
	$batch_check = ($_POST['batchcheck']=='off') ? '' : 'checked';
	$imagegroup = ($_POST['imagegroup']) ? $_POST['imagegroup'] : 1;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$imgdir = ($_POST['imgdir']);
	$apix = ($_POST['apix']) ? $_POST['apix'] : "";
	$kv = ($_POST['kv']) ? $_POST['kv'] : "";
	$mag = ($_POST['mag']) ? $_POST['mag'] : "";
	$df = ($_POST['df']) ? $_POST['df'] : "";
	$dflist = ($_POST['dflist']) ? $_POST['dflist'] : "";
	$az = ($_POST['az']) ? $_POST['az'] : "";
	$tiltlist = ($_POST['tiltlist']) ? $_POST['tiltlist'] : "";
	$doselist = ($_POST['doselist']) ? $_POST['doselist'] : "";
	$serialem_stack = ($_POST['serialem_stack']) ? $_POST[''] : "";
	$serialem_mdoc = ($_POST['serialem_mdoc']) ? $_POST[''] : "";
	$voltage = ($_POST['voltage']) ? $_POST[''] : "voltage";
	$invert_check = ($_POST['invert_check']=='on') ? 'checked' : '';
	$default_cs = ($from_existing_session) ? $leginondata->getCsValueFromSession($expId):'2.0';
	$cs = ($_POST['cs']) ? $_POST['cs'] : $default_cs;


	// Setup Project
	$projectdata = new project();
	if (!$expId && !$projectId) {
		$projectinput = "<b>Project:</b><br/>\n";
		$projectinput .= "<select name='projectId'>";
		$projects=$projectdata->getProjects();
		foreach ($projects as $project) {
			$sel=($project['id']==$projectId) ? "selected" : "";
			$projectinput .= "<option value='".$project['id']."' $sel >".$project['name']."</option>\n";
		}
		$pojectinput .= "</select>\n";
	} else {
		$projectinfo = $projectdata->getProjectInfo($projectId);
		$projectinput .= "<font size='+1'><b>Project:</b>\n";
		$projectinput .=  $projectinfo['name']." <i>($projectId)</i></font>\n";
	}


	// Choose Upload Type
	$uploadtypes = array('normal'=>'None','tiltseries'=>'Tilt Series','serialem_tiltseries'=>'SerialEM Tilt Series');
	if (!$expId)
		$uploadtypes['defocalseries'] = 'Defocal Series';
	$uploadtypeinput = docpop('uploadtype', '<b>Images grouped by:</b>');
	$uploadtypeinput .= "<select name='uploadtype' onchange=submit()>";
	foreach($uploadtypes as $utype=>$udisplay) {
		$u = ($utypeval == $utype) ? 'selected' :'';
		$uploadtypeinput .= "<option value='".$utype."' $u >".$udisplay."</option>";
	}
	$uploadtypeinput .= " </select>";

	// Setup Session Name
	$sessioninput = docpop('uploadsession', '<b>Session Name:</b>');
	$sessioninput .= "<br/>\n";

	if ($from_existing_session) {
		$sessioninput .= $sessionname."<input type='hidden' name='sessionname' value='$sessionname'>\n";
	} else {
		if ($utypeval != 'defocalseries' && !($utypeval == 'tiltseries' && $imgdir)) {
			$sessioninput .= "<input type='text' name='sessionname' value='$sessionname' size='15'>\n";
		} else {
		$sessioninput .= "    Determined automatically";
		}
	}

	// Setup Session Description
	$descriptioninput = "<b>Session Description:</b><br/>";
	if ($from_existing_session) {
		$descriptioninput .= $description."<input type='hidden' name='description' value='$description'>\n";
	} else {
		$descriptioninput .= "<input type='text' name='description' size='46' value='$description'>";
	}

	if (($utypeval != 'normal') && ($utypeval != 'serialem_tiltseries')) {
		// Setup Images in Group
		$imagegroupinput = docpop('images_in_group', 'Number of images in each tilt series:');
		$imagegroupinput .= "<br/>\n<input type='text' name='imagegroup' value='$imagegroup' size='5'>\n";
		$imagegroupinput .= "<br/>\n";
	}
	// scope cs value
	$csinput = docpop('cs', 'Scope Cs value:');
	if ($from_existing_session) {
		$csinput .= $cs."<input type='hidden' name='cs' value='$cs'>\n";
	} else {
		$csinput .= "<input type='text' name='cs' value='$cs' size='8' style='text-align:center'>\n";
	}
	$csinput .= " mm";
	$csinput .=  "&nbsp;(<a href='http://en.wikipedia.org/wiki/Spherical_aberration'>wiki\n";
	$csinput .=  "<img border='0' src='img/external.png'></a>)\n";

	// invert images on upload if needed
	$invertinput = "<input type='checkbox' name='invert_check' $invert_check>\n";
	$invertinput .= "Invert image density\n";

	// Upload parameter options are determined by the upload type and whether a choice has been made previously
	// Currently defocal series can only be uploaded by uploadImages.py which could not be used 
	// for adding more images, for example
	$paramtypes = array(($utypeval != 'defocalseries' && !$imgdir),(!$batch && !($utypeval == 'tiltseries' && $expId)));
	$tiltseriestype = array(($utypeval == 'serialem_tiltseries'));
	if (!$tiltseriestype[0]) {
		if ($paramtypes[0] && $paramtypes[1]) {
			$optiontitle = "<font size='+1'><b>Use one of two following options for upload:</b></font>\n";
		}
		if ($paramtypes[0]) {
			// Setup batchfile
			$fileinput = "<font size='+1'>1. Specify a parameter file:</font><br/>\n";
			$fileinput .= "&nbsp;\n";
			$fileinput .= openRoundBorder();
			$fileinput .= docpop('batchfile', 'Information file for the images (with full path):');
			$fileinput .= "<br/>\n<input type='text' name='batch' value='$batch' size='45'>\n";
			$fileinput .= "<br/>\n<input type='checkbox' NAME='batchcheck' $batch_check>\n";
			$fileinput .= docpop('batchcheck','<B>Confirm existence and format of the information file</B>');
	
			$fileinput .= "<br/><br/>\n";
			$fileinput .=  closeRoundBorder();
		}
		// Title choices
		if ($paramtypes[0] && $paramtypes[1]) {
			$paramtitle = "<font size='+1'>2. Enter parameters manually:</font><br/>\n";
		} elseif ($paramtypes[1]) {
			$paramtitle = "<font size='+1'>Upload all images in the directory using these parameters:</font><br/>\n";
		}
		if ($paramtypes[1]) {
			// Enter parameters manually
			$open_keyinput = "&nbsp;\n";
			$open_keyinput .= openRoundBorder();
			$open_keyinput .= "<table border='0'>\n";
	
			$keyinput_dir = "<tr><td colspan='2'>\n";
			$keyinput_dir .= docpop('imgpath','Directory containing images');
			$keyinput_dir .= "<br/>\n";
			$keyinput_dir .= "<input type='text' name='imgdir' value='$imgdir' size='45'>\n";
			$keyinput_dir .= "</td></tr>\n";
	
			$keyinput_format = "<tr><td>\n";
			$keyinput_format .=  docpop('fileformat', 'file format:');
			$keyinput_format .= "</td><td align='right'>\n";
			$keyinput_format .= " <select name='fileformat'>\n";
			if ($utypeval == 'normal')
				$filetypes = array("mrc","tif","dm3","dm2");
			else
				$filetypes = array("mrc");
			foreach ($filetypes as $ftype) {
				$s = ($ftype==$_POST[fileformat]) ? ' selected' : '';
				$keyinput_format .= "<option".$s.">$ftype</option>";
			}
			$keyinput_format .= "</select>\n";
			$keyinput_format .= "</td></tr>\n";
	
			$keyinput_apix = $html_elements->justifiedInputTableRow
					('apix','pixel size (A):','apix',$apix,5);
			$keyinput_mag = $html_elements->justifiedInputTableRow
					('magnification','magnification:','mag',$mag,6);
			$keyinput_ht = $html_elements->justifiedInputTableRow
					('kev','high tension (kV):','kv',$kv,3);
			if ($utypeval == 'defocalseries') {
				$keyinput_def = $html_elements->justifiedInputTableRow
						('defociilist','defocii list (microns):','dflist',$dflist,30);
			} else {
				$keyinput_def = $html_elements->justifiedInputTableRow
						('defocus','defocus (microns):','df',$df,4);
			}
			if ($utypeval == 'tiltseries') {
				$keyinput_az = $html_elements->justifiedInputTableRow
						('azimuth','tilt azimuth (degrees):','az',$az,3);
			}
			if ($utypeval == 'tiltseries') {
				$keyinput_tilt = $html_elements->justifiedInputTableRow
						('tiltlist','tilt angle list (degrees):','tiltlist',$tiltlist,30);
			}
			if ($utypeval == 'tiltseries') {
				$keyinput_dose = $html_elements->justifiedInputTableRow
						('doselist','dose list (e-/Å^2):','doselist',$doselist,30);
			}
	
			$close_keyinput = "</table>\n";
			$close_keyinput .= closeRoundBorder();
		}
	} else {
		if ($expId) {
			$optiontitle = "<font size='+1'><b>Enter the path of a containing SerialEM stacks and mdocs:</b></font>\n";
			$open_keyinput .= openRoundBorder();
			$open_keyinput .= "<table border='0'>\n";
			$keyinput_dir = "<tr><td colspan='2'>\n";
			$keyinput_dir .= docpop('serialem_dir','SerialEM directory path');
			$keyinput_dir .= "<br/>\n";
			$keyinput_dir .= "<input type='text' name='serialem_dir' value='$serialem_dir' size='45'>\n";
			$keyinput_def = $html_elements->justifiedInputTableRow
					('voltage','voltage (kV):','voltage',$voltage,4);
			$keyinput_dir .= "</td></tr>\n";
			
			$close_keyinput = "</table>\n";
			$close_keyinput .= closeRoundBorder();
		} else {
			$optiontitle = "<font size='+1'><b>Enter the full path for a SerialEM stack and mdoc:</b></font>\n";
			$open_keyinput .= openRoundBorder();
			$open_keyinput .= "<table border='0'>\n";
			$keyinput_dir = "<tr><td colspan='2'>\n";
			$keyinput_dir .= docpop('serialem_stack','SerialEM stack path (.st or .mrc)');
			$keyinput_dir .= "<br/>\n";
			$keyinput_dir .= "<input type='text' name='serialem_stack' value='$serialem_stack' size='45'>\n";
			$keyinput_dir .= "<br/>\n";
			$keyinput_dir .= docpop('serialem_mdoc','SerialEM mdoc');
			$keyinput_dir .= "<br/>";
			$keyinput_dir .= "<input type='text' name='serialem_mdoc' value='$serialem_mdoc' size='45'>\n";
			$keyinput_def = $html_elements->justifiedInputTableRow
					('voltage','voltage (kV):','voltage',$voltage,4);
			$keyinput_dir .= "</td></tr>\n";
			
			$close_keyinput = "</table>\n";
			$close_keyinput .= closeRoundBorder();
		}
	}
	
	// Presentation to the web page
	$headerstuff = $javafunctions."<script src='../js/tabview.js' type='text/javascript'></script>
<link href='../css/tabview.css' rel='stylesheet' type='text/css'/>";
	processing_header($title,$heading,$headerstuff);
	echo "<div id='tab-body'>\n";
	echo "<ul class='tab-collection'>
	<li class='tab' title='Upload TEM Images'>\n";
	echo $extrainput;
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	echo $outdirinput;
	// Start Tables
	echo "<table class=tableborder>\n";
	echo "	<tr><td valign='top'>\n";
	echo "		<table border='0' cellpading='15' cellspacing='5'>\n";
	echo "			<tr><td valign='top'>\n";
	echo "				<br/>\n";
	echo $projectinput;
	echo "				<br/><br/>\n";
	echo $uploadtypeinput;
	echo "				<br/><br/>\n";
	echo $sessioninput;
	echo "				<br/><br/>\n";
	echo $descriptioninput;
	echo "				<br/><br/>\n";
	echo $imagegroupinput;
	echo "			</td></tr>\n";
	echo "			<tr><td valign='top' class='tablebg'>\n";
	echo "				<br/>\n";
	echo $csinput;
	echo "				<br/><br/>\n";
	echo "				<br/>";
	echo $invertinput;
	echo "				<br/><br/>\n";
	echo "			</td></tr>\n";
	echo "			<tr><td>\n";
	echo "				<hr/>\n";
	echo $optiontitle;
	echo "				<br/><br/>\n";
	echo $fileinput;
	echo "				<br/>\n";
	echo $paramtitle;
	if ($paramtypes[1]) {
		echo $open_keyinput;
		echo $keyinput_dir;
		echo $keyinput_format;
		echo $keyinput_apix;
		echo $keyinput_mag;
		echo $keyinput_ht;
		echo $keyinput_def;
		echo $keyinput_az;
		echo $keyinput_tilt;
		echo $keyinput_dose;
		echo $close_keyinput;
	}
	echo "			</tr></td>\n";

	// Launcher
	echo "			<tr><td align='center'>\n";
	echo "				<hr/><br/>\n";
	echo getSubmitForm("Upload Image");

	// End table
	echo "			</td></tr>\n";
	echo "		</table>\n";
	echo "	</td></tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	echo "</li>\n";
	echo "<li class='tab' title='Upload SEM Images'>\n";
	
	echo $extrainput;
	echo "<FORM NAME='upload_sem' method='POST' ACTION='$formAction'>\n";
	echo $outdirinput;
	// Start Tables
	echo $projectinput;
	echo "				<br/><br/>\n";
	echo $sessioninput;
	echo "				<br/><br/>\n";
	echo $descriptioninput;
	echo "				<br/><br/>\n";
	echo $open_keyinput;
	echo docpop('imgpath','&nbsp;Directory containing images');
	echo "<br/>\n";
	echo "<input type='text' name='imgdir' value='$imgdir' size='45'>\n";
	
	echo "<br/>\n";
	echo "<label for='z-slice'>&nbsp;Z Slice: </label>";
	echo "<input type='text' name='z-slice' size='2' style='text-align:center'>\n";
	echo "<br/><br/>\n";
	echo $close_keyinput;
	echo '<input type="hidden" name="semform" value=""/>';
	// Launcher
	echo "<p align='center'>\n";
	echo getSubmitForm("Upload Image");
	
	// End table
	echo "</p>\n";
	echo "</form>\n";
	
	
	echo "</li>\n";
	echo "<script type='text/javascript'>
	UI.Tabview.init('tab-body', { 
									width: '100%',
							 		activeColorBackground: '#386F8F',
									activeColorText: 'white',
									inactiveColorBackground: 'white',
									inactiveColorText: '#386F8F'
								});

	</script>\n";
	echo "</div>\n";
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
	$cs = $_POST['cs'];
	$imagegroup = $_POST['imagegroup']+0;
	$uploadtype = $_POST['uploadtype'];
	$doselist = $_POST['doselist'];
	$tiltlist = $_POST['tiltlist'];
	$serialem_stack = $_POST['serialem_stack'];
	$serialem_mdoc = $_POST['serialem_mdoc'];
	$serialem_dir = $_POST['serialem_dir'];
	$voltage = $_POST['voltage'];
	$outdir = $_POST['outdir'];
	$z_slice = $_POST['z-slice'];
	$imgdir = $_POST['imgdir'];
	if (isset($_POST['semform'])){
		if (!$imgdir) createUploadImageForm($errormsg."Specify an image directory");
		
		$command = "uploadFIB-SEMImages.py ";
		if ($sessionname) $command.="--session-name=$sessionname ";
		$command.="--image-dir=$imgdir ";
		
		$description=$_POST['description'];
		if ($description) $command.="--description='$description' ";
		if ($z_slice) $command.="--z-slice=$z_slice ";
		// command geneeration is handled at the end of the script

	} else {
		// determine which upload script to use
		if (($serialem_stack) OR ($serialem_dir))
			$uploadscript = 'uploadSerialEM';
		elseif (!$batch)
			$uploadscript = ($uploadtype == 'normal') ? 'imageloader': 'uploadImages';
		else
			$uploadscript = 'imageloader';
		// start setting up the imageloader command
		$command = $uploadscript.".py ";
		$command.="--projectid=".$projectId." ";

		$leginon = new leginondata();

		if (($uploadscript == 'imageloader') OR ($uploadscript == 'uploadSerialEM')) {
			//imageloader allows user to enter session name.  Therefore it is
			//necessary to check to see it is valid.
			//make sure a session name was entered if upload an independent file
			if (!$sessionname) createUploadImageForm("<B>ERROR:</B> Enter a session name of the image");
			$has_session = $leginon->checkSessionNameExistance($sessionname,false);
			$session_in_project = $leginon->checkSessionNameExistance($sessionname,$projectId);
			$session_is_reserved = $leginon->checkSessionReservation($sessionname);

			if ($has_session) {
				if ($uploadtype !== 'tiltseries'){
					if (!$leginon->onlyUploadedImagesInSession($has_session[0]['DEF_id'])) {
						createUploadImageForm($errormsg."Session contains images not from  'appion' Host is not available for uploading more images");
					}	
				}
				if ($uploadtype == 'defocalseries')
					createUploadImageForm("<B>ERROR:</B> Defocal series can not be uploaded to an existing session");

				if ($has_session && !$session_in_project)
					createUploadImageForm("<B>ERROR:</B> You have entered an existing session not belonging to this project");
			} else {
				// reserved sessionname do not yet have session entry in SessionData
				if ($session_is_reserved)
					createUploadImageForm("<B>ERROR:</B>  You have entered a session already reserved by others");
			}

			if ($session_in_project)
				$warning = ("<B>Warning:</B>  Will append to an existing session with the original description");
			// add session to the command
			$command.="--session=$sessionname ";
		}

		//make sure a description was provided
		$description=$_POST['description'];
		if (!$description && !$session_in_project)
			createUploadImageForm("<B>ERROR:</B> Enter a brief description of the session");
		$command.="--description='$description' ";

		// for inverting density
		if ($invert_check=='on') $command.="--invert ";
		if ($cs === "") {
			createUploadImageForm($errormsg."Specify the Cs value");
		} else {
			$cs = $cs + 0;
			if ( $cs < 0.0 ) {
				createUploadImageForm($errormsg."The Cs value must be a positive number");
			}
			if ($has_session) {
				$session_cs = $leginon->getCsValueFromSession($has_session[0]['DEF_id']);
				if ($session_cs != $cs) {
					createUploadImageForm("<B>ERROR:</B> Existing session Cs can not be changed");
				}
			}
			$command.="--cs=$cs ";
		}

		//determine if a information batch file was provided
		if ((!$batch) && (!$voltage)) {
			$errormsg = "<b>ERROR:</b> ";
			$imgdir = $_POST['imgdir'];
			if (!$imgdir)
				createUploadImageForm($errormsg."Specify an image directory");
			$fileformat = $_POST['fileformat'];
			$apix = $_POST['apix'];
			if (!$apix)
				createUploadImageForm($errormsg."Specify a pixel size");
			$mag = $_POST['mag'];
			if (!$mag)
				createUploadImageForm($errormsg."Specify a magnification");

			//defocus
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
				$az = $_POST['az'];
				if (strlen($az)==0)
					createUploadImageForm($errormsg."Specify a tilt azimuth");
				$tiltlist = $_POST['tiltlist'];
				if (!$tiltlist) 
					createUploadImageForm($errormsg."Specify a tilt angle list");
				$tiltanglearray = explode(',',trim($tiltlist));
				if (count($tiltanglearray) != $imagegroup)
					createUploadImageForm($errormsg."Specify matched image-per-group and tilt-angle list");
				$dosearray = explode(',',trim($doselist));
				if (count($dosearray) != $imagegroup)
					createUploadImageForm($errormsg."Specify matched image-per-group and dose list");
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
				$mdfarray[] = $df * 1e-6;
			}
			// kv
			$kv = $_POST['kv'];
			if (!$kv)
				createUploadImageForm($errormsg."specify the high tension");
			if ($kv > 1000)
				createUploadImageForm("<b>Error:</b> high tension must be in kilovolts (i.e. 120)");
			// Make reservation only after validation
			$leginon->makeSessionReservation($sessionname);
			// add options to command
			if ($uploadscript == 'imageloader') {
				// imageloader.py
				$command.="--dir=$imgdir ";
				$command.="--filetype=$fileformat ";
				$command.="--apix=$apix ";
				// pass binx=1 and biny=1 all the time
				$command.="--binx=1 ";
				$command.="--biny=1 ";
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
				$command.="--azimuth=$az ";
				if ($uploadtype == 'tiltseries')
					$command.="--angle-list=".implode(',',$tiltanglearray)." ";
				if ($uploadtype == 'tiltseries')
					$command.="--dose-list=".implode(',',$dosearray)." ";
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
				if (count($items)!=7  && (count($items)!=8 && count($items)!=9 && $imagegroup > 1)) {
					$badbatch = true;
					break;
				}
			}
			// add batch file to command
			$command.="--batchparams=$batch ";
			if ($imagegroup >= 2)
				$command.="--tiltgroup=$imagegroup ";
		} elseif ($serialem_stack) {
			$command.="--serialem_stack=$serialem_stack ";
			$command.="--serialem_mdoc=$serialem_mdoc ";
			$command.="--voltage=$voltage ";
		} elseif ($serialem_dir) {
			$command.="--serialem_dir=$serialem_dir ";
			$command.="--voltage=$voltage ";
		} else {
			$badbatch = false;
		}
		if ($badbatch) createUploadImageForm("<B>ERROR:</B> Invalid format in the batch file");

	}
	//Common for all cases
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
