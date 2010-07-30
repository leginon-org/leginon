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
		$projectId=getProjectId();
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
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;
	$firststack = $particle->getStackParams($stackIds[0]['stackid']);
//	$initparts = $particle->getNumStackParticles($stackIds[0]['stackid']);
	
	$javascript .= "<script type='text/javascript'>
	function checkalignment() {
		if (o=document.viewerform.alignment_type) {
			aligntype=o.options[o.selectedIndex].value
			if (o_a=document.viewerform.first_alignment) {
				if (aligntype=='all') {
					o_a.disabled=false
				} else {
					o_a.disabled=true
				}
			}
			if (o_no=document.viewerform.num_orientations) {
				if (aligntype=='brute_force') {
					o_no.disabled=false
				} else {
					o_no.disabled=true
				}
			}
		}
	}

	function disable_brute_force_orientations() {
		if (o=document.viewerform.num_orientations) {
			o.disabled=true
		}
		else {
			o.disabled=false
		}
	}

	function switch_defaults(stackval) {
		var stackArray = stackval.split('|--|');
		stackArray[3] = stackArray[3].replace(/\,/g,'');
		document.viewerform.numpart.value = stackArray[3];
	}

	</script>\n";
	
	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
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
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'multiRefAlign'.($alignruns+1)))
		$alignruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'multiRefAlign'.($alignruns+1);
	$rundescrval = $_POST['description'];
	$stackinfo=explode('|--|',$_POST['stackval']);
	$stackidval=$stackinfo[0];
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	// alignment params
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : "";
	$iters = ($_POST['iters']) ? $_POST['iters'] : 5;
	if ($iters > 5) $iters = 5; // maximum number allowed by imagic
	$lowpass = ($_POST['lowpass']) ? $_POST['lowpass'] : 10;
	$highpass = ($_POST['highpass']) ? $_POST['highpass'] : 2000;
	$lprefs = ($_POST['lowpass_refs']) ? $_POST['lowpass_refs'] : 15;
	$threshrefs = ($_POST['threshrefs']) ? $_POST['threshrefs'] : -999;
	$maskrad_refs = ($_POST['maskrad_refs']) ? $_POST['maskrad_refs'] : 0.9;
	$max_shift_orig = ($_POST['max_shift_orig']) ? $_POST['max_shift_orig'] : 0.2;
	$samp_param = ($_POST['samp_param']) ? $_POST['samp_param'] : 12;
	$minrad = ($_POST['minrad']) ? $_POST['minrad'] : 0.0;
	$maxrad = ($_POST['maxrad']) ? $_POST['maxrad'] : 0.9;
	$boxsz = $firststack['boxsize'];
	$bestbin = floor($boxsz/100);
	$bin = ($_POST['bin']) ? $_POST['bin'] : $bestbin;
	$mirror = ($_POST['mirror']=="on" || !$_POST['process']) ? 'checked' : '';
	$center = ($_POST['center']=="on" || !$_POST['process']) ? 'checked' : '';
	$alignment_type = ($_POST['alignment_type']) ? $_POST['alignment_type'] : 'all';
	$first_alignment = ($_POST['first_alignment']) ? $_POST['first_alignment'] : 'rotation_first';
	$num_orientations = ($_POST['num_orientations']) ? $_POST['num_orientations'] : '17';

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
		</tr>\n";
		echo"<TR>
			<TD VALIGN='TOP'>";
		echo 	docpop('description','<b>Alignment Description:</b>');
		echo"   <br>
			<TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
			</TD>
		</tr>\n";
		echo"<TR>
			<TD VALIGN='TOP'>";
		echo 	docpop('outdir','<b>Output Directory:</b>');	
		echo "  <br>	 
			<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
			</TD>
		</tr>
		<TR>
			<td>\n";

	// select stack
	if (!$stackIds) {
		echo"
		<FONT COLOR='RED'><B>No Stacks for this Session</B></FONT>\n";
	}
	else {
		echo docpop('stack', "<B>Particles:</B>");
		echo "<br/>";
		$particle->getStackSelector($stackIds,$stackidval,'switch_defaults(this.value)');
	}
	echo "<br><br>\n";
	// select template stack
	if (!$templateIds) { 
		echo"<FONT COLOR='red'><B>No Template Stacks for this project</B></FONT>\n";
	}
	else {
		echo docpop('templatestack', "<B>Template Stacks:</B>");
		echo"
		<br><SELECT NAME='templatestackid'>\n";
		foreach ($templateIds as $temp) {
			$templateId = $temp['DEF_id'];
			$templatename = $temp['templatename'];
			$apix = $temp['apix'];
			$boxsz = $temp['boxsize'];
			$totprtls = "";
			if ($temp['cls_avgs'] == 1) $type = "Class Averages";
			elseif ($temp['forward'] == 1) $type = "Forward Projections";
			echo "<OPTION VALUE='$templateId|--|$apix|--|$boxsz|--|$totprtls|--|$type'";
			if ($templateidval == $templateId) echo " SELECTED";
			echo ">$templateId: $templatename ($apix &Aring;/pixel, $boxsz pixels)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
		
	echo"
		</TD>
	</tr>";
	echo"
	<TR>
		<TD VALIGN='TOP'>
		<INPUT TYPE='checkbox' NAME='commit' $commitcheck>";
	echo 	docpop('commit', " <B>Commit to Database</B><br>");
	// number of processors defaulted to 8
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 8;
	echo "<INPUT TYPE='text' SIZE='5' NAME='nproc' VALUE=$nproc> Number of Processors";
	echo"
		</TD>
	</tr>";
	echo"
	</table>
	</TD>
	<TD CLASS='tablebg'>
	<TABLE CELLPADDING='5' BORDER='0'>
	<TR>";
	echo"
		<TD VALIGN='TOP'>
		<B>Particle Params:</B></A><br>";
	echo"
		<INPUT TYPE='text' NAME='lowpass' SIZE='5' VALUE='$lowpass'>";
	echo	docpop('lpstackval', " Low Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><br>");
	echo"
		<INPUT TYPE='text' NAME='highpass' SIZE='5' VALUE='$highpass'>";
	echo	docpop('hpstackval', " High Pass Filter <FONT SIZE='-1'>(in &Aring;ngstroms)</FONT><br>");
	echo"
		<INPUT TYPE='text' NAME='bin' SIZE='5' VALUE='$bin'>";
	echo 	docpop('partbin', " Particle Binning<br>");
	echo"
		</TD>
	</tr>
	<TR>
		<TD VALIGN='TOP' WIDTH=320>
		<B>Reference-Specific Params (optional):</B><br>";
	echo"  
		<INPUT TYPE='text' NAME='lowpass_refs' VALUE='$lprefs' SIZE='4'>";
	echo	docpop('lpfilt_refs', " Low Pass Filter References <FONT SIZE='-1'>(&Aring;ngstroms)</FONT><br>");
	echo"
		<INPUT TYPE='text' NAME='thresh_refs' VALUE='$threshrefs' SIZE='4'>";
	echo 	docpop('thresh_refs', " Threshold Reference Pixel values<br>");
	echo"
		<INPUT TYPE='text' NAME='maskrad_refs' VALUE='$maskrad_refs' SIZE='4'>";
	echo 	docpop('maskrad_refs', " Apply a radial mask to references<br>");
	echo"
	</tr>
	<TR>
		<TD VALIGN='TOP'>
		<B>Alignment Params:</B></A><br>";
	
	echo "<SELECT name='alignment_type' onchange='checkalignment()'>";
	echo "<OPTION VALUE='all'>rotational & translational</OPTION>";
	echo "<OPTION VALUE='rotational'>rotational</OPTION>";
	echo "<OPTION VALUE='translational'>translational</OPTION>";
	echo "<OPTION VALUE='horizontal'>horizontal</OPTION>";
	echo "<OPTION VALUE='vertical'>vertical</OPTION>";
	echo "<OPTION VALUE='brute_force'>brute force</OPTION>";
	echo "</SELECT>\t";
	
	echo "<SELECT name='first_alignment'>";
	echo "<OPTION VALUE='rotation_first'>rotation_first</OPTION>";
	echo "<OPTION VALUE='translation_first'>translation_first</OPTION>";
	echo "</SELECT><br>";
	
	echo"
		<INPUT TYPE='text' NAME='num_orientations' VALUE='$num_orientations' SIZE='4'>";
	echo 	docpop('num_orientations', " Number of Orientations <font size='-1'>(brute force only)</font><br>");
	echo"
		<INPUT TYPE='text' NAME='iters' VALUE='$iters' SIZE='4'>";
	echo 	docpop('numiter_mra', " Iterations<br>");
	echo"
		<INPUT TYPE='text' NAME='max_shift_orig' VALUE='$max_shift_orig' SIZE='4'>";
	echo 	docpop('shift_orig', " Maximum radial shift<br>");
	echo"
		<INPUT TYPE='text' NAME='samp_param' VALUE='$samp_param' SIZE='4'>";
	echo 	docpop('samp_par', " Sampling Parameter<br>");
	echo"
		<INPUT TYPE='text' NAME='minrad' VALUE='$minrad' SIZE='4'>";
	echo 	docpop('minrad', " Minimum Inner radius<br>");
	echo"
                <INPUT TYPE='text' NAME='maxrad' VALUE='$maxrad' SIZE='4'>";
	echo 	docpop('maxrad', " Maximum Inner radius<br>");
	echo"
		<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>";
	echo	docpop('numpart', " Number of Particles to Use<br>");
	echo"
		<INPUT TYPE='checkbox' NAME='inverttempl' $inverttempl>";
	echo 	docpop('invert', " Invert reference density before alignment<br>");
	echo"
		<INPUT TYPE='checkbox' NAME='center' $center>";
	echo	docpop('center', " Center particles prior to MRA<br>");
	echo"
		<INPUT TYPE='checkbox' NAME='mirror' $mirror>";
	echo	docpop('mirror', " Mirror Alignment<br>");
	echo"
		</TD>
	</tr>
	</tr>
	</table>
	</TD>
	</tr>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>";
	echo getSubmitForm("Run Multi Reference Alignment");
	echo "
	  </TD>
	</tr>
	</table>
	</FORM>
	</CENTER>\n";

	// first time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switch_defaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	processing_footer();
	exit;
}

//***************************************
//***************************************
//***************************************
//***************************************
function runAlignment() {
	/* *******************
	PART 1: Get variables
	******************** */
	$nproc = $_POST['nproc'];
	$stackval = $_POST['stackval'];
	list($stackid,$apix_s,$boxsz_s,$totprtls_s) = split('\|--\|', $stackval);
	$templatestackval=$_POST['templatestackid'];
	list($templatestackid,$apix_t,$boxsz_t,$totprtls_t,$type) = split('\|--\|',$templatestackval);
	
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
	$center = ($_POST['center']=="on" || !$_POST['process']) ? 'checked' : '';
	$alignment_type = $_POST['alignment_type'];
	$first_alignment = $_POST['first_alignment'];
	$num_orientations = $_POST['num_orientations'];
	$description=$_POST['description'];
	$numpart=$_POST['numpart'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if (!$description) createAlignmentForm("<B>ERROR:</B> Enter a brief description of the alignment run");
	//make sure a stack was selected
	if (!$stackid) createAlignmentForm("<B>ERROR:</B> No stack selected");
	// make sure template stack was selected
	if (!$templatestackid) createAlignmentForm("<B>ERROR:</B> No template stack selected");

	// alignment
	if ($numpart < 1) 
		createAlignmentForm("<B>ERROR:</B> Number of particles must be at least 1");
	$particle = new particledata();
	$totprtls_s = $particle->getNumStackParticles($stackid);
	if ((int)$numpart > (int)$totprtls_s) { 
		createAlignmentForm("<B>ERROR:</B> Number of particles to align ($numpart) must be less than the number of particles in the stack ($totprtls_s)");
	}

	/* *******************
	PART 3: Create program command
	******************** */
	$command="imagicMultiReferenceAlignment.py ";
	$command.="--stackId=$stackid ";
	$command.="--templateStackId=$templatestackid ";
	$command.="--alignment_type=$alignment_type ";
	if ($first_alignment) $command.="--first_alignment=$first_alignment ";
	if ($num_orientations) $command.="--num_orientations=$num_orientations ";
	$command.="--description=\"$description\" ";

	if ($lowpass) $command.="--lowpass=$lowpass ";
	if ($highpass) $command.="--highpass=$highpass ";
	if ($bin) $command.="--bin=$bin ";
	
	if ($thresh_refs && $maskrad_refs) {
		$command.="--refs ";
		$command.="--thresh_refs=$thresh_refs ";
		$command.="--maskrad_refs=$maskrad_refs ";
	}
	else $command.="--no-refs ";

	if ($mirror) $command.="--mirror ";
	else $command.="--no-mirror ";
	if ($center) $command.="--center ";
	$command.="--max_shift_orig=$max_shift_orig ";
	$command.="--samp_param=$samp_param ";
	$command.="--minrad=$minrad ";
	$command.="--maxrad=$maxrad ";
	$command.="--numiter=$iters ";
	$command.="--num-part=$numpart ";

	if ($inverttempl) $command.="--invert-templates ";
	$command.="--nproc=$nproc ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	// Add reference to top of the page
	$headinfo .= imagicRef();

	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'partalign', $nproc);
	// if error display them
	if ($errors)
		createAlignmentForm($errors);
	exit;
}


?>
