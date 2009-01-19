<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/appionloop.inc";
  
// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runManualPicker();
}
// CREATE FORM PAGE
else {
  createManualPickerForm();
}


function createManualPickerForm($extra=false, $title='Manual Picker Launcher', $heading='Manual Particle Selection and Editing', $results=false) {

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

  // --- find hosts to run Manual Picker

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
  processing_header("Manual Picker Launcher","Manual Particle Selection and Editing",$javafunctions);

  if ($extra) {
    echo "<font COLOR='#DD0000' SIZE=+2>$extra</font>\n<HR>\n";
  }
  if ($results) echo "$results<hr />\n";
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>
  <input type='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

  $sessiondata=getSessionList($projectId,$expId);

  // Set any existing parameters in form
  $particle=new particleData;
  $prtlrunIds = $particle->getParticleRunIds($sessionId, True);
  $prtlruns = count($prtlrunIds);
  $defrunname = ($_POST['runname']) ? $_POST['runname'] : 'manrun'.($prtlruns+1);
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $prtlrunval = ($_POST['pickrunid']) ? $_POST['pickrunid'] : '';
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

  echo"
  <table BORDER=0 CLASS=tableborder CELLPADDING=15>
  <TR>
    <TD VALIGN='TOP'>";

  createAppionLoopTable($sessiondata, $defrunname, "extract");

  if (!$prtlrunIds) {
    echo"<font COLOR='RED'><B>No Particles for this Session</B></font>\n";
    echo"<input type='HIDDEN' NAME='pickrunid' VALUE='None'>\n";
  }
  else {
    echo "<br />Edit Particle Picks:
    <SELECT NAME='pickrunid'>\n";
    echo "<OPTION VALUE='None'>None</OPTION>";
    foreach ($prtlrunIds as $prtlrun){
      $prtlrunId=$prtlrun['DEF_id'];
      $runname=$prtlrun['name'];
      $prtlstats=$particle->getStats($prtlrunId);
      $totprtls=commafy($prtlstats['totparticles']);
      echo "<OPTION VALUE='$prtlrunId'";
      // select previously set prtl on resubmit
      if ($prtlrunval==$prtlrunId) echo " SELECTED";
      echo">$runname ($totprtls prtls)</OPTION>\n";
    }
    echo "</SELECT>\n";
  }
  $diam = ($_POST['diam']) ? $_POST['diam'] : "";
  echo "<TD CLASS='tablebg'>\n";
  echo "<b>Particle Diameter:</b><br />\n";
  echo "<input type='text' NAME='diam' VALUE='$diam' SIZE='4'>\n";
  echo docpop('pdiam','Particle diameter for result images');
  echo "<font SIZE=-2><I>(in &Aring;ngstroms)</I></font>\n";
  echo "<br /><br />\n";
  echo "<B>Picking Icon</B><I>\n";
  echo "<br />(only for visual purposes, does not affect data)</I>:<br />\n";
  echo "<SELECT NAME='shape'>\n";
  $shapes = array('plus', 'circle', 'cross', 'point', 'square', 'diamond', );
  foreach($shapes as $shape) {
    $s = ($_POST['shape']==$shape) ? 'SELECTED' : '';
    echo "<OPTION $s>$shape</OPTION>\n";
  }
  echo "</SELECT>\n&nbsp;Picking icon shape<br />";
  $shapesize = (int) $_POST['shapesize'];
  echo"
    <input type='text' NAME='shapesize' VALUE='$shapesize' SIZE='3'>&nbsp;
    Picking icon diameter <font SIZE=-2><I>(in pixels; 0 = autosize)</I></font><br />
		<I>16 pixels is best</I>
    <br /><br />";    
  createParticleLoopTable(-1, -1);
  echo "
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'><HR/>";
  /*  <input type='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
    Test these settings on image:
    <input type='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
    <HR>
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'>";
	*/
	echo getSubmitForm("Run ManualPicker", false, true);
  echo "</TD>
  </TR>
  </table>
  </CENTER>
  </FORM>
";
  processing_footer();
  exit;
}

function runManualPicker() {
	$expId   = $_GET['expId'];
	$outdir  = $_POST['outdir'];
	$runname = $_POST['runname'];

  $command.="manualpicker.py ";
  $apcommand = parseAppionLoopParams($_POST);
  if ($apcommand[0] == "<") {
    createManualPickerForm($apcommand);
    exit;
  }
  $command .= $apcommand;

  $partcommand = parseParticleLoopParams("manual", $_POST);
  if ($partcommand[0] == "<") {
    createManualPickerForm($partcommand);
    exit;
  }
  $command .= $partcommand;
  $pickrunid=$_POST['pickrunid'];
  if ($pickrunid != 'None') {
    $command .= " --pickrunid=$pickrunid";
  }

  $shape=$_POST['shape'];
  if($shape) {
    $command .= " --shape=$shape";
  }

  $shapesize = (int) $_POST['shapesize'];
  if($shapesize && is_int($shapesize)) {
    $command .= " --shapesize=$shapesize";
  } 

  if ($_POST['testimage']=="on") {
    if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
  }

  if ($testimage && $_POST['process']=="Run ManualPicker") {
    $prefix =  "source /ami/sw/ami.csh;";
    $prefix .= "source /ami/sw/share/python/usepython.csh cvs32;";
    $cmd = "$prefix $command > manualpickerlog.txt";
    $result=exec_over_ssh($host, $user, $password, $cmd, True);
  }

  if ($testimage) {
  	$runname = $_POST['runname'];
    	$outdir = $_POST[outdir];
    	if (substr($outdir,-1,1)!='/') $outdir.='/';
	$images = "<table width='600' border='0'>\n";
	$images.= "<tr><td>\n";
    	$images.= "<b>ManualPicker Command:</b><br />$command";
	$results.= "</td></tr></table>\n";
	$results.= "<br />\n";
    	$testjpg=ereg_replace(".mrc","",$testimage);
	$jpgimg=$outdir.$runname."/jpgs/".$testjpg.".prtl.jpg";
	$ccclist=array();
	$images.= writeTestResults($jpgimg,$ccclist);
	createManualPickerForm(false,'Particle Selection Test Results','Particle Selection Test Results',$images);
  }

  else processing_header("Particle Selection Results","Particle Selection Results");

  echo"
    <table WIDTH='600'>
    <TR><TD COLSPAN='2'>
    <B>Manual Picker Command:</B><br />
    $command<HR>
    </TD></TR>";

  appionLoopSummaryTable();
  particleLoopSummaryTable();
  echo"</table>\n";
  processing_footer();
}

?>
