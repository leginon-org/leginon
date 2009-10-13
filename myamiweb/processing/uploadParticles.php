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
	runUploadParticles();
}

// Create the form page
else {
	createUploadParticlesForm();
}

function createUploadParticlesForm($extra=false, $title='uploadParticles.py Launcher', $heading='Upload particle selection') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// Set any existing parameters in form
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$description = $_POST['description'];

	$javafunctions="<script src='../js/viewer.js'></script>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","extract",$sessionpath);
	$sessionname=$sessioninfo['Name'];

	//query the database for parameters
	$particle = new particledata();

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	$lastrunnumber = $particle->getLastRunNumber($sessionId,'ApSelectionRunData','name','manual');
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manual'.($lastrunnumber+1);
	$particles = ($_POST['particles']) ? $_POST['particles'] : '';
	$scale = ($_POST['scale']) ? $_POST['scale'] : '';

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
	
	echo docpop('particlefiles', "Particle file(s) with path <i>(wild cards are acceptable)</i>:");
	echo " <br> \n";
	echo "<INPUT TYPE='text' NAME='particles' VALUE='$particles' SIZE='55'/>\n";
	echo "<br>\n";			

	echo "<br/>\n";

	echo "Particle Description:<br>";
	echo "<TEXTAREA NAME='description' ROWS='3' COLS='70'>$description</TEXTAREA>";

	echo "</TD></tr><TR><TD VALIGN='TOP'>";

	echo "<br>\n";
	echo docpop("particlescaling","Particle selection scaling:");
	echo " <input type='text' name='scale' size='3' value='$scale'>\n";
	echo "<br><br>\n";
	echo "Particle Diameter (for imageviewer display only):<br>\n"
		."<INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>\n"
		."<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "<br/>\n";

	echo "<br/>\n";

	echo "<br/>\n";
	echo "</td></tr></table></td></tr><tr><td align='center'>";
	echo getSubmitForm("Upload Particles");
	echo "</td></tr></table></form>\n";
	processing_footer();
	exit;
}

function runUploadParticles() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
	$projectId = $_POST['projectId'];
	$runname = $_POST['runname'];
	$particles = $_POST['particles'];
	$diam=$_POST['diam'];
	$scale=$_POST['scale'];
	$description=$_POST['description'];
	$sessionname = $_POST['sessionname'];

	// make sure box files are entered
	if (!$particles) createUploadParticlesForm("<b>Error:</b> Specify particle files for uploading");
	//make sure a description is provided
	if (!$description) createUploadParticlesForm("<B>ERROR:</B> Enter a brief description of the particle selection");
	//make sure a diam was provided
	if (!$diam) createUploadParticlesForm("<B>ERROR:</B> Enter the particle diameter");

	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
	}

	//putting together command
	$command = "uploadParticles.py ";
	$command.="--projectid=$projectId ";
	$command.="--session=$sessionname ";
	$command.="--runname=$runname ";
	$command.="--files=\"$particles\" ";
	$command.="--diam=$diam ";
	$command.="--description=\"$description\" ";
	$command.="--rundir=$rundir ";
	if ($scale) $command.="--scale=$scale ";
	$command.="--commit ";

	// submit job to cluster
	if ($_POST['process']=="Upload Particles") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadParticlesForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'uploadparticles',True);
		// if errors:
		if ($sub) createUploadParticlesForm("<b>ERROR:</b> $sub");

		// check that upload finished properly
		$jobf = $outdir.'/'.$runname.'/'.$runname.'.appionsub.log';
		$status = "Particles were uploaded";
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
		processing_header("Particle Upload", "Particle Upload");
		echo "$status\n";
	}

	else {
		processing_header("UploadParticles Command", "UploadParticles Command");
		if ($particle_warning) echo"$particle_warning<br />";
	}
	//rest of the page
	echo"
	<table class='tableborder' width='600' border='1'>
	<tr><td colspan='2'>
	<B>UploadParticles Command:</B><br>
	$command
	</TD></tr>
	<TR><td>diam</TD><td>$diam</TD></tr>
	<TR><td>session</TD><td>$session</TD></tr>
	<TR><td>description</TD><td>$description</TD></tr>";

	echo"
	</table>\n";
	processing_footer();
}

?>
