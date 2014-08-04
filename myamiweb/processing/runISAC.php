<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      This is a template for starting a new Appion program
 */

// The requirements are the same for all scripts
require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";
require_once "inc/forms/remoteJobParamsForm.inc";

if ($_POST['process']) {
	// if the POST variable process is defined run the script
	runAppionScript();
} else {	
	// otherwise display the input form
	createISACAlignForm();
}


// Function to show the input form
function createISACAlignForm($extra=false, 
 $title='ISAC Launcher', 
 $heading='') {

	$expId=$_GET['expId'];
	$projectId=getProjectId();
	// parse $_GET inputs, used for direct links

	// form action is the page that loads when there is an error
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	if ($_GET['variable']) {
		// example addition of extra variable
		$formAction.="&variable=".$_GET['variable'];
	}

	// connect to appion database, this is confusingly called particle data for historical reasons
	$particle = new particledata();
	$stackIds = $particle->getStackIds($expId);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	$javascript .= "	document.viewerform.clipdiam.value = stackArray[2];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	if (bestbin < 1) {\n";
	$javascript .= "		var bestbin = 1 ;}\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "
		function enablefastmode() {
			if (document.viewerform.fast.checked){
				document.viewerform.fastmode.disabled=false;
			} else {
				document.viewerform.fastmode.disabled=true;
			}

		}
		\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	
	

	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=getBaseAppionPath($sessioninfo).'/align/';
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$analysisruns = $particle->getMaxRunNumber("partalign", $expId);
	
	while (file_exists($sessionpathval.'ISAC'.($analysisruns+1)))
		$analysisruns += 1;
	
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'ISAC'.($analysisruns+1);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$rundescrval = $_POST['description'];

	$defaultmaskrad = 100;	
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$numref = ($_POST['numref']) ? $_POST['numref'] : '20';
	$clipdiam = ($_POST['clipdiam']) ? $_POST['clipdiam'] : '';	
	$maxiter = ($_POST['maxiter']) ? $_POST['maxiter'] : '15';
	$image2imagedistanceval = ($_POST['image2imagedistance']) ? $_POST['image2imagedistance'] : 'correlation';
	$image2clusterdistanceval = ($_POST['image2clusterdistance']) ? $_POST['image2clusterdistance'] : 'minimum';
	
	
	echo"
	<table border='0' class='tableborder'>
	<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	
	// Add cluster parameter form
	$html.= "<tr>";
	$html.= "<td VALIGN='TOP' COLSPAN='2' >";
	
	$remoteParamsForm = new RemoteJobParamsForm($runnameval, $sessionpathval );
	$html.= $remoteParamsForm->generateForm();

	echo $html;	
	
	if (!$stackIds) {
	echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use</b>');
		echo "<br/>";
			$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	
	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "</table>\n";
	
	echo "</TD>\n";

	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";

	if  (!$apix) {
		echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
	
	echo "<br/>\n";
	echo "<b>Limiting numbers</b>\n";
	echo "<br/>\n";
	
	echo "<INPUT TYPE='text' NAME='clipdiam' VALUE='$clipdiam' SIZE='4'>\n";
	echo docpop('clipdiam','Unbinned Clip diameter');
	echo "<font size='-2'>(pixels)</font>\n";
			echo "<br/>\n";
	
			echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
			echo docpop('partbin','Particle binning');
			echo "<br/>\n";
	
			echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";
	
	echo "<br/>\n";
	echo "<b>Filters</b>\n";
	echo "<br/>\n";
	
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
			echo "<br/>\n";
	
			echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
			echo docpop('hpstackval','High Pass Filter Radius');
			echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
			echo "<br/>\n";
	
			echo "<br/>\n";
			echo "<b>Job parameters</b>\n";
			echo "<br/>\n";
	
	
	
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run ISAC Alignment", false);
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";

	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	// Add reference to bottom of the page
	echo appionRef(); // main appion ref
	echo referenceBox("Iterative stable alignment and clustering of 2D transmission electron microscope images.", 2012, "Yang Z, Fang J, Chittuluru J, Asturias FJ, Penczek PA. ", 
			"Structure", 20, 2, 22325773, 3426367, false, "");
	processing_footer();
	exit;
}


// Function to convert the input into a python script and run it
function runAppionScript() {
	/* *******************
	PART 1: Get variables
	******************** */

	// get the stack info from the standard stackSelector()
	$stackval=$_POST['stackval'];
	list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stackval);
	// get other variables
	$maskrad = $_POST['maskrad'];
	$bin = $_POST['bin'];
	$preftype = $_POST['preftype'];
	$description = $_POST['description'];
	$numpart = $_POST['numpart'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$clipdiam=$_POST['clipdiam'];
	$maxiter=$_POST['maxiter'];
		
	// check box is set to 'on' or 'off'
	$commit = ($_POST['commit']=="on") ? true : false;

	// verify processing host parameters
	$remoteParamForm = new RemoteJobParamsForm();
	$errorMsg .= $remoteParamForm->validate( $_POST );
		
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a stack was selected
	if (!$stackid)
		createISACAlignForm("<B>ERROR:</B> No stack selected");
	//make sure a description was provided
	if (!$description)
		createISACAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");
	// other checks
	if ($numpart < 4)
		createISACAlignForm("<B>ERROR:</B> Must have more than 4 particles");
	// make database connection
	$particle = new particledata();
	// complex things like making sure mask is smaller than boxsize
	$stackparams=$particle->getAlignStackParams($stackid);
	$boxrad = $stackparams['pixelsize'] * $stackparams['boxsize'];
	if ($maskrad > $boxrad)
		createISACAlignForm("<b>ERROR:</b> Mask radius too large! $maskrad > $boxrad ".print_r($stackparams));

	if ($clipdiam) {
		if ($clipdiam > $boxsz) {
			// Clip size too big
			createISACAlignForm("<B>ERROR:</B> Clipping diameter ($clipdiam pixels)"
			." must be less than  or equal to the stack boxsize ($boxsz pixels)");
		} else if ($clipdiam == $boxsz) {
		// No clipping needed
		$binclipdiam = '';
		} else {
		// Clipping requested
			$binclipdiam = floor($clipdiam/($bin*2.0))*2;
		}
	}
	/* *******************
	PART 3: Create program command
	******************** */

	$command ="runSparxISAC.py ";
	$command.="--stack=$stackid ";
	$command.="--num-part=$numpart ";
	if ($binclipdiam != '') $command.="--clip=$binclipdiam ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--bin=$bin ";
	$nproc = $_POST['nodes']*$_POST['ppn'];
	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// collect processing host parameters
	$command .= $remoteParamForm->buildCommand( $_POST );
	
	// show or submit command, auto sets up runname, projectid, and rundir (from outdir)
	$errors = showOrSubmitCommand($command, $headinfo, 'sparxisac', $nproc);
	// if error display them
	if ($errors)
		createISACAlignForm($errors);
	exit;

}
?>
