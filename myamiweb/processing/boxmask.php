<?php

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runBoxMask();
}

// Create the form page
else {
	createBoxMask();
}

function createBoxMask($extra=false, $title='BoxMask Launcher', $heading='Mask particles with a box') {
	$expId=$_GET['expId'];

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

	$stackid = ($_GET['sId']);
	$alignid = ($_GET['aId']);
	$vert = ($_GET['vert']);

	// save other params to url formaction
	$formAction.=($stackid) ? "&sId=$stackid" : "";
	$formAction.=($alignid) ? "&aId=$alignid" : "";
	$formAction.=($vert) ? "&vert=True" : "";

	//query the database for parameters
	$particle = new particledata();

	# get stack name
	$stackp = $particle->getStackParams($stackid);
	$filename = $stackp['path'].'/'.$stackp['name'];
	$boxsize = $stackp['boxsize'];
	$apix = $stackp['pixelsize']*1e10;
	$boxang = intval($boxsize*$apix);

	// Set any existing parameters in form
	$description = ($_POST['description']) ? $_POST['description'] : 'boxmasked stack';
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'boxmask'.$stackid;
	$mask = ($_POST['mask']) ? $_POST['mask'] : intval($boxang/2)-ceil(2*$apix);
	$imask = ($_POST['imask']) ? $_POST['imask'] : '0';
	$len = ($_POST['len']) ? $_POST['len'] : '300';
	$falloff = ($_POST['falloff']) ? $_POST['falloff'] : '90';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';		

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
	
	echo"<table border=3 class=tableborder>";
	echo"<tr><td valign='top' align='center'>\n";

	// Information table
	echo "<table border='1' class='tableborder' width='640'>";
		echo "<tr>\n";
		echo "<td>\n";
		echo "<center><h3>Mask Particles with Soft Box</h3></center>";
		echo "This function masks a stack of particles using a rectangular mask, with the option of creating an inner mask as well.  Edges have a falloff.";
		echo "</td></tr>";
	echo "</table>";
	echo "<hr/><br/>\n";

	// Stack info
	echo stacksummarytable($stackid, True, False);
	echo "<hr/><br/>\n";
	echo"<input type='hidden' name='stackid' value='$stackid'>\n";

	// Aligned Stack info, if available
	if ($alignid) {
		echo alignstacksummarytable($alignid, True, False);
		echo "<hr/><br/>\n";
		echo"<input type='hidden' name='alignid' value='$alignid'>\n";
	}
	elseif ($vert)
		echo "<input type='hidden' name='vert' value='True'>\n";
	
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

	echo "<center><b>Stack Box Size (in Angstroms): $boxang x $boxang</b></center><br>\n";
	echo "<table border='0'><tr><td>\n";	

	// image diagram
	echo "<img src='img/boxmask.png'>\n";	
	echo "</td><td>\n";

	// parameters
	echo docpop('mask','Outer Mask Radius: ');
	echo "<input type='text' name='mask' value='$mask' size='4'> (in Angstroms)<br />\n";
	echo "<br/>\n";

	echo docpop('imask','Inner Mask Radius: ');
	echo "<input type='text' name='imask' value='$imask' size='4'> (in Angstroms)<br />\n";
	echo "<br/>\n";

	echo docpop('len','Length Mask: ');
	echo "<input type='text' name='len' value='$len' size='4'> (in Angstroms)<br />\n";
	echo "<br/>\n";

	echo docpop('falloff','Edge Falloff: ');
	echo "<input type='text' name='falloff' value='$falloff' size='4'> (in Angstroms)<br />\n";
	echo "<br/>\n";
	
	echo "<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','<b>Commit stack to database');

	echo "</td></tr></table>\n";
	echo "</td></tr>\n";
	echo "<tr><td align='center'>";
	echo getSubmitForm("Mask Particles");
	echo "</td></tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	processing_footer();
	exit;
}
function runBoxMask() {
	/* *******************
	PART 1: Get variables
	******************** */
	$stackid=$_POST['stackid'];
	$alignid=$_POST['alignid'];
	$vert=$_POST['vert'];
	$mask = $_POST['mask'];
	$imask = $_POST['imask'];
	$len = $_POST['len'];
	$falloff = $_POST['falloff'];
	$commit=$_POST['commit'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$description) createBoxMask("<B>ERROR:</B> Enter a brief description");

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="boxMaskStack.py ";
	$command.="--stack-id=$stackid ";
	if ($alignid) $command.="--align-id=$alignid ";
	elseif ($vert) $command.="--vertical ";
	$command.="--mask=$mask ";
	if ($imask>0) $command.= "--imask=$imask ";
	$command.="--len=$len ";
	$command.="--falloff=$falloff ";
	$command.="--description=\"$description\" ";
	$command.= ($commit=='on') ? "--commit " : "--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'makestack2', $nproc);
	// if error display them
	if ($errors)
		createBoxMask($errors);
	exit;
}

?> 
