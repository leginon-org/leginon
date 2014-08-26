<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runEMANRefine2d();
} else {
	createEMANRefine2dForm();
}

function createEMANRefine2dForm($extra=false, $title='EMAN refine2d.py Launcher', $heading='EMAN Refine 2d Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$sessionId=$expId;
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set # of classes
	$javascript .= "	var numclass = Math.ceil(Math.sqrt(stackArray[3])/4);\n";
	$javascript .= "	document.viewerform.numclass.value = numclass;\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$sessionpath=getBaseAppionPath($sessioninfo).'/align/';

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'emantwod'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'emantwod'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$numclass = ($_POST['numclass']) ? $_POST['numclass'] : ceil(sqrt($numpart)/4.0);
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '8';

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if (!$stackIds) {
		echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use</b>');
		echo "<br/>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";

	echo "<b>Filter Params</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass' >\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass' >\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4' >\n";
	echo docpop('partbin','Particle binning');
	echo "<br/>\n";

	echo "<br/>\n";

	echo "<b>Job Parameters</b>\n";
	echo "<br/>\n";
	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4' >\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numclass' VALUE='$numclass' SIZE='4' >\n";
	echo docpop('refine2dnumclass','Number of classes');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numiter' VALUE='$numiter' SIZE='4'>\n";
	echo docpop('refine2dnumiter','Number of iterations');
	echo "<br/>\n";

	echo "<br/>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "<br/>\n";
	echo getSubmitForm("Run EMAN Refine 2d");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	echo emanRef();

	processing_footer();
	exit;
}

function runEMANRefine2d() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$numclass = $_POST['numclass'];
	$numiter=$_POST['numiter'];
	$bin=$_POST['bin'];
	$description=$_POST['description'];
	$commit = ($_POST['commit']=="on") ? true : false;

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = preg_split('%\|--\|%',$stackval);
	//make sure a session was selected

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$description)
		createEMANRefine2dForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid)
		createEMANRefine2dForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createEMANRefine2dForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createEMANRefine2dForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than the number of particles in the stack ($totprtls)");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	/* *******************
	PART 3: Create program command
	******************** */
	// setup command
	$command ="emanRefine2d.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-class=$numclass ";
	$command.="--bin=$bin ";
	$command.="--num-iter=$numiter ";
	if ($commit)
		$command.="--commit ";
	else
		$command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= emanRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createEMANRefine2dForm("<b>ERROR:</b> $errors");
		
}
?>
