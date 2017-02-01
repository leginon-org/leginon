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
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadParticles();
}

// Create the form page
else {
	createUploadParticlesForm();
}

function createUploadParticlesForm($extra=false, 
$title='uploadParticles.py Launcher', $heading='Upload particle selection') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// Set any existing parameters in form
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';


	$javafunctions="<script src='../js/viewer.js'></script>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');

	$javafunctions .="<script language='JavaScript'>\n";
	$javafunctions .="function emanappion(check){\n";
	$javafunctions .="  if (check=='eman'){\n";
	$javafunctions .="    document.viewerform.emanboxfiles.disabled=false;\n";
	$javafunctions .="    document.viewerform.appionpartfile.disabled=true;\n";
	$javafunctions .="    document.viewerform.uploadfile.disabled=true;\n";
	$javafunctions .="  }\n";
	$javafunctions .="  else if (check=='appion'){\n";
	$javafunctions .="    document.viewerform.emanboxfiles.disabled=true;\n";
	$javafunctions .="    document.viewerform.appionpartfile.disabled=false;\n";
	$javafunctions .="    document.viewerform.uploadfile.disabled=true;\n";
	$javafunctions .="  }\n";
	$javafunctions .="  else if (check=='upload'){\n";
	$javafunctions .="    document.viewerform.emanboxfiles.disabled=true;\n";
	$javafunctions .="    document.viewerform.appionpartfile.disabled=true;\n";
	$javafunctions .="    document.viewerform.uploadfile.disabled=false;\n";
	$javafunctions .="  }\n";
	$javafunctions .="}";
	$javafunctions .="</script>\n";

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction' ENCTYPE='multipart/form-data'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$sessionpath=getBaseAppionPath($sessioninfo).'/extract/';
	$sessionname=$sessioninfo['Name'];

	//query the database for parameters
	$particle = new particledata();

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name');
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manual'.($lastrunnumber+1);
	$scale = ($_POST['scale']) ? $_POST['scale'] : '1';

	echo"<table border='3' class='tableborder'>";
	echo"<tr><td valign='top'>\n";
	echo"<table border='0' cellpading='5' cellspacing='5'><tr><td valign='top'>\n";

	echo openRoundBorder();
	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' VALUE='$defrunname'><br>\n";
	echo "<br>\n";

	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' VALUE='$outdir' size='45'><br />\n";
	echo closeRoundBorder();
	echo "<br />\n";
	echo "<input type='hidden' name='projectId' value='$projectId'>\n";
	echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	
	/*
	**
	** START FILE TYPES
	**
	*/

	$emanfilecheck = (!$_POST['filetype'] || $_POST['filetype'] == 'eman') ? 'CHECKED' : '';
	$emanfiledisable = (!$_POST['filetype'] || $_POST['filetype'] == 'eman') ? '' : 'DISABLED';
	$emanboxfiles = ($_POST['emanboxfiles']) ? $_POST['emanboxfiles'] : '';
	echo "<INPUT TYPE='radio' NAME='filetype' onclick='emanappion(\"eman\")' $emanfilecheck value='eman'>\n";
	echo docpop('emanboxfiles', "EMAN box or Xmipp picking file(s) with path");
	echo " <i>(wild cards are acceptable)</i>:";
	echo " <br> \n";
	echo "<INPUT TYPE='text' NAME='emanboxfiles' VALUE='$emanboxfiles' SIZE='55' $emanfiledisable/>\n";
	echo "<br>\n";

	$appionfilecheck = ($_POST['filetype'] != 'appion') ? '' : 'CHECKED';
	$appionfiledisable = ($_POST['filetype'] != 'appion') ? 'DISABLED' : '';
	$appionpartfile = ($_POST['appionpartfile']) ? $_POST['appionpartfile'] : '';
	echo "<INPUT TYPE='radio' NAME='filetype' onclick='emanappion(\"appion\")' $appionfilecheck value='appion'>\n";
	echo docpop('appionpartfile', "Appion particle list file:");
	echo " <br> \n";
	echo "<INPUT TYPE='text' NAME='appionpartfile' VALUE='$appionpartfile' SIZE='55' $appionfiledisable/>\n";
	echo "<br>\n";

	$uploadfilecheck = ($_POST['filetype'] != 'upload') ? '' : 'CHECKED';
	$uploadfiledisable = ($_POST['filetype'] != 'upload') ? 'DISABLED' : '';
	$uploadfile = ($_FILES['uploadfile']['name']) ? $_FILES['uploadfile']['name'] : '';
		echo "<input type='hidden' name='MAX_FILE_SIZE' value='300000' />\n";
	echo "<INPUT TYPE='radio' NAME='filetype' onclick='emanappion(\"upload\")' $uploadfilecheck value='upload'>\n";
	echo docpop('appionpartfile', "Upload Appion particle list file:");
	echo " <br> \n";
	echo "<INPUT TYPE='file' NAME='uploadfile' VALUE='$uploadfile' SIZE='44' MAXLENGTH='256' $uploadfiledisable/>\n";
	echo "<br>\n";

	/*
	**
	** END FILE TYPES
	**
	*/

	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	echo "<br>\n";
	echo docpop("diameter", "Particle Diameter");
	echo "<INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "<br><br>\n";

	echo docpop("particlescaling","Particle selection scaling:");
	echo " <input type='text' name='scale' size='3' value='$scale'>\n";
	echo "<br/>\n";

	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'>";
	echo getSubmitForm("Upload Particles");
	echo "</td></tr></table></form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runUploadParticles() {
	/* *******************
	PART 1: Get variables
	******************** */
	$emanboxfiles = $_POST['emanboxfiles'];
	$appionpartfile = $_POST['appionpartfile'];
	$uploadfile = $_POST['uploadfile'];
	$diam=$_POST['diam'];
	$scale=$_POST['scale'];
	$sessionname = $_POST['sessionname'];
	$filetype = $_POST['filetype'];


	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	// make sure box files are entered
	//if (!$emanboxfiles && !$appionpartfile && !$_FILES['uploadpdb']['name'])
	//	createUploadParticlesForm("<b>Error:</b> Specify particle files for uploading");
	//make sure a diam was provided
	if (!$diam)
		createUploadParticlesForm("<B>ERROR:</B> Enter the particle diameter");

	/* *******************
	PART 3: Create program command
	******************** */

	// get uploaded files
	if ($_FILES['uploadfile']['tmp_name']) {
		echo "UPLOAD NAME: '".$_FILES['uploadfile']['name']."'<br/>";
		echo "UPLOAD TEMP NAME: '".$_FILES['uploadfile']['tmp_name']."'<br/>";
		echo "UPLOAD SIZE: '".$_FILES['uploadfile']['size']."'<br/>";
		echo "UPLOAD ERRORS: '".$_FILES['uploadfile']['error']."'<br/>";

		$uploaddir = TEMP_IMAGES_DIR;
		if (substr($uploaddir,-1,1)!='/')
			$uploaddir.='/';
		$uploadfile = $uploaddir.basename($_FILES['uploadfile']['name']);
		echo "UPLOAD FILE: '".$uploadfile."'<br/>";
		if (!move_uploaded_file($_FILES['uploadfile']['tmp_name'], $uploadfile)) {
			print_r($_FILES['uploadfile']);
			createUploadParticlesForm("<B>ERROR:</B> Possible file upload attack! ".$_FILES['uploadfile']['tmp_name']);
			exit;
		}
	}

	//putting together command
	if ($filetype=='eman') {
		$command = "uploadEMANParticles.py ";
		$command.="--files=\"$emanboxfiles\" ";
		if ($scale && $scale != 1)
			$command.="--bin=$scale ";
	} elseif ($filetype=='appion') {
		$command = "uploadAppionParticles.py ";
		$command.="--filename=$appionpartfile ";
	} elseif ($filetype=='upload') {
		$command = "uploadAppionParticles.py ";
		$command.="--filename=$uploadfile ";
	}
	$command.="--session=$sessionname ";
	$command.="--diam=$diam ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadparticles', $nproc);

	// if error display them
	if ($errors)
		createAppionForm($errors);
	exit;
}

?>
