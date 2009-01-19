<?php
/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
 *
 *	Make stack function
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/appionloop.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runMakestack();
}

// Create the form page
else {
	createMakestackForm();
}

function createMakestackForm($extra=false, $title='Makestack.py Launcher', $heading='Create an Image Stack') {
	// check if coming directly from a session
	$expId=$_GET['expId'];
	if ($expId){
		$sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctfdata=$particle->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$massessrunIds = $particle->getMaskAssessRunIds($sessionId);
	$stackruns = count($particle->getStackIds($sessionId, True));

	$javascript="<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>

	function enableace(){
		if (document.viewerform.acecheck.checked){
			document.viewerform.ace.disabled=false;
			document.viewerform.ace.value='0.8';
		} else {
			document.viewerform.ace.disabled=true;
			document.viewerform.ace.value='0.8';
		}
	}

	function enablefliptype() {
		if (document.viewerform.phaseflip.checked){
			document.viewerform.fliptype.disabled=false;
		} else {
			document.viewerform.fliptype.disabled=true;
		}
	}

	function enableselex(){
		if (document.viewerform.selexcheck.checked){
			document.viewerform.correlationmin.disabled=false;
			document.viewerform.correlationmin.value='0.5';
			document.viewerform.correlationmax.disabled=false;
			document.viewerform.correlationmax.value='1.0';
		} else {
			document.viewerform.correlationmin.disabled=true;
			document.viewerform.correlationmin.value='0.5';
			document.viewerform.correlationmax.disabled=true;
			document.viewerform.correlationmax.value='1.0';
		}
	}
	</SCRIPT>\n";
	$javascript .= writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font COLOR='RED'>$extra</font>\n<HR>\n";
	}

	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","stacks/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// Set any existing parameters in form
	$single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
	$rundescrval = $_POST['description'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	while (file_exists($sessionpathval.'stack'.($stackruns+1)))
		$stackruns += 1;
	$runnameval = ($_POST['runname']) ? $_POST['runname'] : 'stack'.($stackruns+1);
	$prtlrunval = $_POST['prtlrunId'];
	$massessval = $_POST['massessname'];
	// set phaseflip on by default
	$phasecheck = ($_POST['phaseflip']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$inspectcheck = ($_POST['inspected']=='off') ? '' : 'CHECKED';
	$commitcheck = ($_POST['commit']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	$boxszval = $_POST['boxsize'];
	$binval = ($_POST['bin']) ? $_POST['bin'] : '1';
	$partlimit = $_POST['partlimit'];
	$lpval = ($_POST['lp']) ? $_POST['lp'] : '';
	$hpval = ($_POST['hp']) ? $_POST['hp'] : '';
	// ice check params
	$iceval = ($_POST['icecheck']=='on') ? $_POST['ice'] : '0.8';
	$icecheck = ($_POST['icecheck']=='on') ? 'CHECKED' : '';
	$icedisable = ($_POST['icecheck']=='on') ? '' : 'DISABLED';
	// ace check params
	$acecheck = ($_POST['acecheck']=='on') ? 'CHECKED' : '';
	$acedisable = ($_POST['acecheck']=='on') ? '' : 'DISABLED';
	$aceval = ($_POST['acecheck']=='on') ? $_POST['ace'] : '0.8';
	// correlation check params
	$selexminval = ($_POST['selexcheck']=='on') ? $_POST['correlationmin'] : '0.5';
	$selexmaxval = ($_POST['selexcheck']=='on') ? $_POST['correlationmax'] : '1.0';
	$selexcheck = ($_POST['selexcheck']=='on') ? 'CHECKED' : '';
	$selexdisable = ($_POST['selexcheck']=='on') ? '' : 'DISABLED';
	// density check (checked by default)
	$invcheck = ($_POST['density']=='invert' || !$_POST['process']) ? 'CHECKED' : '';
	// normalization check (checked by default)
	$normcheck = ($_POST['normalize']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";

#	echo docpop('stackname','<b>Stack File Name:</b>');
	echo "<input type='hidden' name='single' value='start.hed'>\n";
#	echo "<br />\n";
#	echo "<br />\n";

	createAppionLoopTable($sessiondata, $runnameval, "stacks");

	echo "<b>Density modifications:</b><br/>";

	echo "<input type='checkbox' name='density' $invcheck value='invert'>\n";
	echo docpop('stackinv','Invert image density');
	echo "<br/>\n";

	echo "<input type='checkbox' name='normalize' $normcheck>\n";
	echo docpop('stacknorm','Normalize Stack Particles');
	echo "<br/>\n";

	if ($ctfdata) {
		echo"<input type='checkbox' name='phaseflip' onclick='enablefliptype(this)' $phasecheck>\n";
		echo docpop('phaseflip','Phaseflip Particle Images');
		echo "<br/>\n";

		echo "Phaseflipping Method:\n";
		echo "&nbsp;&nbsp;<select name='fliptype' ";
			if (!$phasecheck) echo " disabled";
			echo ">\n";
		echo "<option value='emanpart'>EMAN Flip by Stack (default)</option>\n";
		echo "<option value='emanimage'>EMAN Flip Whole Image</option>\n";
		echo "<option value='emantilt'>EMAN Flip by Tilt Location</option>\n";
		echo "<option value='ace2image'>Ace 2 Whole Image</option>\n";
		echo "</select>\n";
		echo "<br/>\n";
	}

	echo "<i>File format:</i>";
	echo "<br/>\n";

	echo "&nbsp;<input type='radio' name='fileformat' value='imagic' ";
	if ($_POST['fileformat'] == 'imagic' || !$_POST['checkimage']) echo "checked";
	echo ">\n";
	echo "Imagic: start.hed/.img <font size='-2'><i>(default)</i></font><br/>\n";

	echo "&nbsp;<input type='radio' name='fileformat' value='spider' ";
	if ($_POST['fileformat'] == 'spider') echo "checked";
	echo ">\n";
	echo "Spider: start.spi <font size='-2'><i>(must be less than 18,000 particles)</i></font> <br/>\n";



	//echo "</td></tr></table>";
	echo "</td><td class='tablebg'>";
	//echo "<table cellpadding='5' border='0'><tr><td valign='TOP'>";

	echo docpop('stackdescr','<b>Stack Description:</b>');
	echo "<br/>\n";
	echo "<textarea name='description' rows='3' cols='36'>$rundescrval</textarea>\n";
	echo "<br/>\n";
	echo "<br/>\n";

	$prtlruns=count($prtlrunIds);

	if (!$prtlrunIds) {
		echo"<font class='apcomment' size='+2'><b>No Particles for this Session</b></font>\n";
	}
	else {
		echo docpop('stackparticles','Particles:');
		echo "<select name='prtlrunId'>\n";
		foreach ($prtlrunIds as $prtlrun){
			$prtlrunId=$prtlrun['DEF_id'];
			$runname=$prtlrun['name'];
			$prtlstats=$particle->getStats($prtlrunId);
			$totprtls=commafy($prtlstats['totparticles']);
			echo "<OPTION value='$prtlrunId'";
			// select previously set prtl on resubmit
			if ($prtlrunval==$prtlrunId) echo " SELECTED";
			echo">$runname ($totprtls prtls)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo "<br/>\n";
	echo "<br/>\n";

	$massessruns=count($massessrunIds);
	$massessname = '';
	$massessnames= $particle->getMaskAssessNames($sessionId);

	if (!$massessnames) {
		echo"<font class='apcomment' size='-2'><i>No Mask Assessed for this Session</i></font>\n";
	}
	else {
		echo "Mask Assessment:
		<SELECT name='massessname'>\n";
		foreach ($massessnames as $name) {
			$massessname = $name;
			$massessruns = $particle->getMaskAssessRunByName($sessionId,$massessname);
			$totkeeps = 0;
			foreach ($massessruns as $massessrun){
				$massessrunId=$massessrun['DEF_id'];
				$massessstats=$particle->getMaskAssessStats($massessrunId);
				$permaskkeeps=$massessstats['totkeeps'];
				$totkeeps = $totkeeps + $permaskkeeps;
			}
			echo "<OPTION value='$massessname'";
			// select previously set assessment on resubmit
			if ($massessval==$massessname) echo " SELECTED";
			$totkeepscm=commafy($totkeeps);
			echo">$massessname ($totkeepscm regions)</OPTION>\n";
		}
		echo "</SELECT>\n";
	}
	echo "<br/>\n";
	echo "<br/>\n";

	echo "<input type='text' name='boxsize' size='5' value='$boxszval'>\n";
	echo docpop('boxsize','Box Size');
	echo "(Unbinned, in pixels)<br />\n";
	echo "<br/>\n";

	echo "<b>Filter Values:</b><br/>";

	echo "<input type='text' name='lp' value='$lpval' size='4'>\n";
	echo docpop('lpstackval', 'Low Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='hp' value='$hpval' size='4'>\n";
	echo docpop('hpstackval', 'High Pass');
	echo "<font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br/>\n";

	echo "<input type='text' name='bin' value='$binval' size='4'>\n";
	echo docpop('stackbin','Binning');
	echo "<br/>\n";
	echo "<br/>\n";

	// commented out for now, since not implemented
//		<input type='checkbox' name='icecheck' onclick='enableice(this)' $icecheck>
//		Ice Thickness Cutoff<br />
//		Use Ice Thinner Than:<input type='text' name='ice' $icedisable value='$iceval' size='4'>
//		(between 0.0 - 1.0)\n";

	if ($ctfdata) {
		echo"<input type='checkbox' name='acecheck' onclick='enableace(this)' $acecheck>\n";
		echo docpop('aceconf','ACE Confidence Cutoff');
		echo "<br />\n";
		echo "Use Values Above:<input type='text' name='ace' $acedisable value='$aceval' size='4'>
		(between 0.0 - 1.0)\n";
		echo "<br/>\n";
		echo "<br/>\n";
	}


	echo"<input type='checkbox' name='selexcheck' onclick='enableselex(this)' $selexcheck>\n";
	echo docpop('partcutoff','Particle Correlation Cutoff');
	echo "<br />\n";
	echo "Use Values Above:<input type='text' name='correlationmin' $selexdisable value='$selexminval' size='4'><br/>\n";
	echo "Use Values Below:<input type='text' name='correlationmax' $selexdisable value='$selexmaxval' size='4'><br/>\n";
	echo "<br/>\n";

	echo "<b>Defocal pairs:</b>\n";
	echo "<br/>\n";
	echo "<input type='checkbox' name='defocpair' $defocpair>\n";
	echo docpop('stackdfpair','Calculate shifts for defocal pairs');
	echo "<br/>\n";
	echo "<br/>\n";

	//if there is CTF data, show min & max defocus range
	if ($ctfdata) {
		$fields = array('defocus1', 'defocus2');
		$bestctf = $particle->getBestStats($fields, $sessionId);
		$min=-1*abs($bestctf['defocus1'][0]['min']);
		$max=-1*abs($bestctf['defocus1'][0]['max']);
		//echo $min."<br/>\n";
		//echo $max."<br/>\n";
		// check if user has changed values on submit
		$minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
		$maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
		$sessionpath=ereg_replace("E","e",$sessionpath);
		$minval = ereg_replace("E","e",round($minval,8));
		$maxval = ereg_replace("E","e",round($maxval,8));
		echo"<b>Defocus Limits</b><br />
			<input type='text' name='dfmin' value='$minval' size='25'>
			<input type='hidden' name='dbmin' value='$minval'>
			Minimum<br />
			<input type='text' name='dfmax' value='$maxval' size='25'>
			<input type='hidden' name='dbmax' value='$maxval'>
			Maximum\n";
		echo "<br/>\n";
		echo "<br/>\n";
	}


	echo docpop('stacklim','Limit # of particles to: ');
	echo "<input type='text' name='partlimit' value='$partlimit' size='8'>\n";
	echo "<br/>\n";

	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td colspan='2' align='CENTER'>\n";
	echo "<hr/>\n";
	echo getSubmitForm("Make Stack");
	echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</form>\n";
	processing_footer();
	exit;
}

function runMakestack() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$command.="makestack2.py"." ";

	$single=$_POST['single'];
	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createMakestackForm("<b>ERROR:</b> Enter a brief description of the stack");

	//make sure a session was selected
	if (!$outdir) createMakestackForm("<b>ERROR:</b> Select an experiment session");

	// get correlation runId
	$prtlrunId=$_POST['prtlrunId'];
	if (!$prtlrunId) createMakestackForm("<b>ERROR:</b> No particle coordinates in the database");

	$invert = ($_POST['density']=='invert') ? 'yes' : 'no';
	$normalize = ($_POST['normalize']=='on') ? 'yes' : 'no';
	$phaseflip = ($_POST['phaseflip']=='on') ? 'phaseflip' : '';
	$fliptype = $_POST['fliptype'];
	$stig = ($_POST['stig']=='on') ? 'stig' : '';
	$commit = ($_POST['commit']=="on") ? 'commit' : '';
	$defocpair = ($_POST['defocpair']=="on") ? "1" : "0";

	// set image inspection selection
	$norejects=$inspected=0;
	if ($_POST['checkimage']=="Non-rejected") {
		$norejects=1;
	} elseif ($_POST['checkimage']=="Best") {
		$norejects=1;
		$inspected=1;
	}
	// binning amount
	$bin=$_POST['bin'];
	if ($bin) {
		if (!is_numeric($bin)) createMakestackForm("<b>ERROR:</b> Binning amount must be an integer");
	}

	// box size
	$boxsize = $_POST['boxsize'];
	if (!$boxsize) createMakestackForm("<b>ERROR:</b> Specify a box size");
	if (!is_numeric($boxsize)) createMakestackForm("<b>ERROR:</b> Box size must be an integer");

	// lp filter
	$lp = $_POST['lp'];
	if ($lp && !is_numeric($lp)) createMakestackForm("<b>ERROR:</b> low pass filter must be a number");

	// hp filter
	$hp = $_POST['hp'];
	if ($hp && !is_numeric($hp)) createMakestackForm("<b>ERROR:</b> high pass filter must be a number");

	// ace cutoff
	if ($_POST['acecheck']=='on') {
		$ace=$_POST['ace'];
		if ($ace > 1 || $ace < 0 || !$ace) createMakestackForm("<b>ERROR:</b> Ace cutoff must be between 0 & 1");
	}

	// correlation cutoff
	if ($_POST['selexcheck']=='on') {
		$correlationmin=$_POST['correlationmin'];
		$correlationmax=$_POST['correlationmax'];
		//if ($correlationmin > 1 || $correlationmin < 0) createMakestackForm("<b>ERROR:</b> correlation Min cutoff must be between 0 & 1");
		//if ($correlationmax > 1 || $correlationmax < 0) createMakestackForm("<b>ERROR:</b> correlation Max cutoff must be between 0 & 1");
	}

	// check defocus cutoffs
	$dfmin = ($_POST['dfmin']==$_POST['dbmin'] || $_POST['dfmin']>$_POST['dbmin']) ? '' : $_POST['dfmin'];
	$dfmax = ($_POST['dfmax']==$_POST['dbmax'] || $_POST['dfmax']<$_POST['dbmax']) ? '' : $_POST['dfmax'];

	// mask assessment
	$massessname=$_POST['massessname'];


	// limit the number of particles
	$partlimit=$_POST['partlimit'];
	if ($partlimit) {
		if (!is_numeric($partlimit)) createMakestackForm("<b>ERROR:</b> Particle limit must be an integer");
	} else $partlimit="none";

	$command.="--single=$single ";
	$command.="--selectionid=$prtlrunId ";
	if ($lp) $command.="--lowpass=$lp ";
	if ($hp) $command.="--highpass=$hp ";
	if ($invert == "yes") $command.="--invert ";
	if ($invert == "no") $command.="--no-invert ";
	if ($normalize == "yes") $command.="--normalized ";
	if ($phaseflip) { 
		$command.="--phaseflip --flip-type=$fliptype ";
	}
	if ($massessname) $command.="--maskassess=$massessname ";
	$command.="--boxsize=$boxsize ";
	if ($bin > 1) $command.="--bin=$bin ";
	if ($ace) $command.="--acecutoff=$ace ";
	if ($defocpair) $command.="--defocpair ";
	if ($correlationmin) $command.="--mincc=$correlationmin ";
	if ($correlationmax) $command.="--maxcc=$correlationmax ";
	if ($dfmin) $command.="--mindef=$dfmin ";
	if ($dfmax) $command.="--maxdef=$dfmax ";
	if ($_POST['fileformat']=='spider') $command.="--spider ";
	if ($partlimit != "none") $command.="--partlimit=$partlimit ";
	$command.="--description=\"$description\" ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createPyAceForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	// submit job to cluster
	if ($_POST['process']=="Make Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMakestackForm("<b>ERROR:</b> Enter a user name and password");

		$sub = submitAppionJob($command,$outdir,$runname,$expId,'makestack',$testimage);
		// if errors:
		if ($sub) createMakestackForm("<b>ERROR:</b> $sub");
		exit;
	}

	processing_header("Makestack Run","Makestack Params");

	if ($massessname) {
		echo"<font color='red'><b>Use a 32-bit machine to use the masks</b></font>\n";
	}
	echo"
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>Makestack Command:</b><br />
	$command
	</td></tr>";
	echo appionLoopSummaryTable();
	echo"
	<tr><td>stack name</td><td>$single</td></tr>
	<tr><td>selection Id</td><td>$prtlrunId</td></tr>
	<tr><td>invert</td><td>$invert</td></tr>
	<tr><td>normalize</td><td>$normalize</td></tr>
	<tr><td>phase flip</td><td>$phaseflip</td></tr>
	<tr><td>flip type</td><td>$fliptype</td></tr>
	<tr><td>mask assessment</td><td>$massessname</td></tr>
	<tr><td>box size</td><td>$boxsize</td></tr>
	<tr><td>binning</td><td>$bin</td></tr>
	<tr><td>ace cutoff</td><td>$ace</td></tr>
	<tr><td>correlationmin cutoff</td><td>$correlationmin</td></tr>
	<tr><td>correlationmax cutoff</td><td>$correlationmax</td></tr>
	<tr><td>minimum defocus</td><td>$dfmin</td></tr>
	<tr><td>maximum defocus</td><td>$dfmax</td></tr>
	<tr><td>particle limit</td><td>$partlimit</td></tr>
	<tr><td>spider</td><td>$_POST[fileformat]</td></tr>";

	echo "</table>\n";
	processing_footer(True,True);
}
?>
