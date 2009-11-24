<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see http://ami.scripps.edu/software/leginon-license
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

	if (is_numeric($projectId)) {
		$particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
		$i=1;
		$javafunctions="<script type='text/javascript'>\n";
		$templatetable="<table class='tableborder' border='1' cellpadding='5'>\n";
		$numtemplates = count($templateData);
		foreach($templateData as $templateinfo) {
			if ($i%2 == 1)
				$templatetable.="<tr><td align='left'>\n";
			else
				$templatetable.="<td align='left'>\n";
			if (is_array($templateinfo)) {
				$filename = $templateinfo[path] ."/".$templateinfo[templatename];
				$checkboxname='template'.$i;
				$templaterundata = $particle->getRecentTemplateRunFromId($templateinfo[DEF_id]);
				//print_r($templaterundata);
				$startval = (int) $templaterundata[range_start];
				$endval = (int) $templaterundata[range_end];
				$incrval = (int) $templaterundata[range_incr];
				if ($endval==0 || $endval==10) $endval='';
				if ($incrval==0 || $incrval==20) $incrval='';
				if ($startval==0 && $endval=='') $startval='';

				// create the javascript functions to enable/disable the templates
				$javafunctions.="function enable".$checkboxname."() {
					if (document.viewerform.$checkboxname.checked){
						 document.viewerform.".$checkboxname."strt.disabled=false;
						 document.viewerform.".$checkboxname."end.disabled=false;
						 document.viewerform.".$checkboxname."incr.disabled=false;
					 }
					 else {
						 document.viewerform.".$checkboxname."strt.disabled=true;
						 document.viewerform.".$checkboxname."end.disabled=true;
						 document.viewerform.".$checkboxname."incr.disabled=true;
					 }
				}\n";
				// create the image template table
				$templatetable.="<img src='loadimg.php?filename=$filename&w=120' width='120'>\n";
				$templatetable.="<br/>\n";
				$templatetable.="Template ID: <i>&nbsp;$templateinfo[DEF_id]</i><br/>\n";
				$templatetable.="Diameter:    <i>&nbsp;$templateinfo[diam] &Aring;</i><br/>\n";
				$templatetable.="Pixel Size:  <i>&nbsp;$templateinfo[apix] &Aring;</i><br/>\n";


				// Table separator
				$templatetable.="</td><td align='left'>\n";

				// set parameters
				$templatetable.="<input type='hidden' name='templateId".$i."' value='$templateinfo[DEF_id]'>\n";
				$templatetable.="<input type='checkbox' name='$checkboxname' onclick='enable".$checkboxname."()'>\n";
				$templatetable.="<b>Use Template $templateinfo[DEF_id]</b>\n";
				$templatetable.="<br/>\n";
				$templatetable.="<br/>\n";
				$templatetable.="<b>Rotation values</b><br/>";
				$templatetable.="<i>(leave blank for no rotation)</i>:<br>\n";
				$templatetable.="<input type='text' name='".$checkboxname
					."strt' DISABLED value='$startval' SIZE='3'> Starting Angle<br/>\n";
				$templatetable.="<input type='text' name='".$checkboxname
					."end' DISABLED value='$endval' SIZE='3'> Ending Angle<br/>\n";
				$templatetable.="<input type='text' name='".$checkboxname
					."incr' DISABLED value='$incrval' SIZE='3'> Angular Increment<br/>\n";
				$templatetable.="<br/>\n";
				$templatetable.="<table width='200'><tr><td>\n";
				$templatetable.="<b>Description:</b>&nbsp;<font size='-2'>$templateinfo[description]</font>\n";
				$templatetable.="</td></tr></table>\n";
				$i++;
			}
			if ($i%2 == 1)
				$templatetable.="</td></tr>\n";
			else
				$templatetable.="</td>\n";
		}
		$javafunctions.="</SCRIPT>\n";
		$templatetable.="</table>\n";
	}
	$javafunctions.="<script src='../js/viewer.js'></script>\n";

	processing_header("Template Correlator Launcher","Automated Particle Selection with Template Correlator",$javafunctions);
	if ($extra) echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	echo"<FORM name='viewerform' method='POST' ACTION='$formAction'><P>\n";
	if ($templatetable) {
		echo"
			<CENTER>
			<input type='submit' name='templates' value='Use These Templates'>
			</CENTER>\n
			$templatetable
			<CENTER>
			<input type='hidden' name='numtemplates' value='$numtemplates'>
			<input type='submit' name='templates' value='Use These Templates'>
			</CENTER>\n";
	}
	else echo "<b>Project does not contain any templates.</b>\n";
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

