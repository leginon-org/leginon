<?php

/**
 *	The Appion software is Copyright 2007
 *	The Scripps Research Institute, La Jolla, CA
 */

function appionLoopJavaCommands () {
	$javafunc = "
<SCRIPT LANGUAGE='JavaScript'>
function appioninfopopup(infoname){
	var newwindow=window.open('','name','height=250, width=400');
	newwindow.document.write('<HTML><BODY>');
	if (infoname=='norejects'){
		newwindow.document.write('If images have been assessed checking this will included REJECTED images from the assessment when unchecked only unassessed and GOOD images will be processed. Unchecking this saves computer time.');
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
	newwindow.document.write('</BODY></HTML>');
	newwindow.document.close();
}
</SCRIPT>\n";
	return $javafunc;

}

function createAppionLoopTable ($sessiondata, $defrunid, $outdirname, $leginon=0) {
	echo "<!-- BEGIN Appion Loop Param -->";
	$norejects = ($_POST[norejects]=="on") ? "CHECKED" : "";
	$nowait = ($_POST[nowait]=="" && $_POST[runid] != "") ? "" : "CHECKED";
	$background = ($_POST[background]=="on") ? "CHECKED" : "";
	$shuffle = ($_POST[shuffle]=="on") ? "CHECKED" : "";
	$limit = $_POST[limit];
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
	echo "<A HREF=\"javascript:infopopup('runid')\"><B>Run Name:</B></A>
	    <INPUT TYPE='text' NAME='runid' VALUE='$runid'><BR/><BR/>";
	
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
	echo"&nbsp;&nbsp;&nbsp;Output Directory<BR/>
	    <INPUT TYPE='text' NAME='outdir' VALUE='$outdir' SIZE='45'><BR/><BR/>";

	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$presets=$sessiondata['presets'];
	if ($presets) {
		echo"<B>Preset</B>\n<SELECT NAME='preset'>\n";
		foreach ($presets as $preset) {
			echo "<OPTION VALUE='$preset' ";
			// make en selected by default
			if ($preset==$presetval) echo "SELECTED";
			echo ">$preset</OPTION>\n";
		}
		echo"</SELECT><br/><br/>\n";
	}
	else {
		echo"<INPUT TYPE='hidden' NAME='alldbimages' VALUE=1>\n";
		echo"<I>No Presets for this Session<br/>\n"
			."Will Process ALL Images</I><BR/>\n";
	}

	echo "
<HR style='margin: 1em 1em 1em 0; border: 1px #333333 solid; border-collapse: collapse;'>
<INPUT TYPE='hidden' name='sessionname' value='$sessionname'>

<INPUT TYPE='checkbox' NAME='norejects' $norejects>
<A HREF=\"javascript:appioninfopopup('norejects')\">
Process rejected images</A><br/>

<INPUT TYPE='checkbox' NAME='nowait' $nowait>
<A HREF=\"javascript:appioninfopopup('nowait')\">
Wait for more images after finishing</A><br/>

<INPUT TYPE='checkbox' NAME='background' $background>
<A HREF=\"javascript:appioninfopopup('background')\">
Run in background mode</A><br/>

<INPUT TYPE='checkbox' NAME='shuffle' $shuffle>
<A HREF=\"javascript:appioninfopopup('shuffle')\">
Shuffle the images</A><br/>

<A HREF=\"javascript:appioninfopopup('limit')\">
Limit</A>: only process&nbsp;
<INPUT TYPE='text' NAME='limit' VALUE='$limit' SIZE='4'>&nbsp;
images<br/>

<A HREF=\"javascript:appioninfopopup('continue')\">
<I>Continuation:</I></A><br/>
<INPUT TYPE='radio' NAME='apcontinue' VALUE='1' $apcontinuecheck>
Continue unfinished run <FONT SIZE=-2><I>(default)</I></FONT><br/>
<INPUT TYPE='radio' NAME='apcontinue' VALUE='0' $apreproccheck>
Reprocess all images<br/><br/>

<HR style='margin: 1em 1em 1em 0; border: 1px #333333 solid;
 border-collapse: collapse;'>

<INPUT TYPE='checkbox' NAME='commit' $commit>
<A HREF=\"javascript:appioninfopopup('commit')\">
<B>Commit results to database</B></A><br/>
";
	echo "<!-- END Appion Loop Param -->";
};

function appionLoopSummaryTable () {
	$norejects = ($_POST[norejects]=="on") ? "0" : "1";
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$background = ($_POST[background]=="on") ? "1" : "0";
	$shuffle = ($_POST[shuffle]=="on") ? "1" : "0";
	$limit = $_POST[limit];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$runid = $_POST[runid];
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	echo "<TR><TD>runid</TD><TD>$runid</TD></TR>\n";
	echo "<TR><TD>outdir</TD><TD>$outdir</TD></TR>\n";
	echo "<TR><TD>norejects</TD><TD>$norejects</TD></TR>\n";
	echo "<TR><TD>nowait</TD><TD>$nowait</TD></TR>\n";
	echo "<TR><TD>commit</TD><TD>$commit</TD></TR>\n";
	echo "<TR><TD>background</TD><TD>$background</TD></TR>\n";
	echo "<TR><TD>shuffle</TD><TD>$shuffle</TD></TR>\n";
	echo "<TR><TD>limit</TD><TD>$limit</TD></TR>\n";
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
	$norejects = ($_POST[norejects]=="on") ? "0" : "1";
	$nowait = ($_POST[nowait]=="on") ? "0" : "1";
	$background = ($_POST[background]=="on") ? "1" : "0";
	$shuffle = ($_POST[shuffle]=="on") ? "1" : "0";
	$limit = $_POST[limit];
	$apcontinue = $_POST[apcontinue];
	$commit = ($_POST[commit]=="on") ? "1" : "0";
	$runid = $_POST[runid];
	$outdir = $_POST[outdir];
	if ($_POST[preset]) $dbimages=$_POST[sessionname].",".$_POST[preset];
	else $alldbimages = $_POST[sessionname];
	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$apcontinue = false;
	}

	// CREATE COMMAND
	if ($runid) $command.=" runid=$runid";
	if ($outdir) $command.=" outdir=$outdir";
	if ($testimage) $command.=" $testimage";
	elseif ($dbimages) $command.=" dbimages=$dbimages";
	else $command.=" alldbimages=$_POST[sessionname]";
	if ($norejects) $command.=" norejects";
	if ($nowait) $command.=" nowait";
	if ($commit) $command.=" commit";
	if ($background) $command.=" background";
	if ($shuffle) $command.=" shuffle";
	if ($limit) $command.=" limit=$limit";
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
<SCRIPT LANGUAGE='JavaScript'>
function particleinfopopup(infoname){
	var newwindow=window.open('','name','height=250, width=400');
	newwindow.document.write('<HTML><BODY>');
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
	if (infoname=='invert'){
		newwindow.document.write('Sometimes the template is inverted to the images or dogPicker needs inverted images in this case use the invert flag.');
	}
	newwindow.document.write('</BODY></HTML>');
	newwindow.document.close();
}
</SCRIPT>\n";

	return $javafunc;
}


