<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ssh.inc');
require ('inc/appionloop.inc');
 
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

function createTemplateForm() {
	// check if coming directly from a session
	$expId = $_GET[expId];
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
		$templatetable="<TABLE BORDER='1' CELLPADDING='5' WIDTH='600'>\n";
		$templatetable.="<style type='text/css'><!-- input { font-size: 14px; } --></style>";
		$numtemplates=count($templateData);

		foreach($templateData as $templateinfo) { 
			if (is_array($templateinfo)) {
				$filename=$templateinfo[templatepath] ."/".$templateinfo[templatename];
				$checkboxname='template'.$i;
				// create the javascript functions to enable the templates
				$javafunctions.="function enable".$checkboxname."() {
						 if (document.viewerform.$checkboxname.checked){
						 document.viewerform.".$checkboxname."strt.disabled=false;
						 document.viewerform.".$checkboxname."strt.value='';
						 document.viewerform.".$checkboxname."end.disabled=false;
						 document.viewerform.".$checkboxname."end.value='';
						 document.viewerform.".$checkboxname."incr.disabled=false;
						 document.viewerform.".$checkboxname."incr.value='';
					 }
					 else {
						 document.viewerform.".$checkboxname."strt.disabled=true;
						 document.viewerform.".$checkboxname."strt.value='0';
						 document.viewerform.".$checkboxname."end.disabled=true;
						 document.viewerform.".$checkboxname."end.value='90';
						 document.viewerform.".$checkboxname."incr.disabled=true;
						 document.viewerform.".$checkboxname."incr.value='10';
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
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname."strt' DISABLED VALUE='0' SIZE='3'> Starting Angle<BR>\n";
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname."end' DISABLED VALUE='90' SIZE='3'> Ending Angle<BR>\n";
				$templatetable.="<INPUT TYPE='text' NAME='".$checkboxname."incr' DISABLED VALUE='10' SIZE='3'> Angular Increment<BR>\n";
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
	$javafunctions.="<script src='js/viewer.js'></script>\n";

	writeTop("Template Correlator Launcher","Automated Particle Selection with Template Correlator",$javafunctions);
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
}

function createTCForm($extra=false, $title='Template Correlator Launcher', $heading='Automated Particle Selection with Template Correlator') {
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

	// --- find hosts to run Template Correlator
	$hosts=getHosts();
 
	$numtemplates=$_POST[numtemplates];
	$templateForm='';
	$templateTable="<TABLE CLASS='tableborder'><TR><TD>\n";
	$templateCheck='';

	$particle=new particleData;
	$prtlruns = count($particle->getParticleRunIds($sessionId));

	for ($i=1; $i<=$numtemplates; $i++) {
		$templateimg="template".$i;
		if ($_POST[$templateimg]){
			$templateIdName="templateId".$i;
			$tmpltstrt=$templateimg."strt";
			$tmpltend=$templateimg."end";
			$tmpltincr=$templateimg."incr";
			$templateId=$_POST[$templateIdName];
			$start=$_POST[$tmpltstrt];
			$end=$_POST[$tmpltend];
			$incr=$_POST[$tmpltincr];

			$templateList.=$i.":".$templateId.",";
			$templateInfo=$particle->getTemplatesFromId($templateId);
			$tmpltrows=$templateInfo[0];
			$filename=$tmpltrows[templatepath]."/".$tmpltrows[templatename];
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
	if ($templateList) { $templateList=substr($templateList,0,-1);}
	else {
		echo "<B>no templates chosen, go back and choose templates</B>\n";
		exit;
	}
	$javascript="
	<script src='js/viewer.js'></script>
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
	appionLoopJavaCommands();
   particleLoopJavaCommands();
	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
		echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
	echo"
	<form name='viewerform' method='POST' ACTION='$formAction'>
	<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";
	$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
	$sessioninfo=$sessiondata['info'];
	$presets=$sessiondata['presets'];
	if (!empty($sessioninfo)) {
		$sessionpath=$sessioninfo['Image path'];
		$sessionpath=ereg_replace("leginon","appion",$sessionpath);
		$sessionpath=ereg_replace("rawdata","extract/",$sessionpath);
		$sessionname=$sessioninfo['Name'];
	}


	// if session is changed, change the output directory
	$sessionpathval=(($_POST['sessionId']==$_POST['lastSessionId'] || $expId) && $_POST['lastSessionId']) ? $_POST['outdir'] : $sessionpath;
	// Set any existing parameters in form
	$runidval = ($_POST['runid']) ? $_POST['runid'] : 'tmplrun'.($prtlruns+1);
	$presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
	$testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
	$testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
	$testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

	echo"
	<P>
	<TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
	<TR>
		<TD VALIGN='TOP'>
			<A HREF=\"javascript:infopopup('runid')\"><B>Run Name:</B></A>
			<INPUT TYPE='text' NAME='runid' VALUE='$runidval'><BR>
			<BR>
     
			<B>Output Directory:</B><BR>
			<INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='45'><BR>
			<BR>\n";

	if ($presets) {
		echo"<B>Preset</B>\n<SELECT NAME='preset'>\n";
		foreach ($presets as $preset) {
			echo "<OPTION VALUE='$preset' ";
			// make en selected by default
			if ($preset==$presetval) echo "SELECTED";
			echo ">$preset</OPTION>\n";
		}
		echo"</SELECT><BR><BR>\n";
	}
	else {
		echo"<INPUT TYPE='hidden' NAME='alldbimages' VALUE=1>\n";
		echo"<FONT COLOR='RED' SIZE=+1><B>No Presets for this Session</B></FONT><BR><BR>\n";
	}
	createAppionLoopTable();
	echo"
		</TD>
		<TD CLASS='tablebg'>
			<B>Mask Diameter:</B><BR>
			<INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>&nbsp;
			Mask diameter for template <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
			<BR><BR>";
		createParticleLoopTable(0.5,"");
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
	User: <INPUT TYPE='text' name='user' value=".$_POST['user'].">
	Password: <INPUT TYPE='password' name='password' value=".$_POST['password'].">\n";
	echo"
		</select>
		<BR>
		<input type='submit' name='process' value='Just Show Command'>
		<input type='submit' name='process' value='Run Correlator'><BR>
		<FONT COLOR='RED'>Submission will NOT run Template Correlator, only output a command that you can copy and paste into a unix shell</FONT>
		</TD>
	</TR>
	</TABLE>
	</TD>
	</TR>
	</TABLE>
	<B>Using Templates:</B>
	<TABLE><TR>
		<TD>\n";
	// Display the templates that will be used for Template Correlator
	echo "<INPUT TYPE='hidden' NAME='templateList' VALUE='$templateList'>\n";
	echo "<INPUT TYPE='hidden' NAME='templates' VALUE='continue'>\n";
	echo "<INPUT TYPE='hidden' NAME='numtemplates' VALUE='$numtemplates'>\n";
	echo "<INPUT TYPE='hidden' NAME='sessionname' VALUE='$sessionname'>\n";
	echo "$templateForm\n";
	echo "$templateTable\n";
	?>
		</TD>
	</TR></TABLE>

	</CENTER>
	</FORM>
	<?
	writeBottom();
}

function runTemplateCorrelator() {
	$host = $_POST['host'];
	$user = $_POST['user'];
	$password = $_POST['password'];
	if ($_POST['process']=="Run Correlator" && !($user && $password)) {
		createTCForm("<B>ERROR:</B> Enter a user name and password");
	}

	//make sure a session was selected
	if (!$_POST[outdir]) {
		createTCForm("<B>ERROR:</B> Select an experiment session");
		exit;
	}
	$outdir=$_POST[outdir];
	// make sure outdir ends with '/'
	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$runid=$_POST[runid];

	// get the list of templates
	$i=1;
	$templateList=$_POST[templateList];
	$templates=split(",", $templateList);
	foreach ($templates as $tmplt) {
		list($tmpltNum,$tmpltId)=split(":",$tmplt);
		$templateIds.="$tmpltId,";
		$tmpltstrt="template".$tmpltNum."strt";
		$tmpltend="template".$tmpltNum."end";
		$tmpltincr="template".$tmpltNum."incr";
		// set the ranges specified
		$rangenum="range".$i;
		if ($_POST[$tmpltstrt]!=''){
			$range=$_POST[$tmpltstrt].",".$_POST[$tmpltend].",".$_POST[$tmpltincr];
		}
		// if no rotation
		else {
			$range="0,10,20";
		}
		$ranges[$rangenum]=$range;
		$i++;
	}
	$templateIds=substr($templateIds,0,-1);
  
	$diam = $_POST[diam];
	if (!$diam) {
		createTCForm("<B>ERROR:</B> Specify a particle diameter");
		exit;
	}

	$thresh = $_POST[thresh];
	if (!$thresh) {
		createTCForm("<B>ERROR:</B> No thresholding value was entered");
		exit;
	}

	if ($_POST['testimage']=="on") {
		if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
		else {
			createTCForm("<B>ERROR:</B> Specify an mrc file to test these parameters");
			exit;
		}
	}
	elseif ($_POST['sessionname']) {
		if ($_POST['preset']) $dbimages=$_POST[sessionname].",".$_POST[preset];
		elseif(!$_POST['alldbimages']) {
			createTCForm("<B>ERROR:</B> Select an image preset for template matching");
			exit;
		}
	}

	if ($testimage && $_POST['process']=="Run Correlator") {
		$command.="source /ami/sw/ami.csh;";
		$command.="source /ami/sw/share/python/usepython.csh cvs32;";
	}
	$command.="templateCorrelator.py ";
	if ($testimage) $command.="$testimage ";
	else $command.="dbimages=$dbimages ";
	$command.="templateIds=$templateIds ";
	foreach ($ranges as $rangenum=>$rangevals) {
		$command.="$rangenum=$rangevals ";
	}
	$command.="runid=$runid ";
	$command.="outdir=$outdir ";
	$command.="diam=$diam ";
	$command .= parseAppionLoopParams($_POST);
	$command .= parseParticleLoopParams($_POST);

	$cmd = "$command > templateCorrelatorLog.txt";
	if ($testimage && $_POST['process']=="Run Correlator") {
		$result=exec_over_ssh($host, $user, $password, $cmd, True);
	}

	writeTop("Particle Selection Results","Particle Selection Results");

	if ($testimage) {
		$testjpg=ereg_replace(".mrc","",$testimage);
		$jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
		$ccclist=array();
		$i=1;
		foreach ($templates as $tmplt) {
   			$cccimg=$outdir.$runid."/ccmaxmaps/".$testjpg.".ccmaxmap".$i.".jpg";
			$ccclist[]=$cccimg;
			$i++;
		}
		$images=writeTestResults($jpgimg,$ccclist);
		createTCForm($images,'Particle Selection Results','');
		exit;
	}

	echo"
  <P>
  <TABLE WIDTH='600'>
  <TR><TD COLSPAN='2'>
  <B>Template Correlator Command:</B><BR>
  $command<HR>
  </TD></TR>
  <TR><TD>outdir</TD><TD>$outdir</TD></TR>
  <TR><TD>templateIds</TD><TD>$templateIds</TD></TR>";
	foreach ($ranges as $rangenum=>$rangevals) {
		echo "<TR><TD>$rangenum</TD><TD>$rangevals</TD></TR>\n";
	}
	echo"<TR><TD>runid</TD><TD>$runid</TD></TR>
  <TR><TD>testimage</TD><TD>$testimage</TD></TR>
  <TR><TD>dbimages</TD><TD>$dbimages</TD></TR>
  <TR><TD>diameter</TD><TD>$diam</TD></TR>";
	appionLoopSummaryTable();
	particleLoopSummaryTable();
	echo"</TABLE>\n";
	writeBottom();
}

function writeTestResults($jpg,$ccclist){
	echo"<CENTER>\n";
	echo"<A HREF='loadimg.php?filename=$jpg&scale=0.8'>\n";
	echo"<IMG SRC='loadimg.php?filename=$jpg&scale=0.35'></A>\n";
	if (count($ccclist)>1) echo "<BR>\n";
	foreach ($ccclist as $ccc){
		echo"<A HREF='loadimg.php?filename=$ccc&scale=0.8'>\n";
		echo"<IMG SRC='loadimg.php?filename=$ccc&scale=0.35'></A>\n";
	}
	echo"</CENTER>\n";
}

?>
