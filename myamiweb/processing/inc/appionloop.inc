<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

function createAppionLoopTable ($sessiondata, $defrunname, $outdirname, $leginon=0) {
	echo "<!-- BEGIN Appion Loop Param -->\n";
	$norejects = ($_POST[norejects]=="on") ? "CHECKED" : "";
	$nowait = ($_POST[nowait]=="") ? "" : "CHECKED";
	$background = ($_POST[background]=="on") ? "CHECKED" : "";
	$shuffle = ($_POST['shuffle']=="on") ? "CHECKED" : "";
	$reverse = ($_POST['reverse']=="on") ? "CHECKED" : "";
	$limit = $_POST[limit];
	$tiltangle = $_POST['tiltangle'];
	$commit = ($_POST[commit]=="on") ? "CHECKED" : "";
	$apcontinue = $_POST[apcontinue];
	// continue is checkmarked by default
	$apcontinuecheck = ($apcontinue || !$_POST['process']) ? "CHECKED" : "";
    	$apreproccheck = (!$apcontinue && $_POST['process']) ? "CHECKED" : "";

	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	$runname = ($_POST[runname]) ? $_POST[runname] : $defrunname;
	echo openRoundBorder();
	echo docpop('runname','<b>Run Name:</b> ');
	echo "<input type='text' name='runname' VALUE='$runname'><BR/><BR/>\n";
	
	//check for output directory [appion = 0, leginon = 1]
	$leg_check = $leginon;
	
	$sessioninfo=$sessiondata['info'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		if (!$leg_check) {
			$sessionpath=ereg_replace("leginon","appion",$sessionpath);
			$sessionpath=ereg_replace("rawdata",$outdirname,$sessionpath);
		}
		
		if ($leg_check) {
			$sessionpath=ereg_replace("rawdata","",$sessionpath);		
		}
		$sessionname=$sessioninfo['Name'];
	}

	$outdir = ($_POST[outdir]) ? $_POST[outdir] : $sessionpath;
	echo docpop('outdir','<b>Output Directory:</b>');
	echo "<br />\n";
	echo "<input type='text' name='outdir' VALUE='$outdir' size='45'><br />\n";
	echo closeRoundBorder();
	echo "<br />\n";

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$presets=$sessiondata['presets'];
	if ($presets && count($presets) > 1) {
		echo"<B>Preset</B>\n<SELECT name='preset'>\n";
		foreach ($presets as $preset) {
			echo "<OPTION VALUE='$preset' ";
			// make en selected by default
			if ($preset==$presetval) echo "SELECTED";
			echo ">$preset</OPTION>\n";
		}
		echo"</SELECT><br/><br/>\n";
	} elseif ($presets) {
		echo"<B>Preset:</B>&nbsp;&nbsp;".$presets[0]."\n\n";
		echo"<input type='hidden' name='preset' VALUE=".$presets[0].">\n";
		echo"<br/>\n";
	} else {
		//no presets
		echo"<input type='hidden' name='alldbimages' VALUE=1>\n";
		echo"<I>No Presets for this Session<br/>\n"
			."Will Process ALL Images</I><BR/>\n";
	}

	echo "<hr>\n";
	echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";


	$checkimageval= ($_POST['checkimage']) ? $_POST['checkimage'] : 'non-rejected';
	$checkimages=array('non-rejected','all','best');
	echo docpop('checkimages','<b>Process</b>');
	echo"<SELECT name='checkimage'>\n";
	foreach ($checkimages as $checkimage) {
		echo "<OPTION VALUE='$checkimage' ";
		// make norejects selected by default
		if ($checkimage==$checkimageval) echo "SELECTED";
		echo ">$checkimage</option>\n";
	}
	echo"</select> images<br /><br />\n";

	echo "<input type='checkbox' name='nowait' $nowait>\n";
	echo docpop('nowait','Wait for more images after finishing');
	echo "<br />\n";

	echo "<input type='checkbox' name='background' $background>\n";
	echo docpop('background','Run in background mode');
	echo "<br />\n";

	echo "<input type='checkbox' name='shuffle' $shuffle>\n";
	echo docpop('shuffle','Shuffle the images');
	echo "<br />\n";

	echo "<input type='checkbox' name='reverse' $reverse>\n";
	echo docpop('reverse','Process new images first');
	echo "<br />\n";

	echo docpop('limit','Limit: ');
	echo "only process&nbsp; <input type='texlt' name='limit' VALUE='$limit' size='4'>&nbsp; images\n";
	echo "<br />\n";

	echo docpop('tiltangle','Tilt Angle:');
	echo "<select name='tiltangle'>\n";
	echo "  <option value='all'>all tilt angles</option>\n";
	echo "  <option value='notilt'>zero tilt angles only</option>\n";
	echo "  <option value='hightilt'>large tilt angles only</option>\n";
	echo "  <option value='lowtilt'>small tilt angles only</option>\n";
	echo "  <option value='minustilt'>negative tilt angles only</option>\n";
	echo "  <option value='plustilt'>positive tilt angles only</option>\n";
	echo "</select>";
	echo "<br />\n";

	echo docpop('cont','<i>Continuation:</i>'); 
	echo "<br />\n";
	echo "<input type='radio' name='apcontinue' VALUE='1' $apcontinuecheck>\n";
	echo "Continue unfinished run <font size=-2><i>(default)</i></font><br/>\n";
	echo "<input type='radio' name='apcontinue' VALUE='0' $apreproccheck>\n";
	echo "Reprocess all images<br/><br/>\n";

	echo "<hr>\n";
	echo "<input type='checkbox' name='commit' $commit>\n";
	echo docpop('commit','<b>Commit results to database</b>');
	echo "<br />\n";
	echo "<!-- END Appion Loop Param -->\n";
};

