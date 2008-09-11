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
	runCenterParticles();
}

// Create the form page
else {
	createCenterForm();
}

function createCenterForm($extra=false, $title='centerParticleStack.py Launcher', $heading='Center Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectFromExpId($expId);
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId=$_GET['sId'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$runid = ($_POST['runid']) ? $_POST['runid'] : 'cenali'.$stackId;
	$mask = ($_POST['mask']) ? $_POST['mask'] : '';
	$maxshift = ($_POST['maxshift']) ? $_POST['maxshift'] : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$stackId) $stackId = $_POST['stackId'];

	// get outdir path
	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","stacks",$outdir);

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr />\n";
	}
  
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	//query the database for parameters
	$particle = new particledata();
	
	# get stack name
	$stackp = $particle->getStackParams($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];
	$boxsize = $stackp['boxSize']/$stackp['bin'];
	echo "<input type='hidden' name='box' value='$boxsize'>\n";

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";
	echo"
					<b>Stack information:</b> <br />
					name & path: $filename <br />	
					ID: $stackId<br />
                                        <input type='hidden' name='stackId' value='$stackId'>
					<br />\n";
	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' value='$runid'><br />\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='3'cols='70'>$description</textarea>\n";
	echo "<br />\n";
	echo "Outer Mask: <input type='text' name='mask' value='$mask' size='4'> (radius in pixels)<br />\n";
	echo "Maximum Shift: <input type='text' name='maxshift' value='$maxshift' size='4'> (pixels)<br />\n";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br />\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo getSubmitForm("Center Particles");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runCenterParticles() {
	$expId = $_GET['expId'];

	$runid=$_POST['runid'];
	$stackId=$_POST['stackId'];
	$outdir=$_POST['outdir'];
	$commit=$_POST['commit'];
	$mask = $_POST['mask'];
	$maxshift = $_POST['maxshift'];
	$box = $_POST['box'];

	$command.="centerParticleStack.py ";

	//make sure a description is provided
	$description=$_POST['description'];
	if (!$runid) createCenterForm("<b>ERROR:</b> Specify a runid");
	if (!$description) createCenterForm("<B>ERROR:</B> Enter a brief description");

	// make sure diameter & max shifts are within box size
	if ($mask > $box/2) createCenterForm("<b>ERROR:</b> Mask radius too large, must be smaller than ".round($box/2)." pixels");
	if ($maxshift > $box/2) createCenterForm("<b>ERROR:</b> Shift too large, must be smaller than ".round($box/2)." pixels");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$procdir = $outdir.$runid;

	//putting together command
	$command.="-n $runid ";
	$command.="-s $stackId ";
	if ($mask) $command.="-m $mask ";
	if ($maxshift) $command.="-x $maxshift ";
	$command.="-d \"$description\" ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Center Particles") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createCenterForm("<B>ERROR:</B> You must be logged in to submit");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'makestack');
		// if errors:
		if ($sub) createCenterForm("<b>ERROR:</b> $sub");
		exit();
	}

	processing_header("Center Particles in Stack", "Center Particles in Stack");

	//rest of the page
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>centerParticleStack.py command:</b><br />
	$command
	</td></tr>\n";
	echo "<tr><td>run id</td><td>$runid</td></tr>\n";
	echo "<tr><td>stack id</td><td>$stackId</td></tr>\n";
	echo "<tr><td>description</td><td>$description</td></tr>\n";
	echo "<tr><td>outdir</td><td>$procdir</td></tr>\n";
	echo"</table>\n";
	processing_footer();
}

?>
