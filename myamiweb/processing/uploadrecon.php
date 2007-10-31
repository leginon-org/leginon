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
	runUploadRecon();
}

// Create the form page
else {
	createUploadReconForm();
}

function createUploadReconForm($extra=false, $title='UploadRecon.py Launcher', $heading='Upload Reconstruction Results') {
  // check if session provided
  $expId = $_GET['expId'];
  $jobId = $_GET['jobId'];
  if ($expId) {
    $sessionId=$expId;
    $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
    if ($jobId) $formAction.="&jobId=$jobId";
  }
  else {
    $sessionId=$_POST['sessionId'];
    $formAction=$_SERVER['PHP_SELF'];
  }

  $particle = new particledata();

  // if uploading a specific recon, get recon info from database & job file
  if ($jobId) {
    $jobinfo = $particle->getJobInfoFromId($jobId);
    $jobrunid = ereg_replace('\.job$','',$jobinfo['name']);
    $sessionpath = ereg_replace($jobrunid,'',$jobinfo['appath']);
    $jobfile = $jobinfo['appath'].'/'.$jobinfo['name'];
    $f = file($jobfile);
    foreach ($f as $line) {
      if (preg_match('/^\#\sstackId:\s/',$line)) $stackid=ereg_replace('# stackId: ','',trim($line));
      elseif (preg_match('/^\#\smodelId:\s/',$line)) $modelid=ereg_replace('# modelId: ','',trim($line));
      if ($stackid && $modelid) break;
    }
  }

  // if user wants to use templates from another project

  if($_POST['projectId'])
    $projectId = $_POST[projectId];
  else
    $projectId=getProjectFromExpId($expId);

  $projects=getProjectList();

  writeTop($title,$heading,$javascript);
  // write out errors, if any came up:

  if ($extra) {
    echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
  }
  
  echo"<FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
  $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
  $sessioninfo=$sessiondata['info'];
  
  if (!empty($sessioninfo) && !$jobId) {
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","recon/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
  }

  
  // Set any existing parameters in form
  $package = ($_POST['package']) ? $_POST['package'] : 'EMAN';
  $contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
  $zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.75';
  $model = ($_POST['model']) ? $_POST['model'] : '';
  $reconname = ($_POST['reconname']) ? $_POST['reconname'] : '';
  $description = $_POST['description'];
  $oneiteration = ($_POST['oneiteration']=="on") ? "CHECKED" : "";
  $iteration = $_POST['iteration'];
  echo"
  <P>
  <TABLE BORDER=3 CLASS=tableborder>
  <TR>
    <TD VALIGN='TOP'>
    <TABLE>
    <TR>
      <TD VALIGN='TOP'>
      <BR/>
      <B>Recon Name: </B>\n";
  if ($jobId) echo "$jobrunid<INPUT TYPE='HIDDEN' NAME='reconname' VALUE='$jobrunid'>";
  else echo "<BR/><INPUT TYPE='text' NAME='reconname' VALUE='$reconname' SIZE='50'>";
  echo "
      <BR/>
      <B>Recon Base Directory:</B>\n";
  if ($jobId) echo "$sessionpath\n";
  else echo "<BR/><INPUT TYPE='text' NAME='reconpath' VALUE='$sessionpath' SIZE='50'/>";
  echo "
      <BR/>
      <P>
      <B>Recon Description:</B><BR/>
      <TEXTAREA NAME='description' ROWS='3' COLS='50'>$description</TEXTAREA>
<BR>
      <INPUT TYPE='checkbox' NAME='oneiteration' $oneiteration><B>Upload only iteration </B>
<INPUT TYPE='text' NAME='iteration' VALUE='$iteration' SIZE='4'/><BR/>
      </TD>

    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>
      <P>";
  echo "Stack: ";
  if ($jobId) echo "$stackid<INPUT TYPE='HIDDEN' NAME='stack' VALUE='$stackid'>\n";
  else {
    echo "<SELECT NAME='stack'>\n";

    // find each stack entry in database
    $stackIds = $particle->getStackIds($sessionId);

    foreach ($stackIds as $stackid){
      // get stack parameters from database
      $s=$particle->getStackParams($stackid['stackid']);
      // get number of particles in each stack
      $nump=commafy($particle->getNumStackParticles($stackid['stackid']));
      // get pixel size of stack
      $apix=($particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
      // get box size
      $box=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
      // get stack path with name
      $opvals = "$stackid[stackid]";
      echo "<OPTION VALUE='$stackid[stackid]'";
      // select previously set stack on resubmit
      if ($stackid['stackid']==$_POST['stack']) echo " SELECTED";
      echo">$stackid[stackid] ($s[stackRunName]: $nump particles, $apix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
    }
    echo "</SELECT>\n";
  }
  echo "<P>Initial Model:\n";
  if ($jobId) echo "$modelid<INPUT TYPE='HIDDEN' NAME='model' VALUE='$modelid'>\n";
  else {
    echo "
      <SELECT NAME='model'>
      <OPTION VALUE=''>Select One</OPTION>\n";

    // get initial models associated with project
    $models=$particle->getModelsFromProject($projectId);

    foreach ($models as $model) {
      echo "<OPTION VALUE='$model[DEF_id]'";
      if ($model['DEF_id']==$_POST['model']) echo " SELECTED";
      echo "> ".$model['DEF_id']." ($model[description])";
      echo "</OPTION>\n";
    }
    echo"</SELECT>\n";
  }
  echo"<P>";
  $eman=array('description'=>'EMAN refine','setting'=>'EMAN');
  $eman_msgp=array('description'=>'EMAN refine followed by message passing subclassification','setting'=>'EMAN/MsgP');
  $packages=array($eman,$eman_msgp);
  echo "Process Used:
      <SELECT NAME='package'> ";
  foreach ($packages as $package) {
    echo "<OPTION VALUE='$package[setting]'";
    // select previously set stack on resubmit
    if ($package['setting']==$_POST['package']) echo " SELECTED";
    echo ">  $package[description]";
    echo "</OPTION>\n";
  }
    echo"
      </SELECT>

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
      <INPUT type='submit' name='process' value='Upload Recon'><BR/>
      <FONT class='apcomment'>Submission will NOT upload the reconstruction,<BR/>
			only output a command that you can copy and paste into a unix shell</FONT>
    </TD>
	</TR>
  </TABLE>
  </FORM>
  </CENTER>\n";
  writeBottom();
  exit;
}

function runUploadRecon() {
  $jobId=$_GET['jobId'];
  $description=$_POST['description'];
  $contour=$_POST['contour'];
  $zoom=$_POST['zoom'];
  $oneiteration=$_POST['oneiteration'];
  $iteration=$_POST['iteration'];

  //make sure a recon run name was entered
  $reconname=$_POST['reconname'];
  if ($_POST['reconname']) $reconname=$_POST['reconname'];
  if (!$reconname) createUploadReconForm("<B>ERROR:</B> Enter a name of the recon run");
  
  //make sure a stack was chosen
  $model=$_POST['stack'];
  if ($_POST['stack']) $stack=$_POST['stack'];
  if (!$stack) createUploadReconForm("<B>ERROR:</B> Select the image stack used");

  //make sure a model was chosen
  $model=$_POST['model'];
  if ($_POST['model']) $model=$_POST['model'];
  if (!$model) createUploadReconForm("<B>ERROR:</B> Select the initial model used");
  
  //make sure a package was chosen
  $package=$_POST['package'];
  if (!$package) createUploadReconForm("<B>ERROR:</B> Enter the reconstruction process used");

  //make sure a description was entered
  $description=$_POST['description'];
  if (!$description) createUploadReconForm("<B>ERROR:</B> Enter a description of the reconstruction");

  //make sure a package was chosen
  if ($_POST['reconpath'] && $_POST['reconpath']!="./") {
    $reconpath = $_POST['reconpath'];
    if (substr($reconpath,-1,1)!='/') $reconpath.='/';
    $runpath = $reconpath.$reconname;
    if (!file_exists($runpath)) createUploadReconForm("<B>ERROR:</B> Could not find recon run directory: ".$runpath);
  } else {
    $runpath = "./";
  }
  //make sure the user only want one iteration to be uploaded
  if ($iteration) {
    if (!$oneiteration=='on') createUploadReconForm("<B>ERROR:</B> Select the check box if you really want to upload only one iteration");
  } else {
    if ($oneiteration) createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really want to upload only one iteration");
  }
  $command.="uploadRecon.py ";
  $command.="runid=$reconname ";
  $command.="stackid=$stack ";
  $command.="modelid=$model ";
  $command.="package=$package ";
  if (!$jobId) $command.="dir=$runpath ";
  if ($jobId) $command.="jobid=$jobId ";
  if ($contour) $command.="contour=$contour ";
  if ($zoom) $command.="zoom=$zoom ";
  if ($oneiteration=='on' && $iteration) $command.="oneiteration=$iteration ";
  $command.="description=\"$description\"";
  
  writeTop("UploadRecon Run","UploadRecon Params");
	
  echo"
	<P>
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>UploadRecon Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>run name</TD><TD>$reconname</TD></TR>
	<TR><TD>stack ID</TD><TD>$stack</TD></TR>
	<TR><TD>model</TD><TD>$model</TD></TR>
	<TR><TD>path</TD><TD>$reconpath</TD></TR>
        <TR><TD>jobid</TD><TD>$jobid</TD></TR>
	<TR><TD>contour</TD><TD>$contour</TD></TR>
	<TR><TD>zoom</TD><TD>$zoom</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
  writeBottom();
}
?>
