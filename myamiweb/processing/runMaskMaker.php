<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
 
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runMaskMaker();
}
// CREATE FORM PAGE
else {
	createMMForm();
}

function createMaskMakerTable ($cannyminthresh, $cannymaxthresh) {
	echo "<!-- BEGIN Mask Maker Param -->";
//	prettytable2();
//	<TR><td BGCOLOR=#660000 ALIGN=CENTER><FONT COLOR=#DDDDDD>Appion Loop Params</FONT></td></tr>
	$blur = ($_POST['blur']) ? $_POST['blur'] : '3.5';
	$minthresh = ($_POST['minthresh']) ? $_POST['minthresh'] : $cannyminthresh;
	$maxthresh = ($_POST['maxthresh']) ? $_POST['maxthresh'] : $cannymaxthresh;
	$bin = ($_POST['bin']) ? $_POST['bin'] : '4';
	$crudstd = ($_POST['crudstd']) ? $_POST['crudstd'] : '';
	$convolve = ($_POST['convolve']) ? $_POST['convolve'] : '';
	$masktype = ($_POST['masktype']) ? $_POST['masktype'] : '';
	$masktypes = array('crud','edge','aggr');
	$masktypeval = ($_POST['masktype']) ? $_POST['masktype'] : 'crud';
	$masktype = $masktypeval;
	echo docpop('masktype','<b>Mask Type : </b>');
	echo "\n<SELECT NAME='masktype'>\n";
	foreach ($masktypes as $masktype) {
		echo "<OPTION VALUE='$masktype' ";
		// make crud selected by default
		if ($masktype==$masktypeval) echo "SELECTED";
		echo ">$masktype</OPTION>\n";
	}
	echo"</SELECT><br><br>\n";
	echo "
		<B>Canny Edge thresholds:</B><br>
		<INPUT TYPE='text' NAME='blur' VALUE='$blur' SIZE='4'>\n";
	echo docpop('blur','Gradient bluring');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='maxthresh' VALUE='$maxthresh' SIZE='4'>\n";
	echo docpop('crudmaxthresh','High threshold for the start of edge detection');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='minthresh' VALUE='$minthresh' SIZE='4'>\n";
	echo docpop('crudminthresh','Low threshold for edge extension');
	echo "<br /><br />\n";
	echo "<B>Image Option:</B><br />\n";
	echo "<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>\n";
	echo docpop('binval','Binning');
	echo "<br /><br />\n";
	echo "<B>Advanced thresholding:</B><br />\n";
	echo "<INPUT TYPE='text' NAME='crudstd' VALUE='$crudstd' SIZE='4'>\n";
	echo docpop('crudstd','Standard deviation threshold');
	echo "<br />\n";
	echo "<INPUT TYPE='text' NAME='convolve' VALUE='$convolve' SIZE='4'>\n";
	echo docpop('convolve','Convoluted map threshold for aggregate mask (0.0-1.0)');
	echo "<br />\n";

	echo "<!-- END Mask Maker Param -->";
};

function parseMaskMakerParams () {
	$diam = $_POST[diam];
	$cdiam = $_POST[cdiam];
	$minthresh = $_POST[minthresh];
	$maxthresh = $_POST[maxthresh];
	$blur = $_POST[blur];
	$bin = $_POST[bin];
	$masktype = ($_POST[masktype]);
	$crudstd = $_POST[crudstd];
	$convolve = $_POST[convolve];

	$command .=" --diam=$diam";
	$command .=" --cruddiam=$cdiam";
	if ($maxthresh && $maxthresh > 0) $command.=" --crudhi=$maxthresh";
	if ($blur && $blur > 0.01) $command.=" --crudblur=$blur";
	if ($minthresh && $minthresh > 0) $command.=" --crudlo=$minthresh";
	if ($crudstd && $crudstd > 0.01 && $crudstd != '') $command.=" --crudstd=$crudstd";
	if ($masktype) $command.=" --masktype=$masktype";
	if ($convolve && $convolve > 0.01 && $convolve != '') $command.=" --convolve=$convolve";
	if ($bin && $bin > 0) $command.=" --bin=$bin";

	return $command;
}


