<?php
/**
 *      The Leginon software is Copyright under 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *
 *      Simple viewer to view a image using mrcmodule
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/forms/remoteJobParamsForm.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runCL2DAlign();
} else {
	createCL2DAlignForm();
}


function createCL2DAlignForm($extra=false, $title='runXmippCL2D.py Launcher', $heading='Clustering 2D Alignment') {
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
	//number of references is the square root of the number of particles divided by 10
	$javascript .= "	var bestref = Math.floor(Math.log(stackArray[3])/2)*2;\n";
	$javascript .= "	if (bestref < 2) {\n";
	$javascript .= "		var bestref = 2 ;}\n";
	$javascript .= "	document.viewerform.numref.value = bestref;\n";
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
		\n";
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
		$sessionpath=getBaseAppionPath($sessioninfo).'/align/';
	}

	// set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'cl2d'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'cl2d'.($alignruns+1);
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = split('\|--\|',$stackidstr);
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : '10';
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : '2000';
	$numref = ($_POST['numref']) ? $_POST['numref'] : '20';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '4';
	$clipdiam = ($_POST['clipdiam']) ? $_POST['clipdiam'] : '';
	$maxiter = ($_POST['maxiter']) ? $_POST['maxiter'] : '15';
	$image2imagedistanceval = ($_POST['image2imagedistance']) ? $_POST['image2imagedistance'] : 'correlation';
	$image2clusterdistanceval = ($_POST['image2clusterdistance']) ? $_POST['image2clusterdistance'] : 'minimum';
//	$dontAlign = ($_POST['dontAlign']=='on' || !$_POST['dontAlign']) ? 'unchecked' : '';
	
	//$fast = ($_POST['fast']=='on' || !$_POST['fast']) ? 'checked' : '';
	
	
	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	
	$remoteParamsForm = new RemoteJobParamsForm($runname, $sessionpathval);
	$html.= $remoteParamsForm->generateForm();

	echo $html;	
	
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

	echo "<INPUT TYPE='text' NAME='clipdiam' VALUE='$clipdiam' SIZE='4'>\n";
	echo docpop('clipdiam','Unbinned Clip diameter');
	echo "<font size='-2'>(pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('partbin','Particle binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Particles');
	echo "<br/>\n";

	echo "<br/>\n";
	echo "<b>Filters</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='lowpass' SIZE='4' VALUE='$lowpass'>\n";
	echo docpop('lpstackval','Low Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='highpass' SIZE='4' VALUE='$highpass'>\n";
	echo docpop('hpstackval','High Pass Filter Radius');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<br/>\n";
	echo "<b>Job parameters</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numref' VALUE='$numref' SIZE='4'>\n";
	echo docpop('numrefcl2d','Number of References');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='maxiter' VALUE='$maxiter' SIZE='4'>\n";
	echo docpop('xmippmaxiter','Maximum number of iterations');
	echo "<br/>\n";

	//echo "<INPUT TYPE='checkbox' NAME='fast' checked disabled>\n";
	//echo docpop('fastmode','Fast Mode Setting');
	//echo "<br/>\n";

	echo docpop('image2imagedistance','Image to Image Distance:');
	echo "<br/>\n";
	echo "<input type='radio' name='image2imagedistance' value='correntropy' ";
	echo ($image2imagedistanceval == 'correntropy') ? 'checked' : '';
	echo ">Correntropy\n";	
	echo "<input type='radio' name='image2imagedistance' value='correlation' ";
	echo ($image2imagedistanceval == 'correlation') ? 'checked' : '';
	echo ">Correlation\n";
	echo "<br/>\n";
	
	echo docpop('image2clusterdistance','Image to Cluster Distance:');
	echo "<br/>\n";
	echo "<input type='radio' name='image2clusterdistance' value='minimum' ";
	echo ($image2clusterdistanceval == 'minimum') ? 'checked' : '';
	echo ">Minimum\n";	
	echo "<input type='radio' name='image2clusterdistance' value='intracluster' ";
	echo ($image2clusterdistanceval == 'intracluster') ? 'checked' : '';
	echo ">Intracluster\n";
	echo "<br/>\n";
	
//	echo "<INPUT TYPE='checkbox' NAME='dontAlign' unchecked>\n";
//	echo docpop('dontAlign','Dont Align Image');
//	echo "<br/>\n";
	
	echo "<br/>\n";

	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";
	echo "<br/>\n";
	echo getSubmitForm("Run CL2D Alignment", false);
	echo "  </td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	echo referenceBox("A clustering approach to multireference alignment of single-particle projections in electron microscopy.", 2010, 
		"Sorzano CO, Bilbao-Castro JR, Shkolnisky Y, Alcorlo M, Melero R, Caffarena-Fernández G, Li M, Xu G, Marabini R, Carazo JM.", 
		"J Struct Biol.", 171, 2, 20362059, false, false, "img/xmipp_logo.png");

	processing_footer();
	exit;

}


function runCL2DAlign() {
	$expId=$_GET['expId'];
	$stackval=$_POST['stackval'];
	$highpass=$_POST['highpass'];
	$lowpass=$_POST['lowpass'];
	$numpart=$_POST['numpart'];
	$numref=$_POST['numref'];
	$clipdiam=$_POST['clipdiam'];
	$maxiter=$_POST['maxiter'];
	$bin=$_POST['bin'];
	$description=$_POST['description'];
	$fast = true;
	$converge = $_POST['converge'];
	$image2imagedistanceval = $_POST['image2imagedistance'];
	$image2clusterdistanceval = $_POST['image2clusterdistance'];
//	$dontAlign = ($_POST['dontAlign']=="on") ? true : false;
	$commit = ($_POST['commit']=="on") ? true : false;

	// get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = split('\|--\|',$stackval);
	
	// verify processing host parameters
	$remoteParamForm = new RemoteJobParamsForm();
	$errorMsg .= $remoteParamForm->validate( $_POST );
	
	// Calculate the total noded required after checking that they are set in the validate
	$nproc = ($_POST['nodes'] * $_POST['ppn']);
	

	if (!$description)
		createCL2DAlignForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");

	//make sure a stack was selected
	if (!$stackid)
		createCL2DAlignForm("<B>ERROR:</B> No stack selected");

	// classification
	if ($numpart < 10)
		createCL2DAlignForm("<B>ERROR:</B> Must have more than 10 particles");

	// check num of particles
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createCL2DAlignForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than or equal to the number of particles in the stack ($totprtls)");


	if ($clipdiam) {
		if ($clipdiam > $boxsz) {
			// Clip size too big
			createCL2DAlignForm("<B>ERROR:</B> Clipping diameter ($clipdiam pixels)"
				." must be less than  or equal to the stack boxsize ($boxsz pixels)");
		} else if ($clipdiam == $boxsz) {
			// No clipping needed
			$binclipdiam = '';
		} else {
			// Clipping requested
			$binclipdiam = floor($clipdiam/($bin*2.0))*2;
		}
	}

	// setup command
	$command ="runXmippCL2D.py ";
	$command.="--stack=$stackid ";
	if ($binclipdiam != '') $command.="--clip=$binclipdiam ";
	if ($lowpass != '') $command.="--lowpass=$lowpass ";
	if ($highpass != '') $command.="--highpass=$highpass ";
	$command.="--num-part=$numpart ";
	$command.="--num-ref=$numref ";
	$command.="--bin=$bin ";
	$command.="--max-iter=$maxiter ";
	if ($nproc && $nproc>1)
		$command.="--nproc=$nproc ";
	if ($fast) 
		$command.="--fast ";
	
//	if ($dontAlign)
//		$command.="--dontAlignImages ";
	if ($image2clusterdistanceval == "minimum")
		$command.="--classical_multiref ";
	if ($image2imagedistanceval == "correlation")
		$command.="--correlation ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	//$command .= "--converge=$converge ";
	
	// collect processing host parameters
	$command .= $remoteParamForm->buildCommand( $_POST );

	// setup header information
	$headinfo = "";
	$headinfo .= referenceBox("A clustering approach to multireference alignment of single-particle projections in electron microscopy.", 2010, 
		"Sorzano CO, Bilbao-Castro JR, Shkolnisky Y, Alcorlo M, Melero R, Caffarena-Fernández G, Li M, Xu G, Marabini R, Carazo JM.", 
		"J Struct Biol.", 171, 2, 20362059, false, false, "img/xmipp_logo.png");
	
	$headinfo .= "<table width='600' class='tableborder' border='1'>";
	$headinfo .= "<tr><td colspan='2'><br/>\n";
	
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);

	// if error display them
	if ($errors)
		createCL2DAlignForm($errors);
	exit;

}
?>

