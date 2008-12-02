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
if ($_POST) {
	runMaxLikeAlign(($_POST['process']=="Run MaxLike Alignment") ? true : false);
} else {
	createMaxLikeAlignForm();
}

function createMaxLikeAlignForm($extra=false, $title='maxlikeAlignment.py Launcher', $heading='Maximum Likelihood Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$maxlikeIds = $particle->getMaxLikeIds($sessionId, True);
	$maxlikeruns=count($maxlikeIds);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackvars) {\n";
	$javascript .= "	var stackArray = stackvars.split('|~~|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#dd0000'>$extra</FONT><br />\n";
	} else {
		echo "<font color='#bb8800' size='+1'>WARNING: Xmipp Maximum Likelihood Alignment "
			."is still in the experimental phases</font><br/><br/>\n";
	}
  
	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","maxlike/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'maxlike'.($maxlikeruns+1);
	$rundescrval = $_POST['description'];
	$stackidval = $_POST['stackid'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '400';
	$numref = ($_POST['numref']) ? $_POST['numref'] : '2';
	echo"
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>MaxLike Run Name:</b>');
	echo "<input type='text' name='runname' value='$runnameval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Max Like Alignment:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='36'>$rundescrval</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		Particles:<BR>
		<select name='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($stackIds as $stack) {
			$stackparams=$particle->getStackParams($stack[stackid]);

			// get pixel size and box size
			$mpix=$particle->getStackPixelSizeFromStackId($stack['stackid']);
			if ($mpix) {
				$apix = $mpix*1E10;
				$apixtxt=format_angstrom_number($mpix)."/pixel";
			}
			$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

			//handle multiple runs in stack
			$runname=$stackparams[shownstackname];
			$totprtls=commafy($particle->getNumStackParticles($stack[stackid]));
			$stackid = $stack['stackid'];
			echo "<OPTION VALUE='$stackid|~~|$apix|~~|$boxsz|~~|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$stackid) echo " SELECTED";
			echo ">$runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo"</SELECT><BR>\n";
	echo "</TD></TR><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></TR>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<BR></TD></TR>\n</TABLE>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><BR>\n";

	echo "<b>Particle-specific Radii (in &Aring;ngstroms)</b>\n";
	echo "<br />\n";
	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
	echo docpop('hpval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('bin','Particle binning');
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo " to Use<BR>\n";

	echo "<INPUT TYPE='text' NAME='numref' VALUE='$numref' SIZE='4'>\n";
	echo docpop('numref','Number of References');
	echo " to Use<BR>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</TR>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run Max Like Alignment");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}
	processing_footer();
	exit;
}

function runMaxLikeAlign($runjob=false) {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];

	$command.="maxlikeAlignment.py ";

	$stackvars=$_POST['stackid'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$numref=$_POST['numref'];
	$bin=$_POST['bin'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|~~\|',$stackvars);

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createMaxLikeAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	//$stackid=$_POST['stackid'];
	if (!$stackid) createMaxLikeAlignForm("<B>ERROR:</B> No stack selected");

	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// classification
	if ($numpart < 10) createMaxLikeAlignForm("<B>ERROR:</B> Must have more than 10 particles");
	if ($numref < 2) createMaxLikeAlignForm("<B>ERROR:</B> Must have at least 2 factors");

	$particle = new particledata();

	// check num of particles
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) createMaxLikeAlignForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls)");

	$stackparams=$particle->getStackParams($stackid);

	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
		$command.="--outdir=$rundir ";
	}
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-ref=$numref ";
	$command.="--bin=$bin ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($runjob) {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMaxLikeAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'maxlikeali');
		// if errors:
		if ($sub) createMaxLikeAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Max Like Align Run Params","Max Like Align Params");
		echo"
	<table width='600' class='tableborder' border='1'>
	<tr><td colspan='2'>
	<b>MaxLike Alignment Command:</b><br />
	$command
	</td></tr>
	<tr><td>run id</td><td>$runname</td></tr>
	<tr><td>stack id</td><td>$stackid</td></tr>
	<tr><td>low pass</td><td>$lowpass</td></tr>
	<tr><td>low pass</td><td>$highpass</td></tr>
	<tr><td>num part</td><td>$numpart</td></tr>
	<tr><td>num factors</td><td>$numref</td></tr>
	<tr><td>binning</td><td>$bin</td></tr>
	<tr><td>out dir</td><td>$outdir</td></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	</table>\n";
		processing_footer();
	}
}
?>
