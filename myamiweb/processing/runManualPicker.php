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


function createManualPickerForm($extra=false, $title='Manual Picker Launcher', $heading='Manual Particle Selection and Editing') {

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
  $javafunctions .= appionLoopJavaCommands();
  $javafunctions .= writeJavaPopupFunctions('appion');
  $javafunctions .= particleLoopJavaCommands();
  processing_header("Manual Picker Launcher","Manual Particle Selection and Editing",$javafunctions);

  if ($extra) {
    echo "<font COLOR='#DD0000' SIZE=+2>$extra</font>\n<HR>\n";
  }
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>
  <input type='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

  $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

  // Set any existing parameters in form
  $particle=new particleData;
  $prtlrunIds = $particle->getParticleRunIds($sessionId);
  $prtlruns = count($prtlrunIds);
  $defrunid = ($_POST['runid']) ? $_POST['runid'] : 'manrun'.($prtlruns+1);
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $prtlrunval = ($_POST['pickrunid']) ? $_POST['pickrunid'] : '';
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

  echo"
  <P>
  <table BORDER=0 CLASS=tableborder CELLPADDING=15>
  <TR>
    <TD VALIGN='TOP'>";

  createAppionLoopTable($sessiondata, $defrunid, "extract");

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
    Host: <select name='host'>\n";

  $hosts=getHosts();
  foreach($hosts as $host) {
    $s = ($_POST['host']==$host) ? 'selected' : '';
    echo "<option $s >$host</option>\n";
  }
  echo "</select>
  <br />
  User: <input type='text' name='user' value=".$_POST['user'].">
  Password: <input type='password' name='password' value=".$_POST['password'].">\n";
  echo"
    </select>*/
  echo"<br />";
  //echo"<input type='submit' name='process' value='Just Show Command'>";
  echo"<input type='submit' name='process' value='Run ManualPicker'><br />";
  echo"<font class='apcomment'>Submission will NOT run Manual Picker,<br />
    only output a command that you can copy and paste into a unix shell</font>
    </TD>
  </TR>
  </table>";
  processing_footer();
  ?>

  </CENTER>
  </FORM>
  <?
}

function runManualPicker() {

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
    $command .= " pickrunid=$pickrunid";
  }

  $shape=$_POST['shape'];
  if($shape) {
    $command .= " shape=$shape";
  }

  $shapesize = (int) $_POST['shapesize'];
  if($shapesize && is_int($shapesize)) {
    $command .= " shapesize=$shapesize";
  } 

  if ($_POST['testimage']=="on") {
    if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
  }

  if ($testimage && $_POST['process']=="Run ManualPicker") {
    $host = $_POST['host'];
    $user = $_POST['user'];
    $password = $_POST['password'];
    if (!($user && $password)) {
      createManualPickerForm("<B>ERROR:</B> Enter a user name and password");
      exit;
    }
    $prefix =  "source /ami/sw/ami.csh;";
    $prefix .= "source /ami/sw/share/python/usepython.csh cvs32;";
    $cmd = "$prefix $command > manualpickerlog.txt";
    $result=exec_over_ssh($host, $user, $password, $cmd, True);
  }

  processing_header("Particle Selection Results","Particle Selection Results");

  if ($testimage) {
    $runid = $_POST[runid];
    $outdir = $_POST[outdir];
    if (substr($outdir,-1,1)!='/') $outdir.='/';
    echo "<B>ManualPicker Command:</B><br />$command";
    $testjpg=ereg_replace(".mrc","",$testimage);
    $jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
    $ccclist=array();
    //$cccimg=$outdir.$runid."/manualmaps/".$testjpg.".manualmap1.jpg";
    //$ccclist[]=$cccimg;
    $images=writeTestResults($jpgimg,$ccclist);
    createManualPickerForm($images,'Particle Selection Test Results','');
    exit;
  }

  echo"
    <P>
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
