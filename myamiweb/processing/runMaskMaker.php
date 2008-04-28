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
//	<TR><TD BGCOLOR=#660000 ALIGN=CENTER><FONT COLOR=#DDDDDD>Appion Loop Params</FONT></TD></TR>
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
		echo"</SELECT><BR><BR>\n";
	echo "

<B>Canny Edge thresholds:</B><BR>

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
	$minthresh = $_POST[minthresh];
	$maxthresh = $_POST[maxthresh];
	$blur = $_POST[blur];
	$bin = $_POST[bin];
	$masktype = ($_POST[masktype]);
	$crudstd = $_POST[crudstd];
	$convolve = $_POST[convolve];

	if ($maxthresh && $maxthresh > 0) $command.=" crudhi=$maxthresh";
	if ($blur && $blur > 0.01) $command.=" crudblur=$blur";
	if ($minthresh && $minthresh > 0) $command.=" crudlo=$minthresh";
	if ($crudstd && $crudstd > 0.01 && $crudstd != '') $command.=" crudstd=$crudstd";
	if ($masktype) $command.=" masktype=$masktype";
	if ($convolve && $convolve > 0.01 && $convolve != '') $command.=" convolve=$convolve";
	if ($bin && $bin > 0) $command.=" bin=$bin";

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

	echo "<TR><TD>mask type</TD><TD>$masktype</TD></TR>\n";
	echo "<TR><TD>minthresh</TD><TD>$minthresh</TD></TR>\n";
	echo "<TR><TD>maxthresh</TD><TD>$maxthresh</TD></TR>\n";
	echo "<TR><TD>bin</TD><TD>$bin</TD></TR>\n";
	echo "<TR><TD>blur</TD><TD>$blur</TD></TR>\n";
	echo "<TR><TD>crudstd</TD><TD>$crudstd</TD></TR>\n";
	echo "<TR><TD>convolve</TD><TD>$convolve</TD></TR>\n";
}


function createMMForm($extra=false, $title='MaskMaker Launcher', $heading='Automated Mask Region Finding with Maskmaker') {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	if ($expId) {
		$sessionId=$expId;
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
		$sessionId=$_POST['sessionId'];
		$formAction=$_SERVER['PHP_SELF'];	
	}
	$projectId=$_POST['projectId'];

	// --- find hosts to run maskmaker 
	$hosts=getHosts();
 

	$particle=new particleData;
	$javascript="
	<script src='../js/viewer.js'></script>
	<script LANGUAGE='JavaScript'>
		 function enabledtest(){
			 if (document.viewerform.testimage.checked){
				 document.viewerform.testfilename.disabled=false;
				 document.viewerform.testfilename.value='';
			 }	
			 else {
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
			 if (infoname=='runid'){
				 newwindow.document.write('Specifies the name associated with the Template Correlator results unique to the specified session and parameters.	An attempt to use the same run name for a session using different Template Correlator parameters will result in an error.');
			 }
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		 }
	</SCRIPT>\n";
	$javascript.=appionLoopJavaCommands();
	$javascript.=writeJavaPopupFunctions('eman');

	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];

	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	$diam = ($_POST['diam']) ? $_POST['diam'] :'';
	$cdiam = ($_POST['cdiam']) ? $_POST['cdiam'] :'';
	$process = ($_POST['process']) ? $_POST['process'] :'';
	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>";
	$maskruns=count($particle->getMaskMakerRunIds($sessionId));
	$defrunid = ($_POST['runid']) ? $_POST['runid'] : 'maskrun'.($maskruns+1);
	createAppionLoopTable($sessiondata, $defrunid, "mask");
	echo"
		</TD>
		<TD CLASS='tablebg'>
			<B>Particle Diameter:</B><BR>
			<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
	echo docpop('pdiam','Particle diameter as reference for template');
	echo "<FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>\n";
	echo "<br /><br />";
	echo"
			<B>Minimal Mask Region Diameter:</B><BR>
			<INPUT TYPE='text' NAME='cdiam' VALUE='$cdiam' SIZE='4'>&nbsp;
			Mask Region diameter as lower area/perimeter threshold <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
			<BR><BR>";

		createMaskMakerTable(0.6,0.95);
		echo "
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these setting on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
		<HR>
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		Host: <select name='host'>\n";
	foreach($hosts as $host) {
		$s = ($_POST['host']==$host) ? 'selected' : '';
		echo "<option $s >$host</option>\n";
	}
	echo "</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run MaskMaker'><BR>
		<FONT class='apcomment'>Submission will NOT run MaskMaker, only output a command that you can copy and paste into a unix shell</FONT>
		</TD>
	</TR>
	</TABLE>
	</TD>
	</TR>
	</TABLE>\n";
	?>

	</CENTER>
	</FORM>
	<?
	writeBottom();
}
function runMaskMaker() {
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
	$command .=" diam=$diam";
	$command .=" cruddiam=$cdiam";
	$command .= parseMaskMakerParams($_POST);
	if ($_POST['testimage']=="on") {
		$command .= " test";
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
	}

	if ($testimage && $_POST['process']=="Run MaskMaker") {
		$host = $_POST['host'];
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) {
			createMMForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}
		$prefix = "source /ami/sw/ami.csh;";
		$prefix.= "source /ami/sw/share/python/usepython.csh cvs32;";
		$cmd = "$prefix webcaller.py '$command' maskMakerLog.txt";
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	writeTop("Bad Region Detection Results","Bad Region Detection Results",$javascript);

	if ($testimage) {
		$outdir=$_POST[outdir];
		// make sure outdir ends with '/'
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$runid=$_POST[runid];
		echo  " <B>MaskMaker Command:</B><BR>$command<HR>";
		$testjpg=ereg_replace(".mrc","",$testimage);
		$testdir=$outdir.$runid."/tests/";
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
			echo "<FONT COLOR='RED'><B>NO RESULT YET</B><BR>";
			echo "<FONT COLOR='RED'><B>Refresh this page when ready</B><BR>";
		}
		createMMForm($images,'Particle Selection Results','');
		exit;
	}


	echo"
  <P>
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>Mask Maker Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>";
	echo"<TR><TD>runname</TD><TD>$runid</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  <TR><TD>diameter</TD><TD>$diam</TD></TR>";
	appionLoopSummaryTable();
	maskMakerSummaryTable();
	echo"</TABLE>\n";
	writeBottom();
}


