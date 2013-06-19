<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
require_once "inc/publication.inc";
require_once "inc/forms/autoMaskForm.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runAutoMasker();
}
// CREATE FORM PAGE
else {
	createForm();
}

function createForm($extra=false, $title='Auto Masking Launcher', $heading='Automated Masking with EM Hole Finder') {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=getProjectId();
	$javafunctions="
		<script src='../js/viewer.js'></script>
		<script LANGUAGE='JavaScript'>
			function enabledtest(){
				if (document.viewerform.testimage.checked){
					document.viewerform.testfilename.disabled=false;
					document.viewerform.testfilename.value='';
				}	else {
					document.viewerform.testfilename.disabled=true;
					document.viewerform.testfilename.value='mrc file name';
				}
			}
			function enable(thresh){
				if (thresh=='auto') {
					document.viewerform.autopik.disabled=false;
					document.viewerform.autopik.value='';
					document.viewerform.thresh.disabled=true;
					document.viewerform.thresh.value='0.4';
				 }
				if (thresh=='manual') {
					document.viewerform.thresh.disabled=false;
					document.viewerform.thresh.value='';
					document.viewerform.autopik.disabled=true;
					document.viewerform.autopik.value='100';
				}
			}
			function infopopup(infoname){
				var newwindow=window.open('','name','height=150,width=300');
				newwindow.document.write('<HTML><BODY>');
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		 }
		</script>\n";
	$javafunctions.=writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	if ($results) echo "$results<hr>\n";
	echo"
		<form name='viewerform' method='POST' ACTION='$formAction'>
		<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

	// Set any existing parameters in form
	$particle=new particleData;
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApMaskMakerRunData','name'); 
    $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'maskrun'.($lastrunnumber+1);

	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	$process = ($_POST['process']) ? $_POST['process'] :'';
	echo"
		<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
			<tr>
				<td VALIGN='TOP'>";
	createAppionLoopTable($sessiondata, $defrunname, "mask");

	// Add parameters specific to the method selected
	echo "<td class='tablebg'>\n";
	echo "<table cellpading='5' border='0'>\n";
	echo "<tr><td valign='top'>\n";
	// Create an instance of the AutoMask param form, setting it's default values then display it 
	$autoMaskForm = new AutoMaskForm($downsample='20', $compsizethresh='50', $adapthresh='500', $blur='10',$dilation='10', $erosion='1');
	echo $autoMaskForm->generateForm();
		echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</td>\n";
	echo "</tr>\n";
		
	echo "
				</td>
			</tr>
			<tr>
				<td COLSPAN='2' ALIGN='CENTER'>
					<HR>
					<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
						Test these setting on image:
					<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
					<hr>
				</td>
			</tr>
			<tr>
				<td COLSPAN='2' ALIGN='CENTER'>
	";
	echo getSubmitForm("Run Auto Masker");
	echo "
				</td>
			</tr>
		</table>
	</td>
	</tr>
	</table>\n";
	echo "

	</CENTER>
	</FORM>
	";

	// Add references for this processing method.
	// Create an instance of a publication with the appropriate 
	// key found in myami/myamiweb/processing/inc/publicationList.inc.
	$pub = new Publication('appion');
	echo $pub->getHtmlTable();

	processing_footer();
}

function runAutoMasker() {
	/* *******************
	PART 1: Get variables and validate
	******************** */
	$autoMaskForm = new autoMaskForm();
	$errorMsg .= $autoMaskForm->validate( $_POST );

	$process = $_POST['process'];
	$expId = $_GET['expId'];
	
	// reload the form with the error messages
	if ( $errorMsg ) createForm( $errorMsg );

	/* *******************
	PART 3: Create program command
	******************** */

	$command="automasker.py ";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	// add automask parameters
	$command .= $autoMaskForm->buildCommand( $_POST );
	
	if ($_POST['testimage']=="on") {
		$command .= " --test";
		if ($_POST['testfilename'])
			$testimage=$_POST['testfilename'];
	}

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= appionRef(); // main appion ref

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'maskmaker', 1, $testimage);

	// if error display them
	if ($errors) {
		createForm($errors);
	} else if ($testimage) {
		$outdir=$_POST[outdir];
		// make sure outdir ends with '/'
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$runname=$_POST[runname];		// add the appion wrapper to the command for display
		$wrappedcmd = addAppionWrapper($command);
			
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<B>MaskMaker Test Command:</B><br />$wrappedcmd";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		echo $results;
		
		$testjpg = ereg_replace(".mrc","",$_POST['testfilename']);
		$jpgimg = $outdir.$runname."/jpgs/".$testjpg.".prtl.jpg";
		
		$testjpg=preg_replace("%.mrc%","",$testimage);
		$testdir=$outdir.$runname."/tests/";
		if (file_exists($testdir)) {
     	// open image directory
     		$pathdir=opendir($testdir);
			// get all files in directory
			$ext='jpg';
			while ($filename=readdir($pathdir)) {
		   	if ($filename == '.' || $filename == '..') continue;
				if (preg_match('`\.'.$ext.'$`i',$filename)) $files[]=$filename;
			}
			closedir($pathdir);
		}
		if (count($files) > 0) 	{
			$images = displayTestResults($testimage,$testdir,$files);
		} else {
			echo "<FONT COLOR='RED'><B>NO RESULT YET</B><br></FONT>";
			echo "<FONT COLOR='RED'><B>Refresh this page when processing completes</B><br></FONT>";
		}
		
		createForm(false, 'Auto Masking Test Results', 'Auto Masking Test Results');
	}		
	exit;
}


function displayTestResults($testimage,$imgdir,$files){
	echo "<CENTER>\n";

  $numfiles=count($files);
	$prefix = '';
	$n = 0;
	sort($files);
	
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='0' WIDTH='400'>\n";
	echo"<tr><td ALIGN='LEFT'>\n";
  echo"<B>$testimage</B>\n";
	echo"</td></tr></table>";
	echo"<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='0'><tr>\n";
	$col = 0;
	$row = 0;
	$colcount = 4;
	while ($col+$colcount*$row < count($files)) {
		if ($col > $colcount-1) {
			$col = 0;
			$row = $row + 1;
			echo "</tr><tr>";
		}
		echo "<td>";	
		$imgindx = $col+$colcount*$row;
		$imgname=$files[$imgindx];
		$imgfull=$imgdir.$imgname;
		echo"<B>$imgname</B>\n<P>";
		echo"<img src='loadimg.php?filename=$imgfull&scale=0.25'><P>\n";
		echo "</td>";
		$col = $col + 1;
	}	
	echo"</tr></table>\n";
	echo "</CENTER>\n";
}
?>
