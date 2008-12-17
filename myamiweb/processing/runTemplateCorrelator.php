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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
require "inc/leginon.inc";
require "inc/project.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runTemplateCorrelator();
}

// CREATE FORM PAGE
elseif ($_POST['templates']) { 
	createTCForm();
}

// MAKE THE TEMPLATE SELECTION FORM
else {
	createTemplateForm();
}

/*
**
**
** TEMPLATE SELECT FORM
**
**
*/

function createTemplateForm($extra=False) {
	// check if coming directly from a session
	$expId = $_GET['expId'];
	$formAction=$_SERVER['PHP_SELF'];	

	// retrieve template info from database for this project
	if ($expId){
	$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	// if user wants to use templates from another project
	if($_POST['projectId']) $projectId =$_POST[projectId];

	$projects=getProjectList();

	if (is_numeric($projectId)) {
		$particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
		$i=1;
		$javafunctions="<SCRIPT LANGUAGE='JavaScript'>\n";
		$templatetable="<TABLE CLASS='tableborder' BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
		$numtemplates = count($templateData);

		foreach($templateData as $templateinfo) { 
			if (is_array($templateinfo)) {
				$filename = $templateinfo[path] ."/".$templateinfo[templatename];
				$checkboxname='template'.$i;
				$templaterundata = $particle->getRecentTemplateRunFromId($templateinfo[DEF_id]);
				//print_r($templaterundata);
				$startval = (int) $templaterundata[range_start];
				$endval = (int) $templaterundata[range_end];
				$incrval = (int) $templaterundata[range_incr];
				if ($startval==0) $startval='';
				if ($endval==0 || $endval==10) $endval='';
				if ($incrval==0 || $incrval==20) $incrval='';

				// create the javascript functions to enable the templates
				$javafunctions.="function enable".$checkboxname."() {
						 if (document.viewerform.$checkboxname.checked){
						 document.viewerform.".$checkboxname."strt.disabled=false;
						 //document.viewerform.".$checkboxname."strt.value='';
						 document.viewerform.".$checkboxname."end.disabled=false;
						 //document.viewerform.".$checkboxname."end.value='';
						 document.viewerform.".$checkboxname."incr.disabled=false;
						 //document.viewerform.".$checkboxname."incr.value='';
					 }
					 else {
						 document.viewerform.".$checkboxname."strt.disabled=true;
						 //document.viewerform.".$checkboxname."strt.value='0';
						 document.viewerform.".$checkboxname."end.disabled=true;
						 //document.viewerform.".$checkboxname."end.value='90';
						 document.viewerform.".$checkboxname."incr.disabled=true;
						 //document.viewerform.".$checkboxname."incr.value='10';
					 }
				 }\n";

				// create the image template table
				$templatetable.="<TR><TD>\n";
				$templatetable.="<IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='200'></TD>\n";
				$templatetable.="<TD>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='templateId".$i."' VALUE='$templateinfo[DEF_id]'>\n";
				$templatetable.="<INPUT TYPE='hidden' NAME='diam' VALUE='$templateinfo[diam]'>\n";
				$templatetable.="<INPUT TYPE='checkbox' NAME='$checkboxname' onclick='enable".$checkboxname."()'>\n";
				$templatetable.="<B>Use This Template</B><BR>\n";
				$templatetable.="Enter rotation values (leave blank for no rotation):<BR>\n";
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname
					."strt' DISABLED VALUE='$startval' SIZE='3'> Starting Angle<BR>\n";
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname
					."end' DISABLED VALUE='$endval' SIZE='3'> Ending Angle<BR>\n";
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname
					."incr' DISABLED VALUE='$incrval' SIZE='3'> Angular Increment<BR>\n";
				$templatetable.="<P>\n";
				$templatetable.="<TABLE BORDER='0'>\n";
				$templatetable.="<TR><TD><B>Template ID:</B></TD><TD>$templateinfo[DEF_id]</TD></TR>\n";
				$templatetable.="<TR><TD><B>Diameter:</B></TD><TD>$templateinfo[diam]</TD></TR>\n";
				$templatetable.="<TR><TD><B>Pixel Size:</B></TD><TD>$templateinfo[apix]</TD></TR>\n";
				$templatetable.="</TABLE>\n";
				$templatetable.="<B>Description:</B><BR>$templateinfo[description]\n";
				$templatetable.="</TD></TR>\n";

				$i++;
			}
		}
		$javafunctions.="</SCRIPT>\n";
		$templatetable.="</TABLE>\n";
	}
	$javafunctions.="<script src='../js/viewer.js'></script>\n";

	processing_header("Template Correlator Launcher","Automated Particle Selection with Template Correlator",$javafunctions);
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	echo"
  <FORM NAME='viewerform' method='POST' ACTION='$formAction'>
  <B>Select Project:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";

	foreach ($projects as $k=>$project) {
		$sel = ($project['id']==$projectId) ? "selected" : '';
		echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
	}
	echo"
  </select>
  <P>\n";
	if ($templatetable) {
		echo"
    <CENTER>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n
    $templatetable
    <CENTER>
    <INPUT TYPE='hidden' NAME='numtemplates' value='$numtemplates'>
    <INPUT TYPE='submit' NAME='templates' value='Use These Templates'>
    </CENTER>\n";
	}
	else echo "<B>Project does not contain any templates.</B>\n";
	echo"</FORM>\n";
	processing_footer();
	exit;
}

