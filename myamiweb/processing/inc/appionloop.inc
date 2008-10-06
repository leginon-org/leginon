<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

function appionLoopJavaCommands () {
	$javafunc = "
<script LANGUAGE='JavaScript'>
function appioninfopopup(infoname){
	var newwindow=window.open('','name','height=250, width=400');
	newwindow.document.write('<html><BODY>');
	if (infoname=='checkimages'){
		newwindow.document.write('Choose what images to process here.  Images can be inspected by Viewer or ImageAssessor.  BEST images include ones inspected as KEEP or as EXAMPLOR in the viewer.  NON-REJECTED images include the BEST images above-mentioned and the uninspected ones and therefore exclude only the REJECTED or HIDDEN images.');
	}
	if (infoname=='runid'){
		newwindow.document.write('Specifies the name associated with the processing results unique to the specified session and parameters. An attempt to use the same run name for a session using different processing parameters will result in an error.');
	}
	if (infoname=='nowait'){
		newwindow.document.write('By default the program will check to see if Leginon has collected more images after finishing for 2 hours. If this is unchecked then when the program finishes it will immediately stop.');
	}
	if (infoname=='background'){
		newwindow.document.write('This a feature the turns off some of the fancy output used when the program runs');
	}
	if (infoname=='shuffle'){
		newwindow.document.write('The shuffle feature shuffles the order of the images before the processing begins that way you do not always start from the beginning.');
	}
	if (infoname=='limit'){
		newwindow.document.write('If you do not want to process all the images, enter a number and the program will only process this number of images. Good for testing a few images before committing the results to the database.');
	}
	if (infoname=='continue'){
		newwindow.document.write('By default you ALWAYS want to continue, unless you are NOT committing to the database yet and you want to reprocess an image.');
	}
	if (infoname=='commit'){
		newwindow.document.write('This is the main checkbox of the program. When testing do NOT commit, but once you are happy with the results. Start commiting the data otherwise all information will be lost.');
	}
	newwindow.document.write('</BODY></html>');
	newwindow.document.close();
}
</script>\n";
	return $javafunc;

}

function createAppionLoopTable ($sessiondata, $defrunid, $outdirname, $leginon=0) {
	echo "<!-- BEGIN Appion Loop Param -->\n";
	$norejects = ($_POST[norejects]=="on") ? "CHECKED" : "";
	$nowait = ($_POST[nowait]=="" && $_POST[runid] != "") ? "" : "CHECKED";
	$background = ($_POST[background]=="on") ? "CHECKED" : "";
	$shuffle = ($_POST[shuffle]=="on") ? "CHECKED" : "";
	$limit = $_POST[limit];
	$tiltangle = $_POST[tiltangle];
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

	$runid = ($_POST[runid]) ? $_POST[runid] : $defrunid;
	echo openRoundBorder();
	echo docpop('runid','<b>Run Name:</b> ');
	echo "<input type='text' name='runid' VALUE='$runid'><BR/><BR/>\n";
	
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
	echo docpop('limit','Limit: ');
	echo "only process&nbsp; <input type='texlt' name='limit' VALUE='$limit' size='4'>&nbsp; images<br />\n";
	echo docpop('tiltangle','Tilt Angle:');
	echo "&nbsp; <input type='text' name='tiltangle' VALUE='$tiltangle' size='4'>&nbsp; degrees<br />\n";
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
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$background = ($_POST[background]=="on") ? "1" : "0";
	$shuffle = ($_POST[shuffle]=="on") ? "1" : "0";
	$limit = $_POST[limit];
	$tiltangle = $_POST[tiltangle];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$runid = $_POST[runid];
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ","\ ", $testimage);
	}

	echo "<TR><TD>runid</TD><TD>$runid</TD></TR>\n";
	echo "<TR><TD>outdir</TD><TD>$outdir</TD></TR>\n";
	echo "<TR><TD>norejects</TD><TD>$norejects</TD></TR>\n";
	echo "<TR><TD>bestimages</TD><TD>$bestimages</TD></TR>\n";
	echo "<TR><TD>nowait</TD><TD>$nowait</TD></TR>\n";
	echo "<TR><TD>commit</TD><TD>$commit</TD></TR>\n";
	echo "<TR><TD>background</TD><TD>$background</TD></TR>\n";
	echo "<TR><TD>shuffle</TD><TD>$shuffle</TD></TR>\n";
	echo "<TR><TD>limit</TD><TD>$limit</TD></TR>\n";
	echo "<TR><TD>tilt angle</TD><TD>$tiltangle</TD></TR>\n";
	echo "<TR><TD>continue</TD><TD>$apcontinue</TD></TR>\n";
}

function parseAppionLoopParams () {
	// CHECK FOR ERRORS
	$error = checkAppionErrors();
	if ($error[0] != false) {
		return $error;
		exit;
	}

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
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$background = ($_POST[background]=="on") ? "1" : "0";
	$shuffle = ($_POST[shuffle]=="on") ? "1" : "0";
	$limit = $_POST[limit];
	$tiltangle = $_POST[tiltangle];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$runid = $_POST[runid];
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ","\ ", $testimage);
		$apcontinue = false;
	}

	// CREATE COMMAND
	if ($testimage) $command.=" $testimage";
	elseif ($dbimages) $command.=" dbimages=$dbimages";
	else $command.=" alldbimages=$_POST[sessionname]";
	if ($runid) $command.=" runid=$runid";
	if ($outdir) $command.=" outdir=$outdir";
	if ($norejects) $command.=" norejects";
	if ($bestimages) $command.=" bestimages";
	if ($nowait) $command.=" nowait";
	if ($commit) $command.=" commit";
	if ($background) $command.=" background";
	if ($shuffle) $command.=" shuffle";
	if ($limit) $command.=" limit=$limit";
	if ($tiltangle) $command.=" tiltangle=$tiltangle";
	if (!$apcontinue) $command.=" nocontinue";
	else $command.=" continue";

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

