<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/particledata.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ctf.inc');

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
  runUploadTemplate();
}

// Create the form page
else {
  createUploadTemplateForm();
}

function createUploadTemplateForm($extra=false, $title='UploadTemplate.py Launcher', $heading='Upload a template') {
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
  
  writeTop($title,$heading,$javascript);
  // write out errors, if any came up:
  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  
  echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
  $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
  $sessioninfo=$sessiondata['info'];
  
  if (!empty($sessioninfo)) {
    $sessionname=$sessioninfo['Name'];
    echo"<INPUT TYPE='hidden' NAME='sessionname' VALUE='$sessionname'>\n";
  }
  
  // Set any existing parameters in form
  $apix = ($_POST['apix']) ? $_POST['apix'] : '';
  $diam = ($_POST['diam']) ? $_POST['diam'] : '';
  $template = ($_POST['template']) ? $_POST['template'] : '';
  $templatename = ($_POST['templatename']) ? $_POST['templatename'] : '';
  $description = $_POST['description'];
  
  echo"
  <P>
  <TABLE BORDER=3 CLASS=tableborder>";
  echo"
  <TR>
    <TD VALIGN='TOP'>
    <TABLE>
    <TR>
      <TD VALIGN='TOP'>
      <BR/>
      <B>Template Root Name (wild cards are valid):</B><BR/>
      <INPUT TYPE='text' NAME='templatename' VALUE='$templatename' SIZE='50'/><BR/>
      <INPUT TYPE='file' NAME='template' VALUE='$template' SIZE='50'/><BR/>
      <FONT SIZE='-2'>Example: <I>/home/user/groEL-template*.mrc</I></FONT>
      <BR/>
      <BR/>
      <B>Template Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='3' COLS='65'>$description</TEXTAREA>
      <BR/>
      <BR/>
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>
      <BR/>
      Particle Diameter:<BR/>
      <INPUT TYPE='text' NAME='diam' SIZE='5' VALUE='$diam'>
      <FONT SIZE='-2'>(in &Aring;ngstroms)</FONT><BR>
      <BR/>
      Pixel Size:<BR/>
      <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>
      <FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>
      <BR/>
      <BR/>
      </TD>
    </TR>
    </TABLE>
    </TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <HR>
      <BR/>
      <INPUT type='submit' name='process' value='Upload Template'><BR/>
      <FONT COLOR='RED'>Submission will NOT upload the template,<BR/>
			only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
  </TR>
  </TABLE>
  </FORM>
  </CENTER>\n";
  writeBottom();
  exit;
}

function runUploadTemplate() {
  //make sure a template root was entered
  $template=$_POST['template'];
  if ($_POST['templatename']) $template=$_POST['templatename'];
  if (!$template) createUploadTemplateForm("<B>ERROR:</B> Enter a the root name of the template");
  
  //make sure a session was selected
  $description=$_POST['description'];
  if (!$description) createUploadTemplateForm("<B>ERROR:</B> Enter a brief description of the template");
  
  //make sure a session was selected
  $session=$_POST['sessionname'];
  if (!$session) createUploadTemplateForm("<B>ERROR:</B> Select an experiment session");
  
  //make sure a diam was provided
  $diam=$_POST['diam'];
  if (!$diam) createUploadTemplateForm("<B>ERROR:</B> Enter the particle diameter");
  
  //make sure a apix was provided
  $apix=$_POST['apix'];
  if (!$apix) createUploadTemplateForm("<B>ERROR:</B> Enter the pixel size");
  
  $command.="uploadTemplate.py ";
  $command.="template=$template ";
  $command.="session=$session ";
  $command.="apix=$apix ";
  $command.="diam=$diam ";
  $command.="description=\"$description\"";
  
  writeTop("UploadTemplate Run","UploadTemplate Params");
  
  echo"
  <P>
  <TABLE WIDTH='600' BORDER='1'>
    <TR><TD COLSPAN='2'>
    <B>UploadTemplate Command:</B><BR>
    $command
    </TD></TR>
    <TR><TD>template name</TD><TD>$template</TD></TR>
    <TR><TD>apix</TD><TD>$apix</TD></TR>
    <TR><TD>diam</TD><TD>$diam</TD></TR>
    <TR><TD>session</TD><TD>$session</TD></TR>
    <TR><TD>description</TD><TD>$description</TD></TR>
  </TABLE>\n";
  writeBottom();
}
?>