function createTCForm($extra=false, $title='Template Correlator Launcher', 
 $heading='Automated Particle Selection with Template Correlator', $results=false) {
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
	$templateTable="<table class='tableborder'><tr><td>\n";
	$templateCheck='';

	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId, True));

	$defdiam = 0;
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

			// set default mask diameter
			if ($defdiam == 0) {
				$tempdiam = $templateinfo['diam'];
				if ($tempdiam)
					$defdiam = $tempdiam*1.3;
			}

			$filename=$templateinfo[path]."/".$templateinfo[templatename];
			$templateTable.="<td VALIGN='TOP'><img src='loadimg.php?filename=$filename&rescale=True' WIDTH='200'><br>\n";
			if (!$start && !$end && !$incr) $templateTable.="<b>no rotation</b>\n";
			elseif ($start=='' || !$end || !$incr) {
				echo "<b>Error in template $i</b><br> missing rotation parameter - fix this<br>\n";
				echo "starting angle: $start<br>ending angle: $end<br>increment: $incr<br>\n";
				exit;
			}	
			else {
				$templateTable.="<b>starting angle:</b> $start<br>\n";
				$templateTable.="<b>ending angle:</b> $end<br>\n";
				$templateTable.="<b>angular incr:</b> $incr</td>\n";
			}
			$templateForm.="<input type='hidden' name='$templateIdName' value='$templateId'>\n";
			$templateForm.="<input type='hidden' name='$templateimg' value='$templateId'>\n";
			$templateForm.="<input type='hidden' name='$tmpltstrt' value='$start'>\n";
			$templateForm.="<input type='hidden' name='$tmpltend' value='$end'>\n";
			$templateForm.="<input type='hidden' name='$tmpltincr' value='$incr'>\n";
		}
	}



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
				document.viewerform.commit.disabled=true;
				document.viewerform.commit.checked=false;
			 }	
			 else {
				document.viewerform.testfilename.disabled=true;
				document.viewerform.testfilename.value='mrc file name';
				document.viewerform.commit.disabled=false;
				document.viewerform.commit.checked=true;
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
	<input type='HIDDEN' name='lastSessionId' value='$sessionId'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$lastrunnumber = $particle->getLastRunNumber($sessionId,'ApSelectionRunData','name','tmplrun'); 
	// Set any existing parameters in form
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'tmplrun'.($lastrunnumber+1);
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
	$diam = ($_POST['diam']) ? $_POST['diam'] : $defdiam;
	$threadcheck = ($_POST['threadfindem']=='off') ? '' : 'CHECKED';
	$keepallcheck = ($_POST['keepall']=='on') ? 'CHECKED' : '';
	$mirrorsv = ($_POST['mirrors']=='on') ? 'CHECKED' : '';

	echo"
	<table border=0 class=tableborder cellpadding=15>
	<tr>
		<td valign='top'>";
	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><img src='img/findem.png' WIDTH='300'></center><br />\n";
	}

	createAppionLoopTable($sessiondata, $defrunname, "extract");

	
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

	echo "</td><td class='tablebg'>\n";
	echo "<b>Mask Diameter:</b><br>\n";
	echo "<input type='text' name='diam' value='$diam' SIZE='4'>&nbsp;\n";
	echo "Mask diameter for template(s) <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='mirrors' $mirrorsv>\n";
	echo docpop('mirror','Use template mirrors');
	echo "<br/><br/>\n";

	createParticleLoopTable(0.5,"",$_POST);

	echo "
		</td>
	</tr>
	<tr>
		<td COLSPAN='2' ALIGN='CENTER'>
		<HR>
		<input type='checkbox' name='testimage' onclick='enabledtest(this)' $testcheck>
		Test these setting on image:
		<input type='text' name='testfilename' $testdisabled value='$testvalue' SIZE='45'>
		<hr />
	";
	echo getSubmitForm("Run Correlator");
	echo"
		</td>
	</tr>
	</table>
	<b>Using Templates:</b>
	<table><tr>
		<td>\n";
	// Display the templates that will be used for Template Correlator
	echo "<input type='hidden' name='templateList' value='$templateList'>\n";
	echo "<input type='hidden' name='templates' value='continue'>\n";
	echo "<input type='hidden' name='numtemplates' value='$numtemplates'>\n";
	echo "$templateForm\n";
	echo "$templateTable\n";
	echo "
		</td>
	</tr></table>
	</form>\n";
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
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$thread = ($_POST['threadfindem']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$keepall = ($_POST['keepall']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$mirrors = ($_POST['mirrors']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";

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
	if ($_POST['mirrors']=='on')
		$command.="--use-mirrors ";

	// END MAKE COMMAND

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		$testimage = ereg_replace(" ",",",$testimage);
		$testimage = ereg_replace(",,",",",$testimage);
	}

	if ($_POST['process']=="Run Correlator") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createTCForm("<b>ERROR:</b> Enter a user name and password");

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
		$jpgimg=$outdir.$runname."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
		$i=1;
		$templateList=$_POST['templateList'];
		$templates=split(",", $templateList);
		foreach ($templates as $tmplt) {
			$cccimg=$outdir.$runname."/maps/".$testjpg.".ccmaxmap".$i.".jpg";
			$ccclist[]=$cccimg;
			$i++;
		}
		$results.= writeTestResults($jpgimg,$ccclist,$bin=$_POST['bin']);
		createTCForm($false,'Particle Selection Results','Particle Selection Results',$results);
		exit;
	} else {
		processing_header("Particle Selection Results","Particle Selection Results");

		echo"
			<table width='600'>
			<tr><td colspan='2'>
			<b>Template Correlation Picker Command:</b><br>
			$command
			<hr>
			</td></tr>";
		$i = 0;
		foreach ( split(",", $templateliststr) as $templateid ) {
			$i++;
			echo"<tr><td>template $i id</td><td>$templateid</td></tr>";
		}
		echo"<tr><td>template list</td><td>$templateliststr</td></tr>";
		$i = 0;
		foreach ( split("x", $rangeliststr) as $rangestr ) {
			$i++;
			echo"<tr><td>template $i range</td><td>$rangestr</td></tr>";
		}
		echo"<tr><td>range list string</td><td>$rangeliststr</td></tr>";
		echo"<tr><td>testimage</td><td>$testimage</td></tr>";
		echo"<tr><td>thread findem</td><td>$thread</td></tr>";
		echo"<tr><td>keep all .dwn.mrc</td><td>$keepall</td></tr>";
		echo"<tr><td>use mirrors</td><td>$mirrors</td></tr>";
		appionLoopSummaryTable($_POST);
		particleLoopSummaryTable($_POST);

		echo"</table>\n";
		processing_footer(True, True);
	}

	exit;
}

?>
