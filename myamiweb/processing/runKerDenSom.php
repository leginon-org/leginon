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
	runKerDenSOM();
} else {
	createKerDenSOMForm();
}

function createKerDenSOMForm($extra=false, $title='kerdenSOM.py Launcher', 
 $heading='Kernel Probability Density Estimator Self-Organizing Map') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	$selectAlignId=$_GET['alignId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
		$projectId=getProjectFromExpId($sessionId);
	}
	if ($selectAlignId)
		$formAction.="&alignId=$selectAlignId";

	// connect to particle database
	$particle = new particledata();
	$alignIds = $particle->getAlignStackIds($sessionId, true);
	$alignruns=count($alignIds);
	$analysisIds = $particle->getAnalysisRuns($sessionId, $projectId, true);
	//foreach ($analysisIds as $analysisId)
	//	echo print_r($analysisId)."<br/><br/>\n";
	$analysisruns=count($analysisIds);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackvars) {\n";
	$javascript .= "	var stackArray = stackvars.split('|~~|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set mask radius
	$javascript .= "	if (stackArray[1]) {\n";
	$javascript .= "		var maxmask = Math.floor(stackArray[2]*stackArray[1]/3);\n";
	$javascript .= "		document.viewerform.maskrad.value = maxmask;\n";
	$javascript .= "	}\n";
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'kerden'.($analysisruns+1)))
		$analysisruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'kerden'.($analysisruns+1);
	$rundescrval = $_POST['description'];
	$xdim = ($_POST['xdim']) ? $_POST['xdim'] : '5';
	$ydim = ($_POST['ydim']) ? $_POST['ydim'] : '4';
	if ($selectAlignId)
		$numpart = ($_POST['numpart']) ? $_POST['numpart'] : $particle->getNumAlignStackParticles($selectAlignId);
	else
		$numpart = ($_POST['numpart']) ? $_POST['numpart'] : 0;

	$defaultmaskrad = 100;

	echo"
	<table border='0' class='tableborder'>
	<tr>
		<td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runid','<b>KerDen SOM Run Name:</b>');
	echo "<input type='text' name='runname' value='$runnameval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of KerDen SOM:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='60'>$rundescrval</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if ($selectAlignId) {
		$alignstack = $particle->getAlignStackParams($selectAlignId);
		// get pixel size and box size
		$apix = $alignstack['pixelsize'];
		if ($apix) {
			$mpix = $apix/1E10;
			$apixtxt=format_angstrom_number($mpix)."/pixel";
		}
		$boxsz = $alignstack['boxsize'];
		$totprtls=commafy($particle->getNumAlignStackParticles($selectAlignId));
		$stackval = "$selectAlignId|~~|$apix|~~|$boxsz|~~|$totprtls";
		//echo $stackval;
		echo "<input type='hidden' name='stackid' value='$stackval'>\n";
		echo alignstacksummarytable($selectAlignId, true);
		$alignstack = $particle->getAlignStackParams($selectAlignId);
		$defaultmaskrad = (int) ($alignstack['boxsize']/3)*$alignstack['pixelsize'];
	} elseif ($alignIds) {
		echo "
		Aligned Stack:<br>
		<select name='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($alignIds as $alignarray) {
			$alignid = $alignarray['alignstackid'];
			$alignstack = $particle->getAlignStackParams($alignid);

			// get pixel size and box size
			$apix = $alignstack['pixelsize'];
			if ($apix) {
				$mpix = $apix/1E10;
				$apixtxt=format_angstrom_number($mpix)."/pixel";
			}
			$boxsz = $alignstack['boxsize'];
			//handle multiple runs in stack
			$runname=$alignstack['runname'];
			$totprtls=commafy($particle->getNumAlignStackParticles($alignid));
			echo "<OPTION VALUE='$alignid|~~|$apix|~~|$boxsz|~~|$totprtls'";
			// select previously set prtl on resubmit
			if ($stackidval==$alignid) echo " SELECTED";
			echo ">$alignid: $runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	} else {
		echo"
		<FONT COLOR='RED'><B>No Aligned Stacks for this Session</B></FONT>\n";
	}

	echo "</TD></tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";

	$maskrad = ($_POST['maskrad']) ? $_POST['maskrad'] : (int) $defaultmaskrad;
	echo "<INPUT TYPE='text' NAME='maskrad' SIZE='4' VALUE='$maskrad'>\n";
	echo docpop('maskrad','Mask Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";
	echo "<br/>\n";


	echo docpop('griddim','Grid Dimensions:');
	echo "<br/>\n";
	echo "<table border='0'><tr><td>\n";
	echo "<INPUT TYPE='text' NAME='xdim' VALUE='$xdim' SIZE='1'>\n";
	echo "</td><td>\n";
	echo "<font size='+2'>X</font>\n";
	echo "</td><td>\n";
	echo "<INPUT TYPE='text' NAME='ydim' VALUE='$ydim' SIZE='1'>\n";
	echo "</td></tr></table>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='5'>\n";
	echo docpop('numpart','Number of particles to use');
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "<br/>\n";
	echo "<br/>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo getSubmitForm("Run KerDen SOM");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackid.options[0].value);</script>\n";
	}
	processing_footer();
	exit;
}

