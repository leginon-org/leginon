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
		$projectId=getProjectFromExpId($sessionId);
		$formAction=$_SERVER['PHP_SELF'];
	}

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
		echo "<span style='font-size: larger; color:#bb3333;'>$extra</span><br />\n";
	} else {
		echo "<font color='#bb8800' size='+1'>WARNING: Xmipp Maximum Likelihood Alignment "
			."is still in the experimental phases</font><br/><br/>\n";
	}
  
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
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
	$angle = ($_POST['angle']) ? $_POST['angle'] : '5';
	$mirror = ($_POST['mirror']=='on' || !$_POST['mirror']) ? 'checked' : '';
	$fast = ($_POST['fast']=='on' || !$_POST['fast']) ? 'checked' : '';

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
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
	echo "<textarea name='description' rows='3' cols='50'>$rundescrval</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if (!$stackIds) {
		echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use</b>');
		echo "<br/>\n<select name='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($stackIds as $stack) {
			$stackparams=$particle->getStackParams($stack['stackid']);

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
			echo "<option value='$stackid|~~|$apix|~~|$boxsz|~~|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$stackid) echo " selected";
			echo ">".$stack['stackid'].": $runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</option>\n";
		}
		echo "</SELECT><br/>\n";
	}
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
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><BR>\n";

	echo "<b>Particle-specific Radii (in &Aring;ngstroms)</b>\n";
	echo "<br />\n";
	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('binval','Particle binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numref' VALUE='$numref' SIZE='4'>\n";
	echo docpop('numref','Number of References');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='angle' VALUE='$angle' SIZE='4'>\n";
	echo docpop('angleinc','Angular Increment');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='fast' $fast>\n";
	echo docpop('fastmode','Use Fast Mode');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='mirror' $mirror>\n";
	echo docpop('mirror','Use Mirrors in Alignment');
	echo "<br/>\n";

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
	$stackvars=$_POST['stackid'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$numref=$_POST['numref'];
	$angle=$_POST['angle'];
	$bin=$_POST['bin'];
	$description=$_POST['description'];
	$fast = ($_POST['fast']=="on") ? true : false;
	$mirror = ($_POST['mirror']=="on") ? true : false;
	$commit = ($_POST['commit']=="on") ? true : false;

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|~~\|',$stackvars);

	//make sure a session was selected

	if (!$description)
		createMaxLikeAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid)
		createMaxLikeAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createMaxLikeAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createMaxLikeAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than the number of particles in the stack ($totprtls)");

	// determine calc time
	$stackdata = $particle->getStackParams($stackid);
	$boxsize = ($stackdata['bin']) ? $stackdata['boxSize']/$stackdata['bin'] : $stackdata['boxSize'];
	$secperiter = 0.12037;
	$calctime = ($numpart/1000.0)*$numref*($boxsize/$bin)*($boxsize/$bin)/$angle*$secperiter;
	if ($mirror) $calctime *= 2.0;
	// kill if longer than 6 hours
	if ($calctime > 6.0*3600.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 6 hours<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/3600.0,2)." hours\n");
	elseif (!$fast && $calctime > 1800.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 30 minutes without fast mode<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/60.0,2)." minutes\n");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// setup command
	$command.="maxlikeAlignment.py ";
	$command.="--outdir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-ref=$numref ";
	$command.="--bin=$bin ";
	$command.="--angle-interval=$angle ";
	if ($fast) $command.="--fast ";
	if ($mirror) $command.="--mirror ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if (false && $runjob) {
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
		echo "<table width='600' class='tableborder' border='1'>";
		echo "<tr><td colspan='2'><br/>\n";
		if ($calctime < 60)
			echo "<span style='font-size: larger; color:#999933;'>\n<b>Estimated calc time:</b> "
				.round($calctime,2)." seconds\n";
		elseif ($calctime < 3600)
			echo "<span style='font-size: larger; color:#33bb33;'>\n<b>Estimated calc time:</b> "
				.round($calctime/60.0,2)." minutes\n";
		else
			echo "<span style='font-size: larger; color:#bb3333;'>\n<b>Estimated calc time:</b> "
				.round($calctime/3600.0,2)." hours\n";
		echo "for the first iteration</span><br/>"
			."<i>it gets much faster after the first iteration with the fast mode</i><br/><br/></td></tr>\n";
		echo "
			<tr><td colspan='2'>
			<b>MaxLike Alignment Command:</b><br />
			$command
			</td></tr>
			<tr><td>run id</td><td>$runname</td></tr>
			<tr><td>stack id</td><td>$stackid</td></tr>
			<tr><td>low pass</td><td>$lowpass</td></tr>
			<tr><td>high pass</td><td>$highpass</td></tr>
			<tr><td>num part</td><td>$numpart</td></tr>
			<tr><td>num ref</td><td>$numref</td></tr>
			<tr><td>angle increment</td><td>$angle</td></tr>
			<tr><td>binning</td><td>$bin</td></tr>
			<tr><td>fast</td><td>$fast</td></tr>
			<tr><td>mirror</td><td>$mirror</td></tr>
			<tr><td>out dir</td><td>$outdir</td></tr>
			<tr><td>commit</td><td>$commit</td></tr>
			</table>\n";
		processing_footer();
	}
}
?>
