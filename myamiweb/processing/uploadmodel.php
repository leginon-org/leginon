<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/ctf.inc";

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadModel();
}

// Create the form page
else {
	createUploadModelForm();
}

function createUploadModelForm($extra=false, $title='UploadModel.py Launcher', $heading='Upload an Initial Model') {
  // check if coming directly from a session
  $expId=$_GET['expId'];
  $rescale=$_GET['rescale'];

  $particle = new particledata();

  // find out if rescaling an existing initial model
  if ($rescale) {
    $modelid=$_GET['modelid'];
    $modelinfo = $particle->getInitModelInfo($modelid);
  }

  if ($expId){
    $sessionId=$expId;
    $projectId=getProjectFromExpId($expId);
    $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
    if ($rescale) $formAction .="&rescale=TRUE&modelid=$modelid";
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
    $sessionpath=$sessioninfo['Image path'];
    $sessionpath=ereg_replace("leginon","appion",$sessionpath);
    $sessionpath=ereg_replace("rawdata","models/",$sessionpath);
  }
  
  // Set any existing parameters in form
  $apix = ($_POST['apix']) ? $_POST['apix'] : '';
  $res = ($_POST['res']) ? $_POST['res'] : '';
  $contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
  $zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.5';
  $model = ($_POST['model']) ? $_POST['model'] : '';
  $modelname = ($_POST['modelname']) ? $_POST['modelname'] : '';
  $description = $_POST['description'];
  $newmodel = ($_POST['newmodel']) ? $_POST['newmodel'] : $sessionpath;
  
  $syms = $particle->getSymmetries();
  echo"
  <P>
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>
    <TABLE>
    <TR>
      <TD VALIGN='TOP'>
      <BR/>\n";
  if ($rescale) {
    echo "
      <B>New Model Name:</B><BR>
      <INPUT TYPE='text' NAME='newmodel' VALUE='$newmodel' SIZE='50'><BR>
    ";
  }
  else {
    echo"
      <B>Model Root Name:</B><BR/>
      <INPUT TYPE='text' NAME='modelname' VALUE='$modelname' SIZE='50'><BR>
      <INPUT TYPE='file' NAME='model' VALUE='$model' SIZE='50'/><BR/>\n";
  }
  echo"
      <P>
      <B>Model Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='3' COLS='65'>$description</TEXTAREA>
      </TD>
    </TR>
    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>
      <P>
      <B>Model Symmetry:</B>\n";
  if ($rescale) {
    $symid=$modelinfo['REF|ApSymmetryData|symmetry'];
    $symmetry=$particle->getSymInfo($symid);
    $res = $modelinfo['resolution'];
    $apix = $modelinfo['pixelsize'];
    echo "$symmetry[symmetry]<BR>
    <INPUT TYPE='hidden' NAME='sym' VALUE='$symid'>
    <B>Model Resolution:</B> $res<BR>
    <INPUT TYPE='hidden' NAME='res' VALUE='$res' SIZE='5'>
    <B>Pixel Size:</B> $apix<BR>
    <INPUT TYPE='hidden' NAME='apix' SIZE='5' VALUE='$apix'>\n";
  }
  else {
    echo"
      <SELECT NAME='sym'>
      <OPTION VALUE=''>Select One</OPTION>\n";
    foreach ($syms as $sym) {
      echo "<OPTION VALUE='$sym[DEF_id]'";
      if ($sym['DEF_id']==$_POST['sym']) echo " SELECTED";
      echo ">$sym[symmetry]";
      if ($sym['symmetry']=='C1') echo " (no symmetry)";
      echo "</OPTION>\n";
    }
    echo"
      </SELECT>
      <P>
      <INPUT TYPE='text' NAME='res' VALUE='$res' SIZE='5'> Model Resolution
      <BR>
      <INPUT TYPE='text' NAME='apix' SIZE='5' VALUE='$apix'>
      Pixel Size <FONT SIZE='-2'>(in &Aring;ngstroms per pixel)</FONT>\n";
  }
  echo "
      <P>
      <B>Snapshot Options:</B>
      <BR>
      <INPUT TYPE='text' NAME='contour' VALUE='$contour' SIZE='5'> Contour Level
      <BR>
      <INPUT TYPE='text' NAME='zoom' VALUE='$zoom' SIZE='5'> Zoom
      <P>
      </TD>
    </TR>
    </TABLE>
  </TD>
  </TR>
  <TR>
    <TD ALIGN='CENTER'>
      <HR>
      <BR/>
      <INPUT type='submit' name='process' value='Upload Model'><BR/>
      <FONT COLOR='RED'>Submission will NOT upload the model,<BR/>
			only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
	</TR>
  </TABLE>
  </FORM>
  </CENTER>\n";
  writeBottom();
  exit;
}

function runUploadModel() {
  $contour=$_POST['contour'];
  $zoom=$_POST['zoom'];

  //make sure a model root was entered
  $model=$_POST['model'];
  if ($_POST['modelname']) $model=$_POST['modelname'];
  if ($_POST['newmodel']) $model=$_POST['newmodel'];
  if (!$model) createUploadModelForm("<B>ERROR:</B> Enter a root name of the model");
  
  //make sure a session was selected
  $description=$_POST['description'];
  if (!$description) createUploadModelForm("<B>ERROR:</B> Enter a brief description of the model");

  //make sure a resolution was provided
  $res=$_POST['res'];
  if (!$res) createUploadModelForm("<B>ERROR:</B> Enter the model resolution");

  //make sure a apix was provided
  $apix=$_POST['apix'];
  if (!$apix) createUploadModelForm("<B>ERROR:</B> Enter the pixel size");
  
  // make sure a symmetry was selected
  $sym = $_POST['sym'];
  if (!$sym) createUploadModelForm("<B>ERROR:</B> Select a symmetry");

  $command.="uploadModel.py ";
  $command.="$model ";
  $command.="session=$session ";
  $command.="apix=$apix ";
  $command.="res=$res ";
  $command.="symmetry=$sym ";
  if ($contour) $command.="contour=$contour ";
  if ($zoom) $command.="zoom=$zoom ";
  $command.="description=\"$description\"";
  
  writeTop("UploadModel Run","UploadModel Params");
	
  echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>UploadModel Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>model name</TD><TD>$model</TD></TR>
	<TR><TD>symmetry ID</TD><TD>$sym</TD></TR>
	<TR><TD>apix</TD><TD>$apix</TD></TR>
	<TR><TD>res</TD><TD>$res</TD></TR>
	<TR><TD>contour</TD><TD>$contour</TD></TR>
	<TR><TD>zoom</TD><TD>$contour</TD></TR>
	<TR><TD>session</TD><TD>$session</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
  writeBottom();
}
?>
