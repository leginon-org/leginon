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
	$projectId=$_POST['projectId'];

	// --- find hosts to run jpgmaker 
	$hosts=getHosts();
 

	$particle=new particleData;
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
			if (infoname=='runid'){
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
	$javascript.=appionLoopJavaCommands();
	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	if ($results) echo "$results<hr />\n";

	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
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
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
	  <TD VALIGN='TOP'>";
	    createAppionLoopTable($sessiondata, 'jpgs', "", 1);
	echo"
	  </TD>
	  <TD CLASS='tablebg'>

	    <A HREF=\"javascript:infopopup('scale')\">
	      <B>Instensity Scale:</B></A><br/>
	    <INPUT TYPE='radio' NAME='scale' VALUE='meanstdv' $scalechecks[0]>&nbsp;mean +/- 3 * stdv&nbsp;&nbsp;<br/>
	    <INPUT TYPE='radio' NAME='scale' VALUE='autominmax' $scalechecks[1]>&nbsp;min and max of the image<br/>
	    <INPUT TYPE='radio' NAME='scale' VALUE='fixed' $scalechecks[2]>&nbsp;Fixed min and max<br/>

	    <TABLE CELLSPACING=0 CELLPADDING=2><TR>
	      <TD VALIGN='TOP' WIDTH = 20></TD>
	      <TD VALIGN='TOP'>
	        <INPUT TYPE='text' NAME='min' VALUE=$min SIZE='8'>Min<br/>
	        <INPUT TYPE='text' NAME='max' VALUE=$max SIZE='8'>Max
	      </TD></TR>
	    </TABLE><br/>
	    <A HREF=\"javascript:infopopup('quality')\">
	      <B>JPEG Quality: </B></A><br/>
	        <INPUT TYPE='text' NAME='quality' VALUE=$quality SIZE='4'> (1-100)<br/><br/>
	    <A HREF=\"javascript:infopopup('size')\">
	      <B>Maximal Image Size: </B></A><br/>
	        <INPUT TYPE='text' NAME='imgsize' VALUE=$imgsize SIZE='4'> pixels<br/>

	  </TD>";
	echo"
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these settings on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>

		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		Host: <select name='host'>\n";
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>
	<BR>
	User: <INPUT TYPE='text' name='user' value=".$_POST['user'].">
	Password: <INPUT TYPE='password' name='password' value=".$_POST['password'].">\n";
	echo"
		</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run JPEG Maker'><BR>
		<FONT class='apcomment'>Submission will NOT run JPEG Maker, only output a command that you can copy and paste into a unix shell</FONT>
		<BR>
		</TD>
	</TR>
	</TABLE>
	</TD>
	</TR> 
	</TABLE>\n";
	?>

	</CENTER>
	</FORM>
	<?
	processing_footer();
	exit;
}

function runjpgmaker() {
	$process = $_POST['process'];

	$outdir = $_POST['outdir'];
	$runid = $_POST['runid'];
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

	if ($runid) $apcommand.=" runid=$runid";
	if ($outdir) $apcommand.=" outdir=$outdir";
	if ($testimage) $apcommand.=" $testimage";
	else {
		if ($alldbimages) {
			$apcommand.=" alldbimages=$_POST[sessionname]";
		} else {
			if ($dbimages) $apcommand.=" dbimages=$dbimages";
		}
	}
	if ($norejects) $apcommand.=" norejects";
	if ($nowait) $apcommand.=" nowait";
	if ($commit) $apcommand.=" commit";
	if (!$apcontinue) $apcommand.=" nocontinue";
	else $apcommand.=" continue";

	if ($apcommand[0] == "<") {
		createJMForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	if ($scale == "autominmax") $command.=" min=100 max=50";
	if ($scale == "fixed") $command.=" min=".$min." max=".$max;
	if ($quality != 80) $command.=" quality=".$quality;
	if ($imgsize != 512) $command.=" imgsize=".$imgsize;

	if ($testimage && $_POST['process']=="Run JPEG Maker") {
		$host = $_POST['host'];
		$user = $_POST['user'];
		$password = $_POST['password'];
		if (!($user && $password)) {
			createJMForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}
		$command="source /ami/sw/ami.csh;".$command;
		$command="source /ami/sw/share/python/usepython.csh cvs32;".$command;
		$cmd = "$command > JpgMakerLog.txt";
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	if ($testimage) {
		$runid = $_POST[runid];
		$outdir = $_POST[outdir];
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$images = "<center><table width='600' border='0'>\n";
  		$images.= "<tr><td>";
		$images.= "<b>JPEG Maker Command:</b><br />$command";
		$images.= "</td></tr></table>\n";
		$images.= "<br />\n";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgdir=$outdir.$runid."/";
		$jpgimg=$testjpg.".jpg";
		$images.= writeTestResults($jpgdir,array($jpgimg));
		createJMForm(false,'JPG File Maker Test Results','JPEG Maker Results',$images);
	}

	else processing_header("JPEG Maker Results","JPEG Maker Results",$javascript);

	echo"
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>JPEG Maker Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>
  <TR><TD>runname</TD><TD>$runid</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  <TR><TD>norejects</TD><TD>$norejects</TD></TR>
  <TR><TD>nowait</TD><TD>$nowait</TD></TR>
  <TR><TD>commit</TD><TD>$commit (always)</TD></TR>
  <TR><TD>continue</TD><TD>$apcontinue</TD></TR>
  ";

  
	//appionLoopSummaryTable();
	echo"</TABLE>\n";
	processing_footer();
}


?>
