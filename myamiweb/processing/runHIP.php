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

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runHIP();
} else {
	createHIPForm();
}

function createHIPForm($extra=false, $title='HIP.py Launcher', $heading='Helical Image Processing') {
	// Check if coming directly from a session
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

	// Connect to particle database
	$particle = new particledata();
	$stackIds = $particle->getStackIds($sessionId);
	$alignrunsarray = $particle->getAlignStackIds($sessionId);
	$alignruns = ($alignrunsarray) ? count($alignrunsarray) : 0;

	$javascript = "<script src='../js/viewer.js'></script>\n";
	// Javascript to switch the defaults based on the stack
	$javascript .= "<script>\n";
	$javascript .= "
		function switchDefaults(stackval) {
			var stackArray = stackval.split('|--|');
			stackArray[3] = stackArray[3].replace(/\,/g,'');
			document.viewerform.numpart.value = stackArray[3];
			var calcreplen = Math.ceil(stackArray[2]*stackArray[1]/2);
			document.viewerform.replen.value = calcreplen;
			document.viewerform.xlngth.value = stackArray[2];
			var calcpad = Math.pow(2, Math.ceil((Math.log(stackArray[2]))/(Math.log(2))));
			document.viewerform.padval.value = calcpad;
			step = stackArray[1];
			estimateyht2(step);
		}
		function newmandir() {
			if (document.viewerform.prehip.checked) {
				var runname = document.viewerform.runname.value;
				var path = document.viewerform.outdir.value;
				document.viewerform.mandir.value = (path+runname);
			}
		}
		function estimatexlngth(step) {
			var replen = document.viewerform.replen.value;
			var calcxlngth = Math.floor((replen/step)*2);
			document.viewerform.xlngth.value = calcxlngth;
			var calcpad = Math.pow(2, Math.ceil((Math.log(calcxlngth))/(Math.log(2))));
			document.viewerform.padval.value = calcpad;
		}
		function estimateyht2(step) {
			var diam = document.viewerform.diam.value;
			var calcyht2 = Math.floor(diam/step);
			var po2yht2 = Math.pow(2, Math.ceil((Math.log(calcyht2))/(Math.log(2))));
			document.viewerform.yht2.value = po2yht2
		}
		function disablecommit(){
			if (document.viewerform.prehip.checked){
				document.viewerform.commit.disabled=true;
				document.viewerform.commit.checked=false;
				document.viewerform.nfold.disabled=false;
				document.viewerform.maxll.disabled=false;
				document.viewerform.maxbo.disabled=false;
				document.viewerform.risecheck.disabled=false;
				document.viewerform.llbocheck.disabled=false;
				var runname = document.viewerform.runname.value;
				var path = document.viewerform.outdir.value;
				document.viewerform.mandir.value = (path+runname);
				alert('PreHIP will NOT run and results will NOT be committed! Select Just Show Command and copy and paste the command into a unix shell. Limit number of filament segments to reduce processing time.');
			}	
			else {
				document.viewerform.commit.disabled=false;
				document.viewerform.commit.checked=true;
				document.viewerform.nfold.disabled=true;
				document.viewerform.maxll.disabled=true;
				document.viewerform.maxbo.disabled=true;
				document.viewerform.risecheck.disabled=true;
				document.viewerform.llbocheck.disabled=true;
				document.viewerform.rise.disabled=true;
				document.viewerform.twist.disabled=true;
				document.viewerform.ll1.disabled=true;
				document.viewerform.bo1.disabled=true;
				document.viewerform.ll2.disabled=true;
				document.viewerform.bo2.disabled=true;
				document.viewerform.mandir.value = '';
			}
		}
		function enablerise(){
			if (document.viewerform.risecheck.checked){
				document.viewerform.llbocheck.checked=false;
				document.viewerform.rise.disabled=false;
				document.viewerform.twist.disabled=false;
				document.viewerform.ll1.disabled=true;
				document.viewerform.bo1.disabled=true;
				document.viewerform.ll2.disabled=true;
				document.viewerform.bo2.disabled=true;
			} else {
				document.viewerform.llbocheck.checked=true;
				document.viewerform.rise.disabled=true;
				document.viewerform.twist.disabled=true;
			}
		}
		function enablellbo(){
			if (document.viewerform.llbocheck.checked){
				document.viewerform.risecheck.checked=false;
				document.viewerform.ll1.disabled=false;
				document.viewerform.bo1.disabled=false;
				document.viewerform.ll2.disabled=false;
				document.viewerform.bo2.disabled=false;
				document.viewerform.rise.disabled=true;
				document.viewerform.twist.disabled=true;
			} else {
				document.viewerform.risecheck.checked=true;
				document.viewerform.ll1.disabled=true;
				document.viewerform.bo1.disabled=true;
				document.viewerform.ll2.disabled=true;
				document.viewerform.bo2.disabled=true;
			}
		}\n";
	$javascript .= "</script>\n";

	$javascript .= writeJavaPopupFunctions('appion');	

	processing_header($title,$heading,$javascript);
	// Write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
  
	echo "<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=preg_replace("%leginon%","appion",$sessionpath);
		$sessionpath=preg_replace("%rawdata%","hip/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
	}

	// Set any existing parameters in form
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'hip'.($alignruns+1)))
		$alignruns += 1;
	$runname = ($_POST['runname']) ? $_POST['runname'] : 'hip'.($alignruns+1);
	$mandir = $_POST['mandir'] ? $_POST['mandir'] : '';
	$description = $_POST['description'];
	$stackidstr = $_POST['stackval'];
	list($stackidval) = preg_split('%\|--\|%',$stackidstr);
	// Set commit on by default when first loading page, else set
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'checked' : '';
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : '1';
	$numpart = ($_POST['numpart']) ? $_POST['numpart'] : '3000';
	$replen = ($_POST['replen']) ? $_POST['replen'] : '';
	$subunits = ($_POST['subunits']) ? $_POST['subunits'] : '';
	$diam = ($_POST['diam']) ? $_POST['diam'] : '';
	$diaminner = ($_POST['diaminner']) ? $_POST['diaminner'] : '';
	$xlngth = ($_POST['xlngth']) ? $_POST['xlngth'] : '';
	$yht2 = ($_POST['yht2']) ? $_POST['yht2'] : '';
	$padval = ($_POST['padval']) ? $_POST['padval'] : '';
	$rescut = ($_POST['rescut']) ? $_POST['rescut'] : '25';
	$filval = ($_POST['filval']) ? $_POST['filval'] : '200';
	$bin = ($_POST['bin']) ? $_POST['bin'] : '1';
	$conchg = ($_POST['conchg']=='on' || !$_POST['process']) ? 'checked' : '';
	$prehip = ($_POST['prehip']=='off' || !$_POST['process']) ? '' : '';
	$risecheck = ($_POST['risecheck']) ?  'checked': 'disabled';
	$rise = ($_POST['rise']) ? $_POST['rise'] : '';
	$twist = ($_POST['twist']) ? $_POST['twist'] : '';
	$llbocheck = ($_POST['llbocheck']) ? 'checked' : 'disabled';
	$ll1 = ($_POST['ll1']) ? $_POST['ll1'] : '';
	$bo1 = ($_POST['bo1']) ? $_POST['bo1'] : '';
	$ll2 = ($_POST['ll2']) ? $_POST['ll2'] : '';
	$bo2 = ($_POST['bo2']) ? $_POST['bo2'] : '';
	$nfold = ($_POST['nfold']) ? $_POST['nfold'] : '1';
	$maxll = ($_POST['maxll']) ? $_POST['maxll'] : '100';
	$maxbo = ($_POST['maxbo']) ? $_POST['maxbo'] : '';


	echo "<table border='0' class='tableborder'>\n<tr><td valign='top'>\n";
	echo "<table border='0' cellpadding='5'>\n";
	echo "<tr><td>\n";
	echo openRoundBorder();
	echo docpop('runname','<b>HIP Run Name:</b>');
	echo "<input type='text' name='runname' value='$runname' onChange='newmandir()'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('mandir','<b>Directory Containing Mandatory Files:</b>');
	echo "<br />\n";
	echo "<input type='text' name='mandir' value='$mandir' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('descr','<b>Description of HIP Run:</b>');
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
		echo docpop('stack','<b>Select a list of filaments to use</b>');
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

	echo "<INPUT TYPE='text' NAME='nproc' SIZE='4' DISABLED VALUE='$nproc'>\n";
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
	echo "<b>Filament Parameters</b>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='numpart' VALUE='$numpart' SIZE='4'>\n";
	echo docpop('numpart','Number of Filament Segments');
	echo "<br/>\n";

