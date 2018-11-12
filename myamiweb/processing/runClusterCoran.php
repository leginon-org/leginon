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
require_once "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runClusterCoran();
} else {
	createClusterCoranForm();
}

function createClusterCoranForm($extra=false, $title='clusterCoran.py Launcher', $heading='Cluster Particles with Coran') {
	$alignid=$_GET['alignId'];
	$analysisid=$_GET['analysisId'];
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&alignId=$alignid&analysisId=$analysisid";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF']."?alignId=$alignid&analysisId=$analysisid";
	}
	$projectId=getProjectId();

	// connect to particle and ctf databases
	$particle = new particledata();
	$analysisparams = $particle->getAnalysisParams($analysisid);
	$rundir = $analysisparams['path'];
	$runname = $analysisparams['runname'];
	$outdir = preg_replace('%'.$runname.'%','',$rundir);

	// in case there are more than 1 '/' at the end
	if (substr($outdir,-1,1)!='/') $outdir.='/';

	$javascript = "<script src='../js/viewer.js'></script>";
	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	
	// Post the runname for showOrSubmitCommand()
	echo "<input type='hidden' name='runname' value='$runname'>\n";
	
	$sessiondata=getSessionList($projectId,$expId);
	$alignparams = $particle->getAlignStackParams($alignid);
	//echo print_r($alignparams)."<br/><br/>\n";
	$analysisparams = $particle->getAnalysisParams($analysisid);
	//echo print_r($analysisparams)."<br/><br/>\n";
	
	// Set any existing parameters in form
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	// classifier params
	$factorlist = ($_POST['factorlist']) ? $_POST['factorlist'] : "1,2,3";
	// default number of classes based on number of particles 
	$nump=$alignparams['num_particles'];
	$defaultNumClasses = round(sqrt($nump));
	$defaultNumClasses.= ",".round(sqrt(4*$nump));
	$defaultNumClasses.= ",".round(sqrt(16*$nump));
	$numclass = ($_POST['numclass']) ? $_POST['numclass'] : $defaultNumClasses;

	echo "<input type='hidden' name='alignid' value=$alignid>";
	
	echo "<table border='0' class='tableborder'>\n";
	echo "<tr><td colspan='2' valign='top'>\n";

	echo openRoundBorder();
	echo alignstacksummarytable($alignid, true);
	echo "<br/>\n";
	echo closeRoundBorder();

	echo "</td></tr>";

	echo "<tr><td valign='top'>\n";
	echo "<table cellpadding='10' border='0'>\n";
	echo "<tr><td valign='top'>\n";

	$dendrofile = $analysisparams['path']."/dendrogram.png";
	if(file_exists($dendrofile)) {
		echo docpop('dendrogram','<b>Dendrogram:</b>');
		echo "<a href='loadimg.php?filename=$dendrofile'><font size='-2'>(click to enlarge)</font><br />"
			."<img src='loadimg.php?filename=$dendrofile&s=256' width='256' border='0'></a><br/><br/>\n";
	}

	echo "<hr />\n";
	echo docpop('outdir','<b>Output directory:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='disoutdir' value='$outdir' size='40' disabled/>\n";
	echo "<input type='hidden' name='outdir' value='$outdir'/>\n";
	echo "<br/>";
	echo "<small><i>Note: Not editable because must be the same as Feature Analysis</i></small>";

	echo "<br/><br/>\n";

	echo docpop('numclass','<b>List of Number of Classes:</b>');
	echo "<br/>\n";
	echo "<input type='text' name='numclass' size='20' value='$numclass'> ";

	echo "<br/><br/>\n";

	echo docpop('classmethod','<B>Particle classification method:</B>');
	echo "<br/>";
	echo "<INPUT TYPE='radio' NAME='classmethod' VALUE='hierarch' "
		.((!$_POST['classmethod'] || $_POST['classmethod'] == 'hierarch') ? 'CHECKED' : '')
		.">\n Hierarchical clustering<br/>\n";
	echo "<INPUT TYPE='radio' NAME='classmethod' VALUE='kmeans' "
		.($_POST['classmethod'] == 'kmeans' ? 'CHECKED' : '')
		.">\n K-means Clustering<br/>\n";
	echo "<br/><br/>";

	echo "<input type='checkbox' name='commit' $commitcheck>";
	echo docpop('commit','Commit to Database');
	echo "";
	echo "<br /></td></tr>\n</table>\n";
	echo "</td>";
	echo "<td class='tablebg'>";


	echo "<table cellpadding='5' border='0'>";
	echo "<tr><td valign='TOP'>\n";
	echo docpop('factorlist','<b>Eigen Images</b>');
	echo "<br/>\n";
	echo "Choose factors to use: ";
	echo "<font size='-2'>(Click on the image to view)</font>\n";
	echo "<b />\n";

	$eigendata = $particle->getCoranEigenDataFromAnalysis($analysisid);
	//print_r($eigendata[0]);

	if($eigendata) {
		echo "<table border='1' cellpadding='5'>\n";
		echo "<tr valign='bottom'>\n";
		foreach ($eigendata as $edata) {
			$index = (int) $edata['num'];
			$efile = $edata['path']."/".$edata['name'];
			$contrib = round($edata['contrib'],1);
			$level = dechex($contrib/$eigendata[0]['contrib']*239 + 16);
			echo "<td>\n";
			echo "<a href='loadimg.php?filename=$efile' target='eigenimage'>\n"
				."<img src='loadimg.php?filename=$efile&s=64' width='64' height='64' border='0'></a><br />\n";
			$imgname = 'eigenimg'.$index;
			echo "<center>$index <input type='checkbox' name='$imgname' ";
			// when first loading page select first 3
			// eigenimgs, otherwise reload selected
			if (($index<=3 && !$_POST['process']) || $_POST[$imgname]) echo "checked";
			echo "><font color='#".$level."2222' size='-2'>($contrib %)</font></center>\n";
			echo "</td>\n";
			if ($index % 4 == 0) echo "</tr>\n";
		}
		if (!$index % 4 == 0) echo "</tr>\n";
		echo "</table>\n";
	}
	echo "<input type='hidden' name='numeigenimgs' value='$index'>\n";

	echo "	</td>\n";
	echo "</tr>\n";
	echo "</table>";
	echo "</td>";
	echo "</tr>";
	echo "<tr>";
	echo "	<td colspan='2' align='center'>";
	echo "<br/>\n";

	echo "	<hr />";
	echo getSubmitForm("Run Cluster Coran");
	echo "<br/><br/>\n";
	echo "  </td>";
	echo "</tr>";
	echo "</table>";
	echo "</form>";

	echo spiderRef();

	processing_footer();
	exit;
}