function appionLoopSummaryTable () {
	if ($_POST[checkimage]=="non-rejected") {
		$norejects = 1;
	} elseif ($_POST[checkimage]=="best") {
		$norejects = 1;
		$bestimages = 1;
	} else {
		$norejects = 0;
		$bestimages = 0;
	}
	$nowait = ($_POST[nowait]=="on") ? false : true;
	$background = ($_POST[background]=="on") ? true : false;
	$shuffle = ($_POST['shuffle']=="on") ? true : false;
	$reverse = ($_POST['reverse']=="on") ? true : false;
	$limit = $_POST[limit];
	$tiltangle = $_POST['tiltangle'];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? true : false;
	$runname = $_POST[runname];
	$reverse = ($_POST['reverse']=="on") ? true : false;
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ","\ ", $testimage);
	}

	echo "<TR><TD>runname</TD><TD>$runname</TD></TR>\n";
	echo "<TR><TD>output directory</TD><TD>$outdir</TD></TR>\n";
	echo "<TR><TD>no rejects</TD><TD>$norejects</TD></TR>\n";
	echo "<TR><TD>only best images</TD><TD>$bestimages</TD></TR>\n";
	echo "<TR><TD>do not wait for more images</TD><TD>$nowait</TD></TR>\n";
	echo "<TR><TD>commit to database</TD><TD>$commit</TD></TR>\n";
	echo "<TR><TD>background</TD><TD>$background</TD></TR>\n";
	echo "<TR><TD>shuffle images</TD><TD>$shuffle</TD></TR>\n";
	echo "<TR><TD>process new images first</TD><TD>$reverse</TD></TR>\n";
	echo "<TR><TD>image limit</TD><TD>$limit</TD></TR>\n";
	echo "<TR><TD>tilt angle restriction</TD><TD>$tiltangle</TD></TR>\n";
	echo "<TR><TD>continue from last image</TD><TD>$apcontinue</TD></TR>\n";
}

