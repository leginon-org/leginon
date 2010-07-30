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

// IF valueS SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
	runUploadRecon();
}

// Create the form page
else {
	createUploadReconForm();
}

function createUploadReconForm($extra=false, $title='UploadXmippRecon.py Launcher', $heading='Upload Reconstruction Results') {
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

  $javafunctions .= writeJavaPopupFunctions('appion');  

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

  $projectId=getProjectId();

  processing_header($title,$heading,$javafunctions);
  // write out errors, if any came up:

  if ($extra) {
    echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
  }
  
  echo"<form name='viewerform' method='post' action='$formAction'>\n";
  $sessiondata=getSessionList($projectId,$expId);
  $sessioninfo=$sessiondata['info'];
  
  if (!empty($sessioninfo) && !$jobId) {
	$sessionpath=$sessioninfo['Image path'];
	$sessionpath=ereg_replace("leginon","appion",$sessionpath);
	$sessionpath=ereg_replace("rawdata","recon/",$sessionpath);
	$sessionname=$sessioninfo['Name'];
  }

  echo "<input type='hidden' name='outdir' value='$sessionpath'>\n";
  
  // Set any existing parameters in form
  $contour = ($_POST['contour']) ? $_POST['contour'] : '2.0';
  $mass = ($_POST['mass']) ? $_POST['mass'] : '';
  $zoom = ($_POST['zoom']) ? $_POST['zoom'] : '1.0';
  $filter = ($_POST['filter']) ? $_POST['filter'] : '';
  $model = ($_POST['model']) ? $_POST['model'] : '';
  $runname = ($_POST['runname']) ? $_POST['runname'] : '';
  $description = $_POST['description'];
  $oneiteration = ($_POST['oneiteration']=="on") ? "CHECKED" : "";
  $iteration = $_POST['iteration'];
  echo"
  <table border='3' class='tableborder'>
  <tr>
    <td valign='top'>
    <table>
    <tr>
      <td valign='top'>
      <br>
      <b>Recon Name:</b> \n";
  if ($jobId) echo "$jobrunid<input type='hidden' name='runname' value='$jobrunid'>";
  else echo "<br><input type='text' name='runname' value='$runname' size='50'>";
  echo "
      <br>
      <B>Recon Base Directory:</B>\n";
  if ($jobId) echo "$sessionpath\n";
  else echo "<br><input type='text' name='reconpath' value='$sessionpath' size='50'/>";
  echo "
      <br/>
      <p>
      <b>Recon Description:</b><br/>
      <textarea name='description' rows='3' cols='50'>$description</textarea>
<br>
      </td>

    <tr>
      <td valign='top' class='tablebg'>
      <p>";
  echo "Stack: ";
  if ($jobId) {
		echo "$stackid <input type='hidden' name='stack' value='$stackid'><br>\n";
		$stackparams = $particle->getStackParams($stackid);
		//print_r($stackparams);
		echo "&nbsp;Name: ".$stackparams['shownstackname']."<br>\n";
		echo "&nbsp;Desc: '".$stackparams['description']."'<br>\n";
	} else {
    echo "<select name='stack'>\n";

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
      $box=$s['boxsize'];
      // get stack path with name
      $opvals = "$stackid[stackid]";
      echo "<option value='$stackid[stackid]'";
      // select previously set stack on resubmit
      if ($stackid['stackid']==$_POST['stack']) echo " selected";
      echo">$stackid[stackid] ($s[shownstackname]: $nump particles, $apix &Aring;/pix, ".$box."x".$box.")</option>\n";
    }
    echo "</select>\n";
  }
  echo "<P>Initial Model:\n";
  if ($jobId) {
		echo "$modelid <input type='hidden' name='model' value='$modelid'><br>\n";
		$modelparams = $particle->getInitModelInfo($modelid);
		//print_r($modelparams);
		//echo "\n<br>";
		echo "&nbsp;Name: ".$modelparams['name']."<br>\n";
		echo "&nbsp;Desc: '".$modelparams['description']."'<br>\n";
	} else {
    echo "
      <SELECT name='model'>
      <OPTION value=''>Select One</OPTION>\n";

    // get initial models associated with project
    $models=$particle->getModelsFromProject($projectId);

    foreach ($models as $model) {
      echo "<OPTION value='$model[DEF_id]'";
      if ($model['DEF_id']==$_POST['model']) echo " SELECTED";
      echo "> ".$model['DEF_id']." ($model[description])";
      echo "</OPTION>\n";
    }
    echo"</SELECT>\n";
  
		echo"<P>";
	}
	echo "
      <p>
      <b>Snapshot Options:</b>
      <br>
      <input type='text' name='mass' value='$mass' size='4'> Mass (in kDa)
      <br>
		";	
	echo "
      <P>
      </td>
    </tr>
    </table>
  </td>
  </tr>
  <tr>
    <td align='center'>
      <hr />\n";
	echo getSubmitForm("Upload Recon");
	echo "
    </td>
	</tr>
  </table>
  </form>
  </center>\n";

	echo referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 
		2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.",
		"J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

  processing_footer();
  exit;
}

