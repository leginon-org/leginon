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
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

if ($_POST['login']) {
  $errors = checkLogin();
  if ($errors) processTable($extra=$errors);
}

processTable();



function processTable($extra=false) {
$leginondata = new leginondata();

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

processing_header("Appion Data Processing","Appion Data Processing", "<script src='../js/viewer.js'></script>", false);

// write out errors, if any came up:
if ($extra) {
  echo "<font color='#cc3333' size='+2'>$extra</font>\n<hr/>\n";
}
// create login form
$display_login = ($_SESSION['username'] && $_SESSION['password']) ? false:true;

if ($display_login) {
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
  displayLogin($formAction);
}

echo"<form name='viewerform' method='post' action='$formaction'>\n";

// Collect session info from database
$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];
$currentproject=$sessiondata['currentproject'];

// Set colors for unprocessed & finished steps:
// --- constants set in inc/processing.inc --- //

$donecolor=DONE_COLOR;
$nonecolor=NONE_COLOR;
$progcolor=PROG_COLOR;

$donepic=DONE_PIC;
$nonepic=NONE_PIC;
$progpic=PROG_PIC;

$particle = new particledata();
// If expId specified, don't show pulldowns, only session info
if (!$expId){
  echo"
  <b>Select Session:</b><br />
  <select name='projectid' onchange='newexp()'>\n";
  $projects=getProjectList();
  foreach ($projects as $k=>$project) {
    $sel = ($project['id']==$projectId) ? "selected" : '';
    echo "<option value='".$project['id']."' ".$sel.">".$project['name']."</option>\n";
  }
  
  echo"
  </select>
  <br />
 
  <select name='sessionid' onchange='newexp()'>
  <option value=''>all sessions</option>\n";
  foreach ($sessions as $k=>$session) {
    $sel = ($session['id']==$sessionId) ? 'selected' : '';
    $shortname=substr($session['name'],0,90);
    echo "<option value='".$session['id']."'".$sel.">".$shortname."</option>";
  }
  echo"</select>\n";
}
// Show project & session pulldowns
else {
	$projectId = $currentproject['projectId'];
  $proj_link= '<a class="header" target="project" href="'.PROJECT_URL."getproject.php?pId=".$projectId.'">'.$currentproject['name'].'</a>';
  $sessionDescr=$sessioninfo['Purpose'];
	$misc = $particle->getMiscInfoFromProject ($projectId);

	
	// --- display Project / Session / Path table info --- //
	$ptable[]=array(
		'c1'=>'<b>Project:</b>',
		'c2'=>$proj_link,
		'c3'=>($misc) ? "<a href='viewmisc.php?projId=$projectId'>[Related Images, Movies, etc]</a>" : "" 
	); 
	$ptable[]=array(
		'c1'=>'<b>Session:</b>',
		'c2'=>$sessionDescr
	);

  // get experiment information
  if ($expinfo = $leginondata->getSessionInfo($expId)) {
		$ptable[]=array(
			'c1'=>'<b>Image Path:</b>',
			'c2'=>$expinfo['Image path']
		);
  }
  echo array2table($ptable, array(), false, "");

}
echo "<p>\n";

