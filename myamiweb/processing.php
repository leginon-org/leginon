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
$progcolor='#CCFFFF';
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

  // --- Get Micrograph Assessment Data
  //$totimgs = $particle->getNumImgsFromSessionId($sessionId);
  $assessedimgs = $particle->getNumAssessedImages($sessionId);
  
  // --- Get Stack Data
  $stackIds = $particle->getStackIds($sessionId);
  $stackruns=count($stackIds);

  // --- Get Class Data
  //$norefIds = $particle->getNoRefIds($sessionId);
  //$norefruns=count($norefIds);
  $norefruns=0;

  // --- Get Reconstruction Data
  if ($stackruns>0) {
          foreach ($stackIds as $stackid) {
	          $reconIds = $particle->getReconIds($stackid['stackid']);
		  if ($reconIds) {
		          $reconruns+=count($reconIds);
		  }
	  }
  }

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
    else {echo "<A HREF='prtlreport.php?expId=$sessionId'>$prtlruns completed</A>\n";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='runPySelexon.php?expId=$sessionId'>";
    if ($prtlruns==0) {echo "Begin Template Picking";}
    else {echo "Continue Template Picking";}
    echo"</A><BR>
    <A HREF='runDogPicker.php?expId=$sessionId'>";
    if ($prtlruns==0) {echo "Begin DoG Picking";}
    else {echo "Continue DoG Picking";}
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
    if ($ctfruns==0) {echo "Begin Estimation";}
    else {echo "Continue Estimation";}
    echo"</A>
    </TD>
  </TR>
  <TR>\n";
  if ($assessedimgs==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {
    if ($assessedimgs < $totimgs) {$bgcolor=$progcolor;$gifimg=$donepic;}
    else {$bgcolor=$donecolor;$gifimg=$donepic;}
  }
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Micrograph Assessment</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>
    $assessedimgs assessed
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='imgAssessor.php?expId=$sessionId'>";
    if ($assessedimgs==0) {echo "Begin Assessment";}
    else {
      if ($assessedimgs < $totimgs) echo "Continue Assessment";
      else echo "Redo Assessment";
    }
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
    else {echo "<A HREF='stacksummary.php?expId=$sessionId'>$stackruns completed<A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='makestack.php?expId=$sessionId'>";
    echo"Create New Stack</A>
    </TD>
  </TR>
  <TR>\n";
  if ($norefruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reference-free Classification</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($norefruns==0) {echo "none";}
    else {echo "<A HREF='norefsummary.php?expId=$sessionId'>$norefruns completed<A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='classifier.php?expId=$sessionId'>";
    echo"Create New Classification</A>
    </TD>
  </TR>
  <TR>\n";
  if ($reconruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}
  echo"  <TD BGCOLOR='$bgcolor'><IMG SRC='$gifimg'></TD>
    <TD BGCOLOR='$bgcolor'>
    <B>Reconstructions</B>
    </TD>
    <TD BGCOLOR='$bgcolor'>\n";
    if ($reconruns==0) {echo "none";}
    else {echo "<A HREF='reconsummary.php?expId=$sessionId'>$reconruns completed</A>";}
    echo"
    </TD>
    <TD BGCOLOR='$bgcolor'>
    <A HREF='emanJobGen.php?expId=$sessionId'>";
    if ($reconruns==0) {echo "Begin Reconstruction";}
    else {echo "Continue Reconstruction";}
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