/*
**
**
** MAIN FORM
**
**
*/

function createTCForm($extra=false, $title='Template Correlator Launcher' , $heading='Automated Particle Selection with Template Correlator', $results=false) {
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

	$numtemplates=$_POST['numtemplates'];
	$templateForm='';
	$templateTable="<TABLE CLASS='tableborder'><TR><TD>\n";
	$templateCheck='';

	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId, True));

	$numtemplatesused = 0;
	for ($i=1; $i<=$numtemplates; $i++) {
		$templateimg="template".$i;
		if ($_POST[$templateimg]){
			$numtemplatesused++;
			$templateIdName="templateId".$i;
			$tmpltstrt=$templateimg."strt";
			$tmpltend=$templateimg."end";
			$tmpltincr=$templateimg."incr";
			$templateId=$_POST[$templateIdName];
			$start = $_POST[$tmpltstrt];
			$end   = $_POST[$tmpltend];
			$incr  = $_POST[$tmpltincr];

			$templateList.=$i.":".$templateId.",";
			$templateinfo=$particle->getTemplatesFromId($templateId);
			$filename=$templateinfo[path]."/".$templateinfo[templatename];
			$templateTable.="<TD VALIGN='TOP'><IMG SRC='loadimg.php?filename=$filename&rescale=True' WIDTH='200'><BR>\n";
			if (!$start && !$end && !$incr) $templateTable.="<B>no rotation</B>\n";
			elseif ($start=='' || !$end || !$incr) {
				echo "<B>Error in template $i</B><BR> missing rotation parameter - fix this<BR>\n";
				echo "starting angle: $start<BR>ending angle: $end<BR>increment: $incr<BR>\n";
				exit;
			}	
			else {
				$templateTable.="<B>starting angle:</B> $start<BR>\n";
				$templateTable.="<B>ending angle:</B> $end<BR>\n";
				$templateTable.="<B>angular incr:</B> $incr</TD>\n";
			}
			$templateForm.="<INPUT TYPE='hidden' NAME='$templateIdName' VALUE='$templateId'>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$templateimg' VALUE='$templateId'>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$tmpltstrt' VALUE='$start'>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$tmpltend' VALUE='$end'>\n";
			$templateForm.="<INPUT TYPE='hidden' NAME='$tmpltincr' VALUE='$incr'>\n";
		}
	}
	$templateTable.="</TD></TR></TABLE>\n";
	
	// check that there are templates, remove last comma
	if (!$templateList) createTemplateForm("ERROR: Choose a template");
	$templateList=substr($templateList,0,-1);
	$javafunctions="
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
	</SCRIPT>\n";
	$javafunctions .= writeJavaPopupFunctions('appion');
	processing_header($title,$heading,$javafunctions,True);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
	}
	if ($results) echo "$results<hr />\n";
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];

	// Set any existing parameters in form
	$defrunid = ($_POST['runid']) ? $_POST['runid'] : 'tmplrun'.($prtlruns+1);
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
	$diam = ($_POST['diam']) ? $_POST['diam'] : "";
	$threadcheck = ($_POST['threadfindem']=='on') ? 'CHECKED' : '';
	$keepallcheck = ($_POST['keepall']=='on') ? 'CHECKED' : '';

	echo"
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>";
	createAppionLoopTable($sessiondata, $defrunid, "extract");

	if ($numtemplatesused > 1) {
		echo "<input type='checkbox' name='threadfindem' $threadcheck>\n";
		echo "Use multi-processor threading\n";
		echo "<br />\n";
	} else {
		echo "<input type='hidden' name='threadfindem' value='off'>";
	}

	echo "<input type='checkbox' name='keepall' $keepallcheck>\n";
	echo "Do not delete .dwn.mrc files after finishing\n";
	echo "<br />\n";

	echo "</TD><TD CLASS='tablebg'>\n";
	echo "<B>Mask Diameter:</B><BR>\n";
	echo "<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>&nbsp;\n";
	echo "Mask diameter for template(s) <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>\n";
	echo "<BR/><BR/>\n";

	createParticleLoopTable(0.5,"",$_POST);

	echo "
		</TD>
	</TR>
	<TR>
		<TD COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
		Test these setting on image:
		<INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
                <hr />
	";
	echo getSubmitForm("Run Correlator");
	echo"
		</TD>
	</TR>
	</TABLE>
	<CENTER>
	<B>Using Templates:</B>
	<TABLE><TR>
		<TD>\n";
	// Display the templates that will be used for Template Correlator
	echo "<INPUT TYPE='hidden' NAME='templateList' VALUE='$templateList'>\n";
	echo "<INPUT TYPE='hidden' NAME='templates' VALUE='continue'>\n";
	echo "<INPUT TYPE='hidden' NAME='numtemplates' VALUE='$numtemplates'>\n";
	echo "$templateForm\n";
	echo "$templateTable\n";
	echo "
		</TD>
	</TR></TABLE>
	</CENTER>
	</FORM>\n";
	processing_footer();
	exit;
}

