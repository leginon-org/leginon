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

define("SCRIPT_NAME", 'contouranalysis');
define("FORM_TITLE", SCRIPT_NAME.' Launcher');
define("FORM_HEADING", ' Object contour analysis');

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runAppionScript();
}

// Create the form page
else {
	createAppionScriptForm();
}
function createAppionScriptForm($extra=false, $title=FORM_TITLE, $heading=FORM_HEADING) {
	$particle = new particledata();
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$contourid=$_GET['selectionId'];
	

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  
	$javafunctions = writeJavaPopupFunctions('appion');  

	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	
	if (!empty($sessioninfo)) {
		$outdir=getBaseAppionPath($sessioninfo).'/sizing';
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$canalysisruns = $particle->getJobIdsFromSession($expId,SCRIPT_NAME,false,false);
	$canalysiscount = (is_array($canalysisruns)) ? count($canalysisruns) : 0;
	$autorunname = ($canalysisruns) ? 'sizing'.($canalysiscount+1):'sizing1';
	$runname = ($_POST['runname']) ? $_POST['runname']:$autorunname;
	$outdir = ($_POST['outdir']) ? $_POST['outdir']: $outdir;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$partrunval = ($_POST['partrunid']) ? $_POST['partrunid'] : $contourid;

	//Build input table
	echo"
  <TABLE BORDER=3 CLASS=tableborder cellspacing='5'>
  <TR>
    <TD VALIGN='TOP'>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' VALUE='$runname'><BR/><BR/>\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' VALUE='$outdir' size='45'><br />\n";
	echo "<br>\n";
	#echo docpop('description','<b>Description:</b>');
	#echo "<br>\n";
	#echo "<textarea name='description' rows='2' cols='50'>$desc</textarea>\n";
	#echo "<br>\n";
	echo closeRoundBorder();
	//Alignment Parameters
	$particle = new particledata();
	$partrunids = $particle->getObjectTracingRuns($expId);
	if (!$partrunids) {
		echo "<font class='apcomment'><b>No Particles for this Session</b></font>\n";
	} else {
		echo docpop('tracerun','Tracing Runs:');
		echo "<select name='partrunid' onchange='fromstackToNone()'>\n";
		echo "<option value='0'>None</option>\n";
		foreach ($partrunids as $partrun){
			$partrunid=$partrun['DEF_id'];
			$runname=$partrun['name'];
			$partstats=$particle->getTraceStats($partrunid);
			$totparts=commafy($partstats['total_object_traced']);
			echo "<option value='$partrunid'";
			// select previously set part on resubmit
			if ($partrunval==$partrunid) {
				echo " selected";
			}
			echo">$runname ($totparts objects)</option>\n";
		}
		echo "</select>\n";
	}
	echo"
		</TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Run ".SCRIPT_NAME);
	echo "
    </td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runAppionScript() {
	/* *******************
	PART 1: Get variables
	******************** */
	$projectId=getProjectId();
	$expId = $_GET['expId'];
	$sessionname=$_POST['sessionname'];
	$outdir = $_POST['outdir'];
	$description=$_POST['description'];
	$runname=$_POST['runname'];
	$partrunid = $_POST['partrunid'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a description was provided
	#if (!$description) createAppionScriptForm("<b>ERROR:</b> Enter a brief description of the tomogram");

	/* *******************
	PART 3: Create program command
	******************** */

	$command = SCRIPT_NAME.".py ";

	$command.="--session=$sessionname ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command.="--rundir=".$outdir.'/'.$runname." ";
	$command.="--contourid=$partrunid ";
	#$command.="--description=\"$description\" ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= ''; // main initModelRef ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, SCRIPT_NAME, $nproc);

	// if error display them
	if ($errors)
		createAppionForm($errors);
	exit;
}
?>
