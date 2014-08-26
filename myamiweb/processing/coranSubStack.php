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

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runSubStack();
}
// Create the form page
else {
	createSubStackForm();
}

function createSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a Coran-only Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$reconId = $_GET['reconId'];
	if (!$reconId) $reconId = $_POST['reconId'];
	$refId = $_GET['refId'];
	if (!$refId) $refId = $_POST['refId'];
	$iter = $_GET['iter'];

	//query the database for parameters
	$particle = new particledata();
	$reconIds = $particle->getReconIdsFromSession($expId, false);

	$defrunname = 'coranstack'.$refId;
	$formAction .= "&reconId=$reconId&refId=$refId&iter=$iter";

	// Set any existing parameters in form
	$description = ($_POST['description']) ? $_POST['description'] : '';
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	$maxjump = ($_POST['maxjump']) ? $_POST['maxjump'] : 20;

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=getBaseAppionPath($sessioninfo).'/stacks';

	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $outdir;

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	

	echo"
	<table border=3 class=tableborder>";
	echo"
	<tr>
		<td valign='top'>\n";

	$basename = basename($classfile);
	$reconlink = "reconreport.php?expId=$expId&reconId=$reconId";
	$recondata = $particle->getReconInfoFromRefinementId($reconId);
	$stackId = $particle->getStackIdFromReconId($reconId);
	$nump = $particle->getNumStackParticles($stackId);

	echo"<b>Reconstruction Run Information:</b> <ul>\n"
		."<li>Recon ID/Name: [ $reconId ] <a href='$reconlink'>$recondata[name]</a>\n"
		."<li>Recon Description: $recondata[description]\n"
		."<li>Stack ID: $stackId\n"
		."</ul>\n";

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname' size='15'><br/><br/>\n";

	#echo "<input type='text' name='outdir' value='$outdir'>\n";
	#echo "Output directory:<i>$outdir</i><br/>\n";
	#echo "<br/>\n";

	echo docpop('outdir','<b>Output directory:</b>');
	echo "<input type='text' name='outdir' value='$outdir' size='40'>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	echo docpop('descr','<b>Description:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='2' cols='60'>$description</textarea>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br/>\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo "<br/>\n";
	echo getSubmitForm("Create SubStack");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	echo spiderRef();
	echo appionRef();

	processing_footer();
	exit;
}

function runSubStack() {
	/* *******************
	PART 1: Get variables
	******************** */
	$refId = $_GET['refId'];
	$commit=$_POST['commit'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$description) createSubStackForm("<B>ERROR:</B> Enter a brief description");
	if (!$refId) createSubStackForm("<B>ERROR:</B> You must specify an iterId");

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="coranSubStack.py ";
	$command.="--description=\"$description\" ";
	$command.="--iterid=$refId ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref
	$headinfo .= spiderRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', 2);
	// if error display them
	if ($errors)
		createSubStackForm($errors);
	exit;
}

?>
