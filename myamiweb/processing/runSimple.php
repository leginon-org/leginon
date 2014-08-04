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
require_once "inc/forms/simpleParamsForm.inc";

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
function createForm( $extra=false, $title='runSimpleCluster.py Launcher', $heading='SIMPLE Common Lines' ) 
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
	
	// Javascript to switch the defaults based on the stack
	// This javascript function is specific to this page, and is not required for others.
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	$javascript .= "	var boxSize = stackArray[2]\n";
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n"; // remove commas from number
	$javascript .= "	var numpart = stackArray[3]\n";
	$javascript .= "	document.viewerform.numpart.value = numpart;\n";
	$javascript .= "	document.viewerform.clip.value = boxSize;\n";
	$javascript .= "	document.viewerform.ring2.value = boxSize/2 - 2;\n";
	$javascript .= "	document.viewerform.mask.value = boxSize/2 - 2;\n";
	$javascript .= "	document.viewerform.ncls.value = Math.floor(numpart/document.viewerform.minp.value) ;\n";
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	if (bestbin < 1) {\n";
	$javascript .= "		var bestbin = 1 ;}\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	// Enable pop-up help. 
	// This does not change and is required for help messages.
	$javascript .= writeJavaPopupFunctions('appion');	

	// This line does not change and is required for Appion processing pages to add the standard header and menu.
	processing_header($title,$heading,$javascript);
	// Write out errors, if any came up:
	// This line should not change
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;
	
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/abinitio/';
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'simple'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'simple'.($alignruns+1);
	//$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	//var_dump($stackidstr);
	list($stackidval,$apix,$boxsz) = split('\|--\|',$stackidstr);

	// start the main form
	echo "<form name='viewerform' method='POST' action='$formAction'>\n";
	
	// --- Row 1 --- 
	// Add processing run parameters
	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	$runParamsForm = new RunParametersForm( $runname, $sessionpathval, $description );
	echo $runParamsForm->generateForm();
	echo "</td>";
	echo "</tr>";
		
	// --- Row 2 ---  
	// Display the heading
	echo "<tr>";
	echo "<td>";
	echo "<H4 style='align=\'center\' >SIMPLE Common Lines Parameters</H4><hr />";
	echo "</td>";
	echo "</tr>";
	
	// --- Row 3 --- 
	// Add common parameters
	echo "<tr>";
	echo "<td>";
	if (!$stackIds) {
		echo "<font color='red'><B>No Stacks for this Session</B></font>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use:</b>');
		echo "<br/>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
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
	
	// Add parameters specific to the method selected
	echo "<td class='tablebg'>\n";
	echo "<table cellpading='5' border='0'>\n";
	echo "<tr><td valign='top'>\n";
	
	if  (!$apix) {
        echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}

	// Create an instance of the SIMPLE param form, setting it's default values then display it 
	$simpleParamsForm = new SimpleParamsForm($clip='', $bin='', $numpart='', $no_center='',$ring2='', $ncls='',
		$minp='10', $nvars='30', $mask='', $lp='20', $hp='100', $froms='2', $tos='2', $maxits='10',
		$mw='', $frac='0.8', $amsklp='40', $edge='3', $trs='3');
	echo $simpleParamsForm->generateForm();
	
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
	
	// --- Row 4 --- 
	// Add submit button
	echo "<tr>\n";
	echo "<td colspan='2' align='center'>\n";
	echo "<hr />\n";
	echo "<br/>\n";	
	echo getSubmitForm("Run SIMPLE common lines");
	echo "</td>";
	echo "</tr>";
	
	// End Table
	echo "</table>\n";	
	echo "<br />";

	// Add references for this processing method.
	// Create an instance of a publication with the appropriate 
	// key found in myami/myamiweb/processing/inc/publicationList.inc.
	$pub = new Publication('simple');
	echo $pub->getHtmlTable();
	$pub = new Publication('appion');
	echo $pub->getHtmlTable();

	// end form
	echo"</form><br/>\n";	
	
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	// This line is required to provide the standard Appion header and side menu
	processing_footer();
	exit;
}


function createCommand() 
{
	/* ***********************************
	 PART 1: Get variables from POST array and validate
	 ************************************* */
	
	// validate processing run parameters
	$runParametersForm = new RunParametersForm();
	$errorMsg = $runParametersForm->validate( $_POST );
	
	$simpleParamsForm = new SimpleParamsForm();
	$errorMsg .= $simpleParamsForm->validate( $_POST );
	
	$stackval=$_POST['stackval'];
	$commit = ($_POST['commit']=="on") ? true : false;

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	
	//make sure a stack was selected
	if (!$stackid)
		$errorMsg .= "<B>ERROR:</B> No stack selected";

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls) {
		$errorMsg .= "<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than or equal to the number of particles in the stack ($totprtls)";
	}
	
	// reload the form with the error messages
	if ( $errorMsg ) createForm( $errorMsg );

	/* *******************
	 PART 2: Create program command
	 ******************** */
	$command = "runSimpleClusterAndOrigami.py ";
	
	// add run parameters
	$command .= $runParametersForm->buildCommand( $_POST );

	// add simple parameters
	$command .= $simpleParamsForm->buildCommand( $_POST );
		
	$command.="--stack=$stackid ";	
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
	$pub = new Publication('appion');
	$headinfo .=  $pub->getHtmlTable();	

	/* *******************
	 PART 5: Show or Run Command
	 ******************** */
	$nproc = 1;
	$jobtype = 'abinitio';
	$errors = showOrSubmitCommand($command, $headinfo, $jobtype, $nproc);

	// if error display them
	if ($errors)
		createForm($errors);
	exit;

}

?>


