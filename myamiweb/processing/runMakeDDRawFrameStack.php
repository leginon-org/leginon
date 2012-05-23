<?php
/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
 *
 *	Make stack function
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/appionloop.inc";

if ($_POST['process']) {
	// IF VALUES SUBMITTED, EVALUATE DATA
	runMakestack();
} else {
	// Create the form page
	createMakestackForm();
}

function createMakestackForm($extra=false, $title='makeDDRawFrameStack.py Launcher', $heading='Create a Direct Detector Image Stack') {
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
	
	// Get the session path
	$sessiondata = getSessionList($projectId,$sessionId);
	$sessioninfo = $sessiondata['info'];
	$sessionpath = getBaseAppionPath($sessioninfo).'/ddstack';

	// Set the runname
	// the default run name is "ddstack" followed by an ever incrementing number
	$jobtype = "makeddrawframestack";
	$particle = new particledata();
	$stackruns = $particle->getMaxRunNumber( $jobtype, $expId );
	
	// sanity check - make certain we are not going to overwrite data
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$sessionpathval = (substr($sessionpathval, -1) == '/')? $sessionpathval : $sessionpathval.'/';
	
	while (file_exists($sessionpathval.'ddstack'.($stackruns+1))) {
		$stackruns += 1;
	}
	$defrunname = "ddstack".($stackruns+1);
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : $defrunname;	
	
	// Set any existing parameters in form
	$single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
	$rundescrval = ($_POST['description']) ? $_POST['description'] : True;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'CHECKED' : '';

	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";

#	echo docpop('stackname','<b>Stack File Name:</b>');
	echo "<input type='hidden' name='single' value='start.hed'>\n";

	createAppionLoopTable($sessiondata, $runnameval, "ddstack", 0, $rundescrval);
 
	echo "</td>";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td colspan='2' align='CENTER'>\n
		<input type='checkbox' name='testimage' onclick='enabledtest(this)' $testcheck>
		Run on a single image:
		<input type='text' name='testfilename' $testdisabled value='$testvalue' size='45'>
		<hr />";	
	echo getSubmitForm("Make Stack");
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	echo appionRef();

	processing_footer();
	exit;
}


function runMakestack() {
	
	/* *******************
	PART 1: Get variables
	******************** */
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$single=$_POST['single'];
	$description = $_POST['description'];
	
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	
	// set image inspection selection
	$norejects=$inspected=0;
	if ($_POST['checkimage']=="Non-rejected") {
		$norejects=1;
	} elseif ($_POST['checkimage']=="Best") {
		$norejects=1;
		$inspected=1;
	}
	
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ","\ ",$testimage);
	}
	
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	
	//make sure a session was selected
	if (!$description)
		createMakestackForm("<b>ERROR:</b> Enter a brief description of the stack");

	//make sure a session was selected
	if (!$outdir)
		createMakestackForm("<b>ERROR:</b> Select an experiment session");

	/* *******************
	PART 3: Create program command
	******************** */
	
	$command = "makeDDRawFrameStack.py"." ";
	$command.="--description=\"$description\" ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMakestackForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
		
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makeddrawframestack', $nproc, $testimage);

	// if error display them
	if ($errors) {
		createMakestackForm("<b>ERROR:</b> $errors");
	} else if ($testimage) {
		// add the appion wrapper to the command for display
		$wrappedcmd = addAppionWrapper($command);
			
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<B>Make DD Raw Frame Stack Command:</B><br />$wrappedcmd";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		$testjpg = ereg_replace(".mrc","",$_POST['testfilename']);
		
		// TODO: writing the test result needs to be completed still, this is not functional!!!
		$testResultFile = $testjpg."_st.mrc";
		$resultimg = Path::join($outdir, $runname, $testResultFile);
				
		if ($_POST['process'] != "Just Show Command") {
			$results .= writeTestResults($resultimg, $dogmaplist, $_POST['bin']);
		} else {
			$results.= writeTestResults($resultimg,$ccclist,$bin=$_POST['bin']);			
		}		
		
		createMakestackForm(false, 'Make DD Raw Frame Stack (Single Image) Results', 'Make DD Raw Frame Stack (Single Image) Results', $results);
	}		
}
	
?>
