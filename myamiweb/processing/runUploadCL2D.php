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
	runCL2DAlign();
} else {
	createCL2DAlignForm();
}

function createCL2DAlignForm($extra=false, $title='uploadXmippCL2D.py Launcher', $heading='Upload Clustering 2D Alignment') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$projectId=getProjectId();
		$formAction=$_SERVER['PHP_SELF'];
	}

	$javascript .= writeJavaPopupFunctions('appion');	
	$javascript .= editTextJava();
	processing_header($title,$heading,$javascript);

	// write out errors, if any came up:
	if ($extra)
		echo "<span style='font-size: larger; color:#bb3333;'>$extra</span><br />\n";

	// connect to particle database
	$particle = new particledata();
	$CL2Djobs = $particle->getFinishedCL2DJobs($projectId);

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';

	if (!$CL2Djobs) {
		echo "<font color='red'><B>No Clustering 2D Jobs for this Project</B></FONT>\n";
	} else {
		foreach ($CL2Djobs as $CL2Djob) {
			$jobid = $CL2Djob['DEF_id'];
			echo "<form name='viewerform' method='POST' action='$formAction&jobid=$jobid'>\n";
			
			// Post values needed for showOrSubmitCommand()
			echo "<input type='hidden' name='runname' value='$jobid'>\n";
			$outdir = $CL2Djob['path'].$jobid;
			echo "<input type='hidden' name='outdir' value='$outdir'>\n";
			
			if ($_POST['hideJob'.$jobid] == 'hide') {
				$particle->updateHide('ApCL2DJobData', $jobid, '1');
				$CL2Djob['hidden']='1';
			} elseif ($_POST['hideUndoJob'.$jobid] == 'unhide') {
				$particle->updateHide('ApCL2DJobData', $jobid, '0');
				$CL2Djob['hidden']='0';
			}

			echo openRoundBorder();
			echo "<table cellspacing='8' cellpading='2' border='0'>\n";

			echo "<tr><td colspan='5'>\n";
			$nameline = "<span style='font-size: larger; color:#111111;'>\n";
			$nameline .= "Job Id: $jobid &nbsp;\n";
			$nameline .= " ".$CL2Djob['runname'];
			$nameline .= "</span>\n";
			if ($CL2Djob['hidden'] == 1) {
				$nameline.= " <font color='#cc0000'>HIDDEN</font>\n";
				$nameline.= " <input class='edit' type='submit' name='hideUndoJob".$jobid."' value='unhide'>\n";
				$display_keys['hidden'] = "<font color='#cc0000'>HIDDEN</font>";
			} else $nameline.= " <input class='edit' type='submit' name='hideJob".$jobid."' value='hide'>\n";

			echo apdivtitle($nameline);
			echo "</td></tr>\n";

			$avgfile = $CL2Djob['path']."/average.mrc";
			if (file_exists($avgfile)) {
				echo "<tr><td align='left' rowspan='30' align='center' valign='top'>";
				echo "<img src='loadimg.php?filename=$avgfile&s=100' height='100'><br/>\n";
				echo "<i>final reference image</i>\n";
				echo "</td></tr>\n";
			}

			//echo "<tr><td colspan='2'>\n";
			//echo print_r($CL2Djob)."<br/><br/>";
			//echo "</td></tr>\n";

			$display_keys['date time'] = $CL2Djob['DEF_timestamp'];
			$display_keys['path'] = "<input type='text' name='path".$jobid."' value='".$CL2Djob['path']."' size='40'>\n";
			$display_keys['file prefix'] = $CL2Djob['timestamp'];

			$dir = opendir($CL2Djob['path']);
			while($entry = readdir($dir)) {
				$dirarray[] = $entry;
			}
			$count = 0;
			foreach ($dirarray as $e) {
				if (preg_match("/level_[0-9][0-9]/i", $e, $matches)){
					$level = substr($matches[0],-2,2);
					if (intval($level) > $count) {
						 $count = intval($level);
					}
				}
			}			
			
			$refstackname = "part".$CL2Djob['timestamp']."_level_%1$02d_.hed";
			$r = vsprintf($refstackname, $count);
			$refstack = $CL2Djob['path']."/".$r;
			if (file_exists($refstack))
				$display_keys['reference stack'] = "<a target='stackview' HREF='viewstack.php?"
					."file=$refstack&expId=$expId'>".$r."</a>";

			echo "<input type='hidden' name='timestamp".$jobid."' value='".$CL2Djob['timestamp']."'>\n";
			foreach($display_keys as $k=>$v) {
				echo formatHtmlRow($k,$v);
			}

			echo "<tr><td colspan='2'>\n";
			echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
			echo docpop('commit','<B>Commit to Database</B>');
			echo "</td></tr>\n";

			echo "<tr><td colspan='2'>\n";
			echo getSubmitForm("Upload Job $jobid");
			echo "</td></tr>\n";

			echo "</table>\n";
			echo closeRoundBorder();
			echo "<br/>\n";
			echo "</form>\n";
		}
	}


	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}

	echo referenceBox("A clustering approach to multireference alignment of single-particle projections in electron microscopy.", 2010, 
		"Sorzano CO, Bilbao-Castro JR, Shkolnisky Y, Alcorlo M, Melero R, Caffarena-Fernández G, Li M, Xu G, Marabini R, Carazo JM.", 
		"J Struct Biol.", 171, 2, 20362059, false, false, "img/xmipp_logo.png");


	processing_footer();
	exit;
}

function runCL2DAlign() {
	/* *******************
	PART 1: Get variables
	******************** */
	$expId=$_GET['expId'];
	$jobid = $_GET['jobid'];
	$timestamp=$_POST['timestamp'.$jobid];
	$rundir=$_POST['path'.$jobid];
	$commit = ($_POST['commit']=="on") ? true : false;

	//make sure a stack was selected
	//if (!$rundir)
	//	createCL2DAlignForm("<B>ERROR:</B> Unknown output directory");

	// make sure outdir ends with '/' and append run name
	$outdir = dirname($rundir);
	$runname = basename($rundir);
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	
	/* *******************
	PART 3: Create program command
	******************** */
	// setup command
	$command="uploadXmippCL2D.py  ";
	$command.="--rundir=$rundir ";
	if ($timestamp) $command.="-t $timestamp ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
//	$command.="--runname=".$runname." ";
	$command.="--projectid=".getProjectId()." ";
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= referenceBox("A clustering approach to multireference alignment of single-particle projections in electron microscopy.", 2010, 
		"Sorzano CO, Bilbao-Castro JR, Shkolnisky Y, Alcorlo M, Melero R, Caffarena-Fernández G, Li M, Xu G, Marabini R, Carazo JM.", 
		"J Struct Biol.", 171, 2, 20362059, false, false, "img/xmipp_logo.png");
		
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'CL2Dali', $nproc);

	// if error display them
	if ($errors)
		createCL2DAlignForm("<b>ERROR:</b> $errors");
	
}
?>
