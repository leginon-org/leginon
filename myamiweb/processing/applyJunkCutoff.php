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
	runApplyJunkCutoff();
}

// Create the form page
else {
	createApplyJunkCutoffForm();
}

function createApplyJunkCutoffForm($extra=false, $title='sortJunkStack.py Launcher', $heading='Sort Particles in a Stack') {
        // check if coming directly from a session
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackId=$_GET['stackId'];
	$partnum=$_GET['partnum'];

	// save other params to url formaction
	$formAction.=($stackId) ? "&stackId=$stackId" : "";
	$formAction.=($partnum) ? "&partnum=$partnum" : "";

	// Set any existing parameters in form
	$description = $_POST['description'];
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'sortjunksubstack'.$stackId;
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
	
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	//query the database for parameters
	$particle = new particledata();
	
	# get stack name
	$stackp = $particle->getStackParams($stackId);
	$filename = $stackp['path'].'/'.$stackp['name'];
	echo "<input type='hidden' name='box' value='$boxsize'>\n";

	echo"
	<TABLE BORDER=3 CLASS=tableborder>";
	echo"
	<TR>
		<TD VALIGN='TOP'>\n";
	echo"
					<b>Stack information:</b> <br />
					name & path: $filename <br />	
					ID: $stackId<br />
                                        <input type='hidden' name='stackId' value='$stackId'>
					<br />\n";
	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' value='$runname'><br />\n";
	echo "<b>Particle number:</b><br />\n";
	echo "<input type='text' name='partnum' value='$partnum' width='5'><br />\n";
	echo "<b>Description:</b><br />\n";
	echo "<textarea name='description' rows='3'cols='70'>$description</textarea>\n";
	echo "<br />\n";
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');
	echo "<br />\n";
	echo "</td>
  </tr>
  <tr>
    <td align='center'>
	";
	echo getSubmitForm("Apply Junk Cutoff");
	echo "
	</td>
	</tr>
  </table>
  </form>\n";
	echo referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 2004, "C.O.S. Sorzano, R. Marabini, J. Velazquez-Muriel, J.R. Bilbao-Castro, S.H.W. Scheres, J.M. Carazo, A. Pascual-Montano.", "J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");
	processing_footer();
	exit;
}

function runApplyJunkCutoff() {
	/* *******************
	PART 1: Get variables
	******************** */
	$partnum=$_POST['partnum'];
	$stackId=$_POST['stackId'];
	$commit=$_POST['commit'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	if (!$partnum)
		createApplyJunkCutoffForm("<b>ERROR:</b> Specify a particle number");
	if (!$description)
		createApplyJunkCutoffForm("<B>ERROR:</B> Enter a brief description");

	/* *******************
	PART 3: Create program command
	******************** */

	$command.="subStack.py ";
	$command.="--no-meanplot ";
	$command.="--sorted ";
	$command.="--last $partnum ";
	$command.="--old-stack-id=$stackId ";
	$command.="--description=\"$description\" ";
	$command.= ($commit=='on') ? "-C " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 
		2004, "C.O.S. Sorzano, R. Marabini, J. Velazquez-Muriel, J.R. Bilbao-Castro, S.H.W. Scheres, J.M. Carazo, A. Pascual-Montano.", 
		"J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack', $nproc);

	// if error display them
	if ($errors)
		createApplyJunkCutoffForm($errors);
	exit;
}

?>
