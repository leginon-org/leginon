<?php
/**
 * The Leginon software is Copyright 2003 
 * The Scripps Research Institute, La Jolla, CA
 * For terms of the license agreement
 * see	http://ami.scripps.edu/software/leginon-license
 *
 * Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";


if ($_POST['process']) {
	// If values submitted, evaluate data
	runRctVolume(($_POST['process']=="Rct Volume") ? true : false);
} else {
	// Create the form page
	createRctVolumeForm();
}

/*
**
** RCT VOLUME FORM
**
*/
function createRctVolumeForm($extra=false, $title='rctVolume.py Launcher', $heading='Run RCT Volume') {
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);

	if ($_GET['norefClass']) {
		$norefClass=$_GET['norefClass'];
	} elseif ($_POST['norefClass']) {
		$norefClass=$_POST['norefClass'];
	} else {
		$norefClass=0;
	}
	if ($_GET['classnum']) {
		$classnum=$_GET['classnum'];
	} elseif ($_POST['classnum']) {
		$classnum=$_POST['classnum'];
	} else {
		$classnum=-1;
	}

	// save other params to url formaction
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$formAction.=($classnum) ? "&classnum=$classnum" : "";
	$formAction.=($norefClass) ? "&norefClass=$norefClass" : "";

	// Set any existing parameters in form
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'rct1';
	$description = $_POST['description'];
	$tiltstack = ($_POST['tiltstack']) ? $_POST['tiltstack'] : '';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '';
	$lowpassvol = ($_POST['lowpassvol']) ? $_POST['lowpassvol'] : '15';
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '4';

	$javascript  = "";
	$javascript .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#dd0000'>$extra</FONT>\n<HR>\n";
	}

	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=displayExperimentForm($projectId,$expId,$expId);
	$sessioninfo=$sessiondata['info'];

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
	}

	//query the database for parameters
	$particle = new particledata();

	echo"<TABLE BORDER=3 CLASS=tableborder>";
	echo"<TR><TD VALIGN='TOP'>\n";

	//Rct Run Name
	echo docpop('runid','Rct Volume Run Name:<br/>');
	echo "<input type='text' name='runname' value='$runname'>\n<br/>\n<br/>\n";
	echo docpop('descr','<b>Description of Rct run:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='60'>$description</textarea><br/><br/>\n";

	//NoRef Class Drop Down Menu
	echo docpop('norefclass','NoRef Class Id:<br/>');
	if ($norefClass == 0) {
		$norefclassruns = $particle->getAllNoRefClassRuns($expId);
		echo "<SELECT name='norefclass'>\n";
		foreach ($norefclassruns as $class){
			$classid  = $class['DEF_id'];
			$runname  = $class['name'];
			$numclass = $class['num_classes'];
			$descript = substr($class['description'],0,40);
			echo "<OPTION value='$classid'";
			if ($classid == $norefclassrun) echo " SELECTED";
			echo">$classid: $runname ($numclass classes) $descript...</OPTION>\n";
		}
		echo "</SELECT>\n<br/>\n<br/>\n";
	} else {
		$norefclassrun = $particle->getNoRefClassRunData($norefClass);
		echo "<INPUT type='hidden' name='norefclass' value='$norefClass'>\n";
		echo "<FONT SIZE='+1'>Selected NoRef ClassId '<b>$norefClass</b>' with "
			.$norefclassrun['num_classes']." classes</FONT>";
		echo "\n<br/>\n<br/>\n";
	}

	//NoRef Class Number
	echo docpop('classnum','NoRef Class Number');
	echo " to generate volume:<br/>";
	if ($classnum == -1) {
		$classnum = 0;
		echo "<INPUT type='text' name='classnum' size='5' value='$classnum'>";
		echo "&nbsp;(starts at 0,1,2,...)\n<br/>\n<br/>\n";
	} else {
		echo "<INPUT type='hidden' name='classnum' value='$classnum'>\n";
		echo "<FONT SIZE='+1'>Selected class number '<b>$classnum</b>'</FONT> ";
		echo "\n<br/>\n<br/>\n";
	}

	//Tilted stack id
	echo docpop('stackid','Tilted Stack Id:<br/>');
	$stackDatas = $particle->getStackIds($expId);
	echo "<SELECT name='tiltstack'>\n";
	foreach ($stackDatas as $stackdata){
		//print_r($stackdata);
		$stackid = $stackdata['DEF_id'];
		$stackparams = $particle->getStackParams($stackid);
		$runname  = $stackparams[0]['stackRunName'];
		$descript  = substr($stackdata['description'],0,40);
		$numpart = $particle->getNumStackParticles($stackid);
		//print_r($stackparams[0]);
		echo "<OPTION value='$stackid'";
		if ($stackid == $tiltstack) echo " SELECTED";
		echo">$stackid: $runname ($numpart parts) $descript...</OPTION>\n";
	}
	echo "</SELECT>\n<br/>\n<br/>\n";

	//Second half of the table
	echo "</TD></TR>\n<TR><TD VALIGN='TOP' CLASS='tablebg' WIDTH='100%'>\n";

	//Mask radius
	echo docpop('mask','Mask Radius:<br/>');
	echo "<INPUT TYPE='text' NAME='maskrad' SIZE='5' VALUE='$maskrad'>";
	echo "<FONT SIZE='-2'>(in pixels)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Low pass filter of 3d volume
	echo docpop('lpval','3d Low Pass Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='lowpassvol' SIZE='5' VALUE='$lowpassvol'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Number of iterations
	echo docpop('numiter','Number of Particle centering iterations:<br/>');
	echo "<INPUT TYPE='text' NAME='numiter' SIZE='2' VALUE='$numiter'>\n";
	echo "\n<br/>\n<br/>\n";

	//Finish up
	echo "</TD></TR><TR><TD ALIGN='CENTER'><hr/>\n";
	echo getSubmitForm("Rct Volume");
	echo "</td></tr></table></form>\n";

	processing_footer();
	exit;
}

/*
**
** RCT VOLUME RUN
**
*/

function runRctVolume($runjob=false) {
	$expId=$_GET['expId'];
	$runname = $_POST['runname'];
	$tiltstack = $_POST['tiltstack'];
	$maskrad = $_POST['maskrad'];
	$lowpassvol = $_POST['lowpassvol'];
	$numiter = $_POST['numiter'];
	$classnum = $_POST['classnum'];
	$norefclass = $_POST['norefclass'];
	$description=$_POST['description'];

	$particle = new particledata();
	$stackparam = $particle->getStackParams($tiltstack);
	$outdir = dirname(dirname($stackparam['path']));
	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
	}


	if (!$description)
		createRctVolumeForm("<B>ERROR:</B> Enter a brief description of the rct volume");


	if (!$maskrad)
		createRctVolumeForm("<B>ERROR:</B> Enter a mask radius");

	if (!$runname)
		createRctVolumeForm("<B>ERROR:</B> Enter a unique run name");

	//putting together command
	$command ="rctVolume.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--runname=$runname ";
	$command.="--norefclass=$norefclass ";
	$command.="--classnum=$classnum ";
	$command.="--tilt-stack=$tiltstack ";
	$command.="--mask-rad=$maskrad ";
	$command.="--num-iters=$numiter ";
	$command.="--lowpassvol=$lowpassvol ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	// submit job to cluster
	if ($runjob) {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createRctVolumeForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'rctvolume');
		// if errors:
		if ($sub) createRctVolumeForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Rct Volume Command", "Rct Volume Command");

		echo"
		<table width='600' border='1'>
		<tr><td colspan='2'>
		<font size='+1'>
		<B>Rct Volume Command:</B><BR>
		$command
		</font>
		</TD></TR>
		<TR><TD>run name</TD><TD>$runname</TD></TR>
		<TR><TD>norefclass</TD><TD>$norefclass</TD></TR>
		<TR><TD>classnum</TD><TD>$classnum</TD></TR>
		<TR><TD>tiltstack</TD><TD>$tiltstack</TD></TR>
		<TR><TD>numiter</TD><TD>$numiter</TD></TR>
		<TR><TD>volume lowpass</TD><TD>$lowpassvol</TD></TR>
		<TR><TD>mask rad</TD><TD>$maskrad</TD></TR>";

		echo"</TABLE>\n";
		processing_footer();
	}
}

?>
