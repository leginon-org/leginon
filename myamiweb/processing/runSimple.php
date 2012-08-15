<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/forms/runParametersForm.inc";
require_once "inc/forms/clusterParamsForm.inc";
require_once "inc/forms/simpleParamsForm.inc";



if ( $_POST ) {
	// IF VALUES SUBMITTED, EVALUATE DATA
	createCommand();
} else {
	createForm();
}

function createForm($extra=false, $title='runSimple.py Launcher', $heading='SIMPLE Common Lines') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF'];
	}

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	if (bestbin < 1) {\n";
	$javascript .= "		var bestbin = 1 ;}\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	// enable pop-up help
	$javascript .= writeJavaPopupFunctions();	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}

	
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
	list($stackidval) = split('\|--\|',$stackidstr);

	// start the main form
	echo "<form name='viewerform' method='POST' ACTION='$formAction'>\n";
	
	// --- Row 1 --- 
	// Add processing run parameters
	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	$runParamsForm = new RunParametersForm( $runname, $sessionpathval, $description );
	echo $runParamsForm->generateForm();

	echo "<H4 style='align=\'center\' >Processing Host Parameters</H4><hr />";
	$clusterParamsForm = new ClusterParamsForm();
	echo $clusterParamsForm->generateFormBasic();
	echo closeRoundBorder();
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
		echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use:</b>');
		echo "<br/>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo "</TD></tr>\n";
	
	// extra space
	echo "<TR><TD VALIGN='TOP'>\n";
	echo "</TD></tr>\n";
	
	// commit checkbox
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<br><br>";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	
	// Add parameters specific to the method selected
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	
	if  (!$apix) {
        echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}

	$simpleParamsForm = new SimpleParamsForm('','','','CHECKED','','','10','30','','20','100','2','2','10','','0.8','40','3','3');
	echo $simpleParamsForm->generateForm();
	
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	
	// --- Row 4 --- 
	// Add submit button
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "<br/>\n";	
	echo getSubmitForm("Run SIMPLE common lines", false );
	echo "</td>";
	echo "</tr>";
	
	// End Table
	echo "</table>\n";	
	echo "<br />";

	// Add reference for selected refinement method
	$pub = new Publication('appion');
	echo $pub->getHtmlTable();

	// end form
	echo"</form><br/>\n";	
	
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

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

	// verify processing host parameters
	$clusterParamForm = new ClusterParamsForm();
	$errorMsg .= $clusterParamForm->validate( $_POST );
	
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
	$command = "runSimpleCluster.py ";
	
	// add run parameters
	$command .= $runParametersForm->buildCommand( $_POST );

	// add simple parameters
	$command .= $simpleParamsForm->buildCommand( $_POST );
	
	// add processing host parameters
	$command = $clusterParamForm->addNProcToCommand( $command );
	
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
	$errors = showOrSubmitCommand($command, $headinfo, 'abinitio', $nproc);

	// if error display them
	if ($errors)
		createForm($errors);
	exit;

}

?>


