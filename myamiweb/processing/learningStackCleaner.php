<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runLearnStackCleaner();
}

// Create the form page
else {
	createLearningStackCleanerForm();
}

function createLearningStackCleanerForm($extra=false, $title='runLearnStackCleaner.py Launcher', $heading='Clean Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId = $_GET['stackId'];
	// save other params to url formaction
	$formAction .=($stackId) ? "&stackId=$stackId" : "";

	// Set any existing parameters in form
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'learn'.$stackId;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$stackId) $stackId = $_POST['stackId'];

	// get outdir path
	$sessiondata=getSessionList($projectId, $expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=getBaseAppionPath($sessioninfo).'/stacks';

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo "<form name='viewerform' method='post' action='$formAction'>\n";
	
	//query the database for parameters
	$particle = new particledata();
	
	# get stack name
	$stackp = $particle->getStackParams($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];
	$boxsize = $stackp['boxsize'];
	echo "<input type='hidden' name='box' value='$boxsize'>\n";

	echo"<table border=3 class=tableborder>";
	echo"<tr><td valign='top' align='center'>\n";

	// Information table
	echo "<table border='1' class='tableborder' width='640'>";
		echo "<tr><td>\n";
		echo "  <h3>Learning Stack Cleaner</h3>";
		echo "  This function open a window that allow you to categorize particles as good or bad. "
			."From your classification it learns the quality of the particles, which then can be extended "
			." to the entire stack. This idea for this is based on the TMaCS particle picker from the "
			." Rubinstein lab [<a href='http://dx.doi.org/10.1016/j.jsb.2012.12.010'>doi:10.1016/j.jsb.2012.12.010</a>]"
			." but has been completely re-implemented by Neil Voss. "
			."<br/><br/>"
			." It is highly recommended to run on a centered stack or stack with decently centered particles. "
			."<br/><br/>";
		echo "</td></tr>";
	echo "</table>";
	echo "<hr/><br/>\n";

	// Stack info
	echo stacksummarytable($stackId, True);
	echo "<hr/><br/>\n";
	echo"<input type='hidden' name='stackId' value='$stackId'>\n";

	echo"<table border='0'>";
	echo"<tr><td valign='top' align='left'>\n";

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname'><br />\n";
	echo "<br/>\n";

	echo docpop('outdir','<b>Output directory:</b> ');
	echo "<input type='text' name='outdir' value='$outdir' size='50'>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br/>\n";
	echo "</td></tr></table>\n";
	echo "<br/>\n";

	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo "<br/>\n";

	echo getSubmitForm("Learning Stack Cleaner");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	echo appionRef();

	processing_footer();
	exit;
}

function runLearnStackCleaner() {
	/* *******************
	PART 1: Get variables
	******************** */
	$stackId=$_POST['stackId'];
	$commit=$_POST['commit'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	/* *******************
	PART 3: Create program command
	******************** */

	$command ="runLearnStackCleaner.py ";
	$command.="--stack-id=$stackId ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', 1);

	// if error display them
	if ($errors)
		createCenterForm($errors);
	exit;
}

?>
