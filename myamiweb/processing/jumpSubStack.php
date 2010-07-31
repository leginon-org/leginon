<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runSubStack();
}

// Create the form page
else {
	createSubStackForm();
}

function createSubStackForm($extra=false, $title='subStack.py Launcher', $heading='Make a partial Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$reconId = $_GET['reconId'];
	if (!$reconId) $reconId = $_POST['reconId'];

	//query the database for parameters
	$particle = new particledata();
	$numrecons = count($particle->getReconIdsFromSession($expId, true));
	$reconIds = $particle->getReconIdsFromSession($expId, false);

	if ($reconId) {
		$defrunname = 'squatstack'.$reconId;
		$formAction .= "&reconId=$reconId";
	} else {
		$defrunname = 'squatstack'.$numrecons;
	}

	// Set any existing parameters in form
	$description = ($_POST['description']) ? $_POST['description'] : '';
	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	$maxjump = ($_POST['maxjump']) ? $_POST['maxjump'] : 20;

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];

	// get path for submission
	$outdir=$sessioninfo['Image path'];
	$outdir=ereg_replace("leginon","appion",$outdir);
	$outdir=ereg_replace("rawdata","stacks",$outdir);

	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";

	$basename = basename($classfile);
	if ($reconId) {
		$reconlink = "reconreport.php?expId=$expId&reconId=$reconId";
		$recondata = $particle->getReconInfoFromRefinementId($reconId);
		$stackId = $particle->getStackIdFromReconId($reconId);
		echo"<b>Reconstruction Run Information:</b> <ul>\n"
			."<li>Recon ID/Name: [ $reconId ] <a href='$reconlink'>$recondata[name]</a>\n"
			."<li>Recon Description: $recondata[description]\n"
			."<li>Stack ID: $stackId\n"
			."<input type='hidden' name='reconId' value='$reconId'>\n"
			."</ul>\n";
	} else if($reconIds) {
		echo"
		Select Reconstruction Run:<br>
		<select name='reconId''>\n";
		foreach ($reconIds as $reconrunarray) {
			$localreconId = $reconrunarray['DEF_id'];
			$reconname=$reconrunarray['name'];
			$stackId = $particle->getStackIdFromReconId($localreconId);
			$totprtls=commafy($particle->getNumStackParticles($stackId));
			echo "<OPTION VALUE='$localreconId'";
			// select previously set prtl on resubmit
			echo ">$localreconId: $reconname ($totprtls particles)";
			echo "</OPTION>\n";
		}
		echo "</SELECT>\n";
		echo "<br/><br/>\n";
	} else {
		echo"<font color='red'><b>No reconstructions for this session</b></font>\n";
	}

	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname' size='15'><br/><br/>\n";

	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	echo "Output directory:<i>$outdir</i><br/>\n";
	echo "<br/>\n";

	// Maximum Median Euler Jump
	echo '<b>Maximum Median Euler Jump value:</b> ';
	echo "<br/>\n<input type='text' name='maxjump' value='$maxjump' size='5'><br/>\n";

	if ($reconId) {
		echo "<img width='640' height='320' src='eulergraph.php?expId=$expId&hg=1&recon=$reconId&w=640&h=320'>";
		echo "<br/>\n";
	}
	echo "<br/>\n";

	echo "<b>Description:</b><br />\n";
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

	echo appionRef();

	processing_footer();
	exit;
}

function runSubStack() {
	/* *******************
	PART 1: Get variables
	******************** */
	$reconId=$_POST['reconId'];
	$maxjump=$_POST['maxjump'];
	$commit=$_POST['commit'];
	$runname=$_POST['runname'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$runname) createSubStackForm("<b>ERROR:</b> Specify a runname");
	if (!$description) createSubStackForm("<B>ERROR:</B> Enter a brief description");
	if (!$maxjump) createSubStackForm("<B>ERROR:</B> You must specify a maximum jump cutoff");
	if (!$reconId) createSubStackForm("<B>ERROR:</B> You must specify a reconId");

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="jumperSubStack.py ";
	$command.="--description=\"$description\" ";
	$command.="--max-jump=$maxjump ";
	$command.="--refinerunid=$reconId ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= initModelRef(); // main init model ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', $nproc);
	// if error display them
	if ($errors)
		createSubStackForm($errors);
	exit;
}

?>
