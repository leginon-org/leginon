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
  runTiltAligner();
}
// CREATE FORM PAGE
else {
  createTiltAlignerForm();
}


function createTiltAlignerForm($extra=false, $title='Tilt Aligner Launcher', $heading='Tilt Aligner Particle Selection and Editing') {

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

  // --- find hosts to run Tilt Aligner

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
  $javafunctions .= particleLoopJavaCommands();
  writeTop("Tilt Aligner Launcher","Tilt Aligner Particle Selection and Editing",$javafunctions);

  if ($extra) {
    echo "<FONT COLOR='#DD0000' SIZE=+2>$extra</FONT>\n<HR>\n";
  }
  echo"
  <form name='viewerform' method='POST' ACTION='$formAction'>
  <INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

  $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

  // Set any existing parameters in form
  $particle=new particleData;
  $prtlrunIds = $particle->getParticleRunIds($sessionId);
  $prtlruns = count($prtlrunIds);
  $defrunid = ($_POST['runid']) ? $_POST['runid'] : 'tiltrun'.($prtlruns+1);
  $presetval = ($_POST['preset']) ? $_POST['preset'] : 'en';
  $prtlrunval = ($_POST['pickrunid']) ? $_POST['pickrunid'] : '';
  $testcheck = ($_POST['testimage']=='on') ? 'CHECKED' : '';
  $testdisabled = ($_POST['testimage']=='on') ? '' : 'DISABLED';
  $testvalue = ($_POST['testimage']=='on') ? $_POST['testfilename'] : 'mrc file name';

  echo"
  <P>
  <TABLE BORDER=0 CLASS=tableborder CELLPADDING=15>
  <TR>
    <TD VALIGN='TOP'>";

  createAppionLoopTable($sessiondata, $defrunid, "extract");

  if (!$prtlrunIds) {
    echo"<FONT COLOR='RED'><B>No Particles for this Session</B></FONT>\n";
    echo"<INPUT TYPE='HIDDEN' NAME='pickrunid' VALUE='None'>\n";
  }
  else {
    echo "<BR/>Edit Particle Picks:
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
  echo"
    <TD CLASS='tablebg'>
    <B>Particle Diameter:</B><BR>
    <INPUT TYPE='text' NAME='diam' VALUE='$diam' SIZE='4'>&nbsp;
    Particle diameter for result images <FONT SIZE=-2><I>(in &Aring;ngstroms)</I></FONT>
    <BR><BR>";
  /*echo"
    <B>Picking Icon:</B><BR/>
    <SELECT NAME='shape'>\n";
  $shapes = array('plus', 'circle', 'cross', 'point', 'square', 'diamond', );
  foreach($shapes as $shape) {
    $s = ($_POST['shape']==$shape) ? 'SELECTED' : '';
    echo "<OPTION $s>$shape</OPTION>\n";
  }
  echo "</SELECT>\n&nbsp;Picking icon shape<BR/>";
  $shapesize = (int) $_POST['shapesize'];
  echo"
    <INPUT TYPE='text' NAME='shapesize' VALUE='$shapesize' SIZE='3'>&nbsp;
    Picking icon diameter <FONT SIZE=-2><I>(in pixels)</I></FONT>
    <BR><BR>";
	*/
  echo"
    <B>Output file type:</B><BR/>
    <SELECT NAME='ftype'>\n";
  $ftypes = array('spider', 'text', 'xml', 'pickle', );
  foreach($ftypes as $ftype) {
    $s = ($_POST['ftype']==$ftype) ? 'SELECTED' : '';
    echo "<OPTION $s>$ftype</OPTION>\n";
  }
  echo "</SELECT><BR/>";
  createParticleLoopTable(-1, -1);
  echo "
    </TD>
  </TR>
  <TR>
    <TD COLSPAN='2' ALIGN='CENTER'><HR/>";
  /*  <INPUT TYPE='checkbox' NAME='testimage' onclick='enabledtest(this)' $testcheck>
    Test these settings on image:
    <INPUT TYPE='text' NAME='testfilename' $testdisabled VALUE='$testvalue' SIZE='45'>
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
  <BR>
  User: <INPUT TYPE='text' name='user' value=".$_POST['user'].">
  Password: <INPUT TYPE='password' name='password' value=".$_POST['password'].">\n";
  echo"
    </select>*/
  echo"<BR/>";
  //echo"<input type='submit' name='process' value='Just Show Command'>";
  echo"<input type='submit' name='process' value='Run Tilt Aligner'><BR>";
  echo"<FONT class='apcomment'>Submission will NOT run Tilt Aligner,<BR/>
    only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
  </TR>
  </TABLE>";
  writeBottom();
  ?>

  </CENTER>
  </FORM>
  <?
}

function runTiltAligner() {

  $command.="tiltaligner.py ";
  $apcommand = parseAppionLoopParams($_POST);
  if ($apcommand[0] == "<") {
    createTiltAlignerForm($apcommand);
    exit;
  }
  $command .= $apcommand;

  $partcommand = parseParticleLoopParams("manual", $_POST);
  if ($partcommand[0] == "<") {
    createTiltAlignerForm($partcommand);
    exit;
  }
  $command .= $partcommand;
  $pickrunid=$_POST['pickrunid'];
  if ($pickrunid != 'None') {
    $command .= " pickrunid=$pickrunid";
  }

  /*$shape=$_POST['shape'];
  if($shape) {
    $command .= " shape=$shape";
  }

  $shapesize = (int) $_POST['shapesize'];
  if($shapesize && is_int($shapesize)) {
    $command .= " shapesize=$shapesize";
  }*/

  $ftype=$_POST['ftype'];
  if($ftype) {
    $command .= " outtype=$ftype";
  }

  if ($_POST['testimage']=="on") {
    if ($_POST['testfilename']) $testimage=$_POST['testfilename'];
  }

  if ($testimage && $_POST['process']=="Run Tilt Aligner") {
    $host = $_POST['host'];
    $user = $_POST['user'];
    $password = $_POST['password'];
    if (!($user && $password)) {
      createTiltAlignerForm("<B>ERROR:</B> Enter a user name and password");
      exit;
    }
    $prefix =  "source /ami/sw/ami.csh;";
    $prefix .= "source /ami/sw/share/python/usepython.csh cvs32;";
    $cmd = "$prefix $command > tiltalignerlog.txt";
    $result=exec_over_ssh($host, $user, $password, $cmd, True);
  }

  writeTop("Particle Selection Results","Particle Selection Results");

  if ($testimage) {
    $runid = $_POST[runid];
    $outdir = $_POST[outdir];
    if (substr($outdir,-1,1)!='/') $outdir.='/';
    echo "<B>TiltAligner Command:</B><BR>$command";
    $testjpg=ereg_replace(".mrc","",$testimage);
    $jpgimg=$outdir.$runid."/jpgs/".$testjpg.".prtl.jpg";
    $ccclist=array();
    //$cccimg=$outdir.$runid."/manualmaps/".$testjpg.".manualmap1.jpg";
    //$ccclist[]=$cccimg;
    $images=writeTestResults($jpgimg,$ccclist);
    createTiltAlignerForm($images,'Particle Selection Test Results','');
    exit;
  }

  echo"
    <P>
    <TABLE WIDTH='600'>
    <TR><TD COLSPAN='2'>
    <B>Tilt Aligner Command:</B><BR>
    $command<HR>
    </TD></TR>";

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
