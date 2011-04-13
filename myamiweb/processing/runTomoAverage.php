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

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runAverageTomogram();
}

// Create the form page
else {
	createAverageTomogramForm();
}

function createAverageTomogramForm($extra=false, $title='tomoaverage.py Launcher', $heading='Average Sub-Tomogram according to Stack Alignment') {
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
		$outdir=getBaseAppionPath($sessioninfo).'/tomo/average';
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$stackval = ($_POST['stackval']) ? $_POST['stackval'] : NULL;
	$avgruns = $particle->getAveragedTomogramsFromSession($expId);
	$lastavgrunid = $avgruns[count($avgruns)-1]['avgid'];
	$nextavgrun = $lastavgrunid+1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'average'.$nextavgrun;
	$description = $_POST['description'];

	// find each stack entry in database
	$primarystackinfo = $particle->getSubTomogramStackIds($expId);
	$stackIds = array();
	$subtomoruns = array();
	$substacknames = array(0=>"align",1=>"cluster");
	foreach ($primarystackinfo as $pstackinfo) {
		$subtomorunid = $pstackinfo['subtomorunid'];
		$substackname = $pstackinfo['substackname'];
		foreach ($substacknames as $name) {
			if (substr_count($substackname,$name)) {
				$stackIds[] = $pstackinfo;
			} else {
				$namedstacks = $particle->getNamedSubStackIds($expId,$pstackinfo['stackid'],$name);
				$stackIds = array_merge($stackIds,$namedstacks);
			}
		}
	}
	// only allow most recent subtomogram stack in the selection for now
	$unique_stacks = array();
	foreach ($stackIds as $info) {
		if (!array_key_exists($info['stackid'],$unique_stacks)) $unique_stacks[$info['stackid']]=$info;
	}
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$apix=$stackinfo[1];
	$box=$stackinfo[2];
  
	echo"
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>\n";
	echo docpop('tomostack','Stack:');
	$particle->getStackSelector($unique_stacks,$stackidval,'switchDefaults(this.value)');
	echo "<br/>\n";
  echo "<P>";
	echo docpop('avgtomorunname','Runname');
  echo "<INPUT TYPE='text' NAME='runname' SIZE='15' VALUE='$runname'>\n";
	echo "<FONT>(averaged tomogram creating run name)</FONT>
		<br/>";
	echo"<P>
			<B> Tomogram Average Description:</B><br>
			<TEXTAREA NAME='description' ROWS='2' COLS='40'>$description</TEXTAREA>
		  </TD>
    </tr>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>";       
	echo "	  		
		<p><br />
		<P>
      </TD>
   </tr>
    </table>
  </TD>
  </tr>
  <td

  <TR>
    <TD ALIGN='CENTER'>
      <hr>
	";
	echo "<input type='hidden' name='outdir' value='$outdir'>\n";
	echo getSubmitForm("Average Tomograms");
	echo "
        </td>
	</tr>
  </table>
  </form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}
	echo initModelRef();
	processing_footer();
	exit;
}

function runAverageTomogram() {
	/* *******************
	PART 1: Get variables
	******************** */

	$projectId=getProjectId();
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];

	$command = "tomoaverage.py ";

	$runname=$_POST['runname'];
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$sessionname=$_POST['sessionname'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

//make sure a tomogram was entered
	if (!$runname) createAverageTomogramForm("<B>ERROR:</B> Select a full tomogram to be boxed");
	//make sure a particle run or stack is chosen
	if (!$stackidval) createAverageTomogramForm("<B>ERROR:</B> Select a stack that is used in making subtomograms");
	//make sure a description was provided
	$description=$_POST['description'];
	if (!$description) createAverageTomogramForm("<B>ERROR:</B> Enter a brief description of the tomogram");

	/* *******************
	PART 3: Create program command
	******************** */

	$particle = new particledata();
	$subtomorunid = $particle->getSubTomoRunFromStack($stackidval);
	$command.="--projectid=$projectId ";
	$command.="--subtomorunId=$subtomorunid ";
	$command.="--runname=$runname ";
	$command.="--rundir=".$outdir.'/'.$runname." ";
	$command.="--stackId=$stackidval ";
	$command.="--description=\"$description\" ";
	$command.="--commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= initModelRef();

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'tomoaverage', $nproc);

	// if error display them
	if ($errors)
		createAverageTomogramForm($errors);
	exit;
}
?>

