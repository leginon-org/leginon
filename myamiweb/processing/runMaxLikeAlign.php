<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 *
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST) {
	runMaxLikeAlign();
} else {
	createMaxLikeAlignForm();
}

function createMaxLikeAlignForm($extra=false, $title='maxlikeAlignment.py Launcher', $heading='Maximum Likelihood Alignment') {
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

	// connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "function switchDefaults(stackval) {\n";
	$javascript .= "	var stackArray = stackval.split('|--|');\n";
	// remove commas from number
	$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
	$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
	$javascript .= "	document.viewerform.clipdiam.value = stackArray[2];\n";
	// set max last ring radius
	$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
	$javascript .= "	if (bestbin < 1) {\n";
	$javascript .= "		var bestbin = 1 ;}\n";
	$javascript .= "	document.viewerform.bin.value = bestbin;\n";
	$javascript .= "	estimatetime();\n";
	// set particle & mask radius and lp
	$javascript .= "}\n";
	$javascript .= "
		function enablefastmode() {
			if (document.viewerform.fast.checked){
				document.viewerform.fastmode.disabled=false;
			} else {
				document.viewerform.fastmode.disabled=true;
			}

		}
		function estimatetime() {
			var secperiter = 0.12037;
			var numpart = document.viewerform.numpart.value;
			var boxsize = document.viewerform.clipdiam.value;
			var numpix = Math.pow(boxsize/document.viewerform.bin.value, 2);
			var calctime = (numpart/1000.0) * document.viewerform.numref.value * numpix * secperiter / document.viewerform.angle.value / (document.viewerform.nproc.value - 1);
			if (document.viewerform.mirror.checked) {
				calctime = calctime*2.0;
			}
			if (calctime < 70) {
				var time = Math.round(calctime*100.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' seconds';
			} else if (calctime < 3700) {
				var time = Math.round(calctime*0.6)/100.0
				document.viewerform.timeestimate.value = time.toString()+' minutes';
			} else if (calctime < 3700*24) {
				var time = Math.round(calctime/36.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' hours';
			} else {
				var time = Math.round(calctime/36.0/24.0)/100.0
				document.viewerform.timeestimate.value = time.toString()+' days';
			}
		}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
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
	while (file_exists($sessionpathval.'maxlike'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'maxlike'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = split('\|--\|',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$numref = ($_POST['numref']) ? $_POST['numref'] : '2';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '4';
	$angle = ($_POST['angle']) ? $_POST['angle'] : '5';
	$clipdiam = ($_POST['clipdiam']) ? $_POST['clipdiam'] : '';
	$maxiter = ($_POST['maxiter']) ? $_POST['maxiter'] : '15';
	$mirror = ($_POST['mirror']=='on' || !$_POST['process']) ? 'checked' : '';
	$savemem = ($_POST['savemem']=='on' || !$_POST['process']) ? 'checked' : '';
	$distributionval = ($_POST['distribution']) ? $_POST['distribution'] : 'gauss';
	$fast = ($_POST['fast']=='on' || !$_POST['fast']) ? 'checked' : '';

	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>MaxLike Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of Max Like Alignment:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='50'>$description</textarea>\n";
	echo closeRoundBorder();
	echo "</td>
		</tr>\n";
	echo "<tr>
			<td>\n";

	if (!$stackIds) {
		echo "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
	} else {
		echo docpop('stack','<b>Select a stack of particles to use</b>');
		echo "<br/>";
		$apix = $particle->getStackSelector($stackIds,$stackidval,'switchDefaults(this.value)');
	}
	echo "</TD></tr><TR>\n";
	echo "<TD VALIGN='TOP'>\n";

	echo "</TD></tr>\n";
	echo "<TR>\n";
	echo "<TD VALIGN='TOP'>\n";
	echo "<INPUT TYPE='checkbox' NAME='commit' $commitcheck>\n";
	echo docpop('commit','<B>Commit to Database</B>');
	echo "";
	echo "<br>";

	echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' VALUE='$nproc' onChange='estimatetime()'>\n";
	echo "Number of Processors";
	echo "<br/>\n";

	echo "</TD></tr>\n</table>\n";
	echo "</TD>\n";
	echo "<TD CLASS='tablebg'>\n";
	echo "  <TABLE cellpading='5' BORDER='0'>\n";
	echo "  <TR><TD VALIGN='TOP'>\n";

	if  (!$apix) {
        	echo "<font color='#DD3333' size='-2'>WARNING: These values will not be checked!<br />\n";
		echo "Make sure you are within the limitations of the box size</font><br />\n";
	}

	echo "<br/>\n";
	echo "<b>Limiting numbers</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='clipdiam' VALUE='$clipdiam' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('clipdiam','Unbinned Clip diameter');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('partbin','Particle binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<br/>\n";
	echo "<b>Filters</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass' onChange='estimatetime()'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass' onChange='estimatetime()'>\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<br/>\n";
	echo "<b>Job parameters</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numref' VALUE='$numref' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('numref','Number of References');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='angle' VALUE='$angle' SIZE='4' onChange='estimatetime()'>\n";
	echo docpop('angleinc','Angular Increment');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='maxiter' VALUE='$maxiter' SIZE='4'>\n";
	echo docpop('xmippmaxiter','Maximum number of iterations');
	echo "<br/>\n";


	echo "<INPUT TYPE='checkbox' NAME='mirror' onChange='estimatetime()' $mirror>\n";
	echo docpop('mirror','Use Mirrors in Alignment');
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='savemem' onChange='estimatetime()' $savemem>\n";
	echo docpop('mlsavemem','Save memory by checking less shifts');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='fast' onClick='estimatetime(this)' checked disabled>\n";
	echo docpop('fastmode','Fast Mode Setting');
	echo "<br/>\n";

	echo "Search space reduction criteria";
	echo "<br/>\n";
	echo "&nbsp;&nbsp;<select name='fastmode' $fastmode";
	if (!$fast) echo " disabled";
	echo ">\n";
	$values = array('normal'=>'Normal search', 'narrow'=>'Faster, narrower search', 'wide'=>'Slower, longer search');
	foreach ($values as $val => $desc) {
		$checkselection = ($_POST['fastmode']==$val) ? 'selected' : '';
		echo " <option value=$val $checkselection>$desc</option>\n";
	}
	echo "</select>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	echo "Convergence stopping criteria";
	echo "<br/>\n";
	echo "&nbsp;&nbsp;<select name='converge' $converge >\n";
	$values = array('normal'=>'Normal search', 'fast'=>'Faster, shorter search', 'slow'=>'Slower, longer search');
	foreach ($values as $val => $desc) {
		$checkselection = ($_POST['converge']==$val) ? 'selected' : '';
		echo " <option value='$val' $checkselection>$desc</option>\n";
	}
	echo "</select>\n";
	echo "<br/>\n";

	echo docpop('noisedistribution','Noise distribution type:');
	echo "<br/>\n";
	echo "<input type='radio' name='distribution' value='gauss' ";
	echo ($distributionval == 'gauss') ? 'checked' : '';
	echo ">Gaussian\n";	
	echo "<input type='radio' name='distribution' value='student' ";
	echo ($distributionval == 'student') ? 'checked' : '';
	echo ">Student's T\n";	

	echo "<br/>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "Time estimate for first iteration: ";
	echo "<INPUT TYPE='text' NAME='timeestimate' SIZE='16' onFocus='this.form.elements[0].focus()'>\n";
	echo "<br/>\n";
	echo getSubmitForm("Run Max Like Alignment");
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	echo referenceBox("Maximum-likelihood multi-reference refinement for electron microscopy images.", 2005, 
		"Scheres SH, Valle M, Nuñez R, Sorzano CO, Marabini R, Herman GT, Carazo JM.", 
		"J Mol Biol.", 348, 1, 15808859, false, false, "img/xmipp_logo.png");

	echo referenceBox("Fast maximum-likelihood refinement of electron microscopy images.", 2005, 
		"Scheres SH, Valle M, Carazo JM.", "Bioinformatics.", 21, 
		"Suppl 2", 16204112, false, false, "img/xmipp_logo.png");

	processing_footer();
	exit;
}

function runMaxLikeAlign() {
	$expId=$_GET['expId'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$numref=$_POST['numref'];
	$angle=$_POST['angle'];
	$clipdiam=$_POST['clipdiam'];
	$maxiter=$_POST['maxiter'];
	$bin=$_POST['bin'];
	$description=$_POST['description'];
	//$fast = ($_POST['fast']=="on") ? true : false;
	$fast = true;
	$fastmode = $_POST['fastmode'];
	$converge = $_POST['converge'];
	$mirror = ($_POST['mirror']=="on") ? true : false;
	$savemem = ($_POST['savemem']=="on") ? true : false;
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;
	$distribution = $_POST['distribution'];

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	//make sure a session was selected

	if (!$description)
		createMaxLikeAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	if ($nproc > 16)
		createMaxLikeAlignForm("<B>ERROR:</B> Let's be reasonable with the nubmer of processors, less than 16 please");

	//make sure a stack was selected
	if (!$stackid)
		createMaxLikeAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createMaxLikeAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createMaxLikeAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than or equal to the number of particles in the stack ($totprtls)");


	if ($clipdiam) {
		if ($clipdiam > $boxsz) {
			// Clip size too big
			createMaxLikeAlignForm("<B>ERROR:</B> Clipping diameter ($clipdiam pixels)"
				." must be less than  or equal to the stack boxsize ($boxsz pixels)");
		} else if ($clipdiam == $boxsz) {
			// No clipping needed
			$binclipdiam = '';
		} else {
			// Clipping requested
			$binclipdiam = floor($clipdiam/($bin*2.0))*2;
		}
	}

	// determine calc time
	$stackdata = $particle->getStackParams($stackid);
	$boxsize = $stackdata['boxsize'];
	$secperiter = 0.12037;
	$calctime = ($numpart/1000.0)*$numref*($boxsize/$bin)*($boxsize/$bin)/$angle*$secperiter/$nproc;
	if ($mirror) $calctime *= 2.0;
	// kill if longer than 10 hours
	if ($calctime > 10.0*3600.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 10 hours<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/3600.0,2)." hours\n");
	elseif (!$fast && $calctime > 1800.0)
		createMaxLikeAlignForm("<b>ERROR:</b> Run time per iteration greater than 30 minutes without fast mode<br/>"
			."<b>Estimated calc time:</b> ".round($calctime/60.0,2)." minutes\n");

	// setup command
	$command ="maxlikeAlignment.py ";
	$command.="--description=\"$description\" ";
	$command.="--stack=$stackid ";
	if ($binclipdiam != '') $command.="--clip=$binclipdiam ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-ref=$numref ";
	$command.="--bin=$bin ";
	$command.="--angle-interval=$angle ";
	$command.="--max-iter=$maxiter ";
	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	if ($fast) {
		$command.="--fast ";
		$command.="--fast-mode=$fastmode ";
	} else
		$command.="--no-fast ";
	if ($mirror)
		$command.="--mirror ";
	else
		$command.="--no-mirror ";
	if ($savemem)
		$command.="--savemem ";
	else
		$command.="--no-savemem ";
	if ($distribution == "student")
		$command.="--student ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	$command .= "--converge=$converge ";

	// setup header information
	$headinfo = "";
	$headinfo .= referenceBox("Maximum-likelihood multi-reference refinement for electron microscopy images.", 2005, 
		"Scheres SH, Valle M, Nuñez R, Sorzano CO, Marabini R, Herman GT, Carazo JM.", 
		"J Mol Biol.", 348, 1, 15808859, false, false, "img/xmipp_logo.png");
	$headinfo .= referenceBox("Fast maximum-likelihood refinement of electron microscopy images.", 2005, 
		"Scheres SH, Valle M, Carazo JM.", "Bioinformatics.", 21, 
		"Suppl 2", 16204112, false, false, "img/xmipp_logo.png");
	$headinfo .= "<table width='600' class='tableborder' border='1'>";
	$headinfo .= "<tr><td colspan='2'><br/>\n";
	if ($calctime < 60)
		$headinfo .= "<span style='font-size: larger; color:#999933;'>\n<b>Estimated calc time:</b> "
			.round($calctime,2)." seconds\n";
	elseif ($calctime < 3600)
		$headinfo .= "<span style='font-size: larger; color:#33bb33;'>\n<b>Estimated calc time:</b> "
			.round($calctime/60.0,2)." minutes\n";
	else
		$headinfo .= "<span style='font-size: larger; color:#bb3333;'>\n<b>Estimated calc time:</b> "
			.round($calctime/3600.0,2)." hours\n";
	$headinfo .= "for the first iteration</span><br/>"
		."<i>it gets much faster after the first iteration with the fast mode</i><br/><br/></td></tr></table><br/>\n";

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createMaxLikeAlignForm($errors);
	exit;

}
?>
