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
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/alignJobs.inc";
require_once "inc/publication.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadIsac();
} else {
	createUploadIsacForm();
}

function createUploadIsacForm($extra=false, $title='uploadSparxISAC.py Launcher', $heading='Upload Sparx ISAC Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$jobId=$_GET['jobId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF'];
	}

	$javascript .= writeJavaPopupFunctions('appion');	
	$javascript .= editTextJava();
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra)
		echo "<span style='font-size: larger; color:#bb3333;'>$extra</span><br />\n";

	// connect to particle database
	$particle = new particledata();
	$isacJob  = $particle->getJobInfoFromId($jobId);

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	$jobId = $isacJob['DEF_id'];
	echo "<form name='viewerform' method='POST' action='$formAction&jobId=$jobId'>\n";
	
	// Post values needed for showOrSubmitCommand()
	$outdir = $isacJob['appath'];
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	$runname = "upload".basename($outdir);
	echo "<input type='hidden' name='runname' value='$runname'>\n";
	
	
	// TODO: The ApSparxISACJobData table does not have an entry for this run at this point
	// so we are unable to implement the hide feature.
//	if ($_POST['hideJob'.$jobId] == 'hide') {
//		$particle->updateHide('ApSparxISACJobData', $jobId, '1');
//		$isacJob['hidden']='1';
//	} elseif ($_POST['hideUndoJob'.$jobId] == 'unhide') {
//		$particle->updateHide('ApSparxISACJobData', $jobId, '0');
//		$isacJob['hidden']='0';
//	}

	echo openRoundBorder();
	echo "<table cellspacing='8' cellpading='2' border='0'>\n";

	echo "<tr><td colspan='5'>\n";
	$nameline = "<span style='font-size: larger; color:#111111;'>\n";
	$nameline .= "Job Id: $jobId &nbsp;\n";
	$nameline .= " ".$isacJob['name'];
	$nameline .= "</span>\n";
//	if ($isacJob['hidden'] == 1) {
//		$nameline.= " <font color='#cc0000'>HIDDEN</font>\n";
//		$nameline.= " <input class='edit' type='submit' name='hideUndoJob".$jobId."' value='unhide'>\n";
//		$display_keys['hidden'] = "<font color='#cc0000'>HIDDEN</font>";
//	} else $nameline.= " <input class='edit' type='submit' name='hideJob".$jobId."' value='hide'>\n";

	echo apdivtitle($nameline);
	echo "</td></tr>\n";

	$avgfile = $isacJob['appath']."/average.mrc";
	if (file_exists($avgfile)) {
		echo "<tr><td align='left' rowspan='30' align='center' valign='top'>";
		echo "<img src='loadimg.php?filename=$avgfile&s=100' height='100'><br/>\n";
		echo "<i>final reference image</i>\n";
		echo "</td></tr>\n";
	}

	//echo "<tr><td colspan='2'>\n";
	//echo print_r($isacJob)."<br/><br/>";
	//echo "</td></tr>\n";

	$display_keys['date time'] = $isacJob['DEF_timestamp'];
	$display_keys['path'] = "<input type='text' name='path' value='".$isacJob['appath']."' size='40'>\n";
	$display_keys['file prefix'] = $isacJob['timestamp'];

	// TODO: what are these files called for isac?
	$refstackname = "part".$isacJob['timestamp']."_average.hed";
	$refstack = $isacJob['path']."/".$refstackname;
	if (file_exists($refstack))
		$display_keys['reference stack'] = "<a target='stackview' HREF='viewstack.php?"
			."file=$refstack&expId=$expId'>".$refstackname."</a>";

	// TODO: since we are using the ApAppionJob ID rather than the ApSparxISACJob Id, (because there is no
	// entry in the latter yet), there is no timestamp info available.
	echo "<input type='hidden' name='timestamp' value='".$isacJob['timestamp']."'>\n";
	foreach($display_keys as $k=>$v) {
		echo formatHtmlRow($k,$v);
	}

	echo "<tr><td colspan='2'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "</td></tr>\n";

	echo "<tr><td colspan='2'>\n";
	echo getSubmitForm("Upload Job $jobId");
	echo "</td></tr>\n";

	echo "</table>\n";
	echo closeRoundBorder();
	echo "<br/>\n";
	echo "</form>\n";


	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}

	$pub = new Publication('isac');
	echo $pub->getHtmlTable();

	processing_footer();
	exit;
}

function runUploadIsac() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$jobId = $_GET['jobId'];
	$timestamp=$_POST['timestamp'];
	$rundir=$_POST['path'];
	$commit = ($_POST['commit']=="on") ? true : false;

	//make sure a stack was selected
	//if (!$rundir)
	//	createUploadIsacForm("<B>ERROR:</B> Unknown output directory");

	// make sure outdir ends with '/' and append run name
	$outdir = dirname($rundir);
	$runname = basename($rundir);
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	
	/* *******************
	PART 3: Create program command
	******************** */
	// setup command
	$command="uploadSparxISAC.py ";
	$command.="--rundir=$rundir ";
	if ($timestamp) $command.="-t $timestamp ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	$command.="--projectid=".getProjectId()." ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$pub = new Publication('isac');
	$headinfo .= $pub->getHtmlTable();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createUploadIsacForm("<b>ERROR:</b> $errors");
	
}
?>
