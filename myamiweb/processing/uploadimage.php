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

$projectId = trim($_GET['pId']);
if (is_numeric($projectId)) {
		$_SESSION['projectId']=$projectId;
}

if ($_POST) {
	if ($_POST['projectId']) {
		$_SESSION['projectId']=$_POST['projectId'];
	}
}

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
	$expId=$_GET['expId'];

	$projectId= $_SESSION['projectId'];
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$javafunctions .= writeJavaPopupFunctions('appion');  
  
	processing_header($title,$heading,$javafunctions);
	#processing_header($title,$heading,False,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$outdir=$sessioninfo['Image path'];
		$outdir=ereg_replace("rawdata","",$outdir);
		$sessionname=$sessioninfo['Name'];
		$description=$sessioninfo['description'];
		$tem=$sessioninfo['InstrumentId'];
		$cam=$sessioninfo['CameraId'];
		echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	}
	// Set any existing parameters in form
	$temval = ($_POST['tem']) ? $_POST['tem'] : $tem;
	$camval = ($_POST['cam']) ? $_POST['cam'] : $cam;
	$sessionname = ($_POST['sessionname']) ? $_POST['sessionname'] : $sessionname;
	$batch = ($_POST['batch']) ? $_POST['batch'] : $batch;
	$tiltgroup = ($_POST['tiltgroup']) ? $_POST['tiltgroup'] : $tiltgroup;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	echo"
  <table border=3 class=tableborder>
  <tr>
    <td valign='TOP'>\n";
	echo"<table >
    <tr>
      <td valign='TOP'>";
	echo "
    <br/>\n
    <b>Project:</b><br/>
    <select name='projectId'>";
	$projectdata=new project();
	$projects=$projectdata->getProjects();
	foreach ($projects as $project) {
	$sel=($project['id']==$projectId) ? "selected" : "";
	echo "<option value='".$project['id']."' $sel >".$project['name']."</option>\n";
	}

	echo "</select><br>";
	echo docpop('uploadsession', 'Session Name:');
	echo "<br>
    <input type='text' name='sessionname' value='$sessionname' size='65'><br />\n";
	echo"
      <p>
      <b>Session Description:</b><br/>
      <textarea name='description' rows='3' cols='65'>$description</textarea>
      </td>
    </tr>
		<tr>
			<td>";
	$leginondata = new leginondata();
	$instrumenthosts = $leginondata->getInstrumentHosts();
	$instrumenthostval = ($_POST[instrumenthost]) ? $_POST[instrumenthost] : $instrumenthosts[0];
	echo docpop('host', 'Host:');
	echo "<br>
		<select name='instrumenthost' onchange=submit()>";
	foreach($instrumenthosts as $host) {
		$s = ($instrumenthostval==$host) ? 'selected' : 'not';
		echo "<option value=".$host." ".$s.">".$host."</option>\n";
	}
	echo"
		</select>";
	$scopes = $leginondata->getScopes($instrumenthostval);
	$cameras = $leginondata->getCameras($instrumenthostval);
	echo docpop('scope', 'Scope:');
	echo "
		<select name='tem' onchange=submit()>";
	foreach($scopes as $sc) {
		$s = ($temval==$sc['id']) ? 'selected' : '';
		echo "<option value=".$sc['id']." ".$s." >".$sc['name']."</option>";
	}
	echo" </select>";
	echo docpop('camera', 'Camera:');
	echo "
		<select name='cam' onchange=submit()>";
	foreach($cameras as $c) {
		echo $c['id'];
		$s = ($camval==$c['id']) ? 'selected' : 'not';
		echo "<option value=".$c['id']." ".$s." >".$c['name']."</option>";
	}
	echo"
		</select>";
	echo " <p>";
	echo docpop('images_in_group', 'Number of images in each tilt series if any:');
	echo "<br>
      <input type='text' name='tiltgroup' value='$tiltgroup' size='5'><br />\n";
	echo " <p>";
	echo docpop('batchfile', 'Information File for the images:');
	echo "<br>
      <input type='text' name='batch' value='$batch' size='65'><br />\n";
	echo "
      </td>
    </tr>
  <tr>
    <td align='CENTER'>
      <hr>
	";
	echo getSubmitForm("Upload Image");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runUploadImage() {
	$projectId = $_SESSION['projectId'];
	$expId = $_POST['expId'];
	$sessionname = $_POST['sessionname'];
	$batch = $_POST['batch'];
	$tiltgroup = $_POST['tiltgroup']+0;
	$tem = $_POST['tem'];
	$cam = $_POST['cam'];
	
	$outdir = $_POST['outdir'];

	$command = "imageloader.py ";
	$command.="--projectid=".$projectId." ";

	//make sure a session name was entered if upload an independent file
	if (!$sessionname) createUploadImageForm("<B>ERROR:</B> Enter a session name of the image");
	$leginon = new leginondata();
	$has_session = $leginon->getSessions('',false,$sessionname);
	$session_in_project = $leginon->getSessions('',$projectId,$sessionname);
	if ($has_session && !$session_in_project) createUploadImageForm("<B>ERROR:</B> You have entered an existing session not belonging to this project");
	if ($session_in_project) $warning = ("<B>Warning:</B>  Will append to an existing session with the original description");
	//make sure a information batch file was provided
	if (!$batch or !file_exists($batch)) createUploadImageForm("<B>ERROR:</B> Enter a batch file with path");
	//make sure  the batch file contains 7 or 8 fields separated by tab at each line
	$bf = file($batch);
	foreach ($bf as $line) {
		$items = explode("\t",$line);
		if (count($items)!=7  && (count($items)!=8 && $tiltgroup > 1)) {
			$badbatch = true;
			break;
		}
	}
	if ($badbatch) createUploadImageForm("<B>ERROR:</B> Invalid format in the batch file");
	// make sure there are valid instrument
	if (!$tem) createUploadImageForm("<B>ERROR:</B> Choose a tem where the images are acquired");
	if (!$cam) createUploadImageForm("<B>ERROR:</B> Choose a camera where the images are acquired");

	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description && !$session_in_project) createUploadImageForm("<B>ERROR:</B> Enter a brief description of the session");


	$command.="--session=$sessionname ";
	$command.="--batchparams=$batch ";	
	$command.="--scopeid=$tem ";	
	$command.="--cameraid=$cam ";	
	$command.="--description=\"$description\" ";
	if ($tiltgroup >= 2)
		$command.="--tiltgroup=$tiltgroup ";
	
	// submit job to cluster
	if ($_POST['process']=="Upload Images") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadImageForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$sessionname,$expId,'uploadimage',True);
		// if errors:
		if ($sub) createUploadImageForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$sessionname.'/'.$runname.'.appionsub.log';
		$status = "Images were uploaded";
		if (file_exists($jobf)) {
			$jf = file($jobf);
			$jfnum = count($jf);
			for ($i=$jfnum-5; $i<$jfnum-1; $i++) {
			  // if anything is red, it's not good
				if (preg_match("/red/",$jf[$i])) {
					$status = "<font class='apcomment'>Error while uploading, check the log file:<br />$jobf</font>";
					continue;
				}
			}
		}
		else $status = "Job did not run, contact the appion team";
		processing_header("Image Upload", "Image Upload");
		echo "$status\n";
	}

	else processing_header("UploadImage Command","UploadImage Command");
	
	// rest of the page
	echo"<font class='apcomment'>".$warning."</font>";
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>UploadImage Command:</b><br/>
	$command
	</td></tr>
	<tr><td>batch file</td><td>$batch</td></tr>
	<tr><td>tem id</td><td>$tem</td></tr>
	<tr><td>camera id</td><td>$cam</td></tr>
	<tr><td>session</td><td>$sessionname</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	</table>\n";
	processing_footer();
}
?>
