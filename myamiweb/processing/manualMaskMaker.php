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
	createMMMForm();
}

function maskMakerJavaCommands () {
	$minthresh = $_POST[minthresh];
	$maxthresh = $_POST[maxthresh];
	$blur = $_POST[blur];
	$bin = $_POST[bin];
	$masktype = ($_POST[masktype]);
	$crudstd = $_POST[crudstd];

	$java ="
      <SCRIPT LANGUAGE='JavaScript'>
		function mminfopopup(infoname){
			 var newwindow=window.open('','name','height=250, width=400');
			 newwindow.document.write('<HTML><BODY>');
			 if (infoname=='minthresh'){
			    newwindow.document.write('Lower limit in gradient amplitude for Canny edge detection.<BR>This should be between 0.0 to 1.0 and should be smaller than that of the high limit<BR>');
			 }
			 if (infoname=='maxthresh'){
			    newwindow.document.write('Threshold for Canny edge detector to consider as an edge in the gradient amplitude map.<BR>  The edge is then extended continuously from such places until the gradient falls below the Low threshold<BR>The value should be between 0.0 to 1.0 and should be close to 1.0');
			 }
			 if (infoname=='blur'){
			    newwindow.document.write('Gaurssian filter bluring used for producing the gradient amplitude map<BR> 1.0=no bluring');
			 }
			 if (infoname=='crudstd'){
			    newwindow.document.write('Threshold to eliminate false positive regions that picks up the background<BR> The region will be removed from the final result if the intensity standard deviation in the region is below the specified number of standard deviation of the map<BR> Leave it blank or as 0.0 if not considered');
			 }
			 if (infoname=='masktype'){
			    newwindow.document.write('Crud: Selexon crudfinder. Canny edge detector and Convex Hull is used<BR>  Edge: Hole Edge detection using region finder in libCV so that the region can be concave.<BR>  Aggr: Aggregate finding by convoluting Sobel edge with a disk of the particle size.');
			 }
			 if (infoname=='bin'){
			    newwindow.document.write('Binning of the image. This takes a power of 2 (1,2,4,8,16) and shrinks the image to help make the processing faster. Typically you want to use 4 or 8 depending on the quality of you templates.');
			 }
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		}
      </SCRIPT>\n";
	return($java);
}

function createManualMaskMakerTable ($sessionId) {
	echo "<!-- BEGIN Mask Maker Param -->";
	
	$bin = ($_POST['bin']) ? $_POST['bin'] : '4';
	$assess = ($_POST['assess']) ? $_POST['assess']:0;
	$assess_same  = ($assess==0 || !$_POST['process']) ? "CHECKED" : "";
	$assess_old  = ($assess==1 && $_POST['process']) ? "CHECKED" : "";
	$assess_new  = ($assess==2 && $_POST['process']) ? "CHECKED" : "";
	$newassess = $_POST['newassessname'];
	$particle=new particleData;
	$assessnames=$particle->getMaskAssessNames($sessionId);
	if ($assessnames) {
		$oldassessval = ($_POST['oldassess']) ? $_POST['oldassess'] : $assessnames[0];
	} else {
		$oldassessval = $_POST['oldassess'];
	}
	echo "	
		<B>Image Option:</B><BR>

		<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>&nbsp;
		<A HREF=\"javascript:mminfopopup('bin')\">
		Binning</A><BR>
		<BR>
	";
	echo "
		<A HREF=\"javascript:mmminfopopup('assess')\">
		<I>Accept the mask region as:</I></A><br/>
		<INPUT TYPE='radio' NAME='assess' VALUE='0' $assess_same>
		Assess run of the same name <FONT SIZE=-2><I>(default)</I></FONT><br/>
	";
	
	if ($assessnames ) {
		echo "
			<INPUT TYPE='radio' NAME='assess' VALUE='1' $assess_old>
			Combined run with existing assessment run
		";
		if ($assessnames && count($assessnames) > 1) {

			echo"<SELECT NAME='oldassess'>\n";
			foreach ($assessnames as $oldassess) {
				echo "<OPTION VALUE='$oldassess' ";
				// make first one selected by default
				if ($oldassess==$oldassessval) echo "SELECTED";
				echo ">$oldassess</OPTION>\n";
			}
			echo "</SELECT><br/>\n";
		} elseif ($assessnames) {
			echo":&nbsp;".$assessnames[0]."\n\n";
			echo"<INPUT TYPE='hidden' NAME='oldassess' VALUE=".$assessnames[0].">\n";
			echo"<br/>\n";
		} else {
			//no presets old assessments
			echo"<FONT SIZE=-2><I>No existing assessment</I></FONT>";
		}
	}
	echo "
		<INPUT TYPE='radio' NAME='assess' VALUE='2' $assess_new>
		Assess run under a new name
<INPUT TYPE='text' NAME='newassessname' VALUE='$newassess' SIZE='4'>&nbsp;<br/>
	";

	echo "<!-- END Mask Maker Param -->";
};

