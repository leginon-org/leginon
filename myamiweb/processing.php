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
require ('inc/project.inc');
require ('inc/particledata.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ctf.inc');

// check if coming directly from a session
$expId=$_GET['expId'];
if ($expId){
  $sessionId=$expId;
  $projectId=getProjectFromExpId($expId);
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
  $sessionId=$_POST['sessionId'];
  $formAction=$_SERVER['PHP_SELF'];	
}
$projectId=$_POST['projectId'];

writeTop("Appion Data Processing","Appion Data Processing", "<script src='js/viewer.js'></script>");

echo"
<TABLE>
<TR><TD ALIGN='LEFT'>
<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";

// Collect session info from database
$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];
$currentproject=$sessiondata['currentproject'];

// Set colors for unprocessed & finished steps:
$nonecolor='#FFFFCC';
$donecolor='#CCFFCC';
$donepic='img/greengo.gif';
$nonepic='/phpMyAdmin/themes/original/img/b_drop.png';

// If expId specified, don't show pulldowns, only session info
if (!$expId){
  echo"
  <B>Select Session:</B><BR>
  <SELECT NAME='projectId' onchange='newexp()'>\n";
  $projects=getProjectList();
  foreach ($projects as $k=>$project) {
    $sel = ($project['id']==$projectId) ? "selected" : '';
    echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
  }
  
  echo"
  </select>
  <BR>
 
  <SELECT NAME='sessionId' onchange='newexp()'>
  <option value=''>all sessions</OPTION>\n";
  foreach ($sessions as $k=>$session) {
    $sel = ($session['id']==$sessionId) ? 'selected' : '';
    $shortname=substr($session['name'],0,90);
    echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>";
  }
  echo"</select>\n";
}
// Show project & session pulldowns
else {
  $proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
  $sessionDescr=$sessioninfo['Purpose'];
  echo "<TABLE>";
  echo "<TR><TD><B>Project:</B></TD><TD>$proj_link</TD></TR>\n";
  echo "<TR><TD><B>Session:</B></TD><TD>$sessionDescr</TD></TR>\n";

  // get experiment information
  $expinfo = $leginondata->getSessionInfo($expId);
  if (!empty($expinfo)) {
    $i=0;
    $imgpath=$expinfo['Image path'];
    echo "<TR><TD><B>Image Path:</B></TD><TD>$imgpath</TD></TR>\n";
  }
  echo "</TABLE>\n";
}
echo "<P>\n";

if ($sessionId) {
// ---  Get CTF Data
  $ctf = new ctfdata();
  $ctfrunIds = $ctf->getCtfRunIds($sessionId);
  $ctfruns=count($ctfrunIds);

  // --- Get Particle Selection Data
  $particle = new particledata();
  $prtlrunIds = $particle->getParticleRunIds($sessionId);
  $prtlruns=count($prtlrunIds);

  // --- Get Stack Data
  $stackruns=0;

  // --- Get Reconstruction Data
  $reconruns=0;

  echo"
  </FORM>
  <TABLE BORDER='1' CLASS='tableborder' CELLPADDING='5'>
  <TR>\n";
  if ($prtlruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Particle Selection</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($prtlruns==0) {echo "none";}
    else {echo "<A HREF='prtlreport.php?Id=$sessionId'>$prtlruns completed</A>\n";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runPySelexon.php?expId=$sessionId'>";
    if ($prtlruns==0) {echo "Begin Processing";}
    else {echo "Continue Processing";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($ctfruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>CTF Estimation</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($ctfruns==0) {echo "none";}
    else {echo "<A HREF='ctfreport.php?Id=$sessionId'>$ctfruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runPyAce.php?expId=$sessionId'>";
    if ($ctfruns==0) {echo "Begin Processing";}
    else {echo "Continue Processing";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($assessruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Micrograph Assessment</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($assessruns==0) {echo "none";}
    else {echo "<A HREF='assessreport.php?Id=$sessionId'>$assessruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runAssessor.php?expId=$sessionId'>";
    if ($assessruns==0) {echo "Begin Processing";}
    else {echo "Continue Processing";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($stackruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Stacks</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($stackruns==0) {echo "none";}
    else {echo "<A HREF='ctfreport.php?Id=$sessionId'>$ctfruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='makestack.php?expId=$sessionId'>";
    if ($stackruns==0) {echo "Begin Processing";}
    else {echo "Continue Processing";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($stackruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reconstructions</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($reconruns==0) {echo "none";}
    else {echo "<A HREF='ctfreport.php?Id=$sessionId'>$ctfruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runPyAce.php?expId=$sessionId'>";
    if ($reconruns==0) {echo "Begin Processing";}
    else {echo "Continue Processing";}
    echo"</A>
    </TD>
  </TR>
  </TABLE>
  </TD>\n";
}
echo"
</TR>
</TABLE>
</CENTER>\n";
writeBottom();
?>