/*
**
**
** RUN THE FUNCTION
**
**
*/

function runTemplateCorrelator() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
	$runname = $_POST['runname'];
	$thread = ($_POST['threadfindem']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$keepall = ($_POST['keepall']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";

	// START MAKE COMMAND

	$command ="templateCorrelator.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createTCForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$partcommand = parseParticleLoopParams($_POST);
	if ($partcommand[0] == "<") {
		createTCForm($partcommand);
		exit;
	}
	$command .= $partcommand;

	// get the list of templates
	$i=1;
	$templateList = $_POST['templateList'];
	$templates=split(",", $templateList);
	$templateliststr = "";
	$rangeliststr = "";
	foreach ($templates as $template) {
		list($num, $templateid) = split(":",$template);
		$templateliststr .= $templateid.",";
		$start = "template".$num."strt";
		$end   = "template".$num."end";
		$incr  = "template".$num."incr";
		// check for invalid range
		if ($_POST[$start]!='' && $_POST[$end]!='0' && $_POST[$incr]!='0') {
			// use user supplied values
			$rangestr = $_POST[$start].",".$_POST[$end].",".$_POST[$incr];
		} else {
			// no rotation
			$rangestr = "0,10,20";
		}
		$rangeliststr .= $rangestr."x";
		$i++;
	}
	// remove extra commas and x's
	$templateliststr = substr($templateliststr,0,-1);
	$rangeliststr    = substr($rangeliststr,0,-1);

	$command.="--template-list=$templateliststr ";
	$command.="--range-list=$rangeliststr ";

	if ($_POST['threadfindem']=='on')
		$command.="--thread-findem ";
	if ($_POST['keepall']=='on')
		$command.="--keep-all ";

	// END MAKE COMMAND

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ",",",$testimage);
		$testimage = ereg_replace(",,",",",$testimage);
	}

	if ($_POST['process']=="Run Correlator") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTCForm("<B>ERROR:</B> Enter a user name and password");

		$sub = submitAppionJob($command, $outdir, $runname, $expId, 'templatepicker', $testimage);
		// if errors:
		if ($sub) createTCForm("<b>ERROR:</b> $sub");
		if (!$testimage) exit;
	}

	if ($testimage) {
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<b>Template Correlator Command:</b><br />$command";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		$testjpg=ereg_replace(".mrc","",$_POST['testfilename']);
		$jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
		$i=1;
		$templateList=$_POST['templateList'];
		$templates=split(",", $templateList);
		foreach ($templates as $tmplt) {
   			$cccimg=$outdir.$runid."/ccmaxmaps/".$testjpg.".ccmaxmap".$i.".jpg";
			$ccclist[]=$cccimg;
			$i++;
		}
		$results.= writeTestResults($jpgimg,$ccclist,$bin=$_POST['bin']);
		createTCForm($false,'Particle Selection Results','Particle Selection Results',$results);
		exit;
	} else {
		processing_header("Particle Selection Results","Particle Selection Results");

		echo"
			<TABLE WIDTH='600'>
			<TR><TD COLSPAN='2'>
			<font size='+1'>
			<B>Template Correlation Picker Command:</B><BR>
			$command</font><HR>
			</TD></TR>";
		$i = 0;
		foreach ( split(",", $templateliststr) as $templateid ) {
			$i++;
			echo"<TR><TD>template $i id</TD><TD>$templateid</TD></TR>";
		}
		echo"<TR><TD>template list</TD><TD>$templateliststr</TD></TR>";
		$i = 0;
		foreach ( split("x", $rangeliststr) as $rangestr ) {
			$i++;
			echo"<TR><TD>template $i range</TD><TD>$rangestr</TD></TR>";
		}
		echo"<TR><TD>range list string</TD><TD>$rangeliststr</TD></TR>";
		echo"<TR><TD>testimage</TD><TD>$testimage</TD></TR>";
		echo"<TR><TD>thread findem</TD><TD>$thread</TD></TR>";
		echo"<TR><TD>keep all .dwn.mrc</TD><TD>$thread</TD></TR>";
		appionLoopSummaryTable($_POST);
		particleLoopSummaryTable($_POST);

		echo"</TABLE>\n";
		processing_footer(True, True);
	}

	exit;
}

?>
