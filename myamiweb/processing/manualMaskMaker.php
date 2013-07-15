<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
 
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
			    newwindow.document.write('Lower limit in gradient amplitude for Canny edge detection.<br>This should be between 0.0 to 1.0 and should be smaller than that of the high limit<br>');
			 }
			 if (infoname=='maxthresh'){
			    newwindow.document.write('Threshold for Canny edge detector to consider as an edge in the gradient amplitude map.<br>  The edge is then extended continuously from such places until the gradient falls below the Low threshold<br>The value should be between 0.0 to 1.0 and should be close to 1.0');
			 }
			 if (infoname=='blur'){
			    newwindow.document.write('Gaurssian filter bluring used for producing the gradient amplitude map<br> 1.0=no bluring');
			 }
			 if (infoname=='crudstd'){
			    newwindow.document.write('Threshold to eliminate false positive regions that picks up the background<br> The region will be removed from the final result if the intensity standard deviation in the region is below the specified number of standard deviation of the map<br> Leave it blank or as 0.0 if not considered');
			 }
			 if (infoname=='masktype'){
			    newwindow.document.write('Crud: Selexon crudfinder. Canny edge detector and Convex Hull is used<br>  Edge: Hole Edge detection using region finder in libCV so that the region can be concave.<br>  Aggr: Aggregate finding by convoluting Sobel edge with a disk of the particle size.');
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
		<B>Image Option:</B><br>

		<INPUT TYPE='text' NAME='bin' VALUE='$bin' SIZE='4'>&nbsp;
		<A HREF=\"javascript:mminfopopup('bin')\">
		Binning</A><br>
		<br>
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
		$assessname = $_POST['oldassess'];
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

	echo "<TR><td>mask type</TD><td>$masktype</TD></tr>\n";
	echo "<TR><td>bin</TD><td>$bin</TD></tr>\n";
	echo "<TR><td>assessment name</TD><td>$assessname</TD></tr>\n";
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
	$projectId=getProjectId();

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
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
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
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApMaskMakerRunData','name'); 
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manualrun'.($lastrunnumber+1);
	createAppionLoopTable($sessiondata, $defrunname, "mask");
	echo"
		</TD>
		<TD CLASS='tablebg'>
	";
	createManualMaskMakerTable($sessionId);
	echo "
		</TD>
		</tr>
		<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>";
	echo getSubmitForm("Run MaskMaker", true, true);
	echo "
		</TD>
	</tr>
	</table>
	</TD>
	</tr>
	</table>\n";
	echo "

	</CENTER>
	</FORM>
	";
	processing_footer();
}

function runMaskMaker() {
	/* *******************
	PART 1: Get variables
	******************** */
	$process = $_POST['process'];
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];
	$assess = $_POST[assess];
	$newassess= $_POST[newassessname];
	$oldassess= $_POST['oldassess'];
	
	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */
	if ($assess==2 && !$newassess) {
		createMMMForm("<B>ERROR:</B> Specify a new assess run name");
		exit;
	}

	if ($assess==1 && !$oldassess) {
		createMMMForm("<B>ERROR:</B> No existing assessment run for merging");
		exit;
	}

	/* *******************
	PART 3: Create program command
	******************** */
	$command="manualmask.py ";
	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createMMMForm($apcommand);
		exit;
	}
	$command .= $apcommand;
	$command .= parseManualMaskMakerParams($_POST);
	
	/* *******************
	PART 4: Create header info, i.e., references
	******************** */
	$headinfo .= appionRef();
	
	/* *******************
	PART 5: Show or Run Command
	******************** */
	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'manualmask', $nproc);

	// if error display them
	if ($errors)
		createMMMForm("<b>ERROR:</b> $errors");
	
}

?>