//Removed onChange='estimatexlngth(step)' from replen in case the box size is not an exact # of helical repeats
	echo "<INPUT TYPE='text' NAME='replen' VALUE='$replen' SIZE='4'>\n";
	echo docpop('replen','Repeat Length');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='subunits' VALUE='$subunits' SIZE='4'>\n";
	echo docpop('subunits','Subunits per Repeat');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4' onChange='estimateyht2(step)'>\n";
	echo docpop('diam','Diameter');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='diaminner' VALUE='$diaminner' SIZE='4'>\n";
	echo docpop('diaminner','Inner Diameter');
	echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
	echo "<br/>\n";


	echo "<br/>\n";
	echo "<b>Processing Parameters</b>\n";
	echo "<br/>\n";

//Hiding this input param because it should always be the same as boxsize
	echo "<INPUT TYPE='hidden' NAME='xlngth' VALUE='$xlngth' SIZE='4'>\n";
	//echo docpop('xlngth','Filament Segment Length');
	//echo "<font size='-2'>(Pixels)</font>\n";
	//echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='yht2' SIZE='4' VALUE='$yht2'>\n";
	echo docpop('yht2','Box Height');
	echo "<font size='-2'>(Pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='padval' SIZE='4' VALUE='$padval'>\n";
	echo docpop('padval','Pad Value');
	echo "<font size='-2'>(Pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='rescut' SIZE='4' VALUE='$rescut'>\n";
	echo docpop('rescut','Phase Residual Cutoff');
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='filval' SIZE='4' VALUE='$filval'>\n";
	echo docpop('filval','Filter Value');
	echo "<font size='-2'>(Pixels)</font>\n";
	echo "<br/>\n";

	echo "<INPUT TYPE='text' NAME='bin' SIZE='4' VALUE='$bin'>\n";
	echo docpop('partbin','Binning');
	echo "<br/>\n";

	echo "<INPUT TYPE='checkbox' NAME='conchg' $conchg>\n";
	echo docpop('conchg','Contrast Change');
	echo "<br/>\n";


	echo "<br/>\n";
	echo "<b>Indexing Parameters</b>\n";
	echo "<br/>\n";

	if($_POST){
		$prehip = ($_POST['prehip'] == 'on') ? 'checked' : '';
		$risecheck = ($_POST['risecheck'] == 'on') ? 'checked' : '';
		$llbocheck = ($_POST['llbocheck'] == 'on') ? 'checked' : '';
	}

	echo "<INPUT TYPE='checkbox' NAME='prehip' onClick='disablecommit(this)' $prehip>\n";
	echo docpop('prehip','Run PreHip to Setup Mandatory Files');
	echo "<br/>\n";
	echo "<br/>\n";

	if ($prehip == 'checked') {
		echo "<INPUT TYPE='text' NAME='nfold' VALUE='$nfold' SIZE='4'>\n";
		echo docpop('nfold','N-fold');
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='maxll' VALUE='$maxll' SIZE='4'>\n";
		echo docpop('maxll','Maximum Layer Line');
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='maxbo' VALUE='$maxbo' SIZE='4'>\n";
		echo docpop('maxbo','Maximum Bessel Order');
		echo "<br/>\n";
	} else {
		echo "<INPUT TYPE='text' NAME='nfold' DISABLED VALUE='$nfold' SIZE='4'>\n";
		echo docpop('nfold','N-fold');
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='maxll' DISABLED VALUE='$maxll' SIZE='4'>\n";
		echo docpop('maxll','Maximum Layer Line');
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='maxbo' DISABLED VALUE='$maxbo' SIZE='4'>\n";
		echo docpop('maxbo','Maximum Bessel Order');
		echo "<br/>\n";
	}

	echo "<br/>\n";
	echo "<INPUT TYPE='radio' NAME='risecheck' onClick='enablerise(this)' $risecheck >\n";
	echo docpop('risecheck','Use Rise and Twist');
	echo "<br/>\n";

	if ($risecheck == 'checked') {
		echo "<INPUT TYPE='text' NAME='rise' SIZE='4' VALUE='$rise' style='background:#ffffff'>\n";
		echo 'Rise ';
		echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='twist' SIZE='4' VALUE='$twist' style='background:#ffffff'>\n";
		echo 'Twist ';
		echo "<font size='-2'>(Degrees)</font>\n";
		echo "<br/>\n";
	} else {
		echo "<INPUT TYPE='text' NAME='rise' SIZE='4' DISABLED >\n";
		echo 'Rise ';
		echo "<font size='-2'>(&Aring;ngstroms)</font>\n";
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='twist' SIZE='4' DISABLED >\n";
		echo 'Twist ';
		echo "<font size='-2'>(degrees)</font>\n";
		echo "<br/>\n";
	}

	echo "<br/>\n";
	echo "<INPUT TYPE='radio' NAME='llbocheck' onClick='enablellbo(this)' $llbocheck>\n";
	echo docpop('llbocheck','Use Layer Line/Bessel Order');
	echo "<br/>\n";

	if ($llbocheck == 'checked') {
		echo "<INPUT TYPE='text' NAME='ll1' SIZE='4' VALUE='$ll1' style='background:#ffffff'>\n";
		echo '(1,0) LL  ';

		echo "<INPUT TYPE='text' NAME='bo1' SIZE='4' VALUE='$bo1' style='background:#ffffff'>\n";
		echo '(1,0) BO';
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='ll2' SIZE='4' VALUE='$ll2' style='background:#ffffff'>\n";
		echo '(0,1) LL  ';

		echo "<INPUT TYPE='text' NAME='bo2' SIZE='4' VALUE='$bo2' style='background:#ffffff'>\n";
		echo '(0,1) BO';
		echo "<br/>\n";
	} else {
		echo "<INPUT TYPE='text' NAME='ll1' SIZE='4' DISABLED >\n";
		echo '(1,0) LL  ';

		echo "<INPUT TYPE='text' NAME='bo1' SIZE='4' DISABLED >\n";
		echo '(1,0) BO';
		echo "<br/>\n";

		echo "<INPUT TYPE='text' NAME='ll2' SIZE='4' DISABLED >\n";
		echo '(0,1) LL  ';

		echo "<INPUT TYPE='text' NAME='bo2' SIZE='4' DISABLED >\n";
		echo '(0,1) BO';
		echo "<br/>\n";
	}



	echo "  </td>\n";
	echo "  </tr>\n";
	echo "</table>\n";
	echo "</TD>\n";
	echo "</tr>\n";
	echo "<TR>\n";
	echo "	<TD COLSPAN='2' ALIGN='CENTER'>\n";
	echo "	<hr />\n";

	echo getSubmitForm("Run HIP");
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	// First time loading page, set defaults:
	if (!$_POST['process']) {
		echo "<script>switchDefaults(document.viewerform.stackval.options[0].value);</script>\n";
	}

	processing_footer();
	exit;
}