function runKerDenSOM() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackvars=$_POST['stackid'];
	list($stackid,$apix,$boxsz,$totpart) = split('\|~~\|',$stackvars);
	$maskrad=$_POST['maskrad'];
	$xdim=$_POST['xdim'];
	$ydim=$_POST['ydim'];
	$numpart=$_POST['numpart'];

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description)
		createKerDenSOMForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid)
		createKerDenSOMForm("<B>ERROR:</B> No stack selected");

	if ($numpart < 10)
		createKerDenSOMForm("<B>ERROR:</B> Must have more than 10 particles");

	if ($xdim > 15 || $ydim > 15)
		createKerDenSOMForm("<B>ERROR:</B> Dimensions must be less than 16");

	$commit = ($_POST['commit']=="on") ? '--commit' : '';

	// check particle radii
	$particle = new particledata();
	$stackparams=$particle->getAlignStackParams($stackid);
	$boxrad = $stackparams['pixelsize'] * $stackparams['boxsize'];
	if ($maskrad > $boxrad)
		createKerDenSOMForm("<b>ERROR:</b> Mask radius too large! $maskrad > $boxrad ".print_r($stackparams));

	// make sure outdir ends with '/' and append run name
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$rundir = $outdir.$runname;

	$command ="kerdenSOM.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--rundir=$rundir ";
	$command.="--description=\"$description\" ";
	$command.="--runname=$runname ";
	$command.="--alignid=$stackid ";
	$command.="--maskrad=$maskrad ";
	$command.="--xdim=$xdim ";
	$command.="--ydim=$ydim ";
	$command.="--numpart=$numpart ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run KerDen SOM") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createKerDenSOMForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'alignanalysis');
		// if errors:
		if ($sub) createKerDenSOMForm("<b>ERROR:</b> $sub");
		exit;
	}
	else {
		processing_header("Kernel Probability Density Estimator Self-Organizing Map","Kernel Probability Density Estimator Self-Organizing Map");
		echo"
		<table width='600' class='tableborder' border='1'>
		<tr><td colspan='2'>
		<b>KerDen SOM Command:</b><br />
		$command
		</td></tr>
		<tr><td>run id</td><td>$runname</td></tr>
		<tr><td>stack id</td><td>$stackid</td></tr>
		<tr><td>x dimension</td><td>$xdim</td></tr>
		<tr><td>y dimension</td><td>$xdim</td></tr>
		<tr><td>num part</td><td>$numpart</td></tr>
		<tr><td>run dir</td><td>$rundir</td></tr>
		<tr><td>commit</td><td>$commit</td></tr>
		</table>\n";
		processing_footer();
	}
}
?>
