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
	runNoRefAlign();
} else {
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

	// connect to particle database
	$particle = new particledata();
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$stackIds = $particle->getStackIds($sessionId);
	$norefruns=0;
	foreach($particle->getNoRefIds($sessionId, True) as $norefr) {
		$runname=$norefr['name'];
		ereg("([0-9]{1,})", $runname, $regs);
		$norefruns=($regs[0]>$norefruns) ? $regs[0]: $norefruns;
	}
	$defrunid = 'noref'.($norefruns+1);

	$javascript = '<script type="text/javascript" src="../js/viewer.js"></script>'."\n";
	// javascript to switch the defaults based on the stack
	$javascript .= '<script type="text/javascript">'."\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
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

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
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
	$runidval = ($_POST['runid']) ? $_POST['runid'] : $defrunid;
	$rundescrval = $_POST['description'];
	$stackidval = $_POST['stackval'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$numfactors = ($_POST['numfactors']) ? $_POST['numfactors'] : '8';
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$partrad = ($_POST['partrad']) ? $_POST['partrad'] : '150';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '200';
	$firstring = ($_POST['numpart']) ? $_POST['firstring'] : '2';
	$lastring = ($_POST['lastring']) ? $_POST['lastring'] : '150';
	$templateid = ($_POST['templateid']) ? $_POST['templateid'] : '';
	echo"
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
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
	echo closeRoundBorder();
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
		Particles:<br>
		<select name='stackval' onchange='switchDefaults(this.value)'>\n";
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
			echo "<OPTION VALUE='$stackid|--|$apix|--|$boxsz|--|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$stackid) echo " SELECTED";
			echo ">$runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo"</SELECT><br>\n";
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo docpop('initmethod','<B>Alignment initialization method:</B>');
	echo "<br/>";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='allaverage' "
		.($_POST['initmethod'] == 'allaverage' ? 'CHECKED' : '')
		.">\n Average all particles in stack<br/>\n";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='selectrand' "
		.((!$_POST['initmethod'] || $_POST['initmethod'] == 'selectrand') ? 'CHECKED' : '')
		.">\n Average random 1% of partcles<br/>\n";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='randpart' "
		.($_POST['initmethod'] == 'randpart' ? 'CHECKED' : '')
		.">\n Pick a random particle<br/>\n";
	echo "<INPUT TYPE='radio' NAME='initmethod' VALUE='template' "
		.($_POST['initmethod'] == 'template' ? 'CHECKED' : '')
		.">\n Use a template image<br/>\n";
	echo docpop('template','Template Id');
	echo ":&nbsp;<INPUT TYPE='text' NAME='templateid' SIZE='4' VALUE='$templateid'>\n";
	echo "<br />\n";

	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br></TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><br>\n";

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
	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('bin','Particle binning');
	echo "<font size='-2'>(adjust above ring numbers)</font><br>\n";


	echo "<br />\n";

	echo "<FONT COLOR='#DD3333' SIZE='-2'>WARNING: more than 3000 particles can take forever to process</FONT><br>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo " to Use<br>\n";


	echo "<INPUT TYPE='text' NAME='numfactors' VALUE='$numfactors' SIZE='4'>\n";
	echo docpop('numfactors','Number of Factors');
	echo " in Coran<br>\n";
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run NoRef Alignment");
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

function runNoRefAlign() {
	$expId=$_GET['expId'];
	$runid=$_POST['runid'];
	$outdir=$_POST['outdir'];

	$command.="norefAlignment.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";

	$stackval=$_POST['stackval'];
	$partrad=$_POST['partrad'];
	$maskrad=$_POST['maskrad'];
	$lowpass=$_POST['lowpass'];
	$firstring=$_POST['firstring'];
	$lastring=$_POST['lastring'];
	$numpart=$_POST['numpart'];
	$numfactors=$_POST['numfactors'];
	$bin=$_POST['bin'];
	$initmethod=$_POST['initmethod'];
	$templateid=$_POST['templateid'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createNoRefAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	//$stackid=$_POST['stackval'];
	if (!$stackid) createNoRefAlignForm("<B>ERROR:</B> No stack selected");

	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// classification
       	if ($numpart < 10) createNoRefAlignForm("<B>ERROR:</B> Must have more than 10 particles");
	if ($numfactors < 2) createNoRefAlignForm("<B>ERROR:</B> Must have at least 2 factors");

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
		$command.="--rundir=$procdir ";
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
	$command.="--bin=$bin ";
	if ($initmethod) $command.="--init-method=$initmethod ";
	if ($initmethod=='template' && $templateid) $command.="--templateid=$templateid ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run NoRef Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createNoRefAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'norefali');
		// if errors:
		if ($sub) createNoRefAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("No Ref Align Run Params","No Ref Align Params");
		echo"
	<table width='600' class='tableborder' border='1'>
	<tr><td colspan='2'>
	<b>NoRef Alignment Command:</b><br />
	$command
	</td></tr>
	<tr><td>run id</td><td>$runid</td></tr>
	<tr><td>stack id</td><td>$stackid</td></tr>
	<tr><td>part rad</td><td>$partrad</td></tr>
	<tr><td>mask rad</td><td>$maskrad</td></tr>
	<tr><td>low pass</td><td>$lowpass</td></tr>
	<tr><td>first ring</td><td>$firstring</td></tr>
	<tr><td>last ring</td><td>$lastring</td></tr>
	<tr><td>num part</td><td>$numpart</td></tr>
	<tr><td>num factors</td><td>$numfactors</td></tr>
	<tr><td>binning</td><td>$bin</td></tr>
	<tr><td>init method</td><td>$initmethod</td></tr>
	<tr><td>out dir</td><td>$outdir</td></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	</table>\n";
		processing_footer();
	}
}
?>