function createParticleLoopTable ($defthresh, $defmaxthresh) {
	echo "<!-- BEGIN Particle Loop Param -->";
//	prettytable2();
//	<TR><TD BGCOLOR=#660000 ALIGN=CENTER><FONT COLOR=#DDDDDD>Appion Loop Params</FONT></TD></TR>
	$threshv = ($_POST['thresh']) ? $_POST['thresh'] : $defthresh;
	$maxthreshv = ($_POST['maxthresh']) ? $_POST['maxthresh'] : $defmaxthresh;
	$lpv = ($_POST['lp'] || $_POST['process']) ? $_POST['lp'] : '5';
	$hpv = ($_POST['hp'] || $_POST['process']) ? $_POST['hp'] : '600';
	$binv = ($_POST['bin']) ? $_POST['bin'] : '4';
	$medianv = ($_POST['median'] || $_POST['process']) ? $_POST['median'] : '2';
	$maxpeaksv = ($_POST['maxpeaks']) ? $_POST['maxpeaks'] : '1500';
	$maxsizev = ($_POST['maxsize']) ? $_POST['maxsize'] : '1.0';
	$overlapmultv = ($_POST['overlapmult']) ? $_POST['overlapmult'] : '1.5';
	$invertv = ($_POST['invert']=="on") ? "CHECKED" : "";
	$defocpairv = ($_POST['defocpair']=="on") ? "CHECKED" : "";
	if ($defthresh != -1) {
		echo "
<B>Peak thresholds:</B><br/>

<INPUT TYPE='text' NAME='thresh' VALUE='$threshv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('thresh')\">
Minimum threshold</A><br/>

<INPUT TYPE='text' NAME='maxthresh' VALUE='$maxthreshv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('maxthresh')\">
Maximum threshold</A><br/>

<INPUT TYPE='text' NAME='maxpeaks' VALUE='$maxpeaksv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('maxpeaks')\">
Max number of particles allowed per image</A><br/>
<br/>
";
	}
	echo"
<B>Filter Values:</B><br/>

<INPUT TYPE='text' NAME='lp' VALUE='$lpv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('lp')\">
Low Pass</A> <FONT SIZE=-2><I>(in &Aring;ngstroms; 0 = off)</I></FONT><br/>

<INPUT TYPE='text' NAME='hp' VALUE='$hpv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('hp')\">
High Pass</A> <FONT SIZE=-2><I>(in &Aring;ngstroms; 0 = off)</I></FONT><br/>

<INPUT TYPE='text' NAME='median' VALUE='$medianv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('median')\">
Median</A> <FONT SIZE=-2><I>(in Pixels; 0 = off)</I></FONT><br/>

<INPUT TYPE='text' NAME='bin' VALUE='$binv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('bin')\">
Binning</A> <FONT SIZE=-2><I>(power of 2)</I></FONT><br/>
<br/>

<B>Defocal pairs:</B><br/>
<INPUT TYPE='checkbox' NAME='defocpair' $defocpairv>&nbsp;
<A HREF=\"javascript:particleinfopopup('defocpair')\">
Calculate shifts for defocal pairs</A><br/>
<br/>
<B>Advanced peak characteristics:</B><br/>";
	if ($defthresh != -1) {
		echo "

<INPUT TYPE='text' NAME='maxsize' VALUE='$maxsizev' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('maxsize')\">
Maximum peak area multiple</A><br/>

<INPUT TYPE='text' NAME='overlapmult' VALUE='$overlapmultv' SIZE='4'>&nbsp;
<A HREF=\"javascript:particleinfopopup('overlapmult')\">
Minimum peak overlap distance multiple</A><br/>";
	}
	echo "
<INPUT TYPE='checkbox' NAME='invert' $invertv>&nbsp;
<A HREF=\"javascript:particleinfopopup('invert')\">
Invert image density</A><br/>
<br/>
";
	echo "<!-- END Particle Loop Param -->";
};

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
	$bin = $_POST[bin];
	$diam = $_POST[diam];
	$defocpair = ($_POST[defocpair]=="on") ? "1" : "0";
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
