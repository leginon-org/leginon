<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

require_once "inc/particledata.inc";
require_once "inc/forms/appionLoopTable.inc";
require_once "inc/forms/runParametersForm.inc";


function createAppionLoopTable ($sessiondata, $defrunname, $outdirname, $leginon=0, $desc=False, $dd=False) {
	//check for output directory [appion = 0, leginon = 1]
	$leg_check = $leginon;
	
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionname=$sessioninfo['Name'];
		echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";
		$sessionpath=$sessioninfo['Image path'];
		if (!$leg_check) {
			$sessionpath=getBaseAppionPath($sessioninfo).'/'.$outdirname;
		}
		
		if ($leg_check) {
			$sessionpath=preg_replace("%rawdata%","",$sessionpath);		
		}
	}

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	
	//--- Add the Run Parameters Form
	$showDesc = $desc;
	$runParamsForm = new RunParametersForm( $runname=$defrunname, $outdir=$outdir, $description='', $desc );
	echo $runParamsForm->generateForm();
	
	//--- Add the Appion Loop Form
	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($_GET['expId']);
	
	// Create a dictionary of preset value=>desc. Desc appears in the gui, value is returned in the code in a selection box.
	$presetList = array_combine( $sessiondata['presets'], $sessiondata['presets'] );
	
	$appionLoopTable = new AppionLoopTable( $checkimage='unrejected', $nowait='', $imgorder='normal', $limit='',$tiltangle='', $maxtiltangle=$maxang, $apcontinue='1',
	$commit='on', $presetList=$presetList, $preset="en", $testimage='', $testfilename='' );
	
	// Only hide advanced parameters if there is not an advanced user logged in.
	// Modify user profile to set to an advanced user. 
	// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
	// We may want to change that someday.
	$displayAdvanced = $_SESSION['advanced_user'];
	echo $appionLoopTable->generateForm( $displayAdvanced=$displayAdvanced );		
	
	return;
};

// Returns an error message if there is an error
// Returns the command flags for the Run Params and appion loop params if there is no error.
// TODO: These should be separated. Call a validate function then the build command function. Not both in same function. 
function parseAppionLoopParams () {
	// CHECK FOR ERRORS
	$error = checkAppionErrors();
	if ($error != false) {
		return $error;
	}

	// add params from run parameters form
	$runParametersForm = new RunParametersForm();
	$command .= $runParametersForm->buildCommand( $_POST );
			
	// add params from Appion Loop form
	$appionLoopTable = new AppionLoopTable();
	$command .= $appionLoopTable->buildCommand( $_POST );	

	// add a space in case there are more params being appended down the road.
	return $command." ";
}

// Returns an error message if there are any issues with the parameters of the appion loop forms
// Returns false if there are no errors.
function checkAppionErrors () {
	$error = false;
	
	// validate params from run parameters form
	$runParametersForm = new RunParametersForm();
	$error .= $runParametersForm->validate( $_POST );
			
	// validate params from Appion Loop form
	$appionLoopTable = new AppionLoopTable();
	$error .= $appionLoopTable->validate( $_POST );	
	
	return $error;	
};

function prettytable2 () {
	echo "
<TABLE border=2 cellpadding=2 cellspacing=0 
 style='margin: 1em 1em 1em 0; border: 1px #333333 solid;
 border-collapse: collapse; text-align: left;'>
";
};

/*
**
**
**  PARTICLE LOOP
**
**
*/

