<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an Eman Job for submission to a cluster
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

/*
******************************************
******************************************
******************************************
*/


if ($_POST['process'])
	runUploadFrealign(); // submit job
elseif ($_GET['prepId'])
	createUploadFrealignForm(); // submit job
else
	selectFrealignJob(); // select a prepared frealign job

/*
******************************************
******************************************
******************************************
*/

function selectFrealignJob($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectid = getProjectId();
	processing_header("Frealign Job Uploader", "Frealign Job Uploader", $javafunc);
	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		exit;
	}
	$particle = new particledata();

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	// get complete run frealign jobs
	$donefrealignjobs = $particle->getJobIdsFromSession($expId, $jobtype='runfrealign', $status='D');
	if (!$donefrealignjobs) {
		echo "<font color='#CC3333' size='+2'>No complete frealign jobs found</font>\n";
		exit;
	} 

	// check if jobs have an associated upload frealign job
	$frealignjobs = array();
	foreach ($donefrealignjobs as $donefrealignjob) {
		$uploadfrealign = $particle->getClusterJobByTypeAndPath('uploadfrealign', $frealignjob['path']);
		if (!$uploadfrealign)
			$frealignjobs[] = $donefrealignjob;
	}

	// print jobs with radio button
	if (!$frealignjobs) {
		echo "<font color='#CC3333' size='+2'>No complete frealign jobs available for upload</font>\n";
		exit;
	}

	echo "<table class='tableborder' border='1'>\n";
	foreach ($frealignjobs as $frealignjob) {
		echo "<tr><td>\n";
		$prepdatas = $particle->getPreparedFrealignJobs(False, $frealignjob['appath']);
		$prepdata = $prepdatas[0];
		$prepid = $prepdata['DEF_id'];

		echo "Frealign $prepid<br/>\n";
		echo "<input type='button' value='Upload Job' "
			."onClick=\"parent.location=('uploadFrealign.php?expId=$expId&prepId=$prepid')\" ";
		echo ">\n";


		echo "</td><td>\n";

		echo frealigntable($prepid);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='selectupload' VALUE='Select Frealign job'></FORM>\n";

	echo frealignRef();

	processing_footer();
	exit;
};

/*
******************************************
******************************************
******************************************
*/

function createUploadFrealignForm($extra=False) {
	// check if session provided
	$expId = $_GET['expId'];
	$projectid = getProjectId();
	$prepid = $_GET['prepId'];

	if ($expId && $prepid) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&prepId=$prepid";
	} else {
		exit;
	}

	$javafunctions .= writeJavaPopupFunctions('appion');  
	processing_header("Frealign Job Uploader", "Frealign Job Uploader", $javafunc);

	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";

	$particle = new particledata();

	// get jobinfo
	$jobinfos = $particle->getPreparedFrealignJobs($prepid);
	$jobinfo = $jobinfos[0];
	$jobname = $jobinfo['name'];
	$jobpath = $jobinfo['path'];
	//print_r($jobinfo);

	// Set any existing parameters in form
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$description = $_POST['description'];

	// main table
	echo "<table border='3' class='tableborder'>\n";
	echo "<tr><td>\n";
	echo "<table border='0' cellspacing='10'>\n";
	echo "<tr><td>\n";

	// stats table
	echo "<table>\n";
	echo "<tr><td>\n";
		echo "<b>Recon Name:</b>\n";
	echo "</td><td>\n";
		echo "$jobname\n";
	echo "<input type='hidden' name='runname' value='$jobname'>\n";	
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo "<b>Recon Directory:</b>\n";
	echo "</td><td>\n";
		echo "$jobpath\n";
	echo "<input type='hidden' name='rundir' value='$jobpath'>\n";	
	echo "</td></tr>\n";

	// Job Info
	echo "<tr><td colspan='2'>\n";
		echo frealigntable($prepid);
	echo "</td></tr>\n";

	echo "</table>\n";

	// description field
	echo "</td></tr>\n";
	echo "<tr><td>\n";
	echo "<br/>";
	echo "<b>Recon Description:</b><br/>";
	echo "<textarea name='description' rows='3' cols='80'>$description</textarea><br/>";
	echo "<br/>";

	echo "</td></tr>\n";

	echo "<tr><td class='tablebg'>";
	echo "<br/>";
	echo "<b>Snapshot Options:</b>\n";
	echo "<br/>";
	echo "<input type='text' name='mass' value='$mass' size='4'> Mass (in kDa)\n";
	echo "<br/>";
	echo "<input type='text' name='zoom' value='$zoom' size='4'>\n";	
	echo docpop('snapzoom', 'Zoom');
	echo "<br/><br/>";
	echo "</td></tr>\n"
;
	echo "<tr><td align='center'>\n";
	echo "<hr/>\n";
	echo getSubmitForm("Upload Frealign Recon");

	// main table
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "</td></tr>\n";
	echo "</table>\n";

	echo "</form>\n";
	echo "</center>\n";

	echo frealignRef();

	processing_footer();
	exit;
};


/*
******************************************
******************************************
******************************************
*/

function runUploadFrealign() {
	/* *******************
	PART 1: Get variables
	******************** */
	$prepid=$_GET['prepId'];

	$zoom=$_POST['zoom'];
	$mass=$_POST['mass'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	if (!$description)
		createUploadFrealignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	if (!$mass)
		createUploadFrealignForm("<B>ERROR:</B> Please provide an approximate mass of the particle");

	/* *******************
	PART 3: Create program command
	******************** */

	// setup command
	$command ="uploadFrealign.py ";
	$command.="--projectid=$projectid ";
	$command.="--prepid=$prepid ";
	$command.="--runname=$runname ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--mass=$mass ";
	if ($zoom) $command.="--zoom=$zoom ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= frealignRef();

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadfrealign', 1);

	// if error display them
	if ($errors)
		createUploadFrealignForm($errors);
	exit;
}

?>
