<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

require_once "inc/particledata.inc";

function createAppionLoopTable ($sessiondata, $defrunname, $outdirname, $leginon=0, $desc=False) {
	echo "<!-- BEGIN Appion Loop Param -->\n";
	$norejects = ($_POST[norejects]=="on") ? "CHECKED" : "";
	$nowait = ($_POST[nowait]=="") ? "" : "CHECKED";
	$background = ($_POST[background]=="on") ? "CHECKED" : "";
	$shuffle = ($_POST['shuffle']=="on") ? "CHECKED" : "";
	$reverse = ($_POST['reverse']=="on") ? "CHECKED" : "";
	$limit = $_POST[limit];
	$tiltangle = $_POST['tiltangle'];
	// commit is checkmarked by default
	$commit = ($_POST['commit']=="on" || !$_POST['process']) ? "CHECKED" : "";
	$apcontinue = $_POST['apcontinue'];
	// continue is checkmarked by default
	$apcontinuecheck = ($apcontinue || !$_POST['process']) ? "CHECKED" : "";
	$apreproccheck = (!$apcontinue && $_POST['process']) ? "CHECKED" : "";
	$normordercheck = ($_POST['imgorder'] == 'normal' || !$_POST['imgorder']) ? "CHECKED" : "";
	$reversecheck = ($_POST['imgorder'] == 'reverse') ? "CHECKED" : "";
	$shufflecheck = ($_POST['imgorder'] == 'shuffle') ? "CHECKED" : "";

	if ($_POST['preset']) $dbimages=$_POST['sessionname'].",".$_POST['preset'];
	else $alldbimages = $_POST['sessionname'];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	$runname = ($_POST['runname']) ? $_POST['runname'] : $defrunname;
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

	// write description entry
	if ($desc!=False) {
		if ($desc==1) $desc='';
		echo "<br>\n";
		echo docpop('stackdescr','<b>Stack Description:</b>');
		echo "<br>\n";
		echo "<textarea name='description' rows='2' cols='50'>$desc</textarea>\n";
		echo "<br>\n";
	}
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
		echo"</SELECT><br/>\n";
	} elseif ($presets) {
		//only one preset
		echo"<B>Preset:</B>&nbsp;&nbsp;".$presets[0]."\n\n";
		echo"<input type='hidden' name='preset' VALUE=".$presets[0]."><br/>\n";
	} else {
		//no presets
		echo"<input type='hidden' name='alldbimages' VALUE=1>\n";
		echo"<I>No presets for this session<br/>\n"
			."processing ALL images</I><br/>\n";
	}

	echo "<hr/>\n";
	echo "<input type='hidden' name='sessionname' value='$sessionname'>\n";

	$particle = new particledata();
	$maxang = $particle->getMaxTiltAngle($_GET['expId']);
	if ($maxang > 5) {
		if ($tiltangle == 'all') $allcheck = 'selected';
		elseif ($tiltangle == 'notilt') $notiltcheck = 'selected';
		elseif ($tiltangle == 'hightilt') $hightiltcheck = 'selected';
		elseif ($tiltangle == 'lowtilt') $lowtiltcheck = 'selected';
		elseif ($tiltangle == 'minustilt') $minustiltcheck = 'selected';
		elseif ($tiltangle == 'plustilt') $plustiltcheck = 'selected';
		echo docpop('tiltangle','Tilt Angle:');
		echo "<select name='tiltangle'>\n";
		echo "  <option value='all' $allcheck>all tilt angles</option>\n";
		echo "  <option value='notilt' $notiltcheck>zero tilt angles only</option>\n";
		echo "  <option value='hightilt' $hightiltcheck>large tilt angles only</option>\n";
		echo "  <option value='lowtilt' $lowtiltcheck>small tilt angles only</option>\n";
		echo "  <option value='minustilt' $minustiltcheck>negative tilt angles only</option>\n";
		echo "  <option value='plustilt' $plustiltcheck>positive tilt angles only</option>\n";
		echo "</select>";
		echo "<br />\n";
	} else
		echo "<input type='hidden' name='tiltangle' value='all'>\n";

	echo "<input type='checkbox' name='nowait' $nowait>\n";
	echo docpop('nowait','Wait for more images after finishing');
	echo "<br />\n";

	echo "<input type='checkbox' name='background' $background>\n";
	echo docpop('background','Run in background mode');
	echo "<br />\n";

	echo docpop('limit','Limit: ');
	echo "only process&nbsp; <input type='texlt' name='limit' VALUE='$limit' size='4'>&nbsp; images\n";
	echo "<br />\n";

	echo docpop('checkimages','<i>Images to process:</i>');
	echo "<br/>\n";
	echo "&nbsp;<input type='radio' name='checkimage' value='unrejected' ";
	if ($_POST['checkimage'] == 'unrejected' || !$_POST['checkimage']) echo "checked";
	echo ">\n";
	echo "Do not process hidden or rejected images <font size=-2><i>(default)</i></font><br/>\n";
	echo "&nbsp;<input type='radio' name='checkimage' value='all' ";
	if ($_POST['checkimage'] == 'all') echo "checked";
	echo ">\n";
	echo "All images independent of status <br/>\n";
	echo "&nbsp;<input type='radio' name='checkimage' value='best' ";
	if ($_POST['checkimage'] == 'best') echo "checked";
	echo ">\n";
	echo "Exemplar and keep images only<br/>\n";

	echo docpop('imgorder','<i>Image order:</i>'); 
	echo "<br/>\n";
	echo "&nbsp;<input type='radio' name='imgorder' value='normal' $normordercheck>\n";
	echo "Forward <font size=-2><i>(default)</i></font>\n";
	echo "&nbsp;<input type='radio' name='imgorder' value='reverse' $reversecheck>\n";
	echo "Reverse\n";
	echo "&nbsp;<input type='radio' name='imgorder' value='shuffle' $shufflecheck>\n";
	echo "Shuffle<br/>\n";

	echo docpop('cont','<i>Continuation:</i>'); 
	echo "<br />\n";
	echo "&nbsp;<input type='radio' name='apcontinue' value='1' $apcontinuecheck>\n";
	echo "Continue unfinished run <font size=-2><i>(default)</i></font><br/>\n";
	echo "&nbsp;<input type='radio' name='apcontinue' value='0' $apreproccheck>\n";
	echo "Reprocess all images<br/>\n";

	echo "<hr/>\n";
	echo "<input type='checkbox' name='commit' $commit>\n";
	echo docpop('commit','<b>Commit results to database</b>');
	echo "<br/>\n";
	echo "<hr/>\n";
	echo "<!-- END Appion Loop Param -->\n";
};