function createParticleLoopTable ($defthresh, $defmaxthresh, $showCCsearchMult=False) {
	echo "<!-- BEGIN Particle Loop Param -->\n";
	$threshv = ($_POST['thresh']) ? $_POST['thresh'] : $defthresh;
	$maxthreshv = ($_POST['maxthresh']) ? $_POST['maxthresh'] : $defmaxthresh;
	$lpv = ($_POST['lp'] || $_POST['process']) ? $_POST['lp'] : '15';
	$hpv = ($_POST['hp'] || $_POST['process']) ? $_POST['hp'] : '0';
	$binv = (int) ($_POST['bin']) ? $_POST['bin'] : '4';
	$medianv = (int) ($_POST['median'] || $_POST['process']) ? $_POST['median'] : '2';
	$pixlimitv = ($_POST['pixlimit'] || $_POST['process']) ? $_POST['pixlimit'] : '4.0';
	$maxpeaksv = (int) ($_POST['maxpeaks']) ? $_POST['maxpeaks'] : '1500';
	$maxsizev = ($_POST['maxsize']) ? $_POST['maxsize'] : '1.0';
	$overlapmultv = ($_POST['overlapmult']) ? $_POST['overlapmult'] : '1.5';
	$centerofmasscheck = ($_POST['peaktype'] && $_POST['peaktype']!='centerofmass') ? '' : 'CHECKED';
	$maximumcheck = ($_POST['peaktype']=='maximum') ? 'CHECKED' : '';
	$invertv = ($_POST['invert']=="on") ? "CHECKED" : "";
	$nojpegsv = ($_POST['nojpegs']=="on") ? "CHECKED" : "";
	$defocpairv = ($_POST['defocpair']=="on") ? "CHECKED" : "";
	$doublesv = ($_POST['doubles']=="on") ? "CHECKED" : "";
	$planeregv = ($_POST['planereg']=="off") ? "" : "CHECKED";
	$ccsearchmult = ($_POST['ccsearchmult']) ? $_POST['ccsearchmult'] : '1.0';
		
	if ($defthresh != -1) {
		echo "<B>Peak thresholds:</B><br/>\n";
		echo "<input type='text' name='thresh' VALUE='$threshv' size='4'>\n";
		echo docpop('minthresh',' Minimum threshold');
		echo "<br />\n";
		echo "<input type='text' name='maxthresh' VALUE='$maxthreshv' size='4'>\n";
		echo docpop('maxthresh',' Maximum threshold');
		echo "<br />\n";		
		echo "<input type='text' name='maxpeaks' VALUE='$maxpeaksv' size='4'>\n";
		echo docpop('maxpeaks',' Max number of particles allowed per image');
		echo "<br />\n";
		echo "<br />\n";
	}
	echo"<b>Filter Values:</b><br />\n";

	echo "<input type='text' name='lp' VALUE='$lpv' size='4'>\n";
	echo docpop('lpval',' Low Pass');
	echo "<font size=-2><I>(in &Aring;ngstroms; 0 = off)</I></font><br />\n";

	echo "<input type='text' name='hp' VALUE='$hpv' size='4'>\n";
	echo docpop('hpval', 'High Pass');
	echo "<font size=-2><I>(in &Aring;ngstroms; 0 = off)</I></font><br />\n";

	echo "<input type='text' name='median' VALUE='$medianv' size='4'>\n";
	echo docpop('medianval',' Median');
	echo "<font size=-2><I>(in pixels; 0 = off)</I></font><br />\n";

	echo "<input type='text' name='pixlimit' VALUE='$pixlimitv' size='4'>\n";
	echo docpop('pixlimit',' Pixel Limit');
	echo "<font size=-2><I>(in Standard Deviations; 0 = off)</I></font><br />\n";

	echo "<input type='text' name='bin' VALUE='$binv' size='4'>\n";
	echo docpop('binval',' Binning');
	echo "<font size=-2><I>(power of 2)</I></font><br />\n";

	echo "<input type='checkbox' name='planereg' $planeregv>\n";
	echo docpop('planereg','Plane regression');
	echo "<br />\n";

	echo "<br />\n";
	echo "<B>Defocal pairs:</B><br />\n";
	echo "<input type='checkbox' name='defocpair' $defocpairv>\n";
	echo docpop('defocpair',' Calculate shifts for defocal pairs');
	echo "<br />\n";
	echo "<br />\n";

	echo "<b>Advanced options:</b><br />\n";
	if ( $showCCsearchMult ) {
		echo "<input type='text' name='ccsearchmult' VALUE='$ccsearchmult' size='4'>\n";
		echo docpop('ccsearchmult','Cross-correlation search multiple');
		echo "<br/>\n";
	}

	if ($defthresh != -1) {
		echo "<input type='text' name='maxsize' VALUE='$maxsizev' size='4'>\n";
		echo docpop('maxsize','Maximum peak area multiple');
		echo "<br/>\n";

		echo "<input type='text' name='overlapmult' VALUE='$overlapmultv' size='4'>\n";
		echo docpop('overlapmult',' Minimum peak overlap distance multiple');
		echo "<br/>\n";

		echo docpop('peaktype',' Peak extraction type');
		echo "<br/>\n";
		echo "&nbsp;<input type='radio' name='peaktype' value='centerofmass' $centerofmasscheck>\n";
		echo "Center of mass <font size=-2><i>(default)</i></font><br/>\n";
		echo "&nbsp;<input type='radio' name='peaktype' value='maximum' $maximumcheck>\n";
		echo "Maximum position";
		echo "<br/>\n";

		echo "<input type='checkbox' name='doubles' $doublesv>\n";
		echo docpop('doubles','Pick only doubles');
		echo "<br/>\n";

	} else {
		echo "<input type='checkbox' name='nojpegs' $nojpegsv>\n";
		echo docpop('nojpegs',' Do NOT create summary peak jpegs');
		echo "<br />\n";
	}
	echo "<input type='checkbox' name='invert' $invertv>\n";
	echo docpop('invert',' Invert image density');
	echo "<br />\n";

	echo "<!-- END Particle Loop Param -->\n";
}

