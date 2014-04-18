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

if ($_POST['process']) {
	// if the POST variable process is defined run the script
	runAppionScript();
} else {	
	// otherwise display the input form
	createCL2DAlignForm();
}


// Function to show the input form
function createCL2DAlignForm($extra=false, 
 $title='runXmipp3CL2D.py Launcher', 
 $heading='Xmipp 3 Clustering 2D Alignment') {

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
	$analysisIds = $particle->getAnalysisRuns($expId, $projectId, true);
	//foreach ($analysisIds as $analysisId)
	//	echo print_r($analysisId)."<br/><br/>\n";
	$analysisruns = ($analysisIds) ? count($analysisIds) : 0;

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
	while (file_exists($sessionpathval.'cl2d'.($analysisruns+1)))
		$analysisruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'cl2d'.($analysisruns+1);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$rundescrval = $_POST['description'];

	$defaultmaskrad = 100;
	$nproc = (isset($_POST['nproc'])) ? $_POST['nproc'] : '4';
	
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$numref = ($_POST['numref']) ? $_POST['numref'] : '20';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '4';
	$clipdiam = ($_POST['clipdiam']) ? $_POST['clipdiam'] : '';	
	$maxiter = ($_POST['maxiter']) ? $_POST['maxiter'] : '15';
	$image2imagedistanceval = ($_POST['image2imagedistance']) ? $_POST['image2imagedistance'] : 'correlation';
	$image2clusterdistanceval = ($_POST['image2clusterdistance']) ? $_POST['image2clusterdistance'] : 'minimum';
	
	
	echo"
	<table border='0' class='tableborder'>
	<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runid','<b>CL2D Run Name::</b>');
	echo "<input type='text' name='runname' value='$runnameval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of CL2D Alignment:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='60'>$rundescrval</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";	
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
	
	echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' VALUE='$nproc'>\n";
	echo "Number of Processors";
	echo "<br/>\n";	
	
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
	
			echo "<INPUT TYPE='text' NAME='numref' VALUE='$numref' SIZE='4'>\n";
	echo docpop('numrefcl2d','Number of References');
	echo "<br/>\n";
	
	echo "<INPUT TYPE='text' NAME='maxiter' VALUE='$maxiter' SIZE='4'>\n";
	echo docpop('xmippmaxiter','Maximum number of iterations');
	echo "<br/>\n";
	
	//echo "<INPUT TYPE='checkbox' NAME='fast' checked disabled>\n";
	//echo docpop('fastmode','Fast Mode Setting');
	//echo "<br/>\n";
	
	echo docpop('image2imagedistance','Image to Image Distance:');
	echo "<br/>\n";
	echo "<input type='radio' name='image2imagedistance' value='correntropy' ";
	echo ($image2imagedistanceval == 'correntropy') ? 'checked' : '';
				echo ">Correntropy\n";
	echo "<input type='radio' name='image2imagedistance' value='correlation' ";
	echo ($image2imagedistanceval == 'correlation') ? 'checked' : '';
		echo ">Correlation\n";
	echo "<br/>\n";
	
	echo docpop('image2clusterdistance','Image to Cluster Distance:');
	echo "<br/>\n";
	echo "<input type='radio' name='image2clusterdistance' value='minimum' ";
	echo ($image2clusterdistanceval == 'minimum') ? 'checked' : '';
				echo ">Minimum\n";
	echo "<input type='radio' name='image2clusterdistance' value='intracluster' ";
	echo ($image2clusterdistanceval == 'intracluster') ? 'checked' : '';
		echo ">Intracluster\n";
	echo "<br/>\n";
	
	
	
	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run CL2D Alignment");
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
	echo referenceBox("A clustering approach to multireference alignment of single-particle projections in electron microscopy.", 2010, "Sorzano CO, Bilbao-Castro JR, Shkolnisky Y, Alcorlo M, Melero R, Caffarena-Fernández G, Li M, Xu G, Marabini R, Carazo JM.", 
			"J Struct Biol.", 171, 2, 20362059, false, false, "img/xmipp_logo.png");
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
	$numpart = $_POST['numpart'];
	$preftype = $_POST['preftype'];
	$description = $_POST['description'];

	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numref=$_POST['numref'];
	$clipdiam=$_POST['clipdiam'];
	$maxiter=$_POST['maxiter'];
	$image2imagedistanceval = $_POST['image2imagedistance'];
	$image2clusterdistanceval = $_POST['image2clusterdistance'];
		
	// check box is set to 'on' or 'off'
	$commit = ($_POST['commit']=="on") ? true : false;

	$nproc = (isset($_POST['nproc'])) ? $_POST['nproc'] : '4';
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a stack was selected
	if (!$stackid)
		createCL2DAlignForm("<B>ERROR:</B> No stack selected");
	//make sure a description was provided
	if (!$description)
		createCL2DAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");
	// other checks
	if ($numpart < 4)
		createCL2DAlignForm("<B>ERROR:</B> Must have more than 4 particles");
	// make database connection
	$particle = new particledata();
	// complex things like making sure mask is smaller than boxsize
	$stackparams=$particle->getAlignStackParams($stackid);
	$boxrad = $stackparams['pixelsize'] * $stackparams['boxsize'];
	if ($maskrad > $boxrad)
		createCL2DAlignForm("<b>ERROR:</b> Mask radius too large! $maskrad > $boxrad ".print_r($stackparams));

	if ($clipdiam) {
		if ($clipdiam > $boxsz) {
			// Clip size too big
			createCL2DAlignForm("<B>ERROR:</B> Clipping diameter ($clipdiam pixels)"
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

	$command ="runXmipp3CL2D.py ";
	$command.="--description=\"$description\" ";
	$command.="--stack=$stackid ";
	if ($binclipdiam != '') $command.="--clip=$binclipdiam ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-ref=$numref ";
	$command.="--bin=$bin ";
	$command.="--max-iter=$maxiter ";
	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	
	if ($image2clusterdistanceval == "minimum")
		$command.="--classical_multiref ";
	if ($image2imagedistanceval == "correlation")
		$command.="--correlation ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";


	
	// show or submit command, auto sets up runname, projectid, and rundir (from outdir)
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);
	// if error display them
	if ($errors)
		createCL2DAlignForm($errors);
	exit;

}
?>
