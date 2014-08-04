<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *
 */

// Include any files that contain needed functions or classes.
// Be sure to use require_once instead of require.
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/clusterParamsForm.inc";
require_once "inc/forms/ddstackForm.inc";

// Decide which method to enter. If this is our first time through, we create the form.
// If the form values have already been submitted by the user, we create a processing run command.
// The POST array is an associative array of variables passed to the current script via the HTTP POST method. 
if ( $_POST['process'] ) 
{
	// if form values have been submitted, evaluate them and create a command
	createCommand();
} else {
	// if this is the first time through, create the launch form
	createForm();
}

// createForm() will output the html code needed to display the launch form to the user
function createForm( $extra=false, $title='runCatchupDDAlign.py Launcher', $heading='DD Alignment Catchup' ) 
{
	// ------ Get Project and Session (aka Experiment) Ids ------ //
	// This is a standard chunck of code that does not often change.
	// Get the experiment ID that was passed to this script in the URL.
	$expId = $_GET['expId'];
	if ( $expId )
	{
		$sessionId = $expId;
		$formAction = $_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId = $_POST['sessionId'];
		$formAction = $_SERVER['PHP_SELF'];
	}
	$projectId = getProjectId();
	
	// ------ Create any needed Javascript ------ //
	// Javascript allows values in the form to change within the client, 
	// rather than reloading the page from the web server. 
	// This line is in all Appion pages.
	$javascript = "<script src='../js/viewer.js'></script>\n";
	
	// Enable pop-up help. 
	// This does not change and is required for help messages.
	$javascript .= writeJavaPopupFunctions('appion');	

	// This line does not change and is required for Appion processing pages to add the standard header and menu.
	processing_header( $title, $heading, $javascript );
	// Write out errors, if any came up:
	// This line should not change
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	// connect to particle database
	$particle = new particledata();
	$stackInfos = $particle->getDDStackRunIdsAlign($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;
	
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/ddstack/';
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	// These are needed if we submit this as a job
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'ddstack'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'ddstack'.($alignruns+1);

	$ddstackform = new DDStackForm('','Select a dd frame stack to align','ddstack.ddstack' );

	// start the main form
	echo "<form name='viewerform' method='POST' action='$formAction'>\n";
	
	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
		
	// --- Row 1 ---  
	// Display the heading
	echo "<tr>";
	echo "<td>";
	echo "<H4 style='align=\'center\' >DD Alignment Catchup Parameters</H4><hr />";
	echo "</td>";
	echo "</tr>";
	
	// --- Row 3 --- 
	// Add common parameters
	echo "<tr>";
	echo "<td>";
	if (!$stackInfos) {
		echo "<font color='red'><B>No DD Frame Stacks for this Session</B></font>\n";
	} else {
		echo docpop('stack','<b>Select a ddstack to align:</b>');
		echo "<br/>";
		echo $ddstackform->generateForm();
	}
	echo "</td></tr>\n";
	
	// extra space
	echo "<tr><td valign='top'>\n";
	echo "</td></tr>\n";
	
	// Add a commit checkbox
	echo "<tr>\n";
	echo "<td valign='top'>\n";
	echo "<br><br>";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	// This is how you manually add pop-up help
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "</td></tr>\n</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
	
	// --- Row 4 --- 
	// Add submit button
	echo "<tr>\n";
	echo "<td colspan='2' align='center'>\n";
	echo "<hr />\n";
	echo "<br/>\n";	
	echo getSubmitForm("Run DD Alignment Catchup");
	echo "</td>";
	echo "</tr>";
	
	// End Table
	echo "</table>\n";	
	echo "<br />";

	// Add references for this processing method.
	// Create an instance of a publication with the appropriate 
	// key found in myami/myamiweb/processing/inc/publicationList.inc.
	$pub = new Publication('appion');
	echo $pub->getHtmlTable();

	// end form
	echo"</form><br/>\n";	

	echo showReference('gpudriftcorr');
	echo showReference("appion");
	// This line is required to provide the standard Appion header and side menu
	processing_footer();
	exit;
}


function createCommand() 
{
	/* ***********************************
	 PART 1: Get variables from POST array and validate
	 ************************************* */	
	$stackid = $_POST['ddstack'];
	$commit = ($_POST['commit']=="on") ? true : false;

	//make sure a stack was selected
	if (!$stackid)
		$errorMsg .= "<B>ERROR:</B> No dd frame stack selected";

	// Get the run name and directory
	// This is not needed for the catchup command, but is needed for appion
	$particle 		= new particledata();
	$outdirResult 	= $particle->getDDStackOutdir($stackid);
	$pathArray 		= explode('/', $outdirResult[0]['path']);
	$runname 		= array_pop($pathArray);
	$outdir 		= implode('/', $pathArray);
	
	$_POST['runname'] = $runname;
	$_POST['outdir']  = $outdir;
	
	// reload the form with the error messages
	if ( $errorMsg ) createForm( $errorMsg );
	
	
	/* *******************
	 PART 2: Create program command
	 ******************** */
	$command = "catchUpDDAlign.py ";
			
	$command.="--ddstack=$stackid ";	
	if ($commit) {
		$command.="--commit ";
	} else {
		$command.="--no-commit ";
	}
	
	/* *******************
	 PART 3: Create header info, i.e., references
	 ******************** */
	$headinfo = "";
	
	// Add reference for selected refinement method
	$headinfo .= showReference("gpudriftcorr");
	$headinfo .= showReference("appion");

	/* *******************
	 PART 5: Show or Run Command
	 ******************** */
	$nproc = 1;
	$jobtype = 'catchupddalign';
	$errors = showOrSubmitCommand($command, $headinfo, $jobtype, $nproc);

	// if error display them
	if ($errors)
		createForm($errors);
	exit;

}


?>


