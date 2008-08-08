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
      elseif (preg_match('/^coran_for_cls.py\s/',$line)) $package='EMAN/SpiCoran';
      elseif (preg_match('/^msgPassing_subClassification.py\s/',$line)) $package='EMAN/MsgP';
      if ($stackid && $modelid && $package) break;
    }
  }
	if (!$package) $package='EMAN';
  // if user wants to use templates from another project

  if($_POST['projectId'])
    $projectId = $_POST[projectId];
  else
    $projectId=getProjectFromExpId($expId);

  $projects=getProjectList();

  processing_header($title,$heading,$javascript);
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

  echo "<input type='hidden' name='outdir' value='$sessionpath'>\n";
  
  // Set any existing parameters in form
  $package = ($_POST['package']) ? $_POST['package'] : $package;
  $contour = ($_POST['contour']) ? $_POST['contour'] : '1.5';
  $zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.5';
  $model = ($_POST['model']) ? $_POST['model'] : '';
  $reconname = ($_POST['reconname']) ? $_POST['reconname'] : '';
  $description = $_POST['description'];
  $oneiteration = ($_POST['oneiteration']=="on") ? "CHECKED" : "";
  $iteration = $_POST['iteration'];
  $contiteration = ($_POST['contiteration']=="on") ? "CHECKED" : "";
  $startiteration = $_POST['startiteration'];
  echo"
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
      <INPUT TYPE='checkbox' NAME='oneiteration' $oneiteration><B>Upload only iteration </b>
<INPUT TYPE='text' NAME='iteration' VALUE='$iteration' SIZE='4'/><br />
      <INPUT TYPE='checkbox' NAME='contiteration' $contiteration><b>Begin with iteration </b>
<INPUT TYPE='text' NAME='startiteration' VALUE='$startiteration' SIZE='4'/><br/>
      </TD>

    <TR>
      <TD VALIGN='TOP' CLASS='tablebg'>
      <P>";
  echo "Stack: ";
  if ($jobId) {
		echo "$stackid <INPUT TYPE='HIDDEN' NAME='stack' VALUE='$stackid'><BR/>\n";
		$stackparams = $particle->getStackParams($stackid);
		//print_r($stackparams);
		echo "&nbsp;Name: ".$stackparams['shownstackname']."<BR/>\n";
		echo "&nbsp;Desc: '".$stackparams['description']."'<BR/>\n";
	} else {
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
      echo">$stackid[stackid] ($s[shownstackname]: $nump particles, $apix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
    }
    echo "</SELECT>\n";
  }
  echo "<P>Initial Model:\n";
  if ($jobId) {
		echo "$modelid <INPUT TYPE='HIDDEN' NAME='model' VALUE='$modelid'><BR/>\n";
		$stackparams = $particle->getInitModelInfo($modelid);
		//print_r($stackparams);
		//echo "\n<BR/>";
		echo "&nbsp;Name: ".$stackparams['name']."<BR/>\n";
		echo "&nbsp;Desc: '".$stackparams['description']."'<BR/>\n";
	} else {
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
  
		echo"<P>";
	}
  echo "<P>Refinement Strategy:\n";
  $eman=array('description'=>'EMAN refine','setting'=>'EMAN');
  $eman_msgp=array('description'=>'EMAN refine followed by message passing subclassification','setting'=>'EMAN/MsgP');
  $eman_coran=array('description'=>'EMAN refine followed by SPIDER coran subclassification','setting'=>'EMAN/SpiCoran');
	$packages=array('EMAN'=>$eman,'EMAN/SpiCoran'=>$eman_coran,'EMAN/MsgP'=>$eman_msgp);
  if ($jobId) {
		echo "$package<INPUT TYPE='HIDDEN' NAME='package' VALUE='$package'><BR/>\n";
		echo "&nbsp;Desc: '".$packages[$package]['description']."'<BR/>\n";
		echo "<BR/>\n";
	} else {
		echo "Process Used:
		    <SELECT NAME='package'> ";
		foreach ($packages as $p) {
			echo "<OPTION VALUE='$p[setting]'";
			// select previously set stack on resubmit
			if ($p['setting']==$_POST['package']) echo " SELECTED";
			echo ">  $p[description]";
			echo "</OPTION>\n";
		}
		echo "
      </SELECT>";
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
      <hr />\n";
	echo getSubmitForm("Upload Recon");
	echo "
    </TD>
	</TR>
  </TABLE>
  </FORM>
  </CENTER>\n";
  processing_footer();
  exit;
}

