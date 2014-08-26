<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCombineStack();
} else {
	createCombineStackForm();
}

function createCombineStackForm($extra=false, $title='combinestack.py Launcher', $heading='Combine Stack') {
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	//echo "Project ID: ".$projectId." <br/>\n";
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['showHidden']) $formAction.="&showHidden=True";

	$javascript.= editTextJava();

	processing_header($title, $heading, $javascript, False);
	// write out errors, if any came up:
	if ($extra)
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";

	// --- Get Stack Data --- //
	$particle = new particledata();
	$stackids = $particle->getStackIdsForProject($projectId, False);
	$description = $_POST['description'];
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/stacks/';
	}
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;

	$stackruninfos = $particle->getStackIds($expId, True);
	$stackruns = ($stackruninfos) ? count($stackruninfos) : 0;
	while (file_exists($sessionpath.'stack'.($stackruns+1)))
		$stackruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'combine'.($stackruns+1);

	if ($stackids) {
		echo "<form name='stackform' method='post' action='$formAction'>\n";
		echo "<table border='1'>";
		echo "<tr><td colspan='4'><h2>New stack info:</h2>\n";
		echo docpop('runname','<b>Combined stack name:</b>');
		echo "<br/>\n";
		echo "<input type='text' name='runname' value='$runname'>\n";
		echo "<br/>\n";
		echo docpop('outdir','<b>Output Directory:</b>');
		echo "<br />\n";
		echo "<input type='text' name='outdir' value='$outdir' size='50'>\n";
		echo "<br />\n";
		echo docpop('descr','<b>Description of combined stack:</b>');
		echo "<br/>\n";
		echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
		echo "<br/>\n";
		echo getSubmitForm("Run Combine Stack");
		echo "</td></tr>\n";
		echo "<tr><td colspan='4'><h2>Select stacks to combine:</h2>\n";
		echo "</td></tr>\n";

		// sort stacks by session
		$sessionids = array();
		$stacknums = array();
		foreach ($stackids as $stackdata) {
			$stackid = (int) $stackdata['stackid'];
			$stacknums[] = $stackid;
			$selectdata = $particle->getStackSelectionRun($stackid);
			$sessionid = (int) $selectdata[0]['sessionId'];
			$sessionids[] = $sessionid;
		}
		array_multisort($sessionids, SORT_DESC, $stacknums, SORT_DESC);
		$currsessionid = 0;
		foreach ($stacknums as $stackid) {
			$selectdata = $particle->getStackSelectionRun($stackid);
			$sessionid = (int) $selectdata[0]['sessionId'];
			if ($currsessionid != $sessionid) {
				$currsessionid = $sessionid;
				$sessiondata = $particle->getSessionData($sessionid);
				echo "<tr><td colspan='4'><font size='+1'><br/>Session: ";
				echo "<a href='index.php?expId=".$sessiondata['DEF_id']."'>".$sessiondata['name']."</a></font>&nbsp;\n";
				echo " --  ".$sessiondata['comment'];
				echo "<br/><br/></td></tr>";
			}
			//echo "<br/><br/><br/><br/>";
			echo "<tr><td>\n<input type='checkbox' name='stack$stackid'";
			if ($_POST['stack'.$stackid]) echo " checked";
			echo ">combine<br/>stack id $stackid\n</td><td>\n";
			echo ministacksummarytable($stackid);
			echo "</td></tr>\n";
		}
		echo "</table>";
		echo "</form>";
	} else {
		echo "<B>Project does not contain any stacks.</B>\n";
	}
	echo appionRef();
	processing_footer();
	exit;
}

function runCombineStack() {

	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$projectId = getProjectId();
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];

	$description=$_POST['description'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a description is entered
	if (!$description) createCombineStackForm("<B>ERROR:</B> Enter a brief description");
	
	$particle = new particledata();
	$stackids = $particle->getStackIdsForProject($projectId, False);
	$stacklist = "";
	$count = 0;
	$stacks = array();
	foreach ($stackids as $stackdata) {
		$stackid = $stackdata['stackid'];
		$key = 'stack'.$stackid;
		//$stacklist .= $key.": ".$_POST[$key]."<br/>\n";
		if ($_POST[$key] == 'on') {
			$count++;
			$stacks[]=$stackid;
		}
	}
	$stacklist = implode(',',$stacks);
	if (strlen($stacklist) < 1) 
		createCombineStackForm("<B>ERROR:</B> No stacks selected ".$count.": ".$stacklist);
	if ($count < 2) 
		createCombineStackForm("<B>ERROR:</B> Selected more than one stack");
	
	/* *******************
	PART 3: Create program command
	******************** */
	$command.="combinestack.py ";
	$command.="--projectid=".getProjectId()." ";
	
	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
		$command.="--rundir=$rundir ";
	}
	
	$command.="--runname=$runname ";
	$command.="--stacks=$stacklist ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', $nproc);

	// if error display them
	if ($errors)
		createCombineStackForm("<b>ERROR:</b> $errors");
	
}



?>