function parseManualMaskMakerParams () {
	$assessname = getAssessname();
	$bin = $_POST[bin];

	$command.=" --assess=$assessname";
	if ($bin && $bin > 0) $command.=" --bin=$bin";

   return $command;
}

function getAssessname () {
	$runname = $_POST[runname];
	$assess = $_POST[assess];
	switch ($assess) {
	case 0:
		$assessname = $runname;
		break;
	case 1:
		$assessname = $_POST[oldassessname];
		break;
	case 2:
		$assessname = $_POST[newassessname];
		break;
	}
	return $assessname;
}

function maskMakerSummaryTable () {
	$assessname = getAssessname();
	$bin = $_POST[bin];
	$masktype = 'manaul';

	echo "<TR><TD>mask type</TD><TD>$masktype</TD></TR>\n";
	echo "<TR><TD>bin</TD><TD>$bin</TD></TR>\n";
	echo "<TR><TD>assessment name</TD><TD>$assessname</TD></TR>\n";
}


function createMMMForm($extra=false, $title='MaskMaker Launcher', $heading='Manual Mask Region Creation with ManualMaskmaker') {
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
			 if (infoname=='runname'){
				 newwindow.document.write('Specifies the name associated with the Template Correlator results unique to the specified session and parameters.	An attempt to use the same run name for a session using different Template Correlator parameters will result in an error.');
			 }
			 newwindow.document.write('</BODY></HTML>');
			 newwindow.document.close();
		 }
	</SCRIPT>\n";
	$javascript.=maskMakerJavaCommands();
	processing_header($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];


	$process = ($_POST['process']) ? $_POST['process'] :'';
	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>";
	$maskruns=count($particle->getMaskMakerRunIds($sessionId));
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manualrun'.($maskruns+1);
	createAppionLoopTable($sessiondata, $defrunname, "mask");
	echo"
		</TD>
		<TD CLASS='tablebg'>
	";
	createManualMaskMakerTable($sessionId);
	echo "
		</TD>
		</TR>
		<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>";
	echo getSubmitForm("Run MaskMaker", true, true);
	echo "
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
	processing_footer();
}
function runMaskMaker() {
	$process = $_POST['process'];
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$assess = $_POST[assess];
	$newassess= $_POST[newassessname];
	$oldassess= $_POST[oldassessname];
	if ($assess==2 && !$newassess) {
		createMMMForm("<B>ERROR:</B> Specify a new assess run name");
		exit;
	}


	if ($assess==1 && !$oldassess) {
		createMMMForm("<B>ERROR:</B> No existing assessment run for merging");
		exit;
	}


	$command="manualmask.py ";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMMMForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	$command .= parseManualMaskMakerParams($_POST);

	if ($testimage && $_POST['process']=="Run ManualMaskMaker") {
		$host = $_POST['processinghost'];
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];
		if (!($user && $password)) {
			createMMMForm("<B>ERROR:</B> Enter a user name and password");
			exit;
		}
		$prefix = "source /ami/sw/ami.csh;";
		$prefix.= "source /ami/sw/share/python/usepython.csh cvs32;";
		$cmd = "$prefix webcaller.py '$command' maskMakerLog.txt";
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	processing_header("Bad Region Detection Results","Bad Region Detection Results",$javascript);


	echo"
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>Mask Maker Command:</B><BR>
  $command<HR>
  </TD></TR>
	";
	appionLoopSummaryTable();
	maskMakerSummaryTable();
	echo"</TABLE>\n";
	processing_footer();
}

?>