function runUploadRecon() {
	$expId = $_GET['expId'];
	$outdir = $_POST['outdir'];
 
	$command.="uploadRecon.py ";

	$particle = new particledata();

	// parse params
	$jobId=$_GET['jobId'];
	$description=$_POST['description'];
	$contour=$_POST['contour'];
	$zoom=$_POST['zoom'];
	$oneiteration=$_POST['oneiteration'];
	$iteration=$_POST['iteration'];
	$contiteration=$_POST['contiteration'];
	$startiteration=$_POST['startiteration'];

	//make sure a recon run name was entered
	$runid=$_POST['reconname'];
	if ($_POST['reconname']) $runid=$_POST['reconname'];
	if (!$runid) createUploadReconForm("<B>ERROR:</B> Enter a name of the recon run");
  
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
		$runpath = $reconpath.$runid;
		if (!file_exists($runpath)) createUploadReconForm("<B>ERROR:</B> Could not find recon run directory: ".$runpath);
	}
	else {
		$runpath = "./";
	}
  
	//make sure specific result file is present
	if ($jobId) {
		$jobinfo = $particle->getJobInfoFromId($jobId);
		$fileerror = checkRequiredFileError($jobinfo['appath'],'resolution.txt'); 
	} else {
		$fileerror = checkRequiredFileError($runpath,'resolution.txt'); 
	}
	if ($fileerror) createUploadReconForm($fileerror);

	//make sure the user only want one iteration to be uploaded
	if ($iteration) {
		if (!$oneiteration=='on') createUploadReconForm("<B>ERROR:</B> Select the check box if you really want to upload only one iteration");
	}
	else {
		if ($oneiteration) createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really want to upload only one iteration");
	}

	//make sure the user wants to start iteration from the middle
	if ($startiteration) {
		if (!$contiteration=='on') createUploadReconForm("<B>ERROR:</B> Select the check box if you really want to begin at iteration $startiteration");
	}
	else {
		if ($contiteration) createUploadReconForm("<B>ERROR:</B> Enter the iteration number if you really don't want to start at the beginning");
	}

	$command.="--runid=$runid ";
	$command.="--stackid=$stack ";
	$command.="--modelid=$model ";
	$command.="--package=$package ";
	if (!$jobId) $command.="--outdir=$runpath ";
	if ($jobId) $command.="--jobid=$jobId ";
	if ($contour) $command.="--contour=$contour ";
	if ($zoom) $command.="--zoom=$zoom ";
	if ($oneiteration=='on' && $iteration) $command.="--oneiter=$iteration ";
	if ($contiteration=='on' && $startiteration) $command.="--startiter=$startiteration ";
	$command.="--description=\"$description\"";
  
	// submit job to cluster
	if ($_POST['process']=="Upload Recon") {
		$user = $_SESSION['username'];
		$password = $_SESSION['password'];

		if (!($user && $password)) createUploadReconForm("<b>ERROR:</b> Enter a user name and password");
		echo $outdir;
		$sub = submitAppionJob($command,$outdir,$runid,$expId,'uploadrecon');
		// if errors:
		if ($sub) createUploadReconForm("<b>ERROR:</b> $sub");
		exit;
	}
	processing_header("UploadRecon Run","UploadRecon Params");
	
	echo"
	<TABLE WIDTH='600' BORDER='1'>
	<TR><TD COLSPAN='2'>
	<B>UploadRecon Command:</B><BR>
	$command
	</TD></TR>
	<TR><TD>run name</TD><TD>$runid</TD></TR>
	<TR><TD>stack ID</TD><TD>$stack</TD></TR>
	<TR><TD>model</TD><TD>$model</TD></TR>
	<TR><TD>path</TD><TD>$reconpath</TD></TR>
        <TR><TD>jobid</TD><TD>$jobId</TD></TR>
	<TR><TD>contour</TD><TD>$contour</TD></TR>
	<TR><TD>zoom</TD><TD>$zoom</TD></TR>
	<TR><TD>description</TD><TD>$description</TD></TR>
	</TABLE>\n";
	processing_footer();
}
?>
