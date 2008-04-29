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
require "inc/ctf.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runNoRefClassify();
} else { // Create the form page
	createNoRefClassifyForm();
}

function createNoRefClassifyForm($extra=false, $title='norefClassify.py Launcher', $heading='Reference Free Classify') {
	$norefid=$_GET['norefId'];
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&norefId=$norefid";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF']."?norefId=$norefId";
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();

	$javascript = "<script src='../js/viewer.js'></script>";
	$javascript .= writeJavaPopupFunctions('eman');	

	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	$helpdiv = "
	<div id='dhelp'
		style='position:absolute; 
        	background-color:FFFFDD;
        	color:black;
        	border: 1px solid black;
        	visibility:hidden;
        	z-index:+1'
    		onmouseover='overdiv=1;'
    		onmouseout='overdiv=0;'>
	</div>\n";
	echo $helpdiv;

	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

	$norefparams = $particle->getNoRefParams($norefid);
	//print_r($norefparams);
	


	// Set any existing parameters in form
	$commitcheck = ($_POST['commit']=='off') ? '' : 'CHECKED';
	// classifier params
	$factorlist = "1,2,3";
	$numclass = 40;

	echo "<INPUT TYPE='hidden' NAME='norefid' VALUE=$norefid>";

	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder>
	<TR>
		<TD VALIGN='TOP'>
		<TABLE CELLPADDING='10' BORDER='0'>
		<TR>";
	echo "<TD VALIGN='TOP'>";

	echo "<INPUT TYPE='text' NAME='numclass' SIZE='4' VALUE='$numclass'>";
	echo docpop('numclass','Number of Classes');
	echo " <BR/><BR/>";

	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>";
	echo docpop('commit','Commit to Database');
	echo "";
	echo "<BR></TD></TR>\n</TABLE>\n";
	echo "</TD>";
	echo "<TD CLASS='tablebg'>";


	echo "<TABLE CELLPADDING='5' BORDER='0'>";
	echo "<TR><TD VALIGN='TOP'>";
	echo "<B>Eigen Images:</B></A><BR>";

	$eigenpath = $norefparams['path']."/coran/";
	$eigendir = opendir($eigenpath);
	//echo $eigenpath;
	while ($f = readdir($eigendir)){
	  if (eregi("eigenimg".'.*\.png$',$f)) {
	    $eigenpngs[] = $f;
	  }
	}
	if($eigenpngs) {
		sort($eigenpngs);
		$i = 0;
	  foreach ($eigenpngs as $epng) {
			$i++;
	    $efile = $eigenpath.$epng;
	    echo "$i <A HREF='loadimg.php?filename=$efile' target='eiginimage'><IMG SRC='loadimg.php?filename=$efile'>\n";
			if ($i % 4 == 0) echo "<BR/>\n";
	  }
	}
	echo "<BR/><BR/>\n\n";

	echo docpop('factorlist','List of Factors<br/>');
	echo "<INPUT TYPE='text' NAME='factorlist' SIZE='20' VALUE='$factorlist'><BR/>";
	echo " (comma separated, e.g. 1,2,3)<BR>";

	echo "</TR>\n";
	echo"</SELECT>";
	echo "	</TD>";
	echo "</TR>";
	echo "</TABLE>";
	echo "</TD>";
	echo "</TR>";
	echo "<TR>";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>";
	echo "	<HR>";
	echo"<input type='submit' name='process' value='Start NoRef Classify'><BR>";
	echo "  </TD>";
	echo "</TR>";
	echo "</TABLE>";
	echo "</FORM>";
	echo "</CENTER>\n";
	writeBottom();
	exit;
}

function runNoRefClassify() {
	$numclass=$_POST['numclass'];
	$factorlist=$_POST['factorlist'];
	$norefid=$_POST['norefid'];

	//make sure a stack was selected
	if (!$norefid) createNoRefClassifyForm("<B>ERROR:</B> No NoRef Alignment selected, norefId=$norefid");

	// make sure outdir ends with '/'
	$commit = ($_POST['commit']=="on") ? 'commit' : '';

	// classification
	if ($numclass > 200 || $numclass < 1) createNoRefClassifyForm("<B>ERROR:</B> Number of classes must be between 2 & 200");

	$particle = new particledata();

	$command.="norefClassify.py ";
	$command.="--num-class=$numclass ";
	$command.="--factor-list=$factorlist ";
	if ($commit) $command.="commit ";

	writeTop("No Ref Classify Run Params","No Ref Classify Params");

	echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>NoRef Classify Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>numclass</TD><TD>$numclass</TD></TR>
	<TR><TD>factorlist</TD><TD>$factorlist</TD></TR>
	<TR><TD>commit</TD><TD>$commit</TD></TR>
	</TABLE>\n";
	writeBottom();
}
?>
