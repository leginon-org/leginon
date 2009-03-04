<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Form for starting a reference-based alignment of a stack
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runAlignment();
}

 // Create the form page
else createAlignmentForm();



//***************************************

function createAlignmentForm($extra=false, $title='imagicMultiReferenceAlignment.py Launcher', $heading='perform an IMAGIC reference-based Alignment') {

	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	} else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}

	// connect to particle info
	$particle = new particledata();
	$templatestackid = $_POST['templatestackid'];
	$stackIds = $particle->getStackIds($sessionId);
	$templateIds = $particle->getTemplateStacksFromProject($projectId);
	$alignruns = count($particle->getAlignStackIds($sessionId));
	$firststack = $particle->getStackParams($stackIds[0]['stackid']);
	$initparts = $particle->getNumStackParticles($stackIds[0]['stackid']);

	$javascript = "<script src='../js/viewer.js'></script>\n";
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackvars) {\n";
	$javascript .= "	var stackArray = stackvars.split('|~~|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/100);\n";
//	$javascript .= "	var lastring = Math.floor(stackArray[2]/3/bestbin);\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
//	$javascript .= "	document.viewerform.lastring.value = lastring;\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
	echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","align/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}
  
  // Set any existing parameters in form
	$sessionpathval = ($_POST['rundir']) ? $_POST['rundir'] : $sessionpath;
	while (file_exists($sessionpathval.'multiRefAlign'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'multiRefAlign'.($alignruns+1);
	$rundescrval = $_POST['description'];
	$stackidval =$_POST['stackid'];
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// alignment params
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : $initparts;
	$iters = ($_POST['iters']) ? $_POST['iters'] : 5;
	if ($iters > 5) $iters = 5; // maximum number allowed by imagic
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : 10;
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : 400;
	$lprefs = ($_POST['lowpass_refs']) ? $_POST['lowpass_refs'] : 15;
	$threshrefs = ($_POST['threshrefs']) ? $_POST['threshrefs'] : -999;
	$maskrad_refs = ($_POST['maskrad_refs']) ? $_POST['maskrad_refs'] : 0.9;
	$max_shift_orig = ($_POST['max_shift_orig']) ? $_POST['max_shift_orig'] : 0.2;
	$samp_param = ($_POST['samp_param']) ? $_POST['samp_param'] : 12;
	$minrad = ($_POST['minrad']) ? $_POST['minrad'] : 0.0;
	$maxrad = ($_POST['maxrad']) ? $_POST['maxrad'] : 0.9;
	$boxsz = ($firststack['bin']) ? $firststack['boxSize']/$firststack['bin'] : $firststack['boxSize'];
	$bestbin = floor($boxsz/100);
	$bin = ($_POST['bin']) ? $_POST['bin'] : $bestbin;
	$mirror = ($_POST['mirror']=="on" || !$_POST['process']) ? 'checked' : '';

  echo"
	<TABLE BORDER=0 CLASS=tableborder>
	<TR>
		<TD VALIGN='TOP'>
		<TABLE CELLPADDING='10' BORDER='0'>
		<TR>
			<TD VALIGN='TOP'>";
		echo 	docpop('runname','<b>Alignment Run Name:</b>');
		echo"
			<INPUT TYPE='text' NAME='runname' VALUE='$runnameval'>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>";
		echo 	docpop('description','<b>Alignment Description:</b>');
		echo"   <BR>
			<TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
			</TD>
		</TR>\n";
		echo"<TR>
			<TD VALIGN='TOP'>";
		echo 	docpop('outdir','<b>Output Directory:</b>');	
		echo "  <BR>	 
			<INPUT TYPE='text' NAME='rundir' VALUE='$sessionpathval' SIZE='38'>
			</TD>
		</TR>
		<TR>
			<TD>\n";

	// select stack
	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo docpop('stack', "<B>Particles:</B>");
		echo "
		<BR><SELECT NAME='stackid' onchange='switchDefaults(this.value)'>\n";
		foreach ($stackIds as $stack) {
			$stackid = $stack['stackid'];
			$stackparams=$particle->getStackParams($stackid);
			$boxsz=($stackparams['bin']) ? $stackparams['boxSize']/$stackparams['bin'] : $stackparams['boxSize'];
			$mpix=$particle->getStackPixelSizeFromStackId($stackid);
			$apixtxt=format_angstrom_number($mpix)."/pixel";
			$stackname = $stackparams['shownstackname'];
			if ($stackparams['substackname'])
				$stackname .= "-".$stackparams['substackname'];
			$totprtls=commafy($particle->getNumStackParticles($stackid));
			echo "<option value='$stackid|~~|$mpix|~~|$boxsz|~~|$totprtls'";
			//echo "<OPTION VALUE='$stackid'";
			// select previously set prtl on resubmit
			if ($stackidval == $stackid) echo " SELECTED";
			echo ">$stackid: $stackname ($totprtls prtls,";
			if ($mpix) echo " $apixtxt,";
			echo " $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo "<BR><BR>\n";
	// select template stack
	if (!$templateIds) { 
		echo"<FONT COLOR='red'><B>No Template Stacks for this project</B></FONT>\n";
	}
	else {
		echo docpop('templatestack', "<B>Template Stacks:</B>");
		echo"
		<BR><SELECT NAME='templatestackid'>\n";
		foreach ($templateIds as $temp) {
			$templateId = $temp['DEF_id'];
			$templatename = $temp['templatename'];
			$apix = $temp['apix'];
			$boxsz = $temp['boxsize'];
			$totprtls = "";
			if ($temp['cls_avgs'] == 1) $type = "Class Averages";
			elseif ($temp['forward'] == 1) $type = "Forward Projections";
			echo "<OPTION VALUE='$templateId|~~|$apix|~~|$boxsz|~~|$totprtls|~~|$type'";
			if ($templateidval == $templateId) echo " SELECTED";
			echo ">$templateId: $templatename ($apix &Aring;/pixel, $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
		
	echo"
		</TD>
	</TR>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
		<INPUT TYPE='checkbox' NAME='commit' $commitcheck>";
	echo 	docpop('commit', " <B>Commit to Database</B><BR>");
	echo"
		</TD>
	</TR>";
	echo"
	</TABLE>
	</TD>
	<TD CLASS='tablebg'>
	<TABLE CELLPADDING='5' BORDER='0'>
	<TR>";
	echo"
		<TD VALIGN='TOP'>
		<B>Particle Params:</B></A><BR>";
	echo"
		<INPUT TYPE='text' NAME='lowpass' SIZE='5' VALUE='$lowpass'>";
	echo	docpop('lpstackval', " Low Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><BR>");
	echo"
		<INPUT TYPE='text' NAME='highpass' SIZE='5' VALUE='$highpass'>";
	echo	docpop('hpstackval', " High Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><BR>");
	echo"
		<INPUT TYPE='text' NAME='bin' SIZE='5' VALUE='$bin'>";
	echo 	docpop('partbin', " Particle Binning<BR>");
	echo"
		</TD>
	</TR>
	<TR>
		<TD VALIGN='TOP' WIDTH=320>
		<B>Reference-Specific Params (optional):</B><BR>";
	echo"  
		<INPUT TYPE='text' NAME='lowpass_refs' VALUE='$lprefs' SIZE='4'>";
	echo	docpop('lpfilt_refs', " Low Pass Filter References <FONT SIZE='-1'>(&Aring;ngstroms)</FONT><BR>");
	echo"
		<INPUT TYPE='text' NAME='thresh_refs' VALUE='$threshrefs' SIZE='4'>";
	echo 	docpop('thresh_refs', " Threshold Reference Pixel values<BR>");
	echo"
		<INPUT TYPE='text' NAME='maskrad_refs' VALUE='$maskrad_refs' SIZE='4'>";
	echo 	docpop('maskrad_refs', " Apply a radial mask to references<BR>");
	echo"
	</TR>
	<TR>
		<TD VALIGN='TOP'>
		<B>Alignment Params:</B></A><BR>";
	echo"
		<INPUT TYPE='text' NAME='iters' VALUE='$iters' SIZE='4'>";
	echo 	docpop('numiter_mra', " Iterations<BR>");
	echo"
		<INPUT TYPE='text' NAME='max_shift_orig' VALUE='$max_shift_orig' SIZE='4'>";
	echo 	docpop('shift_orig', " Maximum radial shift<BR>");
	echo"
		<INPUT TYPE='text' NAME='samp_param' VALUE='$samp_param' SIZE='4'>";
	echo 	docpop('samp_par', " Sampling Parameter<BR>");
	echo"
		<INPUT TYPE='text' NAME='minrad' VALUE='$minrad' SIZE='4'>";
	echo 	docpop('minrad', " Minimum Inner radius<BR>");
	echo"
                <INPUT TYPE='text' NAME='maxrad' VALUE='$maxrad' SIZE='4'>";
	echo 	docpop('maxrad', " Maximum Inner radius<BR>");
	echo"
		<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>";
	echo	docpop('numpart', " Number of Particles to Use<BR>");
	echo"
		<INPUT TYPE='checkbox' NAME='inverttempl' $inverttempl>";
	echo 	docpop('invert', " Invert reference density before alignment<BR>");
	echo"
		<INPUT TYPE='checkbox' NAME='mirror' $mirror>";
	echo	docpop('mirror', " Mirror Alignment<BR>");
	echo"
		</TD>
	</TR>
	</TR>
	</TABLE>
	</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>";
	echo getSubmitForm("Run Multi Reference Alignment");
	echo "
	  </TD>
	</TR>
	</TABLE>
	</FORM>
	</CENTER>\n";

	processing_footer();
	exit;
}

//***************************************
//***************************************
//***************************************
//***************************************
function runAlignment() {
	$expId   = $_GET['expId'];
	$rundir  = $_POST['rundir'];
	$runname = $_POST['runname'];

	$stackvars = $_POST['stackid'];
	list($stackid,$apix_s,$boxsz_s,$totprtls_s) = split('\|~~\|', $stackvars);

	$templatestackvars=$_POST['templatestackid'];
	list($templatestackid,$apix_t,$boxsz_t,$totprtls_t,$type) = split('\|~~\|',$templatestackvars);
	
	// particle parameters
	$bin=$_POST['bin'];
	$lowpass=$_POST['lowpass'];
	$highpass=$_POST['highpass'];

	// imagic reference parameters
	$lprefs = $_POST['lowpass_refs'];
	$thresh_refs = $_POST['thresh_refs'];
	$maskrad_refs = $_POST['maskrad_refs'];	

	// imagic alignment parameters
	$iters=$_POST['iters'];
	$max_shift_orig = $_POST['max_shift_orig'];
	$samp_param = $_POST['samp_param'];
	$minrad = $_POST['minrad'];
	$maxrad = $_POST['maxrad'];
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$inverttempl = ($_POST['inverttempl']=="on") ? 'inverttempl' : '';
	$mirror = ($_POST['mirror']=="on" || !$_POST['process']) ? 'checked' : '';

	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createAlignmentForm("<B>ERROR:</B> Enter a brief description of the alignment run");

	//make sure a stack was selected
	if (!$stackid) createAlignmentForm("<B>ERROR:</B> No stack selected");

	// make sure template stack was selected
	if (!$templatestackid) createAlignmentForm("<B>ERROR:</B> No template stack selected");

	// make sure rundir ends with '/' and append run name
	if (substr($rundir,-1,1)!='/') $rundir.='/';
	$outdir = $rundir;
	$rundir = $rundir.$runname;

	// alignment
	$numpart=$_POST['numpart'];
	if ($numpart < 1) 
		createAlignmentForm("<B>ERROR:</B> Number of particles must be at least 1");
	$particle = new particledata();
	$totprtls_s = $particle->getNumStackParticles($stackid);
	if ((int)$numpart > (int)$totprtls_s) { 
		createAlignmentForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls_s)");
	}

	$command="imagicMultiReferenceAlignment.py ";
	$command.="--projectid=".$_SESSION['projectId']." ";
	$command.="--runname=$runname ";
	$command.="--stackId=$stackid ";
	$command.="--templateStackId=$templatestackid ";
	$command.="--rundir=".$rundir." ";
	$command.="--description=\"$description\" ";

	$command.="--lowpass=$lowpass ";
	$command.="--highpass=$highpass ";
	$command.="--bin=$bin ";
	
	if ($thresh_refs && $maskrad_refs) {
		$command.="--refs ";
		$command.="--thresh_refs=$thresh_refs ";
		$command.="--maskrad_refs=$maskrad_refs ";
	}
	else $command.="--no-refs ";

	if ($mirror) $command.="--mirror ";
	else $command.="--no-mirror ";
	$command.="--max_shift_orig=$max_shift_orig ";
	$command.="--samp_param=$samp_param ";
	$command.="--minrad=$minrad ";
	$command.="--maxrad=$maxrad ";
	$command.="--numiter=$iters ";
	$command.="--num-part=$numpart ";

	if ($inverttempl) $command.="--invert-templates ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	// submit job to cluster
	if ($_POST['process']=="Run Multi Reference Alignment") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password))
			createAlignmentForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,"runAlignment");
		// if errors:
		if ($sub)
			createAlignmentForm("<b>ERROR:</b> $sub");
		exit;
	} else {
		processing_header("Alignment Run","Alignment Params");

		echo"
		<TABLE WIDTH='600' BORDER='1'>
		<TR><TD COLSPAN='2'>
		<B>Alignment Command:</B><BR>
		$command
		</TD></TR>
		<TR><TD>runname</TD><TD>$runname</TD></TR>
		<TR><TD>stackid</TD><TD>$stackid</TD></TR>
		<TR><TD>Template Stack ID</TD><TD>$templatestackid</TD></TR>
		<TR><TD>rundir</TD><TD>$rundir</TD></TR>
		
		<TR><TD>high pass</TD><TD>$highpass</TD></TR>
		<TR><TD>low pass</TD><TD>$lowpass</TD></TR>
		<TR><TD>bin</TD><TD>$bin</TD></TR>";
		if ($thresh_refs && $maskrad_refs) {
		echo "
			<TR><TD>Threshold Reference Densities</TD><TD>$thresh_refs</TD></TR>
			<TR><TD>Reference mask radius</TD><TD>$maskrad_refs</TD></TR>";
		}
		echo "
		<TR><TD>Max translational shift</TD><TD>$max_shift_orig</TD></TR>
		<TR><TD>sampling parameter</TD><TD>$samp_param</TD></TR>
		<TR><TD>minimum radial search</TD><TD>$minrad</TD></TR>
		<TR><TD>maximum radial search</TD><TD>$maxrad</TD></TR>
		<TR><TD>iter</TD><TD>$iters</TD></TR>
		<TR><TD>numpart</TD><TD>$numpart</TD></TR>";
		echo"	</TABLE>\n";
		processing_footer();
	}
}



?>
