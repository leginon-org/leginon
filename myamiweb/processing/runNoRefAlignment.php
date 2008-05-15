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
require "inc/ctf.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['showcommand']) {
	runNoRefAlign(0);
}
else if ($_POST['process']) {
	runNoRefAlign(1);
}
else { // Create the form page
	createNoRefAlignForm();
}

function createNoRefAlignForm($extra=false, $title='norefAlign.py Launcher', $heading='Reference Free Alignment') {
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

	$hosts=getHosts();

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctf = new ctfdata();
	$ctfdata=$ctf->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$stackIds = $particle->getStackIds($sessionId);
	$norefIds = $particle->getNoRefIds($sessionId);
	$norefruns=count($norefIds);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackvars) {\n";
	$javascript .= "	var stackArray = stackvars.split('|~~|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	// limit stack to 3000 particles
	$javascript .= "	if (stackArray[3] >= 3000) {stackArray[3]=3000};\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	//$javascript .= "	document.viewerform.numfactors.value = Math.floor(Math.sqrt(stackArray[3])*.25);\n";
	// set max last ring radius
	$javascript .= "	var maxlastring = (stackArray[2]/2)-2;\n";
	// set particle & mask radius and lp
	$javascript .= "	if (stackArray[1]) {\n";
	$javascript .= "		var maxmask = Math.floor(((stackArray[2]/2)-2)*stackArray[1]);\n";
	$javascript .= "		document.viewerform.maskrad.value = maxmask;\n";
	$javascript .= "		document.viewerform.partrad.value = maxmask-2;\n";
	$javascript .= "		document.viewerform.lowpass.value = Math.floor(maxmask/25);\n";
	$javascript .= "	}\n";
	$javascript .= "	document.viewerform.lastring.value = maxlastring;\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('eman');	

	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","noref/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'noref'.($norefruns+1);
	$rundescrval = $_POST['description'];
	$stackidval = $_POST['stackid'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$numfactors = ($_POST['numfactors']) ? $_POST['numfactors'] : '8';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$partrad = ($_POST['partrad']) ? $_POST['partrad'] : '150';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '200';
	$firstring = ($_POST['numpart']) ? $_POST['firstring'] : '2';
	$lastring = ($_POST['lastring']) ? $_POST['lastring'] : '150';
	echo"
	<p>
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	openRoundBorder();
	echo docpop('runid','<b>NoRef Run Name:</b>');
	echo "<input type='text' name='runid' value='$runidval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of NoRef Alignment:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='36'>$rundescrval</textarea>\n";
	closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	$prtlruns=count($prtlrunIds);

	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		Particles:<BR>
		<select name='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($stackIds as $stack) {
			// echo divtitle("Stack Id: $stack[stackid]");
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
	echo docpop('initmethod','<B>Alignment initialization method:</B>');
	echo "<br/>";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='allaverage' "
		.((!$_POST['initmethod'] || $_POST['initmethod'] == 'allaverage') ? 'CHECKED' : '')
		.">\n Average all particles in stack<br/>\n";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='selectrand' "
		.($_POST['initmethod'] == 'selectrand' ? 'CHECKED' : '')
		.">\n Average random 1% of partcles<br/>\n";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='randpart' "
		.($_POST['initmethod'] == 'randpart' ? 'CHECKED' : '')
		.">\n Pick a random particle<br/>\n";
	//echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='template' "
	//	.($_POST['initmethod'] == 'template' ? 'CHECKED' : '')
	//	.">\n Use a template image<br/>\n";
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
	echo "<INPUT TYPE='text' NAME='partrad' SIZE='4' VALUE='$partrad'>\n";
	echo docpop('partrad','Particle Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='maskrad' SIZE='4' VALUE='$maskrad'>\n";
	echo docpop('maskrad','Mask Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo "<b>Alignment-specific Radii (in Pixels)</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='firstring' SIZE='4' VALUE='$firstring'>\n";
	echo docpop('firstring','First Ring Radius');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='lastring' SIZE='4' VALUE='$lastring'>\n";
	echo docpop('lastring','Last Ring Radius');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br />\n";
	echo "<br />\n";

	echo "<FONT COLOR='#DD3333' SIZE='-2'>WARNING: more than 3000 particles can take forever to process</FONT><BR>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo " to Use<BR>\n";

	echo "<INPUT TYPE='text' NAME='numfactors' VALUE='$numfactors' SIZE='4'>\n";
	echo docpop('numfactors','Number of Factors');
	echo " in Coran<BR>\n";
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</TR>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<HR>\n";
	echo"<input type='submit' name='showcommand' value='Show Command Only'>\n";
	echo"<input type='submit' name='process' value='Start NoRef Alignment'><br />\n";
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process'] && !$_POST['showcommand']) echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	writeBottom();
	exit;
}

function runNoRefAlign($runjob) {
	$expId=$_GET['expId'];
	$runid=$_POST['runid'];
	$outdir=$_POST['outdir'];

	$command.="norefAlignment.py ";

	$stackvars=$_POST['stackid'];
	$partrad=$_POST['partrad'];
	$maskrad=$_POST['maskrad'];
	$lowpass=$_POST['lowpass'];
	$firstring=$_POST['firstring'];
	$lastring=$_POST['lastring'];
	$numpart=$_POST['numpart'];
	$numfactors=$_POST['numfactors'];
	$initmethod=$_POST['initmethod'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|~~\|',$stackvars);

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createNoRefAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	//$stackid=$_POST['stackid'];
	if (!$stackid) createNoRefAlignForm("<B>ERROR:</B> No stack selected");

	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// classification
	if ($numpart > 6000 || $numpart < 10) createNoRefAlignForm("<B>ERROR:</B> Number of particles must be between 10 & 6000");
	if ($numfactors > 20 || $numfactors < 1) createNoRefAlignForm("<B>ERROR:</B> Number of factors must be between 1 & 20");

	$particle = new particledata();

	// check num of particles
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) createNoRefAlignForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls)");

	$stackparams=$particle->getStackParams($stackid);

	// check first & last ring radii
	if ($firstring > (($boxsz/2)-2)) createNoRefAlignForm("<b>ERROR:</b> First Ring Radius too large!");
	if ($lastring > (($boxsz/2)-2)) createNoRefAlignForm("<b>ERROR:</b> Last Ring Radius too large!");

	// check particle radii
	if ($apix) {
		$boxrad = $apix * $boxsz;
		if ($partrad > $boxrad) createNoRefAlignForm("<b>ERROR:</b> Particle radius too large!");
		if ($maskrad > $boxrad) createNoRefAlignForm("<b>ERROR:</b> Mask radius too large!");
	}
	
	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$procdir = $outdir.$runid;
		$command.="--outdir=$procdir ";
	}
	$command.="--description=\"$description\" ";
	$command.="--runname=$runid ";
	$command.="--stack=$stackid ";
	$command.="--rad=$partrad ";
	$command.="--mask=$maskrad ";
	$command.="--first-ring=$firstring ";
	$command.="--last-ring=$lastring ";
	if ($lowpass) $command.="--lowpass=$lowpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-factors=$numfactors ";
	if ($initmethod) $command.="--init-method=$initmethod ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($runjob) {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) {
			createNoRefAlignForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}

		submitAppionJob($command,$outdir,$runid,$expId);
		exit;
	}
	else {
		writeTop("No Ref Align Run Params","No Ref Align Params");
		echo"
	<p><center>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>NoRef Alignment Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>run id</TD><TD>$runid</TD></TR>
	<TR><TD>stack id</TD><TD>$stackid</TD></TR>
	<TR><TD>part rad</TD><TD>$partrad</TD></TR>
	<TR><TD>mask rad</TD><TD>$maskrad</TD></TR>
	<TR><TD>low pass</TD><TD>$lowpass</TD></TR>
	<TR><TD>first ring</TD><TD>$firstring</TD></TR>
	<TR><TD>last ring</TD><TD>$lastring</TD></TR>
	<TR><TD>num part</TD><TD>$numpart</TD></TR>
	<TR><TD>num factors</TD><TD>$numfactors</TD></TR>
	<TR><TD>init method</TD><TD>$initmethod</TD></TR>
	<TR><TD>out dir</TD><TD>$outdir</TD></TR>
	<TR><TD>commit</TD><TD>$commit</TD></TR>
	</table></center>\n";
		writeBottom();
	}
}
?>