function appionLoopSummaryTable () {
	if ($_POST[checkimage]=="unrejected") {
		$norejects = "<font color='green'>true</font>";
		$bestimages = "<font color='red'>false</font>";
	} elseif ($_POST[checkimage]=="best") {
		$norejects = "<font color='green'>true</font>";
		$bestimages = "<font color='green'>true</font>";
	} else {
		$norejects = "<font color='red'>false</font>";
		$bestimages = "<font color='red'>false</font>";
	}
	$nowait = ($_POST[nowait]=="on") ? "<font color='red'>false</font>" : "<font color='green'>true</font>";
	$background = ($_POST[background]=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$shuffle = ($_POST['imgorder']=="shuffle") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$reverse = ($_POST['imgorder']=="reverse") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$limit = ($_POST[limit]) ? $_POST[limit] : "all";
	$tiltangle = $_POST['tiltangle'];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$runname = $_POST[runname];
	$reverse = ($_POST['reverse']=="on") ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ",",,", $testimage);
		$testimage = ereg_replace(",,",",",$testimage);
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
	// CONVERT DATA
	if ($_POST[checkimage]=="unrejected") {
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
	$shuffle = ($_POST['imgorder']=="shuffle") ? true : false;
	$reverse = ($_POST['imgorder']=="reverse") ? true : false;
	$limit = $_POST['limit'];
	$tiltangle = $_POST['tiltangle'];
	$apcontinue = $_POST['apcontinue'];
	$commit = ($_POST['commit']=='on') ? true : false;
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
		$testimage = ereg_replace(",,",",", $testimage);
		$apcontinue = false;
	}

	// CREATE COMMAND
	$command=" ";
	$command .= " --projectid=".$_SESSION['projectId']." ";
	if ($testimage) $command.=" --mrclist=$testimage";
	elseif ($_POST['preset']) $command.=" --preset=".$_POST['preset'];
	$command.=" --session=".$_POST['sessionname'];
	$command.=" --runname=$runname";
	if ($outdir) $command.=" --rundir=$rundir";
	if ($norejects) $command.=" --no-rejects";
	if ($bestimages) $command.=" --best-images";
	if ($nowait) $command.=" --no-wait";
	if ($commit)
		$command.=" --commit";
	else
		$command.=" --no-commit";
	if ($background) $command.=" --background";
	if ($reverse) $command.=" --reverse";
	if ($shuffle) $command.=" --shuffle";
	if ($limit) $command.=" --limit=$limit";

	if ($tiltangle != '' && $tiltangle != 'all') $command.=" --tiltangle=$tiltangle";
	if (!$apcontinue) $command.=" --no-continue";
	else $command.=" --continue";

	return $command." ";
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
	$lpv = ($_POST['lp'] || $_POST['process']) ? $_POST['lp'] : '15';
	$hpv = ($_POST['hp'] || $_POST['process']) ? $_POST['hp'] : '0';
	$binv = (int) ($_POST['bin']) ? $_POST['bin'] : '4';
	$medianv = (int) ($_POST['median'] || $_POST['process']) ? $_POST['median'] : '2';
	$pixlimitv = ($_POST['pixlimit'] || $_POST['process']) ? $_POST['pixlimit'] : '4.0';
	$maxpeaksv = (int) ($_POST['maxpeaks']) ? $_POST['maxpeaks'] : '1500';
	$maxsizev = ($_POST['maxsize']) ? $_POST['maxsize'] : '0.1';
	$overlapmultv = ($_POST['overlapmult']) ? $_POST['overlapmult'] : '1.5';
	$centerofmasscheck = ($_POST['peaktype'] && $_POST['peaktype']!='centerofmass') ? '' : 'CHECKED';
	$maximumcheck = ($_POST['peaktype']=='maximum') ? 'CHECKED' : '';
	$invertv = ($_POST['invert']=="on") ? "CHECKED" : "";
	$nojpegsv = ($_POST['nojpegs']=="on") ? "CHECKED" : "";
	$defocpairv = ($_POST['defocpair']=="on") ? "CHECKED" : "";
	$doublesv = ($_POST['doubles']=="on") ? "CHECKED" : "";
	$planeregv = ($_POST['planereg']=="off") ? "" : "CHECKED";

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
		echo "&nbsp;<input type='radio' name='peaktype' value='maximum' $maximumcheck DISABLED>\n";
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
