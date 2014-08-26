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

define("SCRIPT_NAME", 'tomoautorecon');
define("FORM_TITLE", SCRIPT_NAME.' Launcher');
define("FORM_HEADING", ' Automated Tomogram Alignment and Reconstruction');

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
		$outdir=getBaseAppionPath($sessioninfo).'/tomo';
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$autoreconruns = $particle->getJobIdsFromSession($expId,SCRIPT_NAME,false,false);
	$autoreconcount = (is_array($autoreconruns)) ? count($autoreconruns) : 0;
	$autorunname = ($autoreconruns) ? 'auto'.($autoreconcount+1):'auto1';
	$runname = ($_POST['runname']) ? $_POST['runname']:$autorunname;
	$outdir = ($_POST['outdir']) ? $_POST['outdir']: $outdir;
	$description = ($_POST['description']) ? $_POST['description']: $description;
	$wait = ($_POST['wait']=="on") ? "CHECKED" : "";
	$leginoncheck = ($_POST['alignmethod'] == 'leginon'|| !($_POST['alignmethod'])) ? "CHECKED" : "";
	$protomocheck = ($_POST['alignmethod'] == 'protomo' ) ? "CHECKED" : "";
	$imodcheck = ($_POST['alignmethod'] == 'imod-shift') ? "CHECKED" : "";
	$raptorcheck = ($_POST['alignmethod'] == 'raptor') ? "CHECKED" : "";
	$sample = ($_POST['sample']) ? $_POST['sample'] : 4;
	$region = ($_POST['region']) ? $_POST['region'] : 50;
	$extrabin = ($_POST['extrabin']) ? $_POST['extrabin'] : '1';
	$thickness = ($_POST['thickness']) ? $_POST['thickness'] : '200';
	$timeout = ($_POST['timeout']) ? $_POST['timeout'] : '180';
	$imagelimit = ($_POST['imagelimit']) ? $_POST['imagelimit'] : '50';
	//raptor parameters
	$markersize = ($_POST['markersize']) ? $_POST['markersize'] : 10;
	$markernumber = ($_POST['markernumber']) ? $_POST['markernumber'] : 0;
	if ($raptorcheck) 
	  $extrabin = ($_POST['extrabin']) ? $_POST['extrabin'] : '2';

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
	echo docpop('description','<b>Description:</b>');
	echo "<br>\n";
	echo "<textarea name='description' rows='2' cols='50'>$description</textarea>\n";
	echo "<br>\n";
	echo "<input type='checkbox' name='wait' $wait>\n";
	echo docpop('nowait','Wait for more tilt series after finishing.');
	echo docpop('timeout','Timeout');
	echo " <input type='text' name='timeout' size='3' value='$timeout'>\n";
	echo " min";
	echo "<br /><br />\n";
	echo docpop('imagelimit','<b>Minimum number of images in tilt series for processing:</b>');
	echo " <input type='text' name='imagelimit' size='4' value='$imagelimit'>\n";
	echo "<br />\n";
	echo closeRoundBorder();
	//Alignment Parameters
	echo "<p><b>Alignment Parameters</b><p>";
	echo docpop('tomoalignmethod', 'Method');
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='leginon' $leginoncheck>\n";
	echo "Leginon alignment\n";
	echo "&nbsp;<input type='radio'onClick=submit() name='alignmethod' value='protomo' $protomocheck>\n";
	echo "Protomo refinement\n";
	echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='imod-shift' $imodcheck>\n";
	echo "Imod shift-only alignment\n";
	echo "&nbsp;<input type='radio' onClick=submit() name='alignmethod' value='raptor' $raptorcheck>\n";
	echo "Raptor alignment\n";
	if ($protomocheck) {
		echo "<p>
      <input type='text' name='sample' size='5' value='$sample'>\n";
		echo docpop('protomosample','Alignment Sampling');
		echo "<font>(>=1.0)</font>
		<p>
      <input type='text' name='region' size='8' value='$region'>\n";
		echo docpop('protomoregion','Protomo Alignment Region');
		echo "<font>(% of image length (<100))</font>
		<p>";
	}
	if ($raptorcheck) {
		echo "<P>";
		echo " <input type='text' name='markersize' size='5' value='$markersize'>\n";
		echo docpop('markersize','Marker Size (nm)');
		echo "<P>";
		echo " <input type='text' name='markernumber' size='5' value='$markernumber'>\n";
		echo docpop('tomomarkersize','Number of Markers to be used');
		echo "<font>(0 means automatically determined)</font>";
		//echo "<P>";
		//echo " <input type='text' name='reconbin' size='5' value='$reconbin'>\n";
		//echo docpop('extrabin','Reconstruction Binning');
		echo "<P>";
	}
	echo"
		</TD>
  </TR>
  <TR>
    <TD>";
	//Alignment Parameters
	echo "
		<P>
		<b>Tomogram Creation Params:</b>
			<P>
			<input type='text' name='extrabin' size='5' value='$extrabin'>\n";
	echo docpop('extrabin','Binning');
	echo "<font>(additional binning in tomogram)</font>";
	echo "<p>
		<input type='text' name='thickness' size='8' value='$thickness'>\n";
	echo docpop('tomothickness','Tomogram Thickness');
	echo "<font>(pixels in tilt images)</font>";
	echo"<p><br />";
	echo"
		</TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Run Auto Tomo Align+Recon");
	echo "
    </td>
	</tr>
  </table>
  </form>\n";

	$alignref = ($protomocheck) ? protomoRef(): imodRef();
	echo $alignref.imodWeightedBackProjRef();

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
	$wait=$_POST['wait'];
	$alignmethod = $_POST['alignmethod'];
	if ($alignmethod == 'protomo') {
		$alignsample=$_POST['sample'];
		$alignregion=$_POST['region'];
	} else {
		$alignsample = 1;
		$alignregion = 100;
	}
	$reconbin=$_POST['extrabin'];
	$thickness=$_POST['thickness'];
	$timeout=$_POST['timeout'];
	$imagelimit=$_POST['imagelimit'];
	//for Raptor
	$markersize=$_POST['markersize'];
	$markernumber=$_POST['markernumber'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createAppionScriptForm("<b>ERROR:</b> Enter a brief description of the tomogram");
	//make sure the protomo sampling is valid
	if ($alignsample < 1 && $alignmethod=='protomo') createTomoAlignerForm("<b>ERROR:</b> Protomo Alignment Sampling must >= 1");

	/* *******************
	PART 3: Create program command
	******************** */

	$command = SCRIPT_NAME.".py ";

	$command.="--session=$sessionname ";
	$command.="--projectid=$projectId ";
	$command.="--runname=$runname ";
	$command.="--rundir=".$outdir.'/'.$runname." ";
	$command.="--alignmethod=$alignmethod ";
	$command.="--alignsample=$alignsample ";
	$command.="--alignregion=$alignregion ";
	$command.="--reconbin=$reconbin ";
	$command.="--reconthickness=$thickness ";
	$command.="--description=\"$description\" ";
	$command.="--imagelimit=$imagelimit ";
	if ($alignmethod == 'raptor') {
		$command .="--markersize=".(int)$markersize." ";
		$command .="--markernumber=".(int)$markernumber." ";
	} 
	if (!$wait) $command.=" --no-wait ";
	if ($wait) $command.="--timeout=$timeout ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$alignref = ($alignmethod == 'protomo') ? protomoRef(): imodRef();
	$headinfo .= $alignref.imodWeightedBackProjRef(); // main initModelRef ref

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