function parseParticleLoopParams ($type) {
	// CHECK FOR ERRORS
	$error = checkParticleErrors($type);
	if ($error[0] != false) {
		return $error;
		exit;
	}

	// CONVERT DATA
	$thresh = $_POST['thresh'];
	$maxthresh = $_POST['maxthresh'];
	$maxpeaks = $_POST['maxpeaks'];
	$lp = $_POST['lp'];
	$hp = $_POST['hp'];
	$median = $_POST['median'];
	$pixlimit = $_POST['pixlimit'];
	$bin = $_POST['bin'];
	$diam = $_POST['diam'];
	$maxsize = $_POST['maxsize'];
	$overlapmult = $_POST['overlapmult'];
	$peaktype = $_POST['peaktype'];
	// check boxes
	$defocpair = ($_POST['defocpair']=="on") ? true : false;
	$nojpegs = ($_POST['nojpegs']=="on") ? true : false;
	$invert = ($_POST['invert']=="on") ? true : false;
	$doubles = ($_POST['doubles']=="on") ? true : false;
	$planereg = ($_POST['planereg']=="on") ? true : false;

	// CREATE COMMAND
	$command = " ";
	if ($type != "manual") {
		if ($maxsize && $maxsize > 0 && $maxsize != 1.0) $command.=" --maxsize=$maxsize";
		if ($overlapmult && $overlapmult > 0 && $overlapmult != 1.5) $command.=" --overlapmult=$overlapmult";
		if ($peaktype) $command.=" --peaktype=$peaktype";
		if ($maxthresh && $maxthresh > 0) $command.=" --maxthresh=$maxthresh";
		if ($maxpeaks && $maxpeaks > 0 && $maxpeaks != 1500) $command.=" --maxpeaks=$maxpeaks";
		if ($thresh) $command.=" --thresh=$thresh";
	}
	if ($defocpair) $command.=" --defocpair";
	if ($invert) $command.=" --invert";
	if ($median != '') $command.=" --median=$median";
	if ($lp != '') $command.=" --lowpass=$lp";
	if ($hp != '') $command.=" --highpass=$hp";
	if ($planereg) $command.=" --planereg";
	if ($bin) $command.=" --bin=$bin";
	if ($diam) $command.=" --diam=$diam";
	if ($pixlimit != '') $command.=" --pixlimit=$pixlimit";
	if ($nojpegs) $command.=" --nojpegs";
	if ($doubles) $command.=" --doubles";

	return $command." ";
}

function checkParticleErrors ($type) {
	if (!$_POST[diam]) {
		return "<B>ERROR:</B> Specify a particle diameter";
		exit;
	}
	if ($type != "manual" and !$_POST[thresh]) {
		return "<B>ERROR:</B> No thresholding value was entered";
		exit;
	}
	//$bin = $_POST[bin];
	//$logbin = log($bin)/log(2.0);
	//if ($bin && !is_int($bin)) {
	//	return "<B>ERROR:</B> Bin value must be a power of 2, <I>e.g.</I> 1, 2, 4, 8, 16";
	//	exit;
	//}
	return false;
};

function particleLoopSummaryTable () {
	$thresh = $_POST[thresh];
	$maxthresh = $_POST[maxthresh];
	$maxpeaks = $_POST[maxpeaks];
	$lp = $_POST[lp];
	$hp = $_POST[hp];
	$median = $_POST[median];
	$bin = $_POST[bin];
	$defocpair = ($_POST[defocpair]=="on") ? "<font color='red'>false</font>" : "<font color='green'>true</font>";
	$maxsize = $_POST[maxsize];
	$overlapmult = $_POST[overlapmult];
	$peaktype = $_POST['peaktype'];
	$invert = ($_POST[invert]=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$diam = $_POST[diam];
	$doubles = ($_POST['doubles']=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$planereg = ($_POST['planereg']=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$spectral = ($_POST['spectral']=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";

	echo "<TR><TD>thresh</TD><TD>$thresh</TD></TR>\n";
	echo "<TR><TD>max thresh</TD><TD>$maxthresh</TD></TR>\n";
	echo "<TR><TD>max peaks</TD><TD>$maxpeaks</TD></TR>\n";
	echo "<TR><TD>lp</TD><TD>$lp</TD></TR>\n";
	echo "<TR><TD>hp</TD><TD>$hp</TD></TR>\n";
	echo "<TR><TD>planereg</TD><TD>$planereg</TD></TR>\n";
	echo "<TR><TD>median</TD><TD>$median</TD></TR>\n";
	echo "<TR><TD>bin</TD><TD>$bin</TD></TR>\n";
	echo "<TR><TD>defocal pairs</TD><TD>$defocpair</TD></TR>\n";
	echo "<TR><TD>max size</TD><TD>$maxsize</TD></TR>\n";
	echo "<TR><TD>overlap multiple</TD><TD>$overlapmult</TD></TR>\n";
	echo "<TR><TD>peak type</TD><TD>$peaktype</TD></TR>\n";
	echo "<TR><TD>invert</TD><TD>$invert</TD></TR>\n";
	echo "<TR><TD>diameter</TD><TD>$diam</TD></TR>\n";
	echo "<TR><TD>doubles</TD><TD>$doubles</TD></TR>\n";

}

?>
