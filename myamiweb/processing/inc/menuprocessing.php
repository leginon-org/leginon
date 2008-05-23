<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *	main menu for processing tools
 */

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/ctf.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";


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

// Collect session info from database
$sessiondata=getSessionList($projectId,$sessionId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];
$currentproject=$sessiondata['currentproject'];


$particle = new particledata();

if ($sessionId) {
// ---  Get CTF Data
  $ctf = new ctfdata();

  if ($ctfrunIds = $ctf->getCtfRunIds($sessionId)) {
		$ctfruns=count($ctfrunIds);
	}

  // --- Get Particle Selection Data
  if ($prtlrunIds = $particle->getParticleRunIds($sessionId)) {
		$prtlruns=count($prtlrunIds);
	}
  // --- retrieve template info from database for this project
  if ($expId){
    $projectId=getProjectFromExpId($expId);
  }
  if ($projectId) {
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

  // --- Get NoRef Data
  if ($stackruns>0) {
    $norefIds = $particle->getNoRefIds($sessionId);
    $norefruns=count($norefIds);
  } else {
    $norefruns=0;
  };

  // --- Get Ref-based Alignment Data
  if ($stackruns>0) {
    $refbasedIds = $particle->getRefAliIds($sessionId);
		$refbasedruns=count($refbasedIds);
  } else {
    $refbasedruns=0;
  };

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

	$action = "Particle Selection";

  $result = ($prtlruns==0) ? "none" :
		"<a href='prtlreport.php?expId=$sessionId'>$prtlruns completed</a>\n";

	$nrun=array();
  $nrun[] = "<a href='runPySelexon.php?expId=$sessionId'>Template Picking</a>";
	$nrun[] = "<a href='runDogPicker.php?expId=$sessionId'>DoG Picking</a>";
	$nrun[] = "<a href='runManualPicker.php?expId=$sessionId'>"
						.($prtlruns==0) ? "Manual Picking" : "Manually Edit Picking"
						."</a>";

  $maxangle = $particle->getMaxTiltAngle($sessionId);
  if ($maxangle > 5) {
		$nrun[] ="<a href='tiltAligner.php?expId=$sessionId'>"
						.($prtlruns==0) ? "Align Tilt Pairs" : "Align Tilt Particle Pairs"
						."</a>";
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nrun, $celloption),
	);


	$action = "CTF Estimation";

	if ($ctfruns==0) {
		$result = "none";
	} else {
		$result = "<a href='ctfreport.php?Id=$sessionId'>$ctfruns completed</a>";
	}

	$nruns = array();
	$nruns[] = "<a href='runPyAce.php?expId=$sessionId'>"
					."ACE Estimation"
					."</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);

	$action = "Micrograph Assessment";
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
	$nrun .= "</a>";
	$nruns=array();
	$nruns[]=$nrun;
	$nruns[] = "<a href='runImgRejector.php?expId=$sessionId'>Run Image Rejector</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);

	$action = "Region Mask Creation";
	$result = ($maskruns==0) ? "none" :
			"<a href='maskreport.php?expId=$sessionId'>$maskruns completed</a>\n";
	$nruns=array();
	$nrun = "<a href='runMaskMaker.php?expId=$sessionId'>";
  $nrun .= ($maskruns==0) ? "Crud Finding" : "Crud Finding";
	$nrun .= "</a>";
	$nruns[]=$nrun;
	$nrun = "<a href='manualMaskMaker.php?expId=$sessionId'>";
  $nrun .= "Manual Masking";
	$nrun .= "</a>";
	$nruns[]=$nrun;

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);


	$action = "Stacks";
	$result = ($stackruns==0) ? "none" :
			"<a href='stacksummary.php?expId=$sessionId'>$stackruns completed<A>";
	$nrun = "<a href='makestack.php?expId=$sessionId'>Stack creation</a>";
	if ($prtlruns == 0) {
      $nrun = "<font size=-1><i>Pick some particles first</i></font>";
	}

	$nruns=array();
	$nruns[]=$nrun;

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);

	$action = "Particle Alignment";
	$resultnoref = ($norefruns==0) ? "" : "<a href='norefsummary.php?expId=$sessionId'>$norefruns ref-free aligned</a>\n";
	$resultbasedref = ($refbasedruns==0) ? "" : "<a href='refbasedsummary.php?expId=$sessionId'>$refbasedruns ref-based aligned</a>\n";
	$result = $resultnoref.$resultbasedref;
	if(!$result) $result = "none";

	$nruns=array();
	if ($stackruns == 0) {
		$nruns[] = "<font size=-1><i>Create a stack first</i></font>";
	} else {
		$nruns[] = "<a href='runNoRefAlignment.php?expId=$sessionId'>Ref-free Alignment</a> - $resultnoref";
		$nruns[] = "<a href='refbasedali.php?expId=$sessionId'>Ref-based Alignment</a> - $resultbasedref\n";
	}
	$nruns[]=$nrun;

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);

  // if no submitted jobs, display none
  // for every uploaded job, subtract a submitted job
  // if all submitted jobs are uploaded, it should be 0
  $jobincomp = $jobdone-$reconruns; //incomplete

	$action = "Reconstructions";

	$result = "none";
  if ($jobdone>0 || $jobrun>0 || $jobqueue>0 || $reconruns >0) {
    $jlist=array();
    if ($jobqueue>0)  $jlist[]="<a href='checkjobs.php?expId=$sessionId'>$jobqueue queued</a>\n";
    if ($jobrun>0)    $jlist[]="<a href='checkjobs.php?expId=$sessionId'>$jobrun running</a>\n";
    if ($jobincomp>0) $jlist[]="<a href='checkjobs.php?expId=$sessionId'>$jobincomp ready for upload</a>\n";
    if ($reconruns>0) $jlist[]="<a href='reconsummary.php?expId=$sessionId'>$reconruns uploaded</a>\n";
    $result = implode('<br />',$jlist);
  }

  // first check if there are stacks for a run, then check if logged
  // in.  Then you can submit a job
	$nruns=array();
  if ($stackruns == 0) $nruns[] = "<font size=-1><i>Create a stack first</i></font>"; 
  elseif (!$_SESSION['loggedin']) {$nruns[] = "<font size=-1><i>Log in to submit a job</i>\n";}
  else $nruns[] = "<a href='emanJobGen.php?expId=$sessionId'>EMAN Reconstruction</a>";
  if ($stackruns>0) {
    $nruns[] = "<a href='uploadrecon.php?expId=$sessionId'>Upload Reconstruction</a>";
  }
	$data[]=array(
    'action'=>array($action, $celloption),
		'result'=>array($result),
    'newrun'=>array($nruns, $celloption),
  );

	$action = "Pipeline tools";

  $result = ($templates==0) ? "none" :
			"<a href='viewtemplates.php?expId=$sessionId'>$templates available</a>";
  $nrun = "<a href='uploadtemplate.php?expId=$sessionId'>Upload template</a>";
	$nrun.="	-	".$result;

	$nruns=array();
	$nruns[]=$nrun;

  $result = ($models==0) ? "none" :
			"<a href='viewmodels.php?expId=$sessionId'>$models available</a>";
  $nrun = "<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>";
	$nrun.=" -	".$result;

	$nruns[]=$nrun;
	$data[]=array(
    'action'=>array($action, $celloption),
		'result'=>array(),
    'newrun'=>array($nruns, $celloption),
  );
}

