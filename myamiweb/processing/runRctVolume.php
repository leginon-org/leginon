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
require "inc/summarytables.inc";

if ($_POST['process']) {
	// If values submitted, evaluate data
	runRctVolume();
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

	$alignid = $_GET['alignid'];
	$clusterid = $_GET['clusterid'];
	$classnum = $_GET['classnum'];

	// save other params to url formaction
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	$formAction.=($classnum) ? "&classnum=$classnum" : "";
	$formAction.=($alignid) ? "&alignid=$alignid" : "";
	$formAction.=($clusterid) ? "&clusterid=$clusterid" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$tiltstack = ($_POST['tiltstack']) ? $_POST['tiltstack'] : '';
	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : '';
	$lowpassvol = ($_POST['lowpassvol']) ? $_POST['lowpassvol'] : '15';
	$highpasspart = ($_POST['highpasspart']) ? $_POST['highpasspart'] : '400';
	$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '4';
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","rctvolume/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;

	$javascript  = "";
	$javascript .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#dd0000'>$extra</FONT>\n<HR>\n";
	}

	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' VALUE='$sessionname'>\n";
	}

	//query the database for parameters
	$particle = new particledata();
	$numRctRuns = $particle->getNumberOfRctRuns($sessionId, True);
	while (glob($sessionpathval.'rct'.($numRctRuns+1)."*"))
		$numRctRuns += 1;
	$defrctname = 'rct'.($numRctRuns+1);
	if ($alignid)
		$defrctname .= "align".$alignid;
	if ($clusterid)
		$defrctname .= "clust".$clusterid;
	if ($classnum) {
		$classstr = ereg_replace(",","",$classnum);
		$defrctname .= "class".$classstr;
	}
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrctname;

	echo"<TABLE BORDER=3 CLASS=tableborder>";
	echo"<TR><TD VALIGN='TOP'>\n";

	//Rct Run Name
	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

	echo openRoundBorder();
	echo docpop('runname','<b>Rct Volume Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Rct Volume run:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
	echo closeRoundBorder();

	echo "</td></tr></table>\n";

	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

	if ($_GET['alignid']) {
		//Case 1: Align Id Selected
		echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";
		echo openRoundBorder();
		echo alignstacksummarytable($_GET['alignid'], $mini=true);
		echo closeRoundBorder();
		echo "<INPUT type='hidden' name='stack' value='align".$_GET['alignid']."'>\n";
		echo "</td></tr></table>\n";
	} elseif ($_GET['clusterid']) {
		//Case 2: Cluster Id Selected
		//echo clusterstacksummarytable($_GET['clusterid']);
		echo "<INPUT type='hidden' name='stack' value='clust".$_GET['clusterid']."'>\n";
	} else {
		//Case 3: Drop Down Menus
		$alignids = $particle->getAlignStackIds($expId);
		if ($alignids) {
			echo "<SELECT name='stack'>\n";
			foreach ($alignids as $aligniddata){
				$alignid = $aligniddata['alignstackid'];
				$aligndata = $particle->getAlignStackParams($alignid);
				$runname  = $aligndata['name'];
				$numclass = $particle->getNumAlignStackReferences($alignid);
				$descript = substr($aligndata['description'],0,40);
				echo "<OPTION value='align$alignid'";
				if ($alignid == $_POST['alignid']) echo " SELECTED";
				echo">Align $alignid: $runname ";
				if ($numclass > 0)
					echo "($numclass refs) ";
				echo "$descript...</OPTION>\n";
				$clusterids = $particle->getClusteringStacksForAlignStack($alignid);
				if ($clusterids) {
					foreach ($clusterids as $clusteriddata){
						$clusterid = $clusteriddata['clusterid'];
						$clusterdata = $particle->getClusteringStackParams($clusterid);
						$runname  = $clusterdata['name'];
						$numclass = $clusterdata['num_classes'];
						$descript = substr($clusterdata['description'],0,40);
						echo "<OPTION value='clust$clusterid'";
						if ($clusterid == $_POST['clusterid']) echo " SELECTED";
						echo"> -&gt; Cluster $clusterid: $runname ($numclass classes) $descript...</OPTION>\n";
					}
				}
			}
			echo "</SELECT>\n<br/>\n<br/>\n";
		}
	}

	//Class Numbers
	echo docpop('classnum','Class Numbers');
	echo " to generate volume:<br/>";
	if (!$classnum && $classnum != '0') {
		$classnum = '0,1';
		echo "<INPUT type='text' name='classnum' size='5' value='$classnum'>";
		echo "&nbsp;(starts at 0,1,2,...)\n<br/>\n<br/>\n";
	} else {
		echo "<INPUT type='hidden' name='classnum' value='$classnum'>\n";
		echo "<FONT SIZE='+1'>&nbsp;Selected class numbers '<b>$classnum</b>'</FONT> ";
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
		if (!$stackparams['tiltangle'] ||
		 ($stackparams['tiltangle'] != "notilt" && $stackparams['tiltangle'] != "all")) {
			$descript  = substr($stackparams['description'],0,40);
			#print_r($stackparams);
			$box  = $stackparams['boxSize'];
			$numpart = commafy($particle->getNumStackParticles($stackid));
			//handle multiple runs in stack
			$stackname = $stackparams['shownstackname'];
			if ($stackparams['substackname'])
				$stackname .= "-".$stackparams['substackname'];
			//print_r($stackparams[0]);
			echo "<OPTION value='$stackid'";
			if ($stackid == $tiltstack) echo " SELECTED";
			echo">$stackid: $stackname ($box boxsize, $numpart parts) $descript...</OPTION>\n";
		}
	}
	echo "</SELECT>\n";
	echo "</td></tr></table>\n";

	//Second half of the table
	echo "</TD></TR>\n<TR><TD VALIGN='TOP' CLASS='tablebg' WIDTH='100%'>\n";

	echo "<table border='0' cellspacing='8' cellpading='8'><tr><td>\n";

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

	//High pass filter of particles
	echo docpop('hpval','High Pass Particle Filter:<br/>');
	echo "<INPUT TYPE='text' NAME='highpasspart' SIZE='5' VALUE='$highpasspart'>\n";
	echo "<FONT SIZE='-2'>(in &Aring;ngstroms)</FONT>\n";
	echo "\n<br/>\n<br/>\n";

	//Number of iterations
	echo docpop('numiter','Number of Particle centering iterations:<br/>');
	echo "<INPUT TYPE='text' NAME='numiter' SIZE='2' VALUE='$numiter'>\n";

	echo "</td></tr></table>\n";

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

function runRctVolume() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];

	$tiltstack = $_POST['tiltstack'];
	$maskrad = $_POST['maskrad'];
	$lowpassvol = $_POST['lowpassvol'];
	$highpasspart = $_POST['highpasspart'];
	$numiter = $_POST['numiter'];
	$classnum = $_POST['classnum'];
	$description=$_POST['description'];
	$stack=$_POST['stack'];

	if (!$tiltstack)
		createRctVolumeForm("<B>ERROR:</B> No tilted stack selected");

	if (!$stack)
		createRctVolumeForm("<B>ERROR:</B> No align or cluster stack selected");

	if (!$classnum && $classnum!='0')
		createRctVolumeForm("<B>ERROR:</B> Class numbers were not provided");

	if (!$description)
		createRctVolumeForm("<B>ERROR:</B> Enter a brief description of the rct volume");

	if (!$maskrad)
		createRctVolumeForm("<B>ERROR:</B> Enter a mask radius");

	if (!$runname)
		createRctVolumeForm("<B>ERROR:</B> Enter a unique run name");

	if (!$stack)
		createRctVolumeForm("<B>ERROR:</B> No alignment selected");

	if (substr($stack,0,5) == "align")
		$alignid = (int) substr($stack,5);
	elseif (substr($stack,0,5) == "clust")
		$clusterid = (int) substr($stack,5);

	$particle = new particledata();
	$stackparam = $particle->getStackParams($tiltstack);
	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	//putting together command
	$command ="rctVolume.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--description=\"$description\" ";
	$command.="--rundir=$rundir ";
	$command.="--runname=$runname ";
	if ($alignid)
		$command.="--align-id=$alignid ";
	elseif ($clusterid)
		$command.="--cluster-id=$clusterid ";
	$command.="--classnums=$classnum ";
	$command.="--tilt-stack=$tiltstack ";
	$command.="--mask-rad=$maskrad ";
	$command.="--num-iters=$numiter ";
	$command.="--lowpassvol=$lowpassvol ";
	$command.="--highpasspart=$highpasspart ";

	$command.="--commit ";

	// submit job to cluster
	if (($_POST['process']=="Rct Volume")) {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createRctVolumeForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'rctvolume',False,False,False,8);
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
		<TR><TD>align id</TD><TD>$alignid</TD></TR>
		<TR><TD>cluster id</TD><TD>$clusterid</TD></TR>
		<TR><TD>class nums</TD><TD>$classnum</TD></TR>
		<TR><TD>tilt stack</TD><TD>$tiltstack</TD></TR>
		<TR><TD>num iter</TD><TD>$numiter</TD></TR>
		<TR><TD>volume lowpass</TD><TD>$lowpassvol</TD></TR>
		<TR><TD>particle highpass</TD><TD>$highpasspart</TD></TR>
		<TR><TD>mask rad</TD><TD>$maskrad</TD></TR>";

		echo"</TABLE>\n";
		processing_footer();
	}
}

?>
