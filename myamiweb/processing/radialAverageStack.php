<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://emg.nysbc.org/software/leginon-license
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
	runRadialAverageParticles();
}

// Create the form page
else {
	createRadialAverageForm();
}

function createRadialAverageForm($extra=false, $title='radialAverageParticleStack.py Launcher', $heading='RadialAverage Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId=$_GET['sId'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'r_averaged'.$stackId;
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$stackId) $stackId = $_POST['stackId'];

	// get outdir path
	$sessiondata=getSessionList($projectId,$expId);
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
		echo "<tr><td width='100' align='center'>\n";
		echo "  <img src='img/appionlogo.jpg' width='128'>\n";
		echo "</td><td>\n";
		echo "  <h3>Radial Average</h3>";
		echo "  This function returns radial averaged image of the particles in a stack with origin at the center of the particle image. "
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

	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='3'cols='70'>$description</textarea>\n";
	echo "<br/><br/>\n";

	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br/>\n";
	echo "</td></tr></table>\n";

	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo getSubmitForm("RadialAverage Particles");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	processing_footer();
	exit;
}

function runRadialAverageParticles() {
	/* *******************
	PART 1: Get variables
	******************** */
	$stackId=$_POST['stackId'];
	$commit=$_POST['commit'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a description is provided
	if (!$description) createRadialAverageForm("<B>ERROR:</B> Enter a brief description");

	/* *******************
	PART 3: Create program command
	******************** */

	$command ="radialAverageParticleStack.py ";
	$command.="--stack-id=$stackId ";
	$command.="--description=\"$description\" ";
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
		createRadialAverageForm($errors);
	exit;
}

?>
