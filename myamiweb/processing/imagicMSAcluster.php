<?php
/**
 *      The Leginon software is Copyright 2007
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Create an IMAGIC Reclassification Job initiating a 3d0 model generation
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";

// check for errors in submission form
if ($_POST['process']) {
	if (!$_POST['num_classes']) jobform("error: number of classes not specified");
	runImagicMSAcluster();
}
else jobform();

function jobform($extra=false)	{

	$javafunc .= writeJavaPopupFunctions('appion');
	
	$particle = new particledata();
	
	// get session info
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$analysisId=$_GET['analysisId'];
	$analysisdata=$particle->getImagicAnalysisParams($analysisId);
	$alignId=$_GET['alignId'];
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$analysisdata['path'];
		$sessionname=$sessioninfo['Name'];
	}

	// connect to particle database
#	$prtlrunIds = $particle->getParticleRunIds($expId);
#	$imagicAnalysisIds = $particle->getImagicClassIds($expId);
	
	processing_header("IMAGIC Class Clustering","IMAGIC Class Clustering",$javafunc);
	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	$alignparams = $particle->getAlignStackParams($alignId);
	$nump=$alignparams['num_particles'];
	// Set any existing parameters in form
	$description = $_POST['description'];
	$classidval = $_GET['imagicAnalysisId'];
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$ignore_images = ($_POST['ignore_images']) ? $_POST['ignore_images'] : '0';
	$ignore_members = ($_POST['ignore_members']) ? $_POST['ignore_members'] : '0';
	$defaultNumClasses = round(sqrt($nump));
	$defaultNumClasses.= ",".round(sqrt(4*$nump));
	$defaultNumClasses.= ",".round(sqrt(16*$nump));
	$num_classes = ($_POST['num_classes']) ? $_POST['num_classes'] : $defaultNumClasses;
	$num_factors = ($_POST['num_factors']) ? $_POST['num_factors'] : '8';
	
	echo "<form name='viewerform' method='POST' action='$formaction'>\n";
	echo"
	<table border='0' class='tableborder'>
	<TR>
		<TD valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<TR><td>\n";
	echo openRoundBorder();
	echo "<br>\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br>\n";
	echo "<input type='text' name='outdir' value='$outdir' size='42'>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo docpop('descr','<b>Description of IMAGIC Clustering run:</b>');
	echo "<br>\n";
	echo "<textarea name='description' rows='3' cols='36'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	echo "<TR>";
	echo "    <TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br></TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	echo "<b>Clustering Parameters</b>\n";
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='num_classes' SIZE='8' VALUE='$num_classes'>\n";
	echo docpop('numclass','Number of Classes');
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='num_factors' SIZE='4' VALUE='$num_factors'>\n";
	echo docpop('num_eigenimages','Number of Eigenimages to use');
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='ignore_images' SIZE='4' VALUE='$ignore_images'>\n";
	echo docpop('ignore_images','Percentage of images to ignore');
	echo "<br>\n";
	echo "<br>\n";
	
	echo "<b>Summing Parameters</b>\n";
	echo "<br>\n";
	
	echo "<INPUT TYPE='text' NAME='ignore_members' VALUE='$ignore_members' SIZE='4'>\n";
	echo docpop('ignore_members', 'Percentage of worst class members to ignore');
	echo "<br>";
	
	echo "  </TD>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr>\n";
	echo getSubmitForm("run imagic");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}
	
	echo imagicRef();

	processing_footer();
	exit;
	
	
}

function runImagicMSAcluster($extra=false)	{
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$analysisId=$_GET['analysisId'];
	$runname=date("yMd").random_letters();
	$_POST['runname'] = $runname;
	$outdir=$_POST['outdir'];
	$classvalues=$_POST['imagicAnalysisId'];
	$ignore_images=$_POST['ignore_images'];
	$num_classes=$_POST['num_classes'];
	$num_factors=$_POST['num_factors'];
	$ignore_members=$_POST['ignore_members'];
	$description=$_POST['description'];
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	
	// get stack id, apix, box size, and total particles from input
	list($stackid,$apix,$boxsize,$totpartls) = preg_split('%\|--\|%',$stackvalues);
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	/* *******************
	PART 3: Create program command
	******************** */
	
	// create python command for executing imagic job file	
	$command = "imagicMSAcluster.py";
	$command.= " --projectid=$projectId";
	$command.= " --imagicAnalysisId=$analysisId";
	$command.= " --runname=$runname";
	$command.= " --rundir=$outdir";
	$command.= " --ignore_images=$ignore_images";
	$command.= " --num_classes=$num_classes";
	$command.= " --num_eigenimages=$num_factors";
	$command.= " --ignore_members=$ignore_members";
	$command.= " --description=\"$description\"";
	if ($commit) $command.= " --commit";
	else $command.=" --no-commit";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= imagicRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partcluster', $nproc);

	// if error display them
	if ($errors)
		jobform("<b>ERROR:</b> $errors");
	
}

function random_letters($length = 2, $letters = 'abcdefghijklmnopqrstuvwxyz') {
      $s = '';
      $lettersLength = strlen($letters)-1;
     
      for($i = 0 ; $i < $length ; $i++)	{
	      $s .= $letters[rand(0,$lettersLength)];
      }

      return $s;
 } 
