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
require "inc/summarytables.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
	runClusterCoran(($_POST['process']=="Run Cluster Coran") ? true : false);
} else {
	createClusterCoranForm();
}

function createClusterCoranForm($extra=false, $title='clusterCoran.py Launcher', $heading='Reference Free Classify') {
	$alignid=$_GET['alignId'];
	$analysisid=$_GET['analysisId'];
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId&alignId=$alignid&analysisId=$analysisId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF']."?alignId=$alignid&analysisId=$analysisId";
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();

	$javascript = "<script src='../js/viewer.js'></script>";
	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='red'>$extra</font>\n<hr/><br/>\n";
	}
  
	echo"<form name='viewerform' method='post' action='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

	$alignparams = $particle->getAlignStackParams($alignid);
	echo print_r($alignparams)."<br/><br/>\n";
	$analysisparams = $particle->getAnalysisParams($analysisid);
	echo print_r($analysisparams)."<br/><br/>\n";

	
	// Set any existing parameters in form
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	// classifier params
	$factorlist = ($_POST['factorlist']) ? $_POST['factorlist'] : "1,2,3";
	$numclass = ($_POST['numclass']) ? $_POST['numclass'] : 40;

	echo "<input type='hidden' name='alignid' value=$alignid>";

	echo "<table border='0' class='tableborder'>\n";
	echo "<tr><td colspan='2' valign='top'>\n";
	echo openRoundBorder();
	echo alignstacksummarytable($alignid, true);
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
	echo "<input type='text' name='numclass' size='3' value='$numclass'> ";
	echo docpop('numclass','Number of Classes');
	echo "<br/><br/>";

	echo docpop('classmethod','<B>Particle classification method:</B>');
	echo "<br/>";
	echo "<INPUT TYPE='radio' NAME='classmethod' VALUE='hierarch' "
		.((!$_POST['classmethod'] || $_POST['classmethod'] == 'hierarch') ? 'CHECKED' : '')
		.">\n Hierarchical clustering<br/>\n";
	echo "<INPUT TYPE='radio' NAME='classmethod' VALUE='kmeans' "
		.($_POST['classmethod'] == 'kmeans' ? 'CHECKED' : '')
		.">\n K-means Clustering<br/>\n";
	echo "<br /><br />";

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
				."<img src='loadimg.php?filename=$efile&s=128' width='128' height='128' border='0'></a><br />\n";
			$imgname = 'eigenimg'.$index;
			echo "<center>$index <input type='checkbox' name='$imgname' ";
			// when first loading page select first 3
			// eigenimgs, otherwise reload selected
			if (($index<=3 && !$_POST['process']) || $_POST[$imgname]) echo "checked";
			echo "><font color='#".$level."2222' size='-1'>($contrib %)</font></center>\n";
			echo "</td>\n";
			if ($index % 3 == 0) echo "</tr>\n";
		}
		if (!$index % 3 == 0) echo "</tr>\n";
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
	echo "	<hr />";
	echo getSubmitForm("Run Cluster Coran");
	echo "  </td>";
	echo "</tr>";
	echo "</table>";
	echo "</form>";
	processing_footer();
	exit;
}

function runClusterCoran($runjob=False) {
	$expId = $_GET['expId'];
	$alignid = $_GET['alignId'];
	$analysisid=$_GET['analysisId'];
	$command.="clusterCoran.py ";

	$numclass = $_POST['numclass'];
	$alignid = $_POST['alignid'];
	$numeigenimgs = $_POST['numeigenimgs'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$classmethod=$_POST['classmethod'];

	// get selected eigenimgs
	$factorlistAR=array();
	for ($i=1;$i<=$numeigenimgs;$i++) {
		$imgname = 'eigenimg'.$i;
		if ($_POST[$imgname]) $factorlistAR[]=$i;
	}
	//print_r($factorlistAR);
	$factorlist=implode(',',$factorlistAR);

	// make sure eigenimgs were selected
	if (!$factorlist) 
		createClusterCoranForm('<b>ERROR:</b> No eigenimages selected');

	//make sure a stack was selected
	if (!$alignid) 
		createClusterCoranForm("<b>ERROR:</b> No Alignment selected, alignid=$alignid");

	if (!$analysisid) 
		createClusterCoranForm("<b>ERROR:</b> No Analysis selected, analysisid=$analysisid");

	// classification
	if ($numclass > 999 || $numclass < 2) 
		createClusterCoranForm("<b>ERROR:</b> Number of classes must be between 2 and 999");

	$particle = new particledata();

	$command.="--alignid=$alignid ";
	$command.="--analysisid=$analysisid ";
	$command.="--num-class=$numclass ";
	$command.="--factor-list=$factorlist ";
	if ($classmethod && $classmethod != 'hierarch') $command.="--method=$classmethod ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($runjob) {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createClusterCoranForm("<B>ERROR:</B> Enter a user name and password");

		// get the output directory (already contains runid)
		$alignparams = $particle->getAlignStackParams($alignid);
		$outdir = $alignparams['path'];
		$runid = $alignparams['name'];
		// take runid off of outdir
		$outdir = ereg_replace($runid,'',$outdir);
		// in case there are more than 1 '/' at the end
		if (substr($outdir,-1,1)=='/') $outdir=substr($outdir,0,-1);

		// create unique id for the job, since multiple may be
		// submitted - id is the factor list and num classes
		$uniqId=implode('',$factorlistAR);
		$uniqId.=".$numclass";

		$sub = submitAppionJob($command,$outdir,$runid,$expId,'alignclass',False,False,$uniqId);

		// if errors:
		if ($sub) createClusterCoranForm("<b>ERROR:</b> $sub");
		exit;
	}
	processing_header("No Ref Classify Run Params","No Ref Classify Params");

	echo"
	<table width='600' class='tableborder' border='1'>
	<tr><td colspan='2'>
	<b>Cluster Coran Command:</b><br />
	$command
	</td></tr>
	<tr><td>numclass</td><td>$numclass</td></tr>
	<tr><td>factorlist</td><td>$factorlist</td></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	</table>\n";
	processing_footer();
}
?>