function particleLoopJavaCommands () {
	$javafunc = "
<script LANGUAGE='JavaScript'>
function particleinfopopup(infoname){
	var newwindow=window.open('','name','height=250, width=400');
	newwindow.document.write('<html><BODY>');
	if (infoname=='thresh'){
		newwindow.document.write('Threshold for particle picking from the cross-correlation or dogpicker map. Any values above this threshold are considered particles.<br/>For template correlation, this should be between 0.0 and 1.0, typically 0.4 to 0.6 is used.<br/>For dogPicker, the values is in terms of standard deviations from the mean divided by four. Reasonable range from 0.4 to 3.0 with typical values falling between 0.7 and 1.0');
	}
	if (infoname=='maxthresh'){
		newwindow.document.write('Maximum threshold for particle picking from the cross-correlation or dogpicker map. Any values above this threshold are rejected.<br/>For template correlation, you probably do not need this, but typical values would be between 0.7 and 0.8.<br/>For dogPicker, the values is in terms of standard deviations from the mean divided by four. Reasonable range from 1.0 to 5.0 with typical values falling between 1.5 and 2.5');
	}
	if (infoname=='maxpeaks'){
		newwindow.document.write('This a feature limits the number of particles allowed in an image. By default it is set to 1500, but if you want no more than 50 particles an image fill in this value');
	}
	if (infoname=='lp'){
		newwindow.document.write('Low pass filtering of the image before picking. This should be about 1/10 to 1/50 of the particle diameter, <I>e.g.</I> for a particle with diameter 150 &Aring;, a low pass of 5-10 &Aring; works pretty good');
	}
	if (infoname=='hp'){
		newwindow.document.write('High pass filtering of the image before picking. This removes any darkness gradients in the image. Typically you could disable this by setting it equal to zero, otherwise 600 work pretty good. Warning this feature typically normalizes the crud so more particles get picked from crud.');
	}
	if (infoname=='median'){
		newwindow.document.write('Median filtering of the image before picking. This helps remove any noise spikes in the image. Typical values are 2, 3, or 5. The bigger the number the more information is thrown away.');
	}
	if (infoname=='bin'){
		newwindow.document.write('Binning of the image. This takes a power of 2 (1,2,4,8,16) and shrinks the image to help make the processing faster. Typically you want to use 4 or 8 depending on the quality of you templates.');
	}
	if (infoname=='defocpair'){
		newwindow.document.write('If defocal pairs were collected you want to use this. This feature takes both of the en and ef images and aligns them, so you can use makestack later.');
	}
	if (infoname=='maxsize'){
		newwindow.document.write('Max size multiple of the particle peak. When the peak is found in the thresholded image it has a size in pixels. Now if that size is greater than maxsize*particle diameter then the peak is rejected.');
	}
	if (infoname=='overlapmult'){
		newwindow.document.write('The overlap multiple specifies the minimum distance allowed between two peaks. If two peaks are closer than overlapmult*particle diameter the only the larger of the two peaks is retained.');
	}
	if (infoname=='pixlimit'){
		newwindow.document.write('Limit the values of the pixels to within this number of standard deviations from the mean. 0.0 turns this feature off.');
	}
	if (infoname=='kfactor'){
		newwindow.document.write('The k-factor for dogpicker defines the slopiness in diameter of the picked particles. A k-factor of 1.00001 gives only the exact diameter (1.0 is not allowed), but a k-factor of 5.0 will pick a wide range of sizes. Cannot be used with multi-scale dogpicker: numslices or sizerange');
	}
	if (infoname=='numslices'){
		newwindow.document.write('Defines the number of different sizes (or slices) to break up the size range into for separating particles of different size.');
	}
	if (infoname=='sizerange'){
		newwindow.document.write('Defines the range of sizes for separating particles of different size.');
	}
	if (infoname=='invert'){
		newwindow.document.write('Sometimes the template is inverted to the images or dogPicker needs inverted images in this case use the invert flag.');
	}
	if (infoname=='nojpegs'){
		newwindow.document.write('Do NOT write out the summary jpegs for image assessor.');
	}
	newwindow.document.write('</BODY></html>');
	newwindow.document.close();
}
</script>\n";

	return $javafunc;
}


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
		if ($maxsize && $maxsize > 0 && $maxsize != 1.0) $command.=" maxsize=$maxsize";
		if ($overlapmult && $overlapmult > 0 && $overlapmult != 1.5) $command.=" overlapmult=$overlapmult";
		if ($maxthresh && $maxthresh > 0) $command.=" maxthresh=$maxthresh";
		if ($maxpeaks && $maxpeaks > 0 && $maxpeaks != 1500) $command.=" maxpeaks=$maxpeaks";
		if ($thresh) $command.=" thresh=$thresh";
	}
	if ($defocpair) $command.=" defocpair";
	if ($invert) $command.=" invert";
	if ($median) $command.=" median=$median";
	if ($lp) $command.=" lp=$lp";
	if ($hp) $command.=" hp=$hp";
	if ($bin) $command.=" bin=$bin";
	if ($diam) $command.=" diam=$diam";
	if ($pixlimit) $command.=" pixlimit=$pixlimit";
	if ($nojpegs) $command.=" nojpegs";

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