function maskMakerSummaryTable () {
	$minthresh = $_POST[minthresh];
	$maxthresh = $_POST[maxthresh];
	$blur = $_POST[blur];
	$bin = $_POST[bin];
	$masktype = ($_POST[masktype]);
	$crudstd = $_POST[crudstd];
	$convolve = $_POST[convolve];

	echo "<tr><td>mask type</td><td>$masktype</td></tr>\n";
	echo "<tr><td>minthresh</td><td>$minthresh</td></tr>\n";
	echo "<tr><td>maxthresh</td><td>$maxthresh</td></tr>\n";
	echo "<tr><td>bin</td><td>$bin</td></tr>\n";
	echo "<tr><td>blur</td><td>$blur</td></tr>\n";
	echo "<tr><td>crudstd</td><td>$crudstd</td></tr>\n";
	echo "<tr><td>convolve</td><td>$convolve</td></tr>\n";
}


function createMMForm($extra=false, $title='MaskMaker Launcher', $heading='Automated Mask Region Finding with Maskmaker') {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=$_SESSION['projectId'];

	$javafunctions="
		<script src='../js/viewer.js'></script>
		<script LANGUAGE='JavaScript'>
			function enabledtest(){
				if (document.viewerform.testimage.checked){
					document.viewerform.testfilename.disabled=false;
					document.viewerform.testfilename.value='';
				}	else {
					document.viewerform.testfilename.disabled=true;
					document.viewerform.testfilename.value='mrc file name';
				}
			}
			function enable(thresh){
				if (thresh=='auto') {
					document.viewerform.autopik.disabled=false;
					document.viewerform.autopik.value='';
					document.viewerform.thresh.disabled=true;
					document.viewerform.thresh.value='0.4';
				 }
				if (thresh=='manual') {
					document.viewerform.thresh.disabled=false;
					document.viewerform.thresh.value='';
					document.viewerform.autopik.disabled=true;
					document.viewerform.autopik.value='100';
				}
			}
			function infopopup(infoname){
				var newwindow=window.open('','name','height=150,width=300');
				newwindow.document.write('<HTML><BODY>');
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		 }
		</script>\n";
	$javafunctions.=writeJavaPopupFunctions('appion');

	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	if ($results) echo "$results<hr>\n";
	echo"
		<form name='viewerform' method='POST' ACTION='$formAction'>
		<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

	// Set any existing parameters in form
	$particle=new particleData;
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApMaskMakerRunData','name'); 
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'maskrun'.($lastrunnumber+1);

	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	$diam = ($_POST['diam']) ? $_POST['diam'] :'';
	$cdiam = ($_POST['cdiam']) ? $_POST['cdiam'] :'';
	$process = ($_POST['process']) ? $_POST['process'] :'';
	echo"
		<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
			<tr>
				<td VALIGN='TOP'>";
	createAppionLoopTable($sessiondata, $defrunname, "mask");
	echo"
				</td>
				<td CLASS='tablebg'>
					<B>Particle Diameter:</B><br>
					<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
	echo docpop('pdiam','Particle diameter as reference for template');
	echo "	<FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>\n";
	echo "	<br /><br />";
	echo"
					<B>Minimal Mask Region Diameter:</B><br>
					<INPUT TYPE='text' NAME='cdiam' VALUE='$cdiam' SIZE='4'>&nbsp;
						Mask Region diameter as lower area/perimeter threshold <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
					<br><br>";

	createMaskMakerTable(0.6,0.95);
	echo "
				</td>
			</tr>
			<tr>
				<td COLSPAN='2' ALIGN='CENTER'>
					<HR>
					<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
						Test these setting on image:
					<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
					<hr>
				</td>
			</tr>
			<tr>
				<td COLSPAN='2' ALIGN='CENTER'>
	";
	echo getSubmitForm("Run MaskMaker");
	echo "
				</td>
			</tr>
		</table>
	</td>
	</tr>
	</table>\n";
	?>

	</CENTER>
	</FORM>
	<?
	processing_footer();
}
function runMaskMaker() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];
	$process = $_POST['process'];

	$diam = $_POST[diam];
	if (!$diam) {
		createMMForm("<B>ERROR:</B> Specify a particle diameter");
		exit;
	}

	$convolve = $_POST[convolve];
	if (!$convolve && $_POST[masktype] == "aggr") {
		createMMForm("<B>ERROR:</B> Specify a convolution map threshold");
		exit;
	}

	$cdiam = $_POST[cdiam];
	if (!cdiam) {
		createMMForm("<B>ERROR:</B> No minimal mask region diameter");
		exit;
	}

	$command="maskmaker.py ";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMMForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	$command .= parseMaskMakerParams($_POST);
	if ($_POST['testimage']=="on") {
		$command .= " --test";
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	if ($testimage && $_POST['process']=="Run MaskMaker") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) createMMForm("<b>ERROR:</b> Enter a user name and password"); 
		$sub = submitAppionJob($command,$outdir,$runname,$expId,'maskmaker',False,True);
		// if errors:
		if ($sub) createMMForm("<b>ERROR:</b> $sub");
		exit;
	}

	#processing_header("Bad Region Detection Results","Bad Region Detection Results",$javascript);

	if ($testimage) {
		$outdir=$_POST[outdir];
		// make sure outdir ends with '/'
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$runname=$_POST[runname];
		echo  " <B>MaskMaker Command:</B><br>$command<HR>";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$testdir=$outdir.$runname."/tests/";
    if (file_exists($testdir)) {
     	// open image directory
     	$pathdir=opendir($testdir);
			// get all files in directory
			$ext='jpg';
			while ($filename=readdir($pathdir)) {
		   	if ($filename == '.' || $filename == '..') continue;
				if (preg_match('`\.'.$ext.'$`i',$filename)) $files[]=$filename;
			}
			closedir($pathdir);
		}
//		echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";
		if (count($files) > 0) 	{
			$images=displayTestResults($testimage,$testdir,$files);
		} else {
			echo "<FONT COLOR='RED'><B>NO RESULT YET</B><br></FONT>";
			echo "<FONT COLOR='RED'><B>Refresh this page when ready</B><br></FONT>";
		}

		createMMForm($images,'Particle Selection Results','');
		exit;
	} else {
		processing_header("Create Mask","Create Reusable Image Mask",$javafunctions,True);
	}
	echo"
		<TABLE WIDTH='600'>
			<tr>
				<td COLSPAN='2'>
					<B>Mask Maker Command:</B><br>
					$command<HR>
				</td>
			</tr>
			<tr>
				<td>outdir</td>
				<td>$outdir</td>
			</tr>";
	echo"
			<tr>
				<td>runname</td>
				<td>$runname</td>
			</tr>
			<tr>
				<td>dbimages</td>
				<td>$dbimages</td>
			</tr>
			<tr>
				<td>diameter</td>
				<td>$diam</td>
			</tr>";
	appionLoopSummaryTable();
	maskMakerSummaryTable();
	echo"</table>\n";
	processing_footer();
}


function displayTestResults($testimage,$imgdir,$files){
	echo "<CENTER>\n";

  $numfiles=count($files);
	$prefix = '';
	$n = 0;
	sort($files);
	
	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='0' WIDTH='400'>\n";
	echo"<tr><td ALIGN='LEFT'>\n";
  echo"<B>$testimage</B>\n";
	echo"</td></tr></table>";
	echo"<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='0'><tr>\n";
	$col = 0;
	$row = 0;
	$colcount = 4;
	while ($col+$colcount*$row < count($files)) {
		if ($col > $colcount-1) {
			$col = 0;
			$row = $row + 1;
			echo "</tr><tr>";
		}
		echo "<td>";	
		$imgindx = $col+$colcount*$row;
		$imgname=$files[$imgindx];
		$imgfull=$imgdir.$imgname;
		echo"<B>$imgname</B>\n<P>";
		echo"<img src='loadimg.php?filename=$imgfull&scale=0.25'><P>\n";
		echo "</td>";
		$col = $col + 1;
	}	
	echo"</tr></table>\n";
	echo "</CENTER>\n";
}
?>
