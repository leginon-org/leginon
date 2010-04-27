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

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
	runTopolAlign();
} else {
	createTopolAlignForm();
}

function createTopolAlignForm($extra=false, $title='topologyAlignment.py Launcher', $heading='Topology Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectFromExpId($sessionId);
		$formAction=$_SERVER['PHP_SELF'];
	}

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
	// set mask radius
	$javascript .= "	var mask = Math.floor((stackArray[2]/2)-2);\n";
	$javascript .= "	document.viewerform.mask.value = mask;\n";
	// set starting & ending # of classes
	$javascript .= "	var strcls = Math.ceil(Math.sqrt(stackArray[3])/4);\n";
	$javascript .= "	var endcls = Math.ceil(Math.sqrt(stackArray[3]));\n";
	$javascript .= "	document.viewerform.startnumcls.value = strcls;\n";
	$javascript .= "	document.viewerform.endnumcls.value = endcls;\n";
	$javascript .= "	estimatetime();\n";
	$javascript .= "}\n";
	$javascript .= "
		function estimatetime() {
			var secperiter = 0.001;
			var stackval = document.viewerform.stackval.value;
			var stackArray = stackval.split('|--|');
			var numpart = document.viewerform.numpart.value;
			var boxsize = stackArray[2];
			var numpix = Math.pow(boxsize/document.viewerform.bin.value, 2);
			var calctime = (numpart/1000.0) * document.viewerform.startnumcls.value * numpix * secperiter / (document.viewerform.nproc.value - 1);
			if (calctime < 70) {
				var time = Math.round(calctime*100.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' seconds';
			} else if (calctime < 3700) {
				var time = Math.round(calctime*0.6)/100.0
				document.viewerform.timeestimate.value = time.toString()+' minutes';
			} else if (calctime < 3700*24) {
				var time = Math.round(calctime/36.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' hours';
			} else {
				var time = Math.round(calctime/36.0/24.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' days';
			}
		}\n";
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
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'topol'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'topol'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = split('\|--\|',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$startnumcls = ($_POST['startnumcls']) ? $_POST['startnumcls'] : $numpart/30;
	$endnumcls = ($_POST['endnumcls']) ? $_POST['endnumcls'] : $numpart/50;
	$mask = ($_POST['mask']) ? $_POST['mask'] : 100;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '4';
	$iter = ($_POST['iter']) ? $_POST['iter'] : '15';
	// topology alignment parameters
	$itermult = ($_POST['itermult']) ? $_POST['itermult'] : '10';
	$learn = ($_POST['learn']) ? $_POST['learn'] : '0.01';
	$ilearn = ($_POST['ilearn']) ? $_POST['ilearn'] : '0.0005';
	$age = ($_POST['age']) ? $_POST['age'] : '25';

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>Topology Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Topology Alignment:</b>');
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

	echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' VALUE='$nproc' onChange='estimatetime()'>\n";
	echo "Number of Processors";
	echo "<br/>\n";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	//echo "<B>Particle Params:</B></A><br>\n";

	echo "<b>Filters</b>\n";
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass' onChange='estimatetime()'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass' onChange='estimatetime()'>\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('partbin','Particle binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='mask' VALUE='$mask' SIZE='4'>\n";
	echo docpop('mask','Mask (in pixels, unbinned)');
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<b>Job Parameters</b>\n";
	echo "<br/>\n";
	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='startnumcls' VALUE='$startnumcls' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('startnumcls','Starting # of classes');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='endnumcls' VALUE='$endnumcls' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('endnumcls','Ending # of classes');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='iter' VALUE='$iter' SIZE='4'>\n";
	echo docpop('topoliter','Number of iterations');
	echo "<br/>\n";

	echo "<br/>\n";

	echo "<b>Alignment Parameters</b><br/>\n";

	echo "<input type='text' name='itermult' value='$itermult' size='4'>\n";
	echo docpop('itermult','Iteration multiplier');
	echo "<br/>\n";

	echo "<input type='text' name='learn' value='$learn' size='4'>\n";
	echo docpop('learn','Direct learning rate');
	echo "<br/>\n";

	echo "<input type='text' name='ilearn' value='$ilearn' size='4'>\n";
	echo docpop('ilearn','Indirect learning rate');
	echo "<br/>\n";

	echo "<input type='text' name='age' value='$age' size='4'>\n";
	echo docpop('age','Edge age');
	echo "<br/>\n";
	echo "<br/>\n";
	echo docpop('mramethod','<b>MRA package:</b>');
	echo "<br/>\n";
	$mramethods=array('IMAGIC','EMAN');
	echo "<select name='mramethod'>\n";
	foreach ($mramethods as $mra){
		echo "<option";
		if ($_POST['mramethod']==$mra) echo " selected";
		echo ">$mra</option>\n";
	}
	echo "</select>\n";
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "Time estimate for first iteration: ";
	echo "<INPUT TYPE='text' NAME='timeestimate' SIZE='16' onFocus='this.form.elements[0].focus()'>\n";
	echo "<br/>\n";
	echo getSubmitForm("Run Topology Alignment");
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

function runTopolAlign() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$startnumcls = $_POST['startnumcls'];
	$endnumcls = $_POST['endnumcls'];
	$iter=$_POST['iter'];
	$bin=$_POST['bin'];
	$mask=$_POST['mask'];
	$itermult=$_POST['itermult'];
	$learn=$_POST['learn'];
	$ilearn=$_POST['ilearn'];
	$age=$_POST['age'];
	$description=$_POST['description'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;
	$mramethod = strtolower($_POST['mramethod']);

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	//make sure a session was selected

	if (!$description)
		createTopolAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	if ($nproc > 16)
		createTopolAlignForm("<B>ERROR:</B> Let's be reasonable with the nubmer of processors, less than 16 please");

	//make sure a stack was selected
	if (!$stackid)
		createTopolAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createTopolAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createTopolAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than the number of particles in the stack ($totprtls)");

	// determine calc time
	$stackdata = $particle->getStackParams($stackid);
	$boxsize = ($stackdata['bin']) ? $stackdata['boxSize']/$stackdata['bin'] : $stackdata['boxSize'];
	$secperiter = 0.0025;
	$calctime = ($numpart/1000.0)*$startnumcls*($boxsize/$bin)*($boxsize/$bin)*$secperiter/$nproc;
	// kill if longer than 10 hours
	if ($calctime > 10.0*3600.0)
		createTopolAlignForm("<b>ERROR:</b> Run time per iteration greater than 10 hours<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/3600.0,2)." hours\n");

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	// setup command
	$command ="topologyAlignment.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--stack=$stackid ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--start=$startnumcls ";
	$command.="--end=$endnumcls ";
	$command.="--bin=$bin ";
	$command.="--mask=$mask ";
	$command.="--iter=$iter ";
	$command.="--itermul=$itermult ";
	$command.="--learn=$learn ";
	$command.="--ilearn=$ilearn ";
	$command.="--age=$age ";
	$command.="--mramethod=$mramethod ";

	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	// submit job to cluster
	if ($_POST['process']=="Run Topology Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTopolAlignForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'partalign',False,False,False,$nproc);
		// if errors:
		if ($sub) createTopolAlignForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Topology Align Run Params","Topology Align Params");
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
		echo "
			<tr><td colspan='2'>
			<b>Topology Alignment Command:</b><br />
			$command
			</td></tr>
			<tr><td>run id</td><td>$runname</td></tr>
			<tr><td>stack id</td><td>$stackid</td></tr>
			<tr><td>low pass</td><td>$lowpass</td></tr>
			<tr><td>high pass</td><td>$highpass</td></tr>
			<tr><td>num part</td><td>$numpart</td></tr>
			<tr><td>num start classes</td><td>$startnumcls</td></tr>
			<tr><td>num end classes</td><td>$endnumcls</td></tr>
			<tr><td>iterations</td><td>$iter</td></tr>
			<tr><td>binning</td><td>$bin</td></tr>
			<tr><td>run dir</td><td>$rundir</td></tr>
			<tr><td>commit</td><td>$commit</td></tr>
			</table>\n";
		processing_footer();
	}
}
?>
