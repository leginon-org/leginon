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
elseif ($_POST['jobid'])
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
		$id = $frealignjob['DEF_id'];
		echo "<input type='radio' NAME='jobid' value='$id' ";
		echo "><br/>\n";
		echo "Upload<br/>Job\n";

		echo "</td><td>\n";
		$prepdatas = $particle->getPreparedFrealignJobs(False, $frealignjob['appath']);
		$prepdata = $prepdatas[0];

		echo frealigntable($prepdata);

		echo "</td></tr>\n";
	}
	echo "</table>\n\n";

	echo "<P><input type='SUBMIT' NAME='selectupload' VALUE='Select Frealign job'></FORM>\n";

	processing_footer();
	exit;
};

/*
******************************************
******************************************
******************************************
*/

function frealigntable($data) {
	// initialization
	$table = "";

	$expId = $_GET['expId'];
	$particle = new particledata();

	// start table
	$name = $data['name'];
	$id = $data['DEF_id'];

	$table .= apdivtitle("Frealign Job: <span class='aptitle'>$name</span> (ID: $id) $j\n");
	$display_keys['date time'] = $data['DEF_timestamp'];
	$display_keys['path'] = $data['path'];
	$display_keys['model'] = modelsummarytable($data['REF|ApInitialModelData|model'], true);
	$display_keys['stack'] = stacksummarytable($data['REF|ApStackData|stack'], true);

	$table .= "<table border='0'>\n";
	// show data
	foreach($display_keys as $k=>$v) {
		$table .= formatHtmlRow($k,$v);
	}

	$table .= "</table>\n";
	return $table;
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
	$jobid = $_POST['jobid'];

	if ($expId) {
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
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
	$jobinfo = $particle->getJobInfoFromId($jobid);
	$jobname = $jobinfo['name'];
	$jobpath = $jobinfo['appath'];

	// get prep Frealign data
	$prepdatas = $particle->getPreparedFrealignJobs(False, $jobinfo['appath']);
	$prepdata = $prepdatas[0];
	$modelid = $prepdata['REF|ApInitialModelData|model'];
	$stackid = $prepdata['REF|ApStackData|stack'];

	// Set any existing parameters in form
	$contour = ($_POST['contour']) ? $_POST['contour'] : '2.0';
	$mass = ($_POST['mass']) ? $_POST['mass'] : '';
	$zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
	$filter = ($_POST['filter']) ? $_POST['filter'] : '';
	$description = $_POST['description'];
	$oneiter = ($_POST['oneiter']=="on") ? "CHECKED" : "";
	$startiter = $_POST['startiter'];

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
	echo "</td></tr>\n";

	echo "<tr><td>\n";
		echo "<b>Recon Directory:</b>\n";
	echo "</td><td>\n";
		echo "$jobpath\n";
	echo "</td></tr>\n";

	// Stack Info
	echo "<tr><td colspan='2'>\n";
	echo stacksummarytable($stackid, $mini=true);
	echo "</td></tr>\n";

	// Initial Model Info
	echo "<tr><td colspan='2'>\n";
	echo modelsummarytable($modelid, $mini=true);
	echo "</td></tr>\n";

	echo "</table>\n";

	// description field
	echo "</td></tr>\n";
	echo "<tr><td>\n";
	echo "<br/>";
	echo "<b>Recon Description:</b><br/>";
	echo "<textarea name='description' rows='3' cols='80'>$description</textarea><br/>";
	echo "<input type='checkbox' name='oneiter' $oneiter><B>Upload only iteration </b>";
	echo "<input type='text' name='iter' value='$iter' size='4'/><br />";
	echo "<input type='checkbox' name='contiter' $contiter><b>Begin with iteration </b>";
	echo "<input type='text' name='startiter' value='$startiter' size='4'/><br/>";
	echo "<br/>";

	echo "</td></tr>\n";

	echo "<tr><td class='tablebg'>";
	echo "<br/>";
	echo "<b>Snapshot Options:</b>\n";
	echo "<br/>";
	echo "<input type='text' name='contour' value='$contour' size='4'> Contour Level\n";
	echo "<br/>";
	echo "<input type='text' name='mass' value='$mass' size='4'> Mass (in kDa)\n";
	echo "<br/>";
	echo "<input type='text' name='zoom' value='$zoom' size='4'>\n";	
	echo docpop('snapzoom', 'Zoom');
	echo "<br/>";
	echo "<input type='text' name='filter' value='$filter' size='4'>\n";	
	echo docpop('snapfilter', 'Fixed Low Pass Filter <i>(in &Aring;ngstr&ouml;ms)</i>');
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

	processing_footer();
	exit;
};


/*
******************************************
******************************************
******************************************
*/

function runUploadFrealign() {
	$expId=$_GET['expId'];
	$projectid = getProjectId();

	$filter=$_POST['filter'];
	$zoom=$_POST['zoom'];
	$mass=$_POST['mass'];
	$contour=$_POST['contour'];

	$oneiter=$_POST['oneiter'];
	$startiter=$_POST['startiter'];
	$iter=$_POST['iter'];
	$contiter=$_POST['contiter'];

	$description=$_POST['description'];

	if (!$description)
		createUploadFrealignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// setup command
	$command ="uploadFrealign.py ";
	$command.="--projectid=$projectid ";
	$command.="--runname=$runname ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runfrealignid=$runfrealignid ";
	$command.="--prepfrealignid=$prepfrealignid ";
	if ($contour) $command.="--contour=$contour ";
	if ($mass) $command.="--mass=$mass ";
	if ($zoom) $command.="--zoom=$zoom ";
	if ($filter) $command.="--filter=$filter ";
	if ($oneiter=='on' && $iter) $command.="--oneiter=$iter ";
	if ($contiter=='on' && $startiter) $command.="--startiter=$startiter ";

	// submit job to cluster
	if ($_POST['process']=="Upload Frealign Recon") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadFrealignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'uploadfrealign', False, False, False);
		// if errors:
		if ($sub) createUploadFrealignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Upload Frealign Params","Upload Frealign Params");
		echo "<table width='600' class='tableborder' border='1'>";
		echo "
			<tr><td colspan='2'>
			<b>Upload Frealign Command:</b><br />
			$command
			</td></tr>
			<tr><td>run name</td><td>$runname</td></tr>
			<tr><td>project id</td><td>$projectid</td></tr>
			<tr><td>run dir</td><td>$rundir</td></tr>
			<tr><td>run frealign id</td><td>$runfrealignid</td></tr>
			<tr><td>prep frealign id</td><td>$prepfrealignid</td></tr>
			<tr><td>description</td><td>$description</td></tr>

			<tr><td>contour</td><td>$contour</td></tr>
			<tr><td>mass</td><td>$mass</td></tr>
			<tr><td>zoom</td><td>$zoom</td></tr>
			<tr><td>filter</td><td>$filter</td></tr>
			<tr><td>one iter</td><td>$iter</td></tr>
			<tr><td>start iter</td><td>$startiter</td></tr>

			</table>\n";
		processing_footer();
	}
}

?>
