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
require "inc/processing.inc";
require "inc/ctf.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

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
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctf = new ctfdata();
	$ctfdata=$ctf->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$massessrunIds = $particle->getMaskAssessRunIds($sessionId);
	$stackruns = count($particle->getStackIds($sessionId));

	
	$javascript="<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
	  function enableace(){
	    if (document.viewerform.acecheck.checked){
	      document.viewerform.acecutoff.disabled=false;
	      document.viewerform.acecutoff.value='0.8';
	    }
	    else {
	      document.viewerform.acecutoff.disabled=true;
	      document.viewerform.acecutoff.value='0.8';
	    }
	  }
	  </SCRIPT>\n";
	$javascript .= writeJavaPopupFunctions('eman');
	
	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font COLOR='RED'>$extra</font>\n<HR>\n";
	}

	$helpdiv = "
	<div id='dhelp'
		style='position:absolute; 
        	background-color:FFFFDD;
        	color:black;
        	border: 1px solid black;
        	visibility:hidden;
        	z-index:+1'
    		onmouseover='overdiv=1;'
    		onmouseout='overdiv=0;'>
	</div>\n";
	echo $helpdiv;
  
	echo"
       <FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","imgreject/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// Set any existing parameters in form
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'reject1';	 
	$commitcheck = 'CHECKED';
	$noacecheck = ($_POST['noace']=='on') ? 'CHECKED' : ($ctfdata ? 'CHECKED' : '');
	$nopickscheck = ($_POST['nopicks']=='on') ? 'CHECKED' : '';
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$presets=$sessiondata['presets'];
	// ace check params
	$acecheck = ($_POST['acecheck']=='on') ? 'CHECKED' : '';
	$acedisable = ($_POST['acecheck']=='on') ? '' : 'DISABLED';
	$acecutoff = ($_POST['acecheck']=='on') ? $_POST['acecutoff'] : '0.8';
	echo "<p>\n";
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo docpop('runid','<b>Reject Run Name:</b>');
	echo "<input type='text' name='runid' value='$runidval'>\n";
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
			."Will Process ALL Images</I><BR/>\n";
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
		Use Values Above: <input type='text' name='acecutoff' $acedisable value='$acecutoff' size='4'>
		<FONT SIZE=-2>(btw 0.0 - 1.0)</FONT>
		</td></tr>\n";

		$fields = array('defocus1', 'defocus2');
		$bestctf = $ctf->getBestStats($fields, $sessionId);
		$min="-".$bestctf['defocus1'][0]['min'];
		$max="-".$bestctf['defocus1'][0]['max'];
		// check if user has changed values on submit
		$minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
		$maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
		$sessionpath=ereg_replace("E","e",$sessionpath);
		$minval = ereg_replace("E","e",round($minval,8));
		$maxval = ereg_replace("E","e",round($maxval,8));
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
		<HR>";
  echo"   <BR/>
	  <input type='submit' name='process' value='Just Show Command'>
	  <!--<input type='submit' name='process' value='Make Stack'>--><br />
	  </td>
	</tr>
	</table>
	</FORM>
	</CENTER>\n";
	writeBottom();
	exit;
}

function runImgRejector() {
	$expId = $_GET['expId'];
	$runid = $_POST['runid'];
	$outdir = $_POST['outdir'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';

	if ($_POST[preset]) $dbimages=$_POST['sessionname'].",".$_POST['preset'];

	$command.="imgRejector.py ";

	//make sure a session was selected
	if (!$outdir) createImgRejectorForm("<b>ERROR:</b> Select an experiment session");

	// ace cutoff
	if ($_POST['acecheck']=='on') {
		$acecutoff = $_POST['acecutoff'];
		if ($acecutoff > 1 || $acecutoff < 0 || !$acecutoff) 
			createImgRejectorForm("<b>ERROR:</b> Ace cutoff must be between 0 & 1");
	}

	// check defocus cutoffs
	$dfmin = ($_POST['dfmin']==$_POST['dbmin'] || $_POST['dfmin']>$_POST['dbmin']) ? '' : $_POST['dfmin'];
	$dfmax = ($_POST['dfmax']==$_POST['dbmax'] || $_POST['dfmax']<$_POST['dbmax']) ? '' : $_POST['dfmax'];

	$command.="runid=$runid ";
	$command.="outdir=$outdir ";
	if ($dbimages) $command.=" dbimages=$dbimages ";
	else $command.=" alldbimages=$_POST[sessionname] ";
	if ($_POST['commit']=='on') $command.="commit ";
	if ($_POST['notiltpairs']=='on') $command.="notiltpairs ";
	if ($_POST['nopicks']=='on') $command.="nopicks ";
	if ($_POST['noace']=='on') $command.="noace ";
	if ($acecutoff) $command.="acecutoff=$acecutoff ";
	if ($dfmin) $command.="mindefocus=$dfmin ";
	if ($dfmax) $command.="maxdefocus=$dfmax ";
	elseif ($_POST['sessionname']) {
		if ($_POST['preset']) $dbimages=$_POST[sessionname].",".$_POST[preset];
		elseif(!$_POST['alldbimages']) {
			return ("<B>ERROR:</B> Select an image preset for template matching");
			exit;
		}
	}


	// submit job to cluster
	if ($_POST['process']=="Make Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createImgRejectorForm("<b>ERROR:</b> Enter a user name and password");

		submitAppionJob($command,$outdir,$runid,$expId,$testimage);
		exit;
	}

	writeTop("ImgRejector Run","ImgRejector Params");

	if ($massessname) {
		echo"<font color='red'><b>Use a 32-bit machine to use the masks</b></font>\n";
	}
	echo"
	<P>
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>ImgRejector Command:</b><br />
	$command
	</td></tr>
	<tr><td>runid</td><td>$runid</td></tr>
	<tr><td>outdir</td><td>$outdir</td></tr>
	<tr><td>commit</td><td>".$_POST['commit']."</td></tr>
	<tr><td>notiltpairs</td><td>".$_POST['notiltpairs']."</td></tr>
	<tr><td>nopicks</td><td>".$_POST['nopicks']."</td></tr>
	<tr><td>noace</td><td>".$_POST['noace']."</td></tr>
	<tr><td>ace cutoff</td><td>$acecutoff</td></tr>
	<tr><td>minimum defocus</td><td>$dfmin</td></tr>
	<tr><td>maximum defocus</td><td>$dfmax</td></tr>
	</table>\n";
	writeBottom(True,True);
}
?>
