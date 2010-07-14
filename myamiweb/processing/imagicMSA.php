<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an IMAGIC Reclassification Job initiating a 3d0 model generation
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

// check for errors in submission form
if ($_POST['process']) {
	if (!$_POST['alignid']) jobform("error: no aligned stack specified");
	if (!is_numeric($_POST['numiters'])) jobform("error: number of MSA iterations not specified");
	if (!is_numeric($_POST['overcorrection'])) jobform("error: MSA overcorrection factor not specified");
	if (!is_numeric($_POST['mask_radius'])) jobform("error: mask radius not specified");
	if (!is_numeric($_POST['mask_dropoff'])) jobform("error: mask dropoff not specified");
	if (!$_POST['MSAdistance']) jobform("error: method of calculating MSA distance not specified");
	runImagicMSA();
}
else jobform();


function jobform($extra=false)	{

	$javafunc .= writeJavaPopupFunctions('appion');
	
	$particle = new particledata();
	
	// get session info
	echo "<form name='viewerform' method='POST' action='$formaction'>\n";
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$alignId=$_GET['alignId'];
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// connect to particle database
		$particle = new particledata();
		$alignIds = $particle->getAlignStackIds($expId, true);
		$analysisIds = $particle->getAnalysisRuns($expId, $projectId, true);
		$analysisruns=count($analysisIds);
		$analysisruns = ($analysisIds) ? count($analysisIds) : 0;

	processing_header("IMAGIC Classification (MSA)","IMAGIC Classification (MSA)",$javafunc);

	// write out errors, if any came up:
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	
	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
        $sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while ((file_exists($sessionpathval.'coran'.($analysisruns+1))) || (file_exists($sessionpathval.'imagicmsa'.($analysisruns+1))))
                $analysisruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'imagicmsa'.($analysisruns+1);
	$description = ($_POST['description']) ? $_POST['description'] : '';
//	$alignidval = $_POST['alignid'];
	$outdir = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '5';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '600';
	$mask_radius = ($_POST['mask_radius']) ? $_POST['mask_radius'] : '0.9';	
	$mask_dropoff = ($_POST['mask_dropoff']) ? $_POST['mask_dropoff'] : '0.1';
	$MSAdistance = ($_POST['MSAdistance']) ? $_POST['MSAdistance'] : 'modulation';
	$numiters = ($_POST['numiters']) ? $_POST['numiters'] : '50';
	$overcorrection = ($_POST['overcorrection']) ? $_POST['overcorrection'] : '0.8';
	
	echo"
	<table border='0' class='tableborder'>
	<TR>
		<TD valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<TR><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>MSA Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br>\n";
	echo "<input type='text' name='outdir' value='$outdir' size='38'>\n";
	echo "<br>\n";
	echo "<br>\n";
	echo docpop('descr','<b>Description of IMAGIC MSA run:</b>');
	echo "<br>\n";
	echo "<textarea name='description' rows='3' cols='36'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	if ($alignId) {
		echo "<input type='hidden' name='alignid' value='$alignId'>\n";
		echo alignstacksummarytable($alignId, true);
		$alignstack = $particle->getAlignStackParams($alignId);
		$defaultmaskrad = (int) ($alignstack['boxsize']/2-2)*$alignstack['pixelsize'];
	} elseif ($alignIds) {
		echo "
		Aligned Stack:<br>
		<select name='alignid' onchange='switchDefaults(this.value)'>\n";
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
			if ($alignidval==$alignid) echo " SELECTED";
			echo ">$alignid: $runname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	} else {
		echo"
		<FONT COLOR='RED'><B>No Aligned Stacks for this Session</B></FONT>\n";
	}


	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	
	// rest of the params
	echo "<TR>";
	echo "    <TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "<br>";
	// number of processors defaulted to 8
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 8;
	echo "<INPUT TYPE='text' SIZE='5' NAME='nproc' VALUE=$nproc> Number of Processors";
	echo "<br></TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE CELLPADDING='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";
	echo "<b>Particle-specific Radii (in &Aring;ngstroms)</b>\n";
	echo "<br>\n";
	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}
	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms, 0=off)</font>\n";
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
	echo docpop('hpval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms, 0=off)</font>\n";
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('norefbin','Particle binning');
	echo "<br>\n";
	
	echo "<INPUT TYPE='text' NAME='mask_radius' VALUE='$mask_radius' SIZE='4'>\n";
	echo docpop('mask_radius', 'Mask Radius');
	echo "<br>\n";

	echo "<INPUT TYPE='text' NAME='mask_dropoff' VALUE='$mask_dropoff' SIZE='4'>\n";
	echo docpop('mask_dropoff', 'Mask Drop-off');
	echo "<br>\n";
	echo "<br>\n";
	
	echo "<b>Multivariate Statistical Analysis Parameters</b>\n";
	echo "<br>\n";
	
	// specify selection (modulation, euclidean, chisquare)
	echo docpop('MSAdistance', 'MSA distance criteria');
	echo "<br>\n";
	echo "<SELECT name='MSAdistance'>";
	echo "<OPTION VALUE='modulation'>Modulation</OPTION>";
	echo "<OPTION VALUE='euclidian'>Euclidian Distance</OPTION>";
	echo "<OPTION VALUE='chisquare'>Chi-Square</OPTION>";
	echo "</SELECT><br>";
	
	
	
	echo "<INPUT TYPE='text' NAME='numiters' VALUE='$numiters' SIZE='4'>\n";
	echo docpop('numiters', 'Number of MSA Iterations');
	echo "<br>";
	
	echo "<INPUT TYPE='text' NAME='overcorrection' VALUE='$overcorrection' SIZE='4'>\n";
	echo docpop('overcorrection', 'Overcorrection Factor for MSA');
	echo "<br>";
	
	echo "  </TD>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr>\n";
	echo getSubmitForm("run imagic");
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

function runImagicMSA($extra=false)	{
	$expId=$_GET['expId'];
	$projectId=getProjectId();
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackvalues=$_POST['alignid'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$bin=$_POST['bin'];
	$mask_radius=$_POST['mask_radius'];
	$mask_dropoff=$_POST['mask_dropoff'];
	$numiters=$_POST['numiters'];
	$MSAdistance=$_POST['MSAdistance'];
	$overcorrection=$_POST['overcorrection'];
	$description=$_POST['description'];
	$commit = ($_POST['commit']=="on") ? '--commit' : '';
	$nproc = $_POST['nproc'];
	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];
	
	// get stack id, apix, box size, and total particles from input
	list($alignid,$apix,$boxsize,$totpartls) = split('\|~~\|',$stackvalues);

	// create python command for executing imagic job file	
	$command = "imagicMSA.py";
	$command.= " --projectid=".getProjectId();
	$command.= " --alignid=$alignid";
	$command.= " --runname=$runname";
	$command.= " --outdir=$outdir$runname";
	if ($lowpass && $lowpass!=0) $command.= " --lpfilt=$lowpass";
	if ($highpass && $highpass!=0) $command.= " --hpfilt=$highpass";
	if ($mask_radius) $command.= " --mask_radius=$mask_radius";
	if ($mask_dropoff) $command.= " --mask_dropoff=$mask_dropoff";
	if ($bin) $command.= " --bin=$bin";
	$command.= " --numiters=$numiters";
	$command.= " --MSAdistance=$MSAdistance";
	$command.= " --overcorrection=$overcorrection";
	$command.= " --description=\"$description\"";
	$command.=" --nproc=$nproc";
	if ($commit) $command.= " --commit";
	else $command.=" --no-commit";

	// Add reference to top of the page
	$headinfo .= imagicRef();

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'alignanalysis', $nproc);

	// if error display them
	if ($errors)
		jobform($errors);
	exit;

	/*
	if ($_POST['process']=="run imagic") {
		if (!($user && $pass)) jobform("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'alignanalysis',False,False,False,$nproc,8,1);
		// if errors:
		if ($sub) 
			jobform("<b>ERROR:</b> $sub");
		exit;
	} 
	else {
		processing_header("IMAGIC Classification (MSA)","IMAGIC Classification (MSA) Params");
		echo"
			<TABLE WIDTH='600' BORDER='1'>
			<TR><TD COLSPAN='2'>
				<B>Classification Command:</B><br>
				$command
			</TD></tr>
			<TR><td>runname</TD><td>$outdir$runname</TD></tr>
			<TR><td>alignstackid</TD><td>$alignid</TD></tr>
			<TR><td>outdir</TD><td>$outdir</TD></tr>";
			if ($lowpass & $lowpass!=0) {
				echo "<TR><td>low pass filter</TD><td>$lowpass</TD></tr>";
			} else {
				echo "<TR><td>low pass filter</TD><td>OFF</TD></tr>";
			}
			if ($highpass & $highpass!=0) {
				echo "<TR><td>high pass filter</TD><td>$highpass</TD></tr>";
			} else {
				echo "<TR><td>high pass filter</TD><td>OFF</TD></tr>";
			}
		echo "
			<TR><td>bin</TD><td>$bin</TD></tr>
			<TR><td>mask radius</TD><td>$mask_radius</TD></tr>
			<TR><td>mask dropoff</TD><td>$mask_dropoff</TD></tr>
			<TR><td>distance criteria</TD><td>$MSAdistance</TD></tr>
			<TR><td>overcorrection factor</TD><td>$overcorrection</TD></tr>
			<TR><td>number of iterations</TD><td>$numiters</TD></tr>
			</table>\n";
		processing_footer();
	}
	exit;
	*/
}
?>