function parseAppionLoopParams () {
	// CHECK FOR ERRORS
	$error = checkAppionErrors();
	if ($error[0] != false) {
		return $error;
		exit;
	}
	$expId = $_GET['expId'];
	// CONVERT DATA
	if ($_POST[checkimage]=="non-rejected") {
		$norejects = 1;
	} elseif ($_POST[checkimage]=="best") {
		$norejects = 1;
		$bestimages = 1;
	} else {
		$norejects = 0;
		$bestimages = 0;
	}
	$nowait = ($_POST['nowait']=="on") ? false : true;
	$background = ($_POST['background']=="on") ? true : false;
	$shuffle = ($_POST['shuffle']=="on") ? true : false;
	$reverse = ($_POST['reverse']=="on") ? true : false;
	$limit = $_POST['limit'];
	$tiltangle = $_POST['tiltangle'];
	$apcontinue = $_POST['apcontinue'];
	$commit = ($_POST['commit']=="on") ? true : false;
	$runname = $_POST['runname'];
	$outdir = $_POST['outdir'];
	
	if ($outdir) {
		// make sure outdir ends with '/' and append run name
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$rundir = $outdir.$runname;
	}

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ",",", $testimage);
		$apcontinue = false;
	}

	// CREATE COMMAND
	$command="";
	$command .= " --projectid=".$_SESSION['projectId']." ";
	if ($testimage) $command.=" --mrclist=$testimage";
	elseif ($_POST['preset']) $command.=" --preset=".$_POST['preset'];
	$command.=" --session=".$_POST['sessionname'];
	$command.=" --runname=$runname";
	if ($outdir) $command.=" --rundir=$rundir";
	if ($norejects) $command.=" --no-rejects";
	if ($bestimages) $command.=" --best-images";
	if ($nowait) $command.=" --no-wait";
	if ($commit) $command.=" --commit";
	if ($background) $command.=" --background";
	if ($reverse) $command.=" --reverse";
	if ($shuffle) $command.=" --shuffle";
	if ($limit) $command.=" --limit=$limit";

	if ($tiltangle != '' && $tiltangle != 'all') $command.=" --tiltangle=$tiltangle";
	if (!$apcontinue) $command.=" --no-continue";
	else $command.=" --continue";

	return $command;
}

function checkAppionErrors () {
	if (!$_POST[outdir]) {
		return "<B>ERROR:</B> Select an experiment session";
		exit;
	}
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		else {
			return ("<B>ERROR:</B> Specify an mrc file to test these parameters");
			exit;
		}
	}
	elseif ($_POST['sessionname']) {
		if ($_POST['preset']) $dbimages=$_POST[sessionname].",".$_POST[preset];
		elseif(!$_POST['alldbimages']) {
			return ("<B>ERROR:</B> Select an image preset for template matching");
			exit;
		}
	}


	return false;
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

