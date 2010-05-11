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
	runSignaturePicker();
}

// CREATE FORM PAGE
elseif ($_POST['templates']) { 
	createSigForm();
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
	$projectId=getProjectId();

	// retrieve template info from database for this project
	if ($expId){
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}

	// if user wants to use templates from another project

	if (is_numeric($projectId)) {
		$particle=new particleData;
		$templateData=$particle->getTemplatesFromProject($projectId);
	}

	// extract template info
	if ($templateData) {
		$templatenum=1;
		$javafunctions="<script type='text/javascript'>\n";
		$templatetable="<table class='tableborder' border='1' cellpadding='5'>\n";
		$numtemplates = count($templateData);
		foreach($templateData as $templateinfo) {
			if ($templatenum%2 == 1)
				$templatetable.="<tr><td align='left'>\n";
			else
				$templatetable.="<td align='left'>\n";
			if (is_array($templateinfo)) {
				$filename = $templateinfo[path] ."/".$templateinfo[templatename];
				$checkboxname='template'.$templatenum;
				$templaterundata = $particle->getRecentTemplateRunFromId($templateinfo[DEF_id]);
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
				$templatetable.="<input type='hidden' name='templateId".$templatenum."' value='$templateinfo[DEF_id]'>\n";
				$templatetable.="<input type='checkbox' name='$checkboxname' onclick='enable".$checkboxname."()'>\n";
				$templatetable.="<b>Use Template $templateinfo[DEF_id]</b>\n";
				$templatetable.="<br/>\n";
				$templatetable.="<table width='200'><tr><td>\n";
				$templatetable.="<b>Description:</b>&nbsp;<font size='-2'>$templateinfo[description]</font>\n";
				$templatetable.="</td></tr></table>\n";
				$templatenum++;
			}
			if ($templatenum%2 == 1)
				$templatetable.="</td></tr>\n";
			else
				$templatetable.="</td>\n";
		}
		$javafunctions.="</SCRIPT>\n";
		$templatetable.="</table>\n";
	}
	$javafunctions.="<script src='../js/viewer.js'></script>\n";

	processing_header("Signature Launcher","Automated Particle Selection with Signature",$javafunctions);
	if ($extra) echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
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

function createSigForm($extra=false, $title='Signature Launcher', 
 $heading='Automated Particle Selection with Signature', $results=false) {
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
			$templateId=$_POST[$templateIdName];
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
		echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
	}
	if ($results) echo "$results<hr />\n";
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<input type='HIDDEN' name='lastSessionId' value='$sessionId'>\n";
	$sessiondata=getSessionList($projectId,$sessionId);
	$sessioninfo=$sessiondata['info'];
	$lastrunnumber = $particle->getLastRunNumberForType($sessionId,'ApSelectionRunData','name'); 
	// Set any existing parameters in form
	$defrunname = ($_POST['runname']) ? $_POST['runname'] : 'signaturerun'.($lastrunnumber+1);
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';
	$diam = ($_POST['diam']) ? $_POST['diam'] : $defdiam;
	$keepallcheck = ($_POST['keepall']=='on') ? 'CHECKED' : '';
	$mirrorsv = ($_POST['mirrors']=='on') ? 'CHECKED' : '';

	echo"
	<table border=0 class=tableborder cellpadding=15>
	<tr>
		<td valign='top'>";
	srand(time());
	if ((rand()%2) < 3) {
		echo"<center><img src='img/signature.jpg' WIDTH='300'></center><br />\n";
	}

	createAppionLoopTable($sessiondata, $defrunname, "extract");

	echo "<input type='checkbox' name='keepall' $keepallcheck>\n";
	echo "Do not delete .dwn.mrc files after finishing\n";
	echo "<br />\n";

	echo "</td><td class='tablebg'>\n";
	echo "<b>Particle Diameter:</b><br>\n";
	echo "<input type='text' name='diam' value='$diam' SIZE='4'>&nbsp;\n";
	echo "Particle diameter <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>\n";
	echo "<br/>\n";

	echo "<input type='checkbox' name='mirrors' $mirrorsv>\n";
	echo docpop('mirror','Use template mirrors');
	echo "<br/><br/>\n";

	$threshv = ($_POST['thresh']) ? $_POST['thresh'] : 0.5;
	$lpv = ($_POST['lp'] || $_POST['process']) ? $_POST['lp'] : '15';
	$hpv = ($_POST['hp'] || $_POST['process']) ? $_POST['hp'] : '0';
	$binv = (int) ($_POST['bin']) ? $_POST['bin'] : '4';
	$medianv = (int) ($_POST['median'] || $_POST['process']) ? $_POST['median'] : '2';
	$pixlimitv = ($_POST['pixlimit'] || $_POST['process']) ? $_POST['pixlimit'] : '4.0';
	$invertv = ($_POST['invert']=="on") ? "CHECKED" : "";
	$defocpairv = ($_POST['defocpair']=="on") ? "CHECKED" : "";
	$planeregv = ($_POST['planereg']=="off") ? "" : "CHECKED";
	$overlapmultv = ($_POST['overlapmult']) ? $_POST['overlapmult'] : '1.5';

	echo "<B>Peak thresholds:</B><br/>\n";
	echo "<input type='text' name='thresh' VALUE='$threshv' size='4'>\n";
	echo docpop('minthresh',' Minimum threshold');
	echo "<br />\n";
	echo "<input type='text' name='overlapmult' VALUE='$overlapmultv' size='4'>\n";
	echo docpop('overlapmult',' Minimum peak overlap distance multiple');
	echo "<br />\n";
	echo "<input type='checkbox' name='invert' $invertv>\n";
	echo docpop('invert',' Invert image density');
	echo "<br />\n";
	echo "<br />\n";

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
	echo getSubmitForm("Run Signature");
	echo"
		</td>
	</tr>
	</table>
	<b>Using Templates:</b>
	<table><tr>
		<td>\n";
	// Display the templates that will be used for Signature 
	echo "<input type='hidden' name='templateList' value='$templateList'>\n";
	echo "<input type='hidden' name='templates' value='continue'>\n";
	echo "<input type='hidden' name='numtemplates' value='$numtemplates'>\n";
	echo "<input type='hidden' name='numtemplatesused' value='$numtemplatesused'>\n";
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

function runSignaturePicker() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

	$keepall = ($_POST['keepall']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";
	$mirrors = ($_POST['mirrors']=='on') ? "<font color='green'>true</font>" : "<font color='red'>false</font>";

	$numtemplatesused = $_POST['numtemplatesused'];

	// START MAKE COMMAND

	$command ="signaturePicker.py ";

	$apcommand = parseAppionLoopParams($_POST);
	if ($apcommand[0] == "<") {
		createSigForm($apcommand);
		exit;
	}
	$command .= $apcommand;

	$partcommand = parseParticleLoopParams($_POST);
	if ($partcommand[0] == "<") {
		createSigForm($partcommand);
		exit;
	}
	$command .= $partcommand;

	// get the list of templates
	$i=1;
	$templateList = $_POST['templateList'];
	$templates=split(",", $templateList);
	$templateliststr = "";
	foreach ($templates as $template) {
		list($num, $templateid) = split(":",$template);
		$templateliststr .= $templateid.",";
		$i++;
	}
	// remove extra commas and x's
	$templateliststr = substr($templateliststr,0,-1);

	$command.="--template-list=$templateliststr ";

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

	if ($_POST['process']=="Run Signature") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createSigForm("<b>ERROR:</b> Enter a user name and password");

		$nproc = 1;
		if ($numtemplatesused >= 2 && $numtemplatesused <= 8)
			$nproc = $numtemplatesused;
		elseif ($numtemplatesused > 8)
			$nproc = 8;
		$sub = submitAppionJob($command, $outdir, $runname, $expId, 'signature', $testimage, False, False, $nproc);

		// if errors:
		if ($sub) createSigForm("<b>ERROR:</b> $sub");
		if (!$testimage) exit;
	}

	if ($testimage) {
		if (substr($outdir,-1,1)!='/') $outdir.='/';
		$results = "<table width='600' border='0'>\n";
		$results.= "<tr><td>\n";
		$results.= "<b>Signature Picker Command:</b><br />$command";
		$results.= "</td></tr></table>\n";
		$results.= "<br />\n";
		$testjpg=ereg_replace(".mrc","",$_POST['testfilename']);

		$jpgimg=$outdir.$runname."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist = glob($outdir.$runname."/maps/".$testjpg."*.jpg");

		$results.= writeTestResults($jpgimg,$ccclist,$bin=$_POST['bin']);
		createSigForm($false,'Particle Selection Results','Particle Selection Results',$results);
		exit;
	} else {
		processing_header("Particle Selection Results","Particle Selection Results");

		echo"
			<table width='600'>
			<tr><td colspan='2'>
			<b>Signature Picker Command:</b><br>
			$command
			<hr>
			</td></tr>";
		$i = 0;
		foreach ( split(",", $templateliststr) as $templateid ) {
			$i++;
			echo"<tr><td>template $i id</td><td>$templateid</td></tr>";
		}
		echo"<tr><td>template list</td><td>$templateliststr</td></tr>";
		echo"<tr><td>testimage</td><td>$testimage</td></tr>";
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
