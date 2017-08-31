<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runETomoMaker();
}

// Create the form page
else {
	createETomoMakerForm();
}


function createETomoMakerForm($extra=false, $title='subtomomaker.py Launcher', $heading='Extract Particle Sub-Tomogram') {
	// check if coming directly from a session
	$expId=$_GET['expId'];

	$particle = new particledata();

	$projectId=getProjectId();
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	
	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// set max last ring radius
	$javascript .= "	var box = Math.floor(stackArray[2]);\n";
	$javascript .= "	document.viewerform.sizex.value = box;\n";
	$javascript .= "	document.viewerform.sizey.value = box;\n";
	$javascript .= "}\n";
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
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$sampleruns = $particle->getUnfinishedETomoRunsFromSession($expId);
	$samplerunId = ($_POST['samplerunId']) ? $_POST['samplerunId'] : NULL;
	$description = $_POST['description'];
  
	if (!(is_array($sampleruns) && count($sampleruns) >0)) {
		echo "<h3> No sample tomogram run available for manual reconstruction</h3>";
		exit;
	}
	echo"
  <TABLE BORDER=3 CLASS=tableborder>\n";
	foreach ($sampleruns as $s)		{
		echo "<tr><td ALIGN='RIGHT'>\n";
		$id = $s['DEF_id'];
		echo "<input type='radio' NAME='samplerunId' value='$id' ";
		echo"> Complet this </br>";
		echo"     in eTomo\n";
		echo "</td><td>\n";
		$samplejobs = $particle->getClusterJobByTypeAndPath ('etomosample', $s['rundir']);
		$s = array_merge($s,$particle->getJobCommandParams($samplejobs[0]['DEF_id']));
		$tiltseriesetc = substr($s['rundir'],strpos($s['rundir'],'tiltseries'));
		$nextsubdirpos = strpos($tiltseriesetc,'/');
		$title = 'tilt series '.substr($tiltseriesetc,10,$nextsubdirpos-10)."\n";
		$exclude_fields = array('path','expid','session','jobtype','projectid','commit');
		$particle->displayParameters($title,$s,$exclude_fields,$expId);
		echo "</td></tr>\n";
	}
	echo "
	</TABLE>\n
  <TABLE BORDER=3 CLASS=tableborder>";
	echo "<br/>\n";
	echo "<tr><td>";
	echo"<P>
			<B> More Description to append:</B><br>
			<TEXTAREA NAME='description' ROWS='2' COLS='70'>$description</TEXTAREA>
		  </TD>
    </tr>
    <P>";
   
	echo "	  		
  </TD>
  </tr>
  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo getSubmitForm("Create ETomoMaker",false,true);
	echo "
        </td>
	</tr>
  </table>
  </form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}
	echo imodRef();
	processing_footer();
	exit;
}

function runETomoMaker() {
	/* *******************
	PART 1: Get variables
	******************** */

	$projectId=getProjectId();
	$expId = $_GET['expId'];
	#$outdir = $_POST['outdir'];
	$runname = 'test';

	$sampletomorunId=$_POST['samplerunId'];
	$sessionname=$_POST['sessionname'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a tilt series was provided
	if (!$sampletomorunId) createETomoMakerForm("<B>ERROR:</B> Select sample tomogram run");

	/* *******************
	PART 3: Create program command
	******************** */

	$particle = new particledata();

	$command = "etomo_recon.py ";
	$command.="--session=$sessionname ";
	$command.="--projectid=$projectId ";
	$command.="--samplerunid=$sampletomorunId ";
	#$command.="--rundir=".$outdir.'/'.$runname." ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= imodRef();

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'etomorecon', 1);

	// if error display them
	if ($errors)
		createETomoMakerForm($errors);
	exit;
	
}

?>