function createParticleLoopTable ($defthresh, $defmaxthresh) {
	echo "<!-- BEGIN Particle Loop Param -->\n";
	$threshv = ($_POST['thresh']) ? $_POST['thresh'] : $defthresh;
	$maxthreshv = ($_POST['maxthresh']) ? $_POST['maxthresh'] : $defmaxthresh;
	$lpv = ($_POST['lp'] || $_POST['process']) ? $_POST['lp'] : '5';
	$hpv = ($_POST['hp'] || $_POST['process']) ? $_POST['hp'] : '600';
	$binv = (int) ($_POST['bin']) ? $_POST['bin'] : '4';
	$medianv = (int) ($_POST['median'] || $_POST['process']) ? $_POST['median'] : '2';
	$pixlimitv = ($_POST['pixlimit'] || $_POST['process']) ? $_POST['pixlimit'] : '4.0';
	$maxpeaksv = (int) ($_POST['maxpeaks']) ? $_POST['maxpeaks'] : '1500';
	$maxsizev = ($_POST['maxsize']) ? $_POST['maxsize'] : '1.0';
	$overlapmultv = ($_POST['overlapmult']) ? $_POST['overlapmult'] : '1.5';
	$invertv = ($_POST['invert']=="on") ? "CHECKED" : "";
	$nojpegsv = ($_POST['nojpegs']=="on") ? "CHECKED" : "";
	$defocpairv = ($_POST['defocpair']=="on") ? "CHECKED" : "";
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
	echo "<br />\n";
	echo "<B>Defocal pairs:</B><br />\n";
	echo "<input type='checkbox' name='defocpair' $defocpairv>\n";
	echo docpop('defocpair',' Calculate shifts for defocal pairs');
	echo "<br />\n";
	echo "<br />\n";

	echo "<b>Advanced options:</b><br />\n";
	if ($defthresh != -1) {
		echo "<input type='text' name='maxsize' VALUE='$maxsizev' size='4'>\n";
		echo docpop('maxsize','Maximum peak area multiple');
		echo "<br />\n";
		echo "<input type='text' name='overlapmult' VALUE='$overlapmultv' size='4'>\n";
		echo docpop('overlapmult',' Minimum peak overlap distance multiple');
		echo "<br />\n";
	}
	else {
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
	$thresh = $_POST[thresh];
	$maxthresh = $_POST[maxthresh];
	$maxpeaks = $_POST[maxpeaks];
	$lp = $_POST[lp];
	$hp = $_POST[hp];
	$median = $_POST[median];
	$pixlimit = $_POST[pixlimit];
	$bin = $_POST[bin];
	$diam = $_POST[diam];
	$defocpair = ($_POST[defocpair]=="on") ? "1" : "0";
	$nojpegs = ($_POST[nojpegs]=="on") ? "1" : "0";
	$maxsize = $_POST[maxsize];
	$overlapmult = $_POST[overlapmult];
	$invert = ($_POST[invert]=="on") ? "1" : "0";

	// CREATE COMMAND
	if ($type != "manual") {
		if ($maxsize && $maxsize > 0 && $maxsize != 1.0) $command.=" --maxsize=$maxsize";
		if ($overlapmult && $overlapmult > 0 && $overlapmult != 1.5) $command.=" --overlapmult=$overlapmult";
		if ($maxthresh && $maxthresh > 0) $command.=" --maxthresh=$maxthresh";
		if ($maxpeaks && $maxpeaks > 0 && $maxpeaks != 1500) $command.=" --maxpeaks=$maxpeaks";
		if ($thresh) $command.=" --thresh=$thresh";
	}
	if ($defocpair) $command.=" --defocpair";
	if ($invert) $command.=" --invert";
	if ($median != '') $command.=" --median=$median";
	if ($lp != '') $command.=" --lowpass=$lp";
	if ($hp != '') $command.=" --highpass=$hp";
	if ($bin) $command.=" --bin=$bin";
	if ($diam) $command.=" --diam=$diam";
	if ($pixlimit != '') $command.=" --pixlimit=$pixlimit";
	if ($nojpegs) $command.=" --nojpegs";

	return $command;
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
	$defocpair = ($_POST[defocpair]=="on") ? "0" : "1";
	$maxsize = $_POST[maxsize];
	$overlapmult = $_POST[overlapmult];
	$invert = ($_POST[invert]=="on") ? "1" : "0";

	echo "<TR><TD>thresh</TD><TD>$thresh</TD></TR>\n";
	echo "<TR><TD>maxthresh</TD><TD>$maxthresh</TD></TR>\n";
	echo "<TR><TD>maxpeaks</TD><TD>$maxpeaks</TD></TR>\n";
	echo "<TR><TD>lp</TD><TD>$lp</TD></TR>\n";
	echo "<TR><TD>hp</TD><TD>$hp</TD></TR>\n";
	echo "<TR><TD>median</TD><TD>$median</TD></TR>\n";
	echo "<TR><TD>bin</TD><TD>$bin</TD></TR>\n";
	echo "<TR><TD>defocpair</TD><TD>$defocpair</TD></TR>\n";
	echo "<TR><TD>maxsize</TD><TD>$maxsize</TD></TR>\n";
	echo "<TR><TD>overlapmult</TD><TD>$overlapmult</TD></TR>\n";
	echo "<TR><TD>invert</TD><TD>$invert</TD></TR>\n";
}

?>