function runUploadRecon() {
	/* *******************
	PART 1: Get variables
	******************** */
 	$jobId=$_GET['jobId'];
	$model=$_POST['stack'];
	$description=$_POST['description'];
	$mass=$_POST['mass'];
	$runname=$_POST['runname'];
	if ($_POST['stack']) $stack=$_POST['stack'];
	if ($_POST['model']) $model=$_POST['model'];
	$description=$_POST['description'];

	/* *******************
	PART 2: Check for conflicts, if there is an error display the form again
	******************** */

	//make sure a recon run name was entered
	if (!$runname) createUploadReconForm("<B>ERROR:</B> Enter a name of the recon run");
  
	//make sure a stack was chosen
	if (!$stack) createUploadReconForm("<B>ERROR:</B> Select the image stack used");
	
	//make sure a model was chosen
	if (!$model) createUploadReconForm("<B>ERROR:</B> Select the initial model used");
  
	//make sure a description was entered
	if (!$description) createUploadReconForm("<B>ERROR:</B> Enter a description of the reconstruction");

	//make sure a package was chosen
	if ($_POST['reconpath'] && $_POST['reconpath']!="./") {
		$reconpath = $_POST['reconpath'];
		if (substr($reconpath,-1,1)!='/') $reconpath.='/';
		$runpath = $reconpath.$runname;
		if (!file_exists($runpath)) createUploadReconForm("<B>ERROR:</B> Could not find recon run directory: ".$runpath);
	}
	else {
		$runpath = "./";
	}
  
	$particle = new particledata();
	//make sure specific result file is present
	if ($jobId) {
		$jobinfo = $particle->getJobInfoFromId($jobId);
		$fileerror = checkRequiredFileError($jobinfo['appath'],'resolution.txt'); 
	} else {
		$fileerror = checkRequiredFileError($runpath,'resolution.txt'); 
	}
	if ($fileerror) createUploadReconForm($fileerror);

	/* *******************
	PART 3: Create program command
	******************** */

	$command ="uploadXmippRefine.py ";
	$command.="--stackid=$stack ";
	$command.="--rundir=$runpath ";
	if ($mass) $command.="--mass=$mass ";
  

	/* *******************
	PART 4: Create header info, i.e., references
	******************** */

	// Add reference to top of the page
	$headinfo .= referenceBox("XMIPP: a new generation of an open-source image processing package for electron microscopy", 
		2004, "Sorzano CO, Marabini R, Velázquez-Muriel J, Bilbao-Castro JR, Scheres SH, Carazo JM, Pascual-Montano A.", 
		"J Struct Biol.", 148, 2, 15477099, false, "10.1016/j.jsb.2004.06.006", "img/xmipp_logo.png");

	/* *******************
	PART 5: Show or Run Command
	******************** */

	// submit command
	$errors = showOrSubmitCommand($command, $headinfo, 'uploadrecon', $nproc);

	// if error display them
	if ($errors)
		createUploadReconForm($errors);
	exit;
}
?>
