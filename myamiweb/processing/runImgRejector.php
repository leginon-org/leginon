<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runImgRejector();
}

// Create the form page
else {
	createImgRejectorForm();
}

function createImgRejectorForm($extra=false, $title='imgRejector.py Launcher', $heading='Run Image Rejector') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=getProjectId();

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctfdata=$particle->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);

	$javascript="<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
	  function enableace(){
	    if (document.viewerform.acecheck.checked){
	      document.viewerform.ctfcutoff.disabled=false;
	      document.viewerform.ctfcutoff.value='0.8';
	    }
	    else {
	      document.viewerform.ctfcutoff.disabled=true;
	      document.viewerform.ctfcutoff.value='0.8';
	    }
	  }
	  </SCRIPT>\n";
	$javascript .= writeJavaPopupFunctions('appion');
	
	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"
       <FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/imgreject/';
		$sessionname=$sessioninfo['Name'];
	}

	// Set any existing parameters in form
	$runidval = ($_POST['runname']) ? $_POST['runname'] : 'reject1';	 
	$commitcheck = 'CHECKED';
	$noacecheck = ($_POST['noace']=='on') ? 'CHECKED' : ($ctfdata ? 'CHECKED' : '');
	$nopickscheck = ($_POST['nopicks']=='on') ? 'CHECKED' : '';
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$presets=$sessiondata['presets'];
	// ace check params
	$acecheck = ($_POST['acecheck']=='on') ? 'CHECKED' : '';
	$acedisable = ($_POST['acecheck']=='on') ? '' : 'DISABLED';
	$ctfcutoff = ($_POST['acecheck']=='on') ? $_POST['ctfcutoff'] : '0.8';
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo docpop('runname','<b>Reject Run Name:</b>');
	echo "<input type='text' name='runname' value='$runidval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$outdir' size='38'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$presets=$sessiondata['presets'];
	if ($presets && count($presets) > 1) {
		echo"<B>Preset</B>\n<SELECT name='preset'>\n";
		foreach ($presets as $preset) {
			echo "<OPTION VALUE='$preset' ";
			// make en selected by default
			if ($preset==$presetval) echo "SELECTED";
			echo ">$preset</OPTION>\n";
		}
		echo"</SELECT><br/><br/>\n";
	} elseif ($presets) {
		echo"<B>Preset:</B>&nbsp;&nbsp;".$presets[0]."\n\n";
		echo"<input type='hidden' name='preset' VALUE=".$presets[0].">\n";
		echo"<br/>\n";
	} else {
		//no presets
		echo"<input type='hidden' name='alldbimages' VALUE=1>\n";
		echo"<I>No Presets for this Session<br/>\n"
			."Will Process ALL Images</I><br>\n";
	}
	echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	echo "</td></tr>\n";

	echo "<tr><td>\n";
	echo "<input type='checkbox' name='notiltpairs' $notiltpairscheck>\n";
	echo docpop('notiltpairs','Reject images with no tilt pairs');
	echo "<br/></td></tr>\n";

	echo "<tr><td>\n";
	echo "<input type='checkbox' name='nopicks' $nopickscheck>\n";
	echo docpop('nopicks','Reject images with no particles');
	echo "<br/></td></tr>\n";

	echo "<tr><td>\n";
	echo "<input type='checkbox' name='noace' $noacecheck>\n";
	echo docpop('noace','Reject images with no ACE information');
	echo "<br/></td></tr>\n";

	echo"<tr><td valign='TOP'>\n";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','Commit to Database');
	echo "<br />\n";
	echo "</td></tr>";

	echo "</table>\n";



	echo"
	</td>
	<td class='tablebg'>
	<table cellpadding='5' border='0'>
	<tr><td valign='TOP'>\n";


	if ($ctfdata) {
		echo"
		<tr><td>
		<input type='checkbox' name='acecheck' onclick='enableace(this)' $acecheck>
		ACE Confidence Cutoff<br />
		&nbsp;&nbsp;&nbsp;
		Use Values Above: <input type='text' name='ctfcutoff' $acedisable value='$ctfcutoff' size='4'>
		<FONT SIZE=-2>(btw 0.0 - 1.0)</FONT>
		</td></tr>\n";

		$fields = array('defocus1', 'defocus2');
		$bestctf = $particle->getBestStats($fields, $sessionId);
		$min="-".$bestctf['defocus1'][0]['min'];
		$max="-".$bestctf['defocus1'][0]['max'];
		// check if user has changed values on submit
		$minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
		$maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
		$sessionpath=preg_replace("%E%","e",$sessionpath);
		$minval = preg_replace("%E%","e",round($minval,8));
		$maxval = preg_replace("%E%","e",round($maxval,8));
		echo"
		<tr>
			<td valign='TOP'>
			<b>Defocus Limits</b><br />
			<input type='text' name='dfmin' value='$minval' size='25'>
			<input type='hidden' name='dbmin' value='$minval'>
			Minimum<br />
			<input type='text' name='dfmax' value='$maxval' size='25'>
			<input type='hidden' name='dbmax' value='$maxval'>
			Maximum
			</td>
		</tr>\n";
	}
	echo "</table>
	</td>
	</tr>
	<tr>
		<td colspan='2' align='CENTER'>
		<hr />";
  echo getSubmitForm("Run Image Rejector", false, false);
	echo "
	  </td>
	</tr>
	</table>
	</form>
	</center>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runImgRejector() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$runname = $_POST['runname'];
	$outdir = $_POST['outdir'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';

	if ($_POST[preset]) $dbimages=$_POST['sessionname'].",".$_POST['preset'];
	
	// check defocus cutoffs
	$dfmin = ($_POST['dfmin']==$_POST['dbmin'] || $_POST['dfmin']>$_POST['dbmin']) ? '' : $_POST['dfmin'];
	$dfmax = ($_POST['dfmax']==$_POST['dbmax'] || $_POST['dfmax']<$_POST['dbmax']) ? '' : $_POST['dfmax'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a session was selected
	if (!$outdir) createImgRejectorForm("<b>ERROR:</b> Select an experiment session");
	
	// ctf cutoff
	if ($_POST['acecheck']=='on') {
		$ctfcutoff = $_POST['ctfcutoff'];
		if ($ctfcutoff > 1 || $ctfcutoff < 0 || !$ctfcutoff) 
			createImgRejectorForm("<b>ERROR:</b> CTF cutoff must be between 0 & 1");
	}
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command.="imgRejector.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--runname=$runname ";
	$command.="--rundir=".$outdir."/".$runname." ";
	if ($_POST['preset']) $command.="--preset=".$_POST['preset']." ";
	$command.="--session=".$_POST['sessionname']." ";
	if ($_POST['commit']=='on') $command.="--commit ";
	if ($_POST['notiltpairs']=='on') $command.="--notiltpairs ";
	if ($_POST['nopicks']=='on') $command.="--nopicks ";
	if ($_POST['noace']=='on') $command.="--noace ";
	if ($ctfcutoff) $command.="--ctfcutoff=$ctfcutoff ";
	if ($dfmin) $command.="--mindefocus=$dfmin ";
	if ($dfmax) $command.="--maxdefocus=$dfmax ";
	$command.="--no-wait ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'imgRejector', $nproc);

	// if error display them
	if ($errors)
		createImgRejectorForm("<b>ERROR:</b> $errors");
	
}
?>
