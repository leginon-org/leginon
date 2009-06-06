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
	runSpiderNoRefAlign();
} else {
	createSpiderNoRefAlignForm();
}

function createSpiderNoRefAlignForm($extra=false, $title='spiderNoRefAlign.py Launcher', $heading='Spider Reference Free Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
		$projectId=getProjectFromExpId($sessionId);
	}

	// connect to particle database
	$particle = new particledata();
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$stackIds = $particle->getStackIds($sessionId);
	$alignIds = $particle->getAlignStackIds($sessionId);
	$alignruns=count($alignIds);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set max last ring radius
	$javascript .= "	var maxlastring = (stackArray[2]/2)-2;\n";
	// set particle radius and lp
	$javascript .= "	if (stackArray[1]) {\n";
	$javascript .= "		var maxmask = Math.floor(((stackArray[2]/2)-2)*stackArray[1]);\n";
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
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$rundescrval = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = split('\|--\|',$stackidstr);
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'noref'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'noref'.($alignruns+1);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '400';
	$partrad = ($_POST['partrad']) ? $_POST['partrad'] : '150';
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
	echo docpop('runid','<b>Spider NoRef Run Name:</b>');
	echo "<input type='text' name='runname' value='$runnameval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Spider NoRef Alignment:</b>');
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
		Particles:<br>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
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

	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br />\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
	echo docpop('hpval','High Pass Filter Radius');
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

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo " to Use<br>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run Spider NoRef Alignment");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}
	processing_footer();
	exit;
}

function runSpiderNoRefAlign() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];



	$stackval=$_POST['stackval'];
	$partrad=$_POST['partrad'];
	$lowpass=$_POST['lowpass'];
	$highpass=$_POST['highpass'];
	$firstring=$_POST['firstring'];
	$lastring=$_POST['lastring'];
	$numpart=$_POST['numpart'];
	$bin=$_POST['bin'];
	$initmethod=$_POST['initmethod'];
	$templateid=$_POST['templateid'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createSpiderNoRefAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid) createSpiderNoRefAlignForm("<B>ERROR:</B> No stack selected");

	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// classification
	if ($numpart < 10) createSpiderNoRefAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	$particle = new particledata();

	// check num of particles
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) createSpiderNoRefAlignForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls)");

	// check first & last ring radii
	if ($firstring > (($boxsz/2)-2)) createSpiderNoRefAlignForm("<b>ERROR:</b> First Ring Radius too large!");
	if ($lastring > (($boxsz/2)-2)) createSpiderNoRefAlignForm("<b>ERROR:</b> Last Ring Radius too large!");

	// check particle radii
	if ($apix) {
		$boxrad = $apix * $boxsz;
		if ($partrad > $boxrad) createSpiderNoRefAlignForm("<b>ERROR:</b> Particle radius too large!");
	}
	
	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;

	}

	$command="spiderNoRefAlign.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	$command.="--rad=$partrad ";
	$command.="--first-ring=$firstring ";
	$command.="--last-ring=$lastring ";
	if ($lowpass) $command.="--lowpass=$lowpass ";
	if ($highpass) $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--bin=$bin ";
	if ($initmethod) $command.="--init-method=$initmethod ";
	if ($initmethod=='template' && $templateid) $command.="--templateid=$templateid ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process'] == "Run Spider NoRef Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createSpiderNoRefAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'partalign');
		// if errors:
		if ($sub) createSpiderNoRefAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("No Ref Align Run Params","No Ref Align Params");
		echo"
		<table width='600' class='tableborder' border='1'>
		<tr><td colspan='2'>
		<b>Spider NoRef Alignment Command:</b><br />
		$command
		</td></tr>
		<tr><td>run id</td><td>$runname</td></tr>
		<tr><td>stack id</td><td>$stackid</td></tr>
		<tr><td>part rad</td><td>$partrad</td></tr>
		<tr><td>low pass</td><td>$lowpass</td></tr>
		<tr><td>high pass</td><td>$highpass</td></tr>
		<tr><td>first ring</td><td>$firstring</td></tr>
		<tr><td>last ring</td><td>$lastring</td></tr>
		<tr><td>num part</td><td>$numpart</td></tr>
		<tr><td>binning</td><td>$bin</td></tr>
		<tr><td>init method</td><td>$initmethod</td></tr>
		<tr><td>run dir</td><td>$rundir</td></tr>
		<tr><td>commit</td><td>$commit</td></tr>
		</table>\n";
		processing_footer();
	}
}
?>
