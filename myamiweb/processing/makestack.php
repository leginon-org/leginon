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
require "inc/processing.inc";
require "inc/ctf.inc";
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

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
	$ctf = new ctfdata();
	$ctfdata=$ctf->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);
	$massessrunIds = $particle->getMaskAssessRunIds($sessionId);
	$stackruns = count($particle->getStackIds($sessionId));

	$hosts=getHosts();

	// --- make list of file formats
	$fileformats=array('imagic','spider');
	
	$javascript="<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
	function enableice(){
	  if (document.viewerform.icecheck.checked){
	      document.viewerform.ice.disabled=false;
	      document.viewerform.ice.value='';
	    }
	    else {
	      document.viewerform.ice.disabled=true;
	      document.viewerform.ice.value='0.8';
	    }
	  }
	  function enableace(){
	    if (document.viewerform.acecheck.checked){
	      document.viewerform.ace.disabled=false;
	      document.viewerform.ace.value='0.8';
	    }
	    else {
	      document.viewerform.ace.disabled=true;
	      document.viewerform.ace.value='0.8';
	    }
	  }
          function uncheckstig(){
            document.viewerform.stig.checked=false;
          }
          function uncheckflip(){
            document.viewerform.phaseflip.checked=false;
          }
	  function enableselex(){
	    if (document.viewerform.selexcheck.checked){
	      document.viewerform.selexonmin.disabled=false;
	      document.viewerform.selexonmin.value='0.5';
	      document.viewerform.selexonmax.disabled=false;
	      document.viewerform.selexonmax.value='1.0';
	    }
	    else {
	      document.viewerform.selexonmin.disabled=true;
				document.viewerform.selexonmin.value='0.5';
	      document.viewerform.selexonmax.disabled=true;
	      document.viewerform.selexonmax.value='1.0';
	    }
	  }
	  </SCRIPT>\n";
	$javascript .= writeJavaPopupFunctions('eman');
	
	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font COLOR='RED'>$extra</font>\n<HR>\n";
	}

	$helpdiv = "
	<div id='dhelp'
		style='position:absolute; 
        	background-color:FFFFDD;
        	color:black;
        	border: 1px solid black;
        	visibility:hidden;
        	z-index:+1'
    		onmouseover='overdiv=1;'
    		onmouseout='overdiv=0;'>
	</div>\n";
	echo $helpdiv;
  
	echo"
       <FORM name='viewerform' method='POST' ACTION='$formAction'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","stacks/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}

	// Set any existing parameters in form
	$single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'stack'.($stackruns+1);
	$rundescrval = $_POST['description'];
	$sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
	$prtlrunval = $_POST['prtlrunId'];
	$massessval = $_POST['massessname'];
	// set phaseflip on by default
	$phasecheck = ($_POST['phaseflip']=='on' || !$_POST['process']) ? 'CHECKED' : ''; 		 
	$stigcheck = ($_POST['stig']=='on') ? 'CHECKED' : ''; 		 
	$inspectcheck = ($_POST['inspected']=='off') ? '' : 'CHECKED';
	$commitcheck = ($_POST['commit']=='on') ? 'CHECKED' : '';
	$boxszval = $_POST['boxsize'];
	$binval = ($_POST['bin']) ? $_POST['bin'] : '1';
	$plimit = $_POST['plimit'];
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
	// selexon check params
	$selexminval = ($_POST['selexcheck']=='on') ? $_POST['selexonmin'] : '0.5';
	$selexmaxval = ($_POST['selexcheck']=='on') ? $_POST['selexonmax'] : '1.0';
	$selexcheck = ($_POST['selexcheck']=='on') ? 'CHECKED' : '';
	$selexdisable = ($_POST['selexcheck']=='on') ? '' : 'DISABLED';
	// density check (checked by default)
	$invcheck = ($_POST['density']=='invert' || !$_POST['process']) ? 'CHECKED' : '';
	// normalization check (checked by default)
	$normcheck = ($_POST['normalize']=='on' || !$_POST['process']) ? 'CHECKED' : '';
	echo "<p>\n";
	echo "<table border=0 class=tableborder>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	echo "<table cellpadding='5' border='0'>\n";
	echo "<tr>\n";
	echo "<td valign='TOP'>\n";
	openRoundBorder();
	echo docpop('stackname','<b>Stack File Name:</b>');
	echo "<input type='text' name='single' value='$single'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('runid','<b>Stack Run Name:</b>');
	echo "<input type='text' name='runid' value='$runidval'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' value='$sessionpathval' size='38'>\n";
	echo "<br />\n";
	echo "<br />\n";
	echo docpop('stackdescr','<b>Stack Description:</b>');
	echo "<br />\n";
	echo "<textarea name='description' rows='3' cols='36'>$rundescrval</textarea>\n";
	closeRoundBorder();
	echo "</td>\n";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>\n";

	$prtlruns=count($prtlrunIds);

	if (!$prtlrunIds) {
		echo"<font COLOR='RED'><b>No Particles for this Session</b></font>\n";
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
	echo"
		</td>
	</tr>
	<tr>
		<td>\n";

	$massessruns=count($massessrunIds);
	$massessname = '';
	$massessnames= $particle->getMaskAssessNames($sessionId);

	if (!$massessnames) {
		echo"<font class='apcomment'><b>No Mask Assessed for this Session</b></font>\n";
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
	echo"
		</td>
	</tr>
	<tr>
		<td valign='TOP'>
		<b>Density:</b><br />
		<input type='checkbox' name='density' $invcheck value='invert'>\n";
	echo docpop('stackinv','Invert image density');
	echo "<br />
		</td>
	</tr>
	<tr>
		<td>
		<input type='checkbox' name='normalize' $normcheck>\n";
	echo docpop('stacknorm','Normalize Stack Particles');
	echo "<br />\n";
	if ($ctfdata) {
	  echo"<input type='checkbox' name='phaseflip' onclick='uncheckstig(this)' $phasecheck>"
		."\nPhaseflip Particle Images<br />";
	  echo"<input type='checkbox' name='stig' onclick='uncheckflip(this)' $stigcheck>"
		."\nPhaseflip Micrograph Images <I>(experimental)</I><br />";
	}

	$checkimageval= ($_POST['checkimage']) ? $_POST['checkimage'] : 'best';
	$checkimages=array('Non-rejected','Best','All');
	echo docpop('checkimage','<b>Use</b>');
	echo "<select name='checkimage'>\n";
	foreach ($checkimages as $checkimage) {
		echo "<option value='$checkimage' ";
		// make norejects selected by default
		echo ($checkimage==$checkimageval) ? "selected" : "";
		echo ">$checkimage</option>\n";
	}
	echo"</select>images<br />\n";

	echo "
		<input type='checkbox' name='commit' $commitcheck>\n";
	echo docpop('commit','Commit to Database');
	echo "<br />\n";
	echo "</td>
	</tr>
	<tr>
		<td valign='TOP'>
		<b>File Format:</b><br />
		<SELECT name='fileformat'>\n";
	foreach($fileformats as $format) {
		$s = ($_POST['fileformat']==$format) ? 'SELECTED' : '';
		echo "<OPTION $s >$format</option>\n";
	}
	echo"
		</SELECT>
		</td>
	</tr>
	</table>
	</td>
	<td class='tablebg'>
	<table cellpadding='5' border='0'>
	<tr>
		<td valign='TOP'>
		<input type='text' name='boxsize' size='5' value='$boxszval'>\n";
	echo docpop('boxsize','Box Size');
	echo "(Unbinned, in pixels)<br />\n";
	echo "		</td>
	</tr>
	<tr>
		<td valign='TOP'>
		<b>Filter Values:</b></A><br />
		<input type='text' name='lp' value='$lpval' size='4'>\n";
	echo "Low Pass <font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br />\n";
	echo "<input type='text' name='hp' value='$hpval' size='4'>\n";
	echo "High Pass <font size=-2><i>(in &Aring;ngstroms)</i></font>\n";
	echo "<br />\n";
	echo "<input type='text' name='bin' value='$binval' size='4'>\n";
	echo docpop('stackbin','Binning');
	echo "<br />
	</tr>\n";

	// commented out for now, since not implemented
//	<tr>
//		<td>
//		<input type='checkbox' name='icecheck' onclick='enableice(this)' $icecheck>
//		Ice Thickness Cutoff<br />
//		Use Ice Thinner Than:<input type='text' name='ice' $icedisable value='$iceval' size='4'>
//		(between 0.0 - 1.0)
//		</td>
//	</tr>\n";
	if ($ctfdata) {
		echo"
	<tr>
		<td>
		<input type='checkbox' name='acecheck' onclick='enableace(this)' $acecheck>
		ACE Confidence Cutoff<br />
		Use Values Above:<input type='text' name='ace' $acedisable value='$aceval' size='4'>
		(between 0.0 - 1.0)
		</td>
	</tr>\n";
	}
	if ($prtlrunIds) {
		echo"	
	<tr>
		<td>
		<input type='checkbox' name='selexcheck' onclick='enableselex(this)' $selexcheck>
		Particle Correlation Cutoff<br />
		(between 0.0 - 1.0)<br />
		Use Values Above:<input type='text' name='selexonmin' $selexdisable value='$selexminval' size='4'><br />
		Use Values Below:<input type='text' name='selexonmax' $selexdisable value='$selexmaxval' size='4'><br />
		<br />\n";
		echo "<b>Defocal pairs:</b>\n";
		echo "<br />\n";
		echo "<input type='checkbox' name='defocpair' $defocpair>\n";
		echo docpop('stackdfpair','Calculate shifts for defocal pairs');
		echo "<br />
		</td>
	</tr>\n";
	}	
	//if there is CTF data, show min & max defocus range
	if ($ctfdata) {
		$fields = array('defocus1', 'defocus2');
		$bestctf = $ctf->getBestStats($fields, $sessionId);
		$min="-".$bestctf['defocus1'][0]['min'];
		$max="-".$bestctf['defocus1'][0]['max'];
		// check if user has changed values on submit
		$minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
		$maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
		$sessionpath=ereg_replace("E","e",$sessionpath);
		$minval = ereg_replace("E","e",round($minval,8));
		$maxval = ereg_replace("E","e",round($maxval,8));
		echo"
		<tr>
			<td valign='TOP'>
			<b>Defocus Limits</b><br />
			<input type='text' name='dfmin' value='$minval' size='25'>
			<input type='hidden' name='dbmin' value='$minval'>
			Minimum<br />
			<input type='text' name='dfmax' value='$maxval' size='25'>
			<input type='hidden' name='dbmax' value='$maxval'>
			Maximum
			</td>
		</tr>\n";
	}
	echo "<tr><td>\n";
	echo docpop('stacklim','Limit # of particles to: ');
	echo "<input type='text' name='plimit' value='$plimit' size='8'>\n";
	echo "</td></tr>
	</table>
	</td>
	</tr>
	<tr>
		<td colspan='2' align='CENTER'>
		<HR>";

	echo "Host: <select name='host'>\n";
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
  	echo "</SELECT><BR/>
	  <input type='submit' name='process' value='Just Show Command'>
	  <input type='submit' name='process' value='Make Stack'><br />
	  </td>
	</tr>
	</table>
	</FORM>
	</CENTER>\n";
	writeBottom();
	exit;
}

function runMakestack() {
	$expId = $_GET['expId'];
	$runid = $_POST['runid'];
	$outdir = $_POST['outdir'];

	$command.="makestack.py ";

	$single=$_POST['single'];
print_r($_POST);
	//make sure a session was selected
	$description=$_POST['description'];
	if (!$description) createMakestackForm("<b>ERROR:</b> Enter a brief description of the stack");

	//make sure a session was selected
	if (!$outdir) createMakestackForm("<b>ERROR:</b> Select an experiment session");

	// get selexon runId
	$prtlrunId=$_POST['prtlrunId'];
	if (!$prtlrunId) createMakestackForm("<b>ERROR:</b> No particle coordinates in the database");
	
	$invert = ($_POST['density']=='invert') ? '' : 'noinvert';
	$normalize = ($_POST['normalize']=='on') ? '' : 'nonorm';
	$phaseflip = ($_POST['phaseflip']=='on') ? 'phaseflip' : '';
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
		if (!is_numeric($bin)) createMakestackForm("<b>ERROR:</b> Binning amount must be 2, 4, 8, 16, 32...");
	}
	// don't bother with bin if it's just 1
	if ($bin == 1) $bin='';

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

	// selexon cutoff
	if ($_POST['selexcheck']=='on') {
		$selexonmin=$_POST['selexonmin'];
		$selexonmax=$_POST['selexonmax'];
		if ($selexonmin > 1 || $selexonmin < 0) createMakestackForm("<b>ERROR:</b> Selexon Min cutoff must be between 0 & 1");
		if ($selexonmax > 1 || $selexonmax < 0) createMakestackForm("<b>ERROR:</b> Selexon Max cutoff must be between 0 & 1");
	}

	// check defocus cutoffs
	$dfmin = ($_POST['dfmin']==$_POST['dbmin'] || $_POST['dfmin']>$_POST['dbmin']) ? '' : $_POST['dfmin'];
	$dfmax = ($_POST['dfmax']==$_POST['dbmax'] || $_POST['dfmax']<$_POST['dbmax']) ? '' : $_POST['dfmax'];

	$fileformat = ($_POST['fileformat']=='spider') ? 'spider' : '';

	// mask assessment
	$massessname=$_POST['massessname'];


	// limit the number of particles
	$limit=$_POST['plimit'];
	if ($limit) {
		if (!is_numeric($limit)) createMakestackForm("<b>ERROR:</b> Particle limit must be an integer");
	}

	$command.="single=$single ";
	$command.="runid=$runid ";
	$command.="outdir=$outdir ";
	$command.="prtlrunId=$prtlrunId ";
	if ($lp) $command.="lp=$lp ";
	if ($hp) $command.="hp=$hp ";
	if ($invert) $command.="noinvert ";
	if ($normalize) $command.="nonorm ";
	if ($phaseflip) $command.="phaseflip ";
	if ($stig) $command.="stig ";
	if ($inspected) $command.="inspected ";
	if ($norejects) $command.="norejects ";
	if ($massessname) $command.="maskassess=$massessname ";
	if ($commit) $command.="commit ";
	$command.="boxsize=$boxsize ";
	if ($bin) $command.="bin=$bin ";
	if ($ace) $command.="ace=$ace ";
	if ($defocpair) $command.="defocpair ";
	if ($selexonmin) $command.="selexonmin=$selexonmin ";
	if ($selexonmax) $command.="selexonmax=$selexonmax ";
	if ($dfmin) $command.="mindefocus=$dfmin ";
	if ($dfmax) $command.="maxdefocus=$dfmax ";
	if ($fileformat) $command.="spider ";
	if ($limit) $command.="partlimit=$limit ";
	$command.="description=\"$description\"";

	// submit job to cluster
	if ($_POST['process']=="Make Stack") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createMakestackForm("<b>ERROR:</b> Enter a user name and password");

		submitAppionJob($command,$outdir,$runid,$expId,$testimage);
		exit;
	}

	writeTop("Makestack Run","Makestack Params");

	if ($massessname) {
		echo"<font color='red'><b>Use a 32-bit machine to use the masks</b></font>\n";
	}
	echo"
	<P>
	<table width='600' border='1'>
	<tr><td colspan='2'>
	<b>Makestack Command:</b><br />
	$command
	</td></tr>
	<tr><td>stack name</td><td>$single</td></tr>
	<tr><td>runid</td><td>$runid</td></tr>
	<tr><td>outdir</td><td>$outdir</td></tr>
	<tr><td>description</td><td>$description</td></tr>
	<tr><td>selexonId</td><td>$prtlrunId</td></tr>
	<tr><td>invert</td><td>$invert</td></tr>
	<tr><td>nonorm</td><td>$nonorm</td></tr>
	<tr><td>phaseflip</td><td>$phaseflip</td></tr>
	<tr><td>stig</td><td>$stig</td></tr>
	<tr><td>inspected</td><td>$inspected</td></tr>
	<tr><td>norejects</td><td>$norejects</td></tr>
	<tr><td>mask assessment</td><td>$massessname</td></tr>
	<tr><td>commit</td><td>$commit</td></tr>
	<tr><td>box size</td><td>$boxsize</td></tr>
	<tr><td>binning</td><td>$bin</td></tr>
	<tr><td>ace cutoff</td><td>$ace</td></tr>
	<tr><td>selexonmin cutoff</td><td>$selexonmin</td></tr>
	<tr><td>selexonmax cutoff</td><td>$selexonmax</td></tr>
	<tr><td>minimum defocus</td><td>$dfmin</td></tr>
	<tr><td>maximum defocus</td><td>$dfmax</td></tr>
	<tr><td>particle limit</td><td>$limit</td></tr>
	<tr><td>spider</td><td>$fileformat</td></tr>
	</table>\n";
	writeBottom(True,True);
}
?>
