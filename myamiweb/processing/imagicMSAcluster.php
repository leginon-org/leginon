<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an IMAGIC Reclassification Job initiating a 3d0 model generation
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

// check for errors in submission form
if ($_POST['process']) {
	if (!is_numeric($_POST['num_classes'])) jobform("error: number of classes not specified");
	runImagicMSAcluster();
}
else jobform();



function jobform($extra=false)	{

	$javafunc .= writeJavaPopupFunctions('appion');
	
	$particle = new particledata();
	
	// get session info
	echo "<form name='viewerform' method='POST' action='$formaction'>\n";
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// connect to particle database
#	$prtlrunIds = $particle->getParticleRunIds($expId);
#	$imagicAnalysisIds = $particle->getImagicClassIds($expId);
	
	processing_header("IMAGIC Class Clustering","IMAGIC Class Clustering",$javafunc);

	// write out errors, if any came up:
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$runid = ($_POST['runid']) ? $_POST['runid'] : 'cluster'.($imagicnorefruns+1);
	$description = $_POST['description'];
	$classidval = $_GET['imagicAnalysisId'];
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$ignore_images = ($_POST['ignore_images']) ? $_POST['ignore_images'] : '0';
	$ignore_members = ($_POST['ignore_members']) ? $_POST['ignore_members'] : '0';
	$num_classes = ($_POST['num_classes']) ? $_POST['num_classes'] : '';
	
	echo"
	<table border='0' class='tableborder'>
	<TR>
		<TD valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<TR><TD>\n";
	echo openRoundBorder();
	echo docpop('runid','<b>Cluster Run Name:</b>');
	echo "<input type='text' name='runid' value='$runid'>\n";
	echo "<BR/>\n";
	echo "<BR/>\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<BR/>\n";
	echo "<input type='text' name='outdir' value='$outdir' size='38'>\n";
	echo "<BR/>\n";
	echo "<BR/>\n";
	echo docpop('descr','<b>Description of IMAGIC Clustering run:</b>');
	echo "<BR/>\n";
	echo "<textarea name='description' rows='3' cols='36'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</TD></TR><TR>\n";
	echo "<TD VALIGN='TOP'>\n";
/*	if (!$imagicAnalysisIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo "
		<select name='classid'>\n";
		foreach ($imagicAnalysisIds as $class) {
			$stackparams=$particle->getStackParams($stack[stackid]);

			// get pixel size and box size
			$mpix=$particle->getStackPixelSizeFromStackId($stack['stackid']);
			if ($mpix) {
				$apix = $mpix*1E10;
				$apixtxt=format_angstrom_number($mpix)."/pixel";
			}
			$boxsize=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];

			//handle multiple runs in stack
			$runname=$stackparams[shownstackname];
			$totprtls=commafy($particle->getNumStackParticles($stack[stackid]));
			$stackid = $stack['stackid'];
			echo "<OPTION VALUE='$stackid|--|$apix|--|$boxsize|--|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$stackid) echo " SELECTED";
			echo ">$runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsize pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
*/	echo "</TD></TR><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></TR>\n";
	echo "<TR>";
	echo "    <TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<BR/></TD></TR>\n</TABLE>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	echo "<b>Clustering Parameters</b>\n";
	echo "<BR/>\n";
/*	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
*/	echo "<INPUT TYPE='text' NAME='num_classes' SIZE='4' VALUE='$num_classes'>\n";
	echo docpop('num_classes','Number of Classes');
	echo "<BR/>\n";

	echo "<INPUT TYPE='text' NAME='ignore_images' SIZE='4' VALUE='$ignore_images'>\n";
	echo docpop('ignore_images','Percentage of images to ignore');
	echo "<BR/>\n";
        echo "<BR/>\n";
	
	echo "<b>Summing Parameters</b>\n";
	echo "<BR/>\n";
	
	echo "<INPUT TYPE='text' NAME='ignore_members' VALUE='$ignore_members' SIZE='4'>\n";
	echo docpop('ignore_members', 'Percentage of worst class members to ignore');
	echo "<BR/>";
	
	echo "  </TD>\n";
	echo "  </TR>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</TR>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<HR />\n";
	echo getSubmitForm("run imagic");
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

function runImagicMSAcluster($extra=false)	{
	$expId=$_GET['expId'];
	$projectId=getProjectFromExpId($expId);
	$runid=$_POST['runid'];
	$outdir=$_POST['outdir'];
	$classvalues=$_POST['imagicAnalysisId'];
	$ignore_images=$_POST['ignore_images'];
	$num_classes=$_POST['num_classes'];
	$ignore_members=$_POST['ignore_members'];
	$description=$_POST['description'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	
	// get stack id, apix, box size, and total particles from input
	list($stackid,$apix,$boxsize,$totpartls) = split('\|--\|',$stackvalues);

	// create python command for executing imagic job file	
	$pythoncmd = "imagicMSAcluster.py";
	$pythoncmd.= " --projectId=$projectId --imagicAnalysisId=$imagicAnalysisId --runname=$runid --rundir=$outdir/cluster";
	$pythoncmd.= " --ignore_images=$ignore_images --num_classes=$num_classes --ignore_members=$ignore_members";
	$pythoncmd.= " --description=\"$description\"";
	if ($commit) $pythoncmd.= " --commit\n";
	else $pythoncmd.=" --no-commit\n";
/*
	// write to jobfile
	$jobfile = "{$runid}_imagicMSAcluster.job";
	$tmpjobfile = "/tmp/$jobfile";
	$f = fopen($tmpjobfile,'w');
	fwrite($f,$pythoncmd);
	fclose($f);	

	// create appion directory & copy job & batch files
	$cmd = "mkdir -p $outdir/$runid\n";
	$cmd.= "cp $tmpjobfile $outdir/$runid/$jobfile\n";
	$cmd.= "cd $outdir/$runid\n";
	$cmd.= "chmod 777 $jobfile\n";
	exec_over_ssh($_SERVER['HTTP_HOST'], $user, $pass, $cmd, True);
*/
	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($pythoncmd,$outdir,$runid,$expId,'runImagicMSAcluster');
		// if errors:
		if ($sub) jobform("<b>ERROR:</b> $sub");
	}

	processing_header("IMAGIC Clustering","IMAGIC Clustering",$javafunc);

	echo "<pre>";
	echo htmlspecialchars($pythoncmd);
	echo "</pre>";

	processing_footer();
	exit;
	


}
