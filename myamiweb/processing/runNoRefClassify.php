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
		echo "<font color='red'>$extra</font>\n<hr>\n";
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
       <form name='viewerform' method='post' action='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

	$norefparams = $particle->getNoRefParams($norefid);
	//print_r($norefparams);
	


	// Set any existing parameters in form
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	// classifier params
	$factorlist = ($_POST['factorlist']) ? $_POST['factorlist'] : "1,2,3";
	$numclass = ($_POST['numclass']) ? $_POST['numclass'] : 40;

	echo "<input type='hidden' name='norefid' value=$norefid>";

	echo"
	<p>
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>
		<table cellpadding='10' border='0'>
		<tr>";
	echo "<td valign='top'>";

	echo "<input type='text' name='numclass' size='4' value='$numclass'>";
	echo docpop('numclass','Number of Classes');
	echo " <br /><br />";

	echo "<input type='checkbox' name='commit' $commitcheck>";
	echo docpop('commit','Commit to Database');
	echo "";
	echo "<br /></td></tr>\n</table>\n";
	echo "</td>";
	echo "<td class='tablebg'>";


	echo "<table cellpadding='5' border='0'>";
	echo "<tr><td valign='TOP'>\n";
	echo docpop('factorlist','<b>Eigen Images</b>');
	echo "<br />\n";
	echo "Choose factors to use: ";
	echo "<font size='-2'>(Click on the image to view)</font>\n";
	echo "<br />\n";

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
		echo "<table border='1' cellpadding='5'>\n";
		echo "<tr>\n";
		foreach ($eigenpngs as $epng) {
			$i++;
			$efile = $eigenpath.$epng;
			echo "<td>\n";
			echo "<a href='loadimg.php?filename=$efile' target='eigenimage'><img src='loadimg.php?filename=$efile'></a><br />\n";
			$imgname = 'eigenimg'.$i;
			echo "<center><input type='checkbox' name='$imgname' ";
			// when first loading page select first 3
			// eigenimgs, otherwise reload selected
			if (($i<=3 && !$_POST['process']) || $_POST[$imgname]) echo "checked";
			echo "></center>\n";
			echo "</td>\n";
			if ($i % 4 == 0) echo "</tr>\n";
		}
		if (!$i % 4 == 0) echo "</tr>\n";
		echo "</table>\n";
	}
	echo "<input type='hidden' name='numeigenimgs' value='$i'>\n";

	echo "</tr>\n";
	echo"</select>";
	echo "	</td>";
	echo "</tr>";
	echo "</table>";
	echo "</td>";
	echo "</tr>";
	echo "<tr>";
	echo "	<td colspan='2' align='center'>";
	echo "	<hr>";
	echo "<input type='submit' name='process' value='Start NoRef Classify'><br />";
	echo "  </td>";
	echo "</tr>";
	echo "</table>";
	echo "</form>";
	echo "</center>\n";
	writeBottom();
	exit;
}

function runNoRefClassify() {
	$numclass=$_POST['numclass'];
#	$factorlist=$_POST['factorlist'];
	$norefid=$_POST['norefid'];
	$numeigenimgs = $_POST['numeigenimgs'];

	// get selected eigenimgs
	$factorlistAR=array();
	for ($i=1;$i<=$numeigenimgs;$i++) {
		$imgname = 'eigenimg'.$i;
		if ($_POST[$imgname]) $factorlistAR[]=$i;
	}
	$factorlist=implode(',',$factorlistAR);

	// make sure eigenimgs were selected
	if (!$factorlist) createNoRefClassifyForm('<b>ERROR:</b> No eigenimages selected');

	//make sure a stack was selected
	if (!$norefid) createNoRefClassifyForm("<b>ERROR:</b> No NoRef Alignment selected, norefId=$norefid");

	// make sure outdir ends with '/'
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
 
	// classification
	if ($numclass > 200 || $numclass < 2) createNoRefClassifyForm("<b>ERROR:</b> Number of classes must be between 2 & 200");

	$particle = new particledata();

	$command.="norefClassify.py ";
	$command.="--num-class=$numclass ";
	$command.="--factor-list=$factorlist ";
	if ($commit) $command.="commit ";
	else $command.="--no-commit ";

	writeTop("No Ref Classify Run Params","No Ref Classify Params");

	echo"
	<p>
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>NoRef Classify Command:</b><br />
	$command
	</td></tr>
	<tr><td>numclass</td><td>$numclass</td></tr>
	<tr><td>factorlist</td><td>$factorlist</td></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	</table>\n";
	writeBottom();
}
?>