function displayTestResults($testimage,$imgdir,$files){
	echo "<CENTER>\n";
	echo"<form name='viewerform' method='POST' ACTION='$formAction'>\n";


        $numfiles=count($files);
	$prefix = '';
	$n = 0;

	sort($files);

	$imlst=($_POST['imagelist']) ? $_POST['imagelist'] : 'First';
        $imgindx= ($_POST['imgindex']) ? $_POST['imgindex'] : 0;
	$imgrescl= ($_POST['imgrescale']) ? $_POST['imgrescale'] : 0.25; 
	$process= ($_POST['process']) ? $_POST['process'] : '';
	// go directly to a particular image number
	if ($_POST['imgjump']) {
	        $imgindx=$_POST['imgjump']-1;
		// make sure it's within range
		if ($imgindx < 0) $imgindx=0;
		elseif ($imgindx > $numfiles-1) $imgindx=$numfiles-1;
		$imgname=$files[$imgindx];
	}
	// otherwise, increment or decrement the displayed image
	else {
	        if ($imlst=='Back') {
				$imgindx--;
				if ($imgindx < 0) {
				        echo "<FONT COLOR='RED'> At beginning of image list</FONT><BR>\n";
					$imgindx=0;
					$imgname=$files[$imgindx];
				}
				$imgname=$files[$imgindx];
		}
		elseif ($imlst=='Next') {
			        $imgindx++;
				if ($imgindx > $numfiles-1) {
					$imgindx=$numfiles-1;
					$imgname=$files[$imgindx];
				        echo "<FONT COLOR='RED'> At end of image list</FONT><BR>\n";
				}
				$imgname=$files[$imgindx];
		}
		else {
		        if ($imlst=='First') $imgindx=0;
			elseif ($imlst=='Last') $imgindx=$numfiles-1;
			$imgname=$files[$imgindx];
		}
	}

	$thisnum=$imgindx+1;

	echo"<TABLE BORDER='0' CELLPADDING='0' CELLSPACING='0' WIDTH='400'>\n";
	echo"<TR><TD ALIGN='LEFT'>\n";
        echo"<B>$testimage</B>\n";
	echo"</TD></TR><TR><TD ALIGN='CENTER'>\n";
        echo"Scale Factor:<INPUT TYPE='text' NAME='imgrescale' VALUE='$imgrescl' SIZE='4'>\n";
	echo"</TD></TR></TABLE>";

	$imgfull=$imgdir.$imgname;
	echo"<INPUT TYPE='HIDDEN' NAME='imgindex' VALUE='$imgindx'>\n";
	echo"<HR>\n";
	echo"<TABLE BORDER='0' CELLPADDING='5' CELLSPACING='0'><TR><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/firstbutton.jpg' ALT='First' NAME='imagelist' VALUE='First'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/backbutton.jpg' ALT='Back' NAME='imagelist' VALUE='Back'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' SRC='img/nextbutton.jpg' ALT='Next' NAME='imagelist' VALUE='Next'>\n";
	echo"</TD><TD>\n";
	echo"<INPUT TYPE='IMAGE' WIDTH='30' SRC='img/lastbutton.jpg' ALT='Last' NAME='imagelist' VALUE='Last'>\n";
	echo"</TD></TR></TR></TABLE>\n";
	echo"<B>$imgname</B>\n<P>";
	echo"<IMG SRC='loadimg.php?filename=$imgfull&scale=$imgrescl'><P>\n";
	echo "</CENTER>\n";
	echo"<INPUT TYPE='HIDDEN' NAME='process' VALUE=$process>\n";
}
?>
