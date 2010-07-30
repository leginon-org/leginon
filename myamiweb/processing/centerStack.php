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
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCenterParticles();
}

// Create the form page
else {
	createCenterForm();
}

function createCenterForm($extra=false, $title='centerParticleStack.py Launcher', $heading='Center Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId=$_GET['sId'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&sId=$stackId" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'centered'.$stackId;
	$mask = ($_POST['mask']) ? $_POST['mask'] : '';
	$maxshift = ($_POST['maxshift']) ? $_POST['maxshift'] : '';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		
	if (!$stackId) $stackId = $_POST['stackId'];

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
		echo "  <img src='img/eman_logo.png' width='128'>\n";
		echo "</td><td>\n";
		echo "  <h3>EMAN CenAlignInt</h3>";
		echo "  This function centers the particles in a stack based on a radial average of all the particles in the stack. "
			."This program functions iteratively, using only integer shifts to avoid interpolation artifacts. "
			."Particles that do not consistently center are removed from the stack."
			."<a href='http://ncmi.bcm.tmc.edu/homes/stevel/EMAN/doc/progs/cenalignint.html'>EMAN webpage"
			."&nbsp;<img border='0' src='img/external.png'></a>. "
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

	echo docpop('mask','Outer Mask Radius: ');
	echo "<input type='text' name='mask' value='$mask' size='4'> (in pixels)<br />\n";
	echo "<br/>\n";

	echo docpop('maxshift', 'Maximum Shift: ');
	echo "<input type='text' name='maxshift' value='$maxshift' size='4'> (in pixels)<br />\n";
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
	echo getSubmitForm("Center Particles");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";

	echo emanRef();

	processing_footer();
	exit;
}

function runCenterParticles() {
	/* *******************
	PART 1: Get variables
	******************** */
	$stackId=$_POST['stackId'];
	$commit=$_POST['commit'];
	$mask = $_POST['mask'];
	$maxshift = $_POST['maxshift'];
	$box = $_POST['box'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a description is provided
	if (!$description) createCenterForm("<B>ERROR:</B> Enter a brief description");

	// make sure diameter & max shifts are within box size
	if ($mask > $box/2) createCenterForm("<b>ERROR:</b> Mask radius too large, must be smaller than ".round($box/2)." pixels");
	if ($maxshift > $box/2) createCenterForm("<b>ERROR:</b> Shift too large, must be smaller than ".round($box/2)." pixels");
	if ($mask) $runname.='_'.$mask;
	if ($maxshift) $runname.='_'.$maxshift;

	/* *******************
	PART 3: Create program command
	******************** */

	$command ="centerParticleStack.py ";
	$command.="--stack-id=$stackId ";
	if ($mask) $command.="--mask=$mask ";
	if ($maxshift) $command.="--maxshift=$maxshift ";
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
		createCenterForm($errors);
	exit;
}

?>