if ($sessionId) {
// ---  Get CTF Data

  if ($ctfrunIds = $particle->getCtfRunIds($sessionId))
		$ctfruns=count($ctfrunIds);

  // --- Get Particle Selection Data
  if ($prtlrunIds = $particle->getParticleRunIds($sessionId))
		$prtlruns=count($prtlrunIds);

  // retrieve template info from database for this project
  if ($expId){
    $projectId=getProjectFromExpId($expId);
  }
  if (is_numeric($projectId)) {
    if ($templatesData=$particle->getTemplatesFromProject($projectId))
			$templates = count($templatesData);
    if ($modelData=$particle->getModelsFromProject($projectId))
			$models = count($modelData);
  }

  // --- Get Mask Maker Data
  if ($maskrunIds = $particle->getMaskMakerRunIds($sessionId))
		$maskruns=count($maskrunIds);

  // --- Get Micrograph Assessment Data
  $totimgs = $particle->getNumImgsFromSessionId($sessionId);
  $assessedimgs = $particle->getNumTotalAssessImages($sessionId);
  
  // --- Get Stack Data
  if ($stackIds = $particle->getStackIds($sessionId))
		$stackruns=count($stackIds);

  // --- Get Reconstruction Data
  if ($stackruns>0) {
    foreach ((array)$stackIds as $stackid) {
      $reconIds = $particle->getReconIds($stackid['stackid']);
      if ($reconIds) {
        $reconruns+=count($reconIds);
      }
    }
    // get number of jobs submitted
    $subjobs = $particle->getSubmittedJobs($sessionId);

    // get num of jubs queued, submitted or done
    $jobqueue=0;
    $jobrun=0;
    $jobdone=0;
    foreach ($subjobs as $j) {
      // skip appion jobs
      if (!(ereg('.appionsub.',$j['name']))) {
	if ($j['status']=='Q') $jobqueue++;
	elseif ($j['status']=='R') $jobrun++;
	elseif ($j['status']=='D') $jobdone++;
      }
    }
  }

  echo"</form>";

  if ($prtlruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Particle Selection");

  $result = ($prtlruns==0) ? "none" :
		"<a href='prtlreport.php?expId=$sessionId'>$prtlruns completed</a>\n";

  $nrun = "<a href='runTemplateCorrelator.php?expId=$sessionId'>Template Picking</a>";
	$nrun .= "<br />";
	$nrun .= "<a href='runDogPicker.php?expId=$sessionId'>";
  $nrun .= "DoG Picking";
  $nrun .= "</a><br />";
	$nrun .= "<a href='runManualPicker.php?expId=$sessionId'>";
  $nrun .= ($prtlruns==0) ? "Manual Picking" : "Manually Edit Picking";
	$nrun .= "</a><br />";
  $maxangle = $particle->getMaxTiltAngle($sessionId);
  if ($maxangle > 5) {
		$nrun .="<a href='tiltAligner.php?expId=$sessionId'>";
		$nrun .= ($prtlruns==0) ? "Align Tilt Pairs" :
				"Align Tilt Particle Pairs";
		$nrun .= "</a>";
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result, $celloption),
		'newrun'=>array($nrun, $celloption),
	);

  if ($ctfruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "CTF Estimation");

	if ($ctfruns==0) {
		$result = "none";
	} else {
		$result = "<a href='ctfreport.php?Id=$sessionId'>$ctfruns completed</a>";
		//$best = $ctf->getPercentPassCtfForSessionId($sessionId, 0.8);
		//print_r($best);
		//$all = $ctf->getPercentPassCtfForSessionId($sessionId);
		//$percent = 100.0 * count($best) / ((float) count($all));
		//$result .= "<br/>\n".round($percent,1)."% pass criteria";
	}

	$nrun = "<a href='runPyAce.php?expId=$sessionId'>";
	$nrun .= "ACE Estimation";
	$nrun .= "</a><br/>";
	$nrun .= "<a href='runCtfTilt.php?expId=$sessionId'>";
	$nrun .= "CtfTilt Estimation";
	$nrun .= "</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result, $celloption),
		'newrun'=>array($nrun, $celloption),
	);

  if ($assessedimgs==0 || $totimgs == 0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  elseif ($assessedimgs < $totimgs) {$bgcolor=$progcolor; $gifimg=$progpic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Micrograph Assessment");
	if ($assessedimgs < $totimgs) {
		$result = "<a href='assesssummary.php?expId=$sessionId'>";
		$result .= "$assessedimgs of $totimgs completed"; 
		$result .= "</a>";
	} elseif ($totimgs!=0) {
		$result = "<a href='assesssummary.php?expId=$sessionId'>";
		$result .= "All $assessedimgs completed";
		$result .= "</a>";
	} else {
		$result = "none";
	}

	$nrun = "<a href='imgassessor.php?expId=$sessionId'>";
	if ($assessedimgs==0) {
		$nrun .= "Web Image Assessment";
	} else {
    $nrun .= ($assessedimgs < $totimgs || $totimgs==0) ? 
			"Continue Web Assessment" : "Re-Assess Images";
	}
	$nrun .= "</a><br/>";
	$nrun .= "<a href='runImgRejector.php?expId=$sessionId'>";
	$nrun .= "Run Image Rejector</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result, $celloption),
		'newrun'=>array($nrun, $celloption),
	);

  if ($maskruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Region Mask Creation");
	$result = ($maskruns==0) ? "none" :
			"<a href='maskreport.php?expId=$sessionId'>$maskruns completed</a>\n";
	$nrun = "<a href='runMaskMaker.php?expId=$sessionId'>";
  $nrun .= ($maskruns==0) ? "Crud Finding" : "Crud Finding";
	$nrun .= "</a><br />";
	$nrun .= "<a href='manualMaskMaker.php?expId=$sessionId'>";
  $nrun .= "Manual Masking";
	$nrun .= "</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result, $celloption),
		'newrun'=>array($nrun, $celloption),
	);

  if ($stackruns==0) {$bgcolor=$nonecolor;$gifimg=$nonepic;}
  else {$bgcolor=$donecolor;$gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Stacks");
	$result = ($stackruns==0) ? "none" :
			"<a href='stacksummary.php?expId=$sessionId'>$stackruns completed<A>";
	$nrun = "<a href='makestack.php?expId=$sessionId'>Stack creation</a>";
	if ($prtlruns == 0) {
      $nrun = "<font size=-1><i>Pick some particles first</i></font>";
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result, $celloption),
		'newrun'=>array($nrun, $celloption),
	);

  // if no submitted jobs, display none
  // for every uploaded job, subtract a submitted job
  // if all submitted jobs are uploaded, it should be 0
  $jobincomp = $jobdone-$reconruns; //incomplete
	//echo "  D=".$jobdone."  R=".$jobrun."  Q=".$jobqueue."  T=".$reconruns."  I=".$jobincomp;
  if ($jobincomp>0 || $jobrun>0 || $jobqueue>0) { $bgcolor=$progcolor; $gifimg=$progpic; }
  elseif ($reconruns>0) { $bgcolor=$donecolor; $gifimg=$donepic;  }
  else { $bgcolor=$nonecolor; $gifimg=$nonepic; }

	$celloption="bgcolor='$bgcolor'";
	$action = formatAction($gifimg, "Reconstructions");

	$result = "none";
  if ($jobdone>0 || $jobrun>0 || $jobqueue>0 || $reconruns >0) {
    $jlist=array();
    if ($jobqueue>0)  $jlist[]="<a href='checkRefineJobs.php?expId=$sessionId'>$jobqueue queued</a>\n";
    if ($jobrun>0)    $jlist[]="<a href='checkRefineJobs.php?expId=$sessionId'>$jobrun running</a>\n";
    if ($jobincomp>0) $jlist[]="<a href='checkRefineJobs.php?expId=$sessionId'>$jobincomp ready for upload</a>\n";
    if ($reconruns>0) $jlist[]="<a href='reconsummary.php?expId=$sessionId'>$reconruns uploaded</a>\n";
    $result = implode('<br />',$jlist);
  }

  // first check if there are stacks for a run, then check if logged
  // in.  Then you can submit a job
  if ($stackruns == 0) $nrun = "<font size=-1><i>Create a stack first</i></font>"; 
  elseif (!$_SESSION['loggedin']) {$nrun = "<font size=-1><i>Log in to submit a job</i>\n";}
  else $nrun = "<a href='emanJobGen.php?expId=$sessionId'>EMAN Reconstruction</a>";
  if ($stackruns>0) {
    $nrun .= "<br /><a href='uploadrecon.php?expId=$sessionId'>Upload Reconstruction</a>";
  }
	$data[]=array(
    'action'=>array($action, $celloption),
    'result'=>array($result, $celloption),
    'newrun'=>array($nrun, $celloption),
  );

	$celloption="colspan='3'";
	$data[]=array(
    'action'=>array("<br /><b>Pipeline tools:</b>", $celloption)
	);

  if ($templates==0) {$bgcolor=$nonecolor; $gifimg=$nonepic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Templates");

  $result = ($templates==0) ? "none" :
			"<a href='viewtemplates.php?expId=$sessionId'>$templates available</a>";
  $nrun = ($templates==0) ? 
		"<a href='uploadtemplate.php?expId=$sessionId'>Upload template</a>" : 
		"<a href='uploadtemplate.php?expId=$sessionId'>Upload template</a>";

	$data[]=array(
    'action'=>array($action, $celloption),
    'result'=>array($result, $celloption),
    'newrun'=>array($nrun, $celloption),
  );

  if ($models==0) {$bgcolor=$nonecolor; $gifimg=$nonepic;}
  else {$bgcolor=$donecolor; $gifimg=$donepic;}

	$celloption="bgcolor='$bgcolor'";

	$action = formatAction($gifimg, "Initial Models");

  $result = ($models==0) ? "none" :
			"<a href='viewmodels.php?expId=$sessionId'>$models available</a>";
  $nrun = ($models==0) ? 
		"<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>" :
		"<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>";

	$data[]=array(
    'action'=>array($action, $celloption),
    'result'=>array($result, $celloption),
    'newrun'=>array($nrun, $celloption),
  );

	// --- display Processing table ---//
	$columns=array(
		'action'=>'<h4>Action</h4>',
		'result'=>'<h4>Results</h4>',
		'newrun'=>'<h4>New run</h4>'
	);
	$display_header=true;

	echo array2table($data, $columns, $display_header);

}
processing_footer($showproclink=False);
exit;
}

function formatAction($img, $str) {
	return "<img style='padding-left: .5em; ' src='$img'><span style='padding-left:1em' ><b>$str</b></span>";
}

?>