$menujs='<script type="text/javascript">

	function updatelink(id, value, link) {
		if (l=document.getElementById(id)) {
			l.innerHTML=value
			l.href=link
		}
	}

	function m_hideall() {
		if (leftdiv=document.getElementById("leftcontent")) {
			if (leftdiv.style.visibility=="hidden") {
				leftdiv.style.visibility="visible"
				updatelink("hidelk", "Hide", "javascript:m_hideall()")
					leftdiv.style.width="350px"
			} else {
				leftdiv.style.visibility="hidden"
				if (maindiv=document.getElementById("maincontent")) {
					leftdiv.style.width="0px"
					updatelink("hidelk", "View Menu", "javascript:m_hideall()")
				}
			}
		}
	}

	function m_expandcontract() {
		if (lk=document.getElementById("eclk")) {
			if (lk.innerHTML=="Expand") {
				updatelink("eclk", "Contract", "javascript:m_expandcontract()")
				m_expandall()
			} else {
				updatelink("eclk", "Expand", "javascript:m_expandcontract()")
				m_collapseall()
			}
		}
	}
</script>
';

$menulink='<a id="hidelk" href="javascript:m_hideall()">Hide</a> /
<a id="eclk" href="javascript:m_expandcontract()">Expand</a>';

$menuprocessing="";
	foreach((array)$data as $menu) {
		$action=$menu['action'][0]; 
		$result=$action.' : '.$menu['result'][0]; 
		$menuprocesing.=addMenu($result);
		$menuprocesing.=addSubmenu($menu['newrun'][0]);
	}

	function addMenu($title) {
		$html = '<span class="title" id="top"><img src="../img/lvmenu/expanded.gif" class="arrow" alt="-" />'
		.$title
		.'</span>';
		return $html;
	}

	function addSubmenu($data) {
		$text="<ul>";
		foreach((array)$data as $submenu) {
			$text.="<li>$submenu</li>";
		}
		$text.="</ul>";
		return '<div class="submenu">'.$text.'</div>';
	}

?>