function runHIP() {
	$expId=$_GET['expId'];
	$sessionname=$_POST['sessionname'];
	$runname=$_POST['runname'];
	$outdir=$_POST['outdir'];
	$mandir=$_POST['mandir'];
	$description=$_POST['description'];
	$stackval=$_POST['stackval'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$nproc = ($_POST['nproc']) ? $_POST['nproc'] : 1;
	$numpart=$_POST['numpart'];
	$replen=$_POST['replen'];
	$subunits=$_POST['subunits'];
	$diam=$_POST['diam'];
	$diaminner=$_POST['diaminner'];
	$xlngth=$_POST['xlngth'];
	$yht2=$_POST['yht2'];
	$padval=$_POST['padval'];
	$rescut=$_POST['rescut'];
	$filval=$_POST['filval'];
	$bin=$_POST['bin'];
	$conchg = ($_POST['conchg']=="on") ? true : false;
	$prehip = ($_POST['prehip']=="on") ? true : false;
	$risecheck=$_POST['risecheck'];
	$rise=$_POST['rise'];
	$twist=$_POST['twist'];
	$llbocheck=$_POST['llbocheck'];
	$ll1=$_POST['ll1'];
	$bo1=$_POST['bo1'];
	$ll2=$_POST['ll2'];
	$bo2=$_POST['bo2'];
	$nfold=$_POST['nfold'];
	$maxll=$_POST['maxll'];
	$maxbo=$_POST['maxbo'];

	// Get stack id, apix, & box size from input
	list($stackid,$apix,$boxsz) = preg_split('%\|--\|%',$stackval);

	// Make sure all fields have been entered
	if (!$description)
		createHIPForm("<B>ERROR:</B> Enter a brief description of the particles to be aligned");
	if (!$mandir)
		createHIPForm("<B>ERROR:</B> Enter directory containing mandatory input files");
	if (!$stackid)
		createHIPForm("<B>ERROR:</B> No stack selected");
	if (!$diam)
		createHIPForm("<B>ERROR:</B> Specify a filament diameter");
	if (!$diaminner)
		createHIPForm("<B>ERROR:</B> Specify an inner filament diameter");
	if (!$replen)
		createHIPForm("<B>ERROR:</B> Specify a filament repeat length");
	if ($numpart < 5)
		createHIPForm("<B>ERROR:</B> Must have more than 5 segments");
	if ($prehip == true) {
		if (!$nfold)
			createHIPForm("<B>ERROR:</B> Enter the order of helical symmetry (nfold)");
		if (!$maxll)
			createHIPForm("<B>ERROR:</B> Enter the max layer line");
		if (!$maxbo)
			createHIPForm("<B>ERROR:</B> Enter the max bessel order");
		if (!$risecheck && !$llbocheck)
			createHIPForm("<B>ERROR:</B> Choose a method for generating llbo.sa");
		if ($risecheck && !$rise)
			createHIPForm("<B>ERROR:</B> Please enter a value for rise");
		if ($risecheck && !$twist)
			createHIPForm("<B>ERROR:</B> Please enter a value for twist");
		if ($llbocheck && !$ll1)
			createHIPForm("<B>ERROR:</B> Please enter a value for (1,0) LL");
		if ($llbocheck && !$ll2)
			createHIPForm("<B>ERROR:</B> Please enter a value for (0,1) LL");
		if ($llbocheck && !$bo1)
			createHIPForm("<B>ERROR:</B> Please enter a value for (1,0) BO");
		if ($llbocheck && !$bo2)
			createHIPForm("<B>ERROR:</B> Please enter a value for (0,1) BO");
	}

	// Error checks
	$onerep = floor($replen/$apix);
	//if ($xlngth < $onerep) {
	//	createHIPForm("<B>ERROR:</B> Filament segment length must be greater than one helical"
	//		." repeat ($onerep pixels)");
	//} 
	$calcyht2 = floor($diam/$apix);
	$po2yht2 = round(pow(2, ceil(log($calcyht2, 2))));
	if ($yht2 < $calcyht2) {
		createHIPForm("<B>ERROR:</B> Box height can not be less than filament diameter"
			." ($calcyht2 pixels)");
	} 
	if ($yht2 < $po2yht2) {
		createHIPForm("<B>ERROR:</B> Box height must be a power of two ($po2yht2 pixels)");
	} 
	$calcpad = round(pow(2, ceil(log($xlngth, 2))));
	if ($padval < $calcpad) {
		createHIPForm("<B>ERROR:</B> Pad value must be larger than box size"
			." and must be a power of two");
	} 
	if ($nproc > 16)
		createHIPForm("<B>ERROR:</B> Let's be reasonable with the number of processors,"
			." less than 16 please");
	$particle = new particledata();
	$totprtls=$particle->getNumStackParticles($stackid);
	if ($numpart > $totprtls)
		createHIPForm("<B>ERROR:</B> Number of particles to align ($numpart)"
			." must be less than or equal to the number of particles in the stack ($totprtls)");
		

	// Calculate processing parameters based on filament parameters
	$stackdata = $particle->getStackParams($stackid);

	// Setup command
	$command ="HIP.py ";
	$command.="--session=$sessionname ";
	$command.="--mandir=$mandir ";
	$command.="--description=\"$description\" ";
	$command.="--stack=$stackid ";
	if ($commit) $command.="--commit ";
	else $command.="--no-commit ";
	if ($nproc && $nproc>1) $command.="--nproc=$nproc ";
	$command.="--num-part=$numpart ";
	$command.="--rep-len=$replen ";
	$command.="--subunits=$subunits ";
	$command.="--diam=$diam ";
	$command.="--diam-inner=$diaminner ";
	$command.="--xlngth=$xlngth ";
	$command.="--yht2=$yht2 ";
	$command.="--pad-val=$padval ";
	$command.="--res-cut=$rescut ";
	$command.="--fil-val=$filval ";
	$command.="--bin=$bin ";
	if ($conchg) $command.="--conchg=yes ";
	else $command.="--conchg=no ";
	if ($prehip) $command.="--prehip=yes ";
	else $command.="--prehip=no ";
	if ($rise != '') $command.="--rise=$rise ";
	if ($twist != '') $command.="--twist=$twist ";
	if ($ll1 != '') $command.="--ll1=$ll1 ";
	if ($bo1 != '') $command.="--bo1=$bo1 ";
	if ($ll2 != '') $command.="--ll2=$ll2 ";
	if ($bo2 != '') $command.="--bo2=$bo2 ";
	if ($nfold != '') $command.="--nfold=$nfold ";
	if ($maxll != '') $command.="--maxll=$maxll ";
	if ($maxbo != '') $command.="--maxbo=$maxbo ";

	// Setup header information
	$headinfo = "";
	$headinfo .= referenceBox("Helical Processing Using PHOELIX.", 1996, 
		"Carragher B, Whittaker M, Milligan R.", 
		"J Struct Biol.", 116, 1, 8742731, false, false, "img/phoelix_icon.png");
	$headinfo .= referenceBox("PHOELIX: a package for semi-automated helical reconstruction.", 1995, 
		"Whittaker M, Carragher BO, Milligan RA.", "Ultramicroscopy.", 58, 
		"3-4", 7571117, false, false, "img/phoelix_icon.png");
	$headinfo .= "<table width='600' class='tableborder' border='1'>";
	$headinfo .= "<tr><td colspan='2'><br/>\n";
	
	// Submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'helical', $nproc);

	// If error display them
	if ($errors)
		createHIPForm($errors);
	exit;

}
?>