function runClusterCoran() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId = $_GET['expId'];
	$alignid = $_GET['alignId'];
	$analysisid=$_GET['analysisId'];

	$numclass = $_POST['numclass'];
	$alignid = $_POST['alignid'];
	$numeigenimgs = $_POST['numeigenimgs'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$classmethod=$_POST['classmethod'];
	$outdir=$_POST['outdir'];

	$particle = new particledata();
	$analysisparams = $particle->getAnalysisParams($analysisid);
	//echo print_r($analysisparams)."<br/><br/>\n";
	$rundir = $analysisparams['path'];
	$runname = $analysisparams['runname'];
	$outdir = preg_replace('%'.$runname.'%','',$rundir);

	// in case there are more than 1 '/' at the end
	if (substr($outdir,-1,1)!='/') $outdir.='/';

	// get selected eigenimgs
	$factorlistAR=array();
	for ($i=1;$i<=$numeigenimgs;$i++) {
		$imgname = 'eigenimg'.$i;
		if ($_POST[$imgname]) $factorlistAR[]=$i;
	}
	//print_r($factorlistAR);
	$factorlist=implode(',',$factorlistAR);

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	// make sure eigenimgs were selected
	if (!$factorlist) 
		createClusterCoranForm('<b>ERROR:</b> No eigenimages selected');

	//make sure a stack was selected
	if (!$alignid) 
		createClusterCoranForm("<b>ERROR:</b> No Alignment selected, alignid=$alignid");

	if (!$analysisid) 
		createClusterCoranForm("<b>ERROR:</b> No Analysis selected, analysisid=$analysisid");

	// classification
	//if ($numclass > 999 || $numclass < 2) 
	//	createClusterCoranForm("<b>ERROR:</b> Number of classes must be between 2 and 999");

	/* *******************
	PART 3: Create program command
	******************** */
	$command ="clusterCoran.py ";
	$command.="--projectid=".getProjectId()." ";
	$command.="--analysisid=$analysisid ";
	$command.="--num-class-list=$numclass ";
	$command.="--factor-list=$factorlist ";
	$command.="--runname=".$runname." ";
	$command.="--rundir=".$outdir.$runname." ";
	if ($classmethod && $classmethod != 'hierarch') $command.="--method=$classmethod ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= spiderRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partcluster', $nproc);

	// if error display them
	if ($errors)
		createClusterCoranForm("<b>ERROR:</b> $errors");
	
}
?>
