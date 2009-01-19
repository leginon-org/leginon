<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
 
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runjpgmaker();
}

// CREATE FORM PAGE
else {
	createJMForm();
}


function createJMForm($extra=false, $title='JPEG Maker', $heading='Automated JPEG convertion with jpgmaker',$results=false) {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=$_SESSION['projectId'];

	$javascript="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		 function enabledtest(){
			 if (document.viewerform.testimage.checked){
				 document.viewerform.testfilename.disabled=false;
				 document.viewerform.testfilename.value='';
			 }	
			 else {
				 document.viewerform.testfilename.disabled=true;
				 document.viewerform.testfilename.value='mrc file name';
			 }
		 }

		 function infopopup(infoname){
			var newwindow=window.open('','name','height=150,width=300');
			newwindow.document.write('<HTML><BODY>');
			if (infoname=='runname'){
				 newwindow.document.write('The files will be saved under a subdirectory of Output Directory named after Run Name.  Best not to change this.');
			}
			if (infoname=='scale'){
				 newwindow.document.write('Scale these thresholds to 0 and 255 for the 8-bit gray-scale output');
			} 
			if (infoname=='quality'){
				 newwindow.document.write('100 is the highest and original quality.');
			}
			if (infoname=='size'){
				 newwindow.document.write('The output jpg image will not be larger than this value in either dimension');
			}

			newwindow.document.write('</BODY></HTML>');
			newwindow.document.close();
		}

	</SCRIPT>\n";
	echo $javascript;
	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#DD0000' size=+2>$extra</font>\n<hr>\n";
	}
	if ($results) echo "$results<hr />\n";

	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>";
	#<input type='HIDDEN' name='lastSessionId' value='$sessionId'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];

	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	$quality = ($_POST['quality']) ? $_POST['quality'] : '80';
	$imgsize = ($_POST['imgsize']) ? $_POST['imgsize'] : '512';
	$min = ($_POST['min']) ? $_POST['min'] : '0';
	$max = ($_POST['max']) ? $_POST['max'] : '100000';
	$scale = ($_POST['scale']) ? $_POST['scale'] : 'meanstdv';
	if ($scale == 'meanstdv') $scalechecks = array( 'CHECKED','','');
	else if ($scale == 'autominmax') $scalechecks = array('','CHECKED','');
	else $scalechecks = array('','','CHECKED');

	$process = ($_POST['process']) ? $_POST['process'] :'';
	$_POST['commit']='on';
	echo"
	<table border=0 class=tableborder cellpadding=15>
	<tr>
	  <td valign='top'>";
	    createAppionLoopTable($sessiondata, 'jpgs', "", 1);
	echo"
	  </td>
	  <td class='tablebg'>

	    <a href=\"javascript:infopopup('scale')\">
	      <b>Instensity Scale:</b></a><br/>
	    <input type='radio' name='scale' value='meanstdv' $scalechecks[0]>&nbsp;mean +/- 3 * stdv&nbsp;&nbsp;<br/>
	    <input type='radio' name='scale' value='autominmax' $scalechecks[1]>&nbsp;min and max of the image<br/>
	    <input type='radio' name='scale' value='fixed' $scalechecks[2]>&nbsp;Fixed min and max<br/>

	    <table cellspacing=0 cellpadding=2><tr>
	      <td valign='TOP' width = 20></td>
	      <td valign='TOP'>
	        <input type='text' name='min' value=$min size='8'>Min<br/>
	        <input type='text' name='max' value=$max size='8'>Max
	      </td></tr>
	    </table><br/>
	    <a href=\"javascript:infopopup('quality')\">
	      <b>JPEG Quality: </b></a><br/>
	        <input type='text' name='quality' value=$quality size='4'> (1-100)<br/><br/>
	    <a href=\"javascript:infopopup('size')\">
	      <b>Maximal Image Size: </b></a><br/>
	        <input type='text' name='imgsize' value=$imgsize size='4'> pixels<br/>

	  </td>";
	echo"
	</tr>
	<tr>
		<td colspan='2' ALIGN='CENTER'>
		<hr>
		<input type='checkbox' name='testimage' onclick='enabledtest(this)' $testcheck>
		Test these settings on image:
		<input type='text' name='testfilename' $testdisabled value='$testvalue' size='45'>

		</td>
	</tr>
	<tr>
		<td colspan='2' align='center'>
	";
	echo getSubmitForm("Run JPEG Maker", true, true);
	echo "
		<br />
		</td>
	</tr>
	</table>
	</td>
	</tr> 
	</table>\n";
	?>

	</center>
	</form>
	<?
	processing_footer();
	exit;
}

function runjpgmaker() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$process = $_POST['process'];
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$runname = $_POST['runname'];
	$rundir=$outdir.$runname."/";
	$alldbimages = $_POST['alldbimages'];
	$dbimages = $_POST[sessionname].",".$_POST[preset];
	$norejects = ($_POST[norejects]=="on") ? "0" : "1";
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$commit = 1;
	$apcontinue = $_POST[apcontinue];
	$scale = $_POST[scale];
	if ($scale == "fixed") {
		$max = $_POST[max];
		$min = $_POST[min];
	}
	$quality = $_POST[quality];
	$imgsize = $_POST[imgsize];
	
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) {
			$testimage=$_POST['testfilename'];
			$_POST['apcontinue']=0;
			$apcontinue=0;
		}
	}

	$command="jpgmaker.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createJMForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	if ($scale == "autominmax") $command.=" --min=100 --max=50";
	if ($scale == "fixed") $command.=" --min=".$min." --max=".$max;
	if ($quality != 80) $command.=" --quality=".$quality;
	if ($imgsize != 512) $command.=" --imgsize=".$imgsize;

	if ($testimage && $_POST['process']=="Run JPEG Maker") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) createJMForm("<b>ERROR:</b> Enter a user name and password"); 
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'jpgmaker',False,True);
		// if errors:
		if ($sub) createJMForm("<b>ERROR:</b> $sub");
		exit;
	}

	if ($testimage) {
		$images = "<center><table width='600' border='0'>\n";
  		$images.= "<tr><td>";
		$images.= "<b>JPEG Maker Command:</b><br />$command";
		$images.= "</td></tr></table>\n";
		$images.= "<br />\n";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgimg=$rundir.$testjpg.".jpg";
		$images.= writeTestResults($jpgimg,array(),1);
		createJMForm(false,'JPG File Maker Test Results','JPEG Maker Results',$images);
	} else {
		processing_header("JPEG Maker Results","JPEG Maker Results",$javascript);
		echo"
			<table width='600'>
			<tr><td colspan='2'>
			<b>JPEG Maker Command:</b><br>
			$command
			<hr>
			</td></tr>";
		appionLoopSummaryTable();
		echo"</table>\n";
		processing_footer();
	}
}
?>
