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
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";

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

if ($expId) {
	// sort out submitted job information
	$clusterjobs = $particle->getJobIdsFromSession($expId);
	$subclusterjobs=array();
	foreach ($clusterjobs as $job) {
		$jobtype = $job['jobtype'];
		if ($job['status']=='D') $subclusterjobs[$jobtype]['done'][]=$job['DEF_id'];
		elseif ($job['status']=='R') $subclusterjobs[$jobtype]['running'][]=$job['DEF_id'];
		elseif ($job['status']=='Q') $subclusterjobs[$jobtype]['queued'][]=$job['DEF_id'];
	}

	// ---  Get CTF Data
	if ($ctfrunIds = $particle->getCtfRunIds($expId)) {
		$ctfruns=count($ctfrunIds);
	}

	// --- Get Particle Selection Data
	if ($prtlrunIds = $particle->getParticleRunIds($sessionId)) {
		$prtlruns=count($prtlrunIds);
	}

	// --- retrieve template info from database for this project
	$projectId=getProjectFromExpId($expId);

	if ($projectId) {
		if ($templatesData=$particle->getTemplatesFromProject($projectId)) $templates = count($templatesData);
		if ($modelData=$particle->getModelsFromProject($projectId)) $models = count($modelData);
	}

	// --- Get Mask Maker Data
	if ($maskrunIds = $particle->getMaskMakerRunIds($sessionId))
		$maskruns=count($maskrunIds);

	// --- Get Micrograph Assessment Data
	$totimgs = $particle->getNumImgsFromSessionId($sessionId);
	$assessedimgs = $particle->getNumTotalAssessImages($sessionId);

	// --- Get Stack Data
	if ($stackIds = $particle->getStackIdsWithProjectId($sessionId, $projectId))
		$stackruns=count($stackIds);

	// --- Get NoRef Data
	if ($stackruns>0) {
		$norefIds = $particle->getNoRefIds($sessionId);
		$norefruns=count($norefIds);
	}
	else {
		$norefruns=0;
	};

	// --- Get Alignment Data
	if ($stackruns>0) {
		$alignIds = $particle->getAlignStackIds($sessionId, $projectId);
		$alignruns=count($alignIds);
	}
	else {
		$alignruns=0;
	}

	// --- Get Reconstruction Data
	if ($stackruns>0) {
		foreach ((array)$stackIds as $stackid) {
			$reconIds = $particle->getReconIds($stackid['stackid']);
			if ($reconIds) $reconruns+=count($reconIds);
		}
		// get number of jobs submitted
		$subjobs = $particle->getSubmittedJobs($sessionId);

		// get num of jubs queued, submitted or done
		$jobqueue=count($subclusterjobs['recon']['queued']);
		$jobrun=count($subclusterjobs['recon']['running']);
		$jobdone=count($subclusterjobs['recon']['done']);
	}

	// --- Get TiltSeries Data
	if ($tiltseries = $particle->getTiltSeries($sessionId))
		$tiltruns=count($tiltseries);
	if ($tomograms = $particle->getTomogramsFromSession($sessionId))
		$tomoruns=count($tomograms);

	$action = "Particle Selection";

	// get template picking stats:
	$tresults=array();
	$drsults=array();
	$mresults=array();

	$tdone = count($subclusterjobs['templatepicker']['done']);
	$trun = count($subclusterjobs['templatepicker']['running']);
	$tq = count($subclusterjobs['templatepicker']['queued']);

	$ddone = count($subclusterjobs['dogpicker']['done']);
	$drun = count($subclusterjobs['dogpicker']['running']);
	$dq = count($subclusterjobs['dogpicker']['queued']);

	$mdone = count($subclusterjobs['manualpicker']['done']);
	$mrun = count($subclusterjobs['manualpicker']['running']);
	$mq = count($subclusterjobs['manualpicker']['queued']);

	$tresults[] = ($tdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$tdone complete</a>";
	$tresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatepicker'>$trun running</a>";
	$tresults[] = ($tq==0) ? "" : "$tq queued";

	$dresults[] = ($ddone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$ddone complete</a>";
	$dresults[] = ($drun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$drun running</a>";
	$dresults[] = ($dq==0) ? "" : "$dq queued";

	$mresults[] = ($mdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$mdone complete</a>";
	$mresults[] = ($mrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mrun running</a>";
	$mresults[] = ($mq==0) ? "" : "$mq queued";

	// in case weren't submitted by web:
	$totruns = $tdone+$trun+$tq+$ddone+$drun+$dq+$mdone+$mrun+$mq;
	if  ($prtlruns > $totruns) $totruns = $prtlruns;

	$result = ($prtlruns==0) ? "" :
		"<a href='prtlreport.php?expId=$sessionId'>$prtlruns</a>\n";

	$nrun=array();
	$nrun[] = array(
			'name'=>"<a href='runPySelexon.php?expId=$sessionId'>Template Picking</a>",
			'result'=>$tresults,
			);
	$nrun[] = array(
			'name'=>"<a href='runDogPicker.php?expId=$sessionId'>DoG Picking</a>",
			'result'=>$dresults,
			);
	$nrun[] = array(
			'name'=>"<a href='runManualPicker.php?expId=$sessionId'>Manual Picking</a>",
			'result'=>$mresults,
			);

	$maxangle = $particle->getMaxTiltAngle($sessionId);
	if ($maxangle > 5) {
		$nrun[] ="<a href='tiltAligner.php?expId=$sessionId'>Align and Edit Tilt Pairs</a>";
		$nrun[] ="<a href='runTiltAutoAligner.php?expId=$sessionId'>Auto Align Tilt Pairs</a>";
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nrun, $celloption),
	);


	$action = "CTF Estimation";

	// get ctf estimation stats:
	$ctfresults=array();
	$ctfdone = count($subclusterjobs['ace']['done']);
	$ctfrun = count($subclusterjobs['ace']['running']);
	$ctfq = count($subclusterjobs['ace']['queued']);

	$ctfresults[] = ($ctfdone==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ctfdone complete</a>";
	$ctfresults[] = ($ctfrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ace'>$ctfrun running</a>";
	$ctfresults[] = ($ctfq==0) ? "" : "$ctfq queued";

	$ace2done = count($subclusterjobs['ace2']['done']);
	$ace2run = count($subclusterjobs['ace2']['running']);
	$ace2q = count($subclusterjobs['ace2']['queued']);

	$ace2results[] = ($ace2done==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ace2done complete</a>";
	$ace2results[] = ($ace2run==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ace2'>$ace2run running</a>";
	$ace2results[] = ($ace2q==0) ? "" : "$ace2q queued";


	// number running and number finished:
	$totruns=$ctfdone+$ctfrun+$ctfq;

	// in case weren't submitted by web:
	if  ($ctfruns > $totruns) $totruns = $ctfruns;
	$totresult = ($totruns==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$totruns</a>";

	$nruns = array();
	$nruns[] = array(
			 'name'=>"<a href='runPyAce.php?expId=$sessionId'>ACE Estimation</a>",
			 'result'=>$ctfresults,
			 );
	$nruns[] = array(
			'name'=>"<a href='runAce2.php?expId=$sessionId'>ACE 2 Estimation</a>",
			'result'=>$ace2results,
			);
	$nruns[] = array(
			'name'=>"<a href='runCtfTilt.php?expId=$sessionId'>CtfTilt Estimation</a>",
			'result'=>$ctftiltresults,
			);


	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($totresult),
		'newrun'=>array($nruns, $celloption),
	);

	// display the stack menu only if have particles picked
	if ($prtlruns > 0) {
		$action = "Stacks";

		// get ctf estimation stats:
		$sresults=array();
		$sdone = count($subclusterjobs['makestack']['done']);
		$srun = count($subclusterjobs['makestack']['running']);
		$sq = count($subclusterjobs['makestack']['queued']);

		$sresults[] = ($sdone==0) ? "" : "<a href='stacksummary.php?expId=$sessionId'>$sdone complete</a>";
		$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makestack'>$srun running</a>";
		$sresults[] = ($sq==0) ? "" : "$sq queued";

		// stacks being created and stacks completed
		$totstack = $sdone+$srun+$sq;

		$totstack = ($totstack > $stackruns) ? $totstack : $stackruns;
		$totresult = ($totstack==0) ? "" :
			"<a href='stacksummary.php?expId=$sessionId'>$totstack</a>";

		$nruns=array();
		$nruns[]=array (
				'name'=>"<a href='makestack2.php?expId=$sessionId'>Stack creation</a>",
				'result'=>$sresults,
				);
		$nruns[]=array (
				'name'=>"<a href='moreStackTools.php?expId=$sessionId'>more stack tools</a>",
				);

		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array($totresult),
			      'newrun'=>array($nruns, $celloption),
			      );
	}

	// display particle alignment only if there is a stack
	if ($stackruns > 0) {
		$action = "Particle Alignment";

		// get ref-free alignment stats:
		$norefresults=array();
		$norefdone = count($subclusterjobs['norefali']['done']);
		$norefrun = count($subclusterjobs['norefali']['running']);
		$norefq = count($subclusterjobs['norefali']['queued']);

		$norefdone = ($norefruns > $norefdone) ? $norefruns : $norefdone;

		// get ref-free alignment stats:
		$norefclresults=array();
		$norefcldone = count($subclusterjobs['norefclass']['done']);
		$norefclrun = count($subclusterjobs['norefclass']['running']);
		$norefclq = count($subclusterjobs['norefclass']['queued']);

		$done = "<a href='norefsummary.php?expId=$sessionId'>$norefdone complete";
		$done.= (!$norefcldone==0) ? " ($norefcldone avg)" : "";
		$done.= "</a>";
		$norefresults[] = ($norefdone==0) ? "" : $done;
		$norefresults[] = ($norefrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=norefali'>$norefrun align running</a>";
		$norefresults[] = ($norefclrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=norefclass'>$norefclrun avg running</a>";
		$norefresults[] = ($norefq==0) ? "" : "$norefq align queued";
		$norefresults[] = ($norefclq==0) ? "" : "$norefq avg queued";

		// get alignment stats:
		$alignresults=array();
		$aligndone  = count($subclusterjobs['maxlikeali']['done'])
			+ count($subclusterjobs['refbasedali']['done'])
			+ count($subclusterjobs['norefali']['done']);
		$norefrun = count($subclusterjobs['maxlikeali']['running']);
		$refbasedrun = count($subclusterjobs['refbasedali']['running']);
		$maxlikerun = count($subclusterjobs['maxlikeali']['running']);
		$alignrun   = $norefrun+$refbasedrun+$maxlikerun;
		$alignqueue  = count($subclusterjobs['maxlikeali']['queued'])
			+ count($subclusterjobs['refbasedali']['queued'])
			+ count($subclusterjobs['norefali']['queued']);
		$norbaseddone = ($alignrun > $aligndone) ? $alignrun : $aligndone;

		$alignresults[] = ($alignruns==0) ? "" : "<a href='alignsummary.php?expId=$sessionId'>$alignruns complete</a>";
		$alignresults[] = ($norefrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=norefali'>$norefrun running</a>";
		$alignresults[] = ($refbasedrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=refbasedali'>$refbasedrun running</a>";
		$alignresults[] = ($maxlikerun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=maxlikeali'>$maxlikerun running</a>";
		$alignresults[] = ($alignqueue==0) ? "" : "$alignqueue queued";

		$nruns=array();

		$nruns[] = array(
			'name'=>"<a href='particleAlignment.php?expId=$sessionId'>Run Alignment</a>",
			'result'=>$alignresults,
		);
		if ($alignruns > 0) {
			// alignment classifications
			$coranresults=array();
			$corandone  = count($particle->getCoranRuns($expId, $projectId));
			$coranrun  = count($subclusterjobs['coranclass']['running']);
			$coranqueue  = count($subclusterjobs['coranclass']['queued']);
			$coranresults[] = ($corandone==0) ? "" : "<a href='coransummary.php?expId=$sessionId'>$corandone complete</a>";
			$coranresults[] = ($coranrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=coranclass'>$coranrun running</a>";
			$coranresults[] = ($coranqueue==0) ? "" : "$coranqueue queued";
			$nruns[] = array (
				'name'=>"<a href='alignClassify.php?expId=$sessionId'>Run Classification</a>",
				'result'=>$coranresults,
			);
		}

		// old spider alignment
		$nruns[]=array(
			       'name'=>"<a href='runNoRefAlignment.php?expId=$sessionId'>Old Spider Ref-free</a>",
			       'result'=>$norefresults,
				 );

		// only give option of reclassification if ref-free
		// stacks exist
		if ($norefresults) {
			$numreresults = count($particle->getImagicReclassFromSessionId($expId));
			$sreresults = ($numreresults==0) ? "" : "<a href='imagicReclassifySummary.php?expId=$sessionId'>$numreresults complete</a>";
			// imagic reclassifications
			$nruns[] = array (
					  'name'=>"<a href='imagicReclassifyClassums.php?expId=$sessionId'>IMAGIC Reclassify</a>",
					  'result'=>$sreresults,
					  );
		}

		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array(""),
			      'newrun'=>array($nruns, $celloption),
			      );

	}

	// initial model creation tools
	$action = "Initial Model Creation";

	$nruns=array();
	$nruns[]=array(
		'name'=>"<a href='pdb2density.php?expId=$sessionId'>PDB to Model</a>"
	);

	$nruns[]=array(
		'name'=>"<a href='emdb2density.php?expId=$sessionId'>EMDB to Model</a>"
	);

	/* RCT Volumes */
	$numrctvols = $particle->getNumberOfRctRuns($sessionId);
	$nrct = ($numrctfvols > 0) ? "<a href='rctsummary.php?expId=$sessionId'>$numrctvols complete</a>" : '';

	if ($norefdone >= 1 && $stackruns >= 2) {
		$nruns[]=array(
			'name'=>"<a href='runRctVolume.php?expId=$sessionId'>RCT Volume</a>",
			'result'=>$nrct,
		);
	}

	if ($norefdone >= 1 ) {
		$nruns[]=array(
			'name'=>"<a href='createEmanModel.php?expId=$sessionId'>EMAN Common Lines</a>"
		);
	}

	/* IMAGIC Common Lines */
	$numimagicrefinements = count($particle->getImagic3dRefinementRunsFromSessionId($sessionId));
	$refineresults = ($numimagicrefinements==0) ? "" : "<a href='imagic3dRefineSummary.php?expId=$sessionId'>$numimagicrefinements complete</a>";
	if ($norefdone >= 1) {
		$nruns[]=array(
			'name'=>"<a href='imagic3dRefine.php?expId=$sessionId'>IMAGIC Common Lines</a>",
			'result'=>$refineresults,
		);
	}


	/* 3d Density Volumes */
	$threedvols = $particle->get3dDensitysFromSession($sessionId);
	$num3dvols = count($threedvols);
	if ($num3dvols >= 1) {
		$nruns[]=array(
			'name'=>"<a href='upgradeVolume.php?expId=$sessionId'>3d Density Volumes</a>",
			'result'=>"<a href='densitysummary.php?expId=$sessionId'>$num3dvols complete</a>",
		);
	}

	$data[]=array(
		      'action'=>array($action, $celloption),
		      'result'=>array(),
		      'newrun'=>array($nruns, $celloption),
		      );

	// display reconstructions only if there is a stack
	if ($stackruns > 0) {
		// for every uploaded job, subtract a submitted job
		// if all submitted jobs are uploaded, it should be 0
		$jobincomp = $jobdone-$reconruns; //incomplete

		$action = "Reconstructions";

		$reconresults = array();

		$reconresults[] = ($jobqueue>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobqueue queued</a>" : "";
		$reconresults[] = ($jobrun>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobrun running</a>" : "";
		$reconresults[] = ($jobincomp>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobincomp ready for upload</a>" : "";
		$reconresults[] = ($reconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$reconruns complete</a>" : "";

		$totresult = ($reconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$reconruns</a>" : "";

		$nruns=array();
//		if ($_SESSION['loggedin']) {
		if (TRUE) {
			$nruns[] = array(
					 'name'=>"<a href='emanJobGen.php?expId=$sessionId'>EMAN Reconstruction</a>",
					 'result'=>$reconresults,
					 );
			$nruns[] = "<a href='frealignJobGen.php?expId=$sessionId'>Frealign Reconstruction</a>" ;
//			$nruns[] = "<a href='uploadrecon.php?expId=$sessionId'>Upload Reconstruction</a>";
		} else {
			$nruns[] = "<font color='888888'><i>please login first</i></font>";
		}
		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array($totresult),
			      'newrun'=>array($nruns, $celloption),
			      );
	}

	// display the tomography menu only if there are tilt serieses
	if ($tiltruns > 0) {
		$action = "Tomography";

		// get ctf estimation stats:
		$sresults=array();
		$sdone = count($subclusterjobs['uploadtomo']['done']);
		$srun = count($subclusterjobs['uploadtomo']['running']);
		$sq = count($subclusterjobs['uploadtomo']['queued']);

		$sresults[] = ($sdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$sdone complete</a>";
		$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$srun running</a>";
		$sresults[] = ($sq==0) ? "" : "$sq queued";

		// tomograms being created and completed
		$tottomo = $sdone+$srun+$sq;

		$tottomo = ($tottomo > $tomoruns) ? $tottomo : $tomoruns;
		$totresult = ($tottomo==0) ? "" :
			"<a href='tomosummary.php?expId=$sessionId'>$tottomo</a>";

		$nruns=array();
		$nruns[]=array (
				'name'=>"<a href='uploadtomo.php?expId=$sessionId'>Upload Tomogram</a>",
				'result'=>$sresults,
				);

		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array($totresult),
			      'newrun'=>array($nruns, $celloption),
			      );
	}

	// upload model & template tools
	$action = "Pipeline tools";

	$result = ($templates==0) ? "" :
	  "<a href='viewtemplates.php?expId=$sessionId'>$templates available</a>";

	$nruns=array();
	$nruns[]=array(
		       'name'=>"<a href='uploadtemplate.php?expId=$sessionId'>Upload template</a>",
		       'result'=>$result,
		       );

	$result = ($models==0) ? "" :
	  "<a href='viewmodels.php?expId=$sessionId'>$models available</a>";

	$nruns[]=array(
		       'name'=>"<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>",
		       'result'=>$result,
		       );

	$data[]=array(
		      'action'=>array($action, $celloption),
		      'result'=>array(),
		      'newrun'=>array($nruns, $celloption),
		      );

	// image assessment and contamination finding
	$action = "Img Assessment";

	$result='';
	if ($assessedimgs <= $totimgs && $totimgs!=0) {
		$result = "<a href='assesssummary.php?expId=$sessionId'>";
		$result .= "$assessedimgs/$totimgs";
		$result .= "</a>";
	}

	$nrun = "<a href='imgassessor.php?expId=$sessionId'>Web Img Assessment</a>";
	$nruns=array();
	$nruns[]=$nrun;
	$nruns[] = "<a href='runImgRejector.php?expId=$sessionId'>Run Image Rejector</a>";

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nruns, $celloption),
	);

	$action = "Region Mask Creation";
	$result = ($maskruns==0) ? "" :
			"<a href='maskreport.php?expId=$sessionId'>$maskruns</a>";
	$nruns=array();
	$nrun = "<a href='runMaskMaker.php?expId=$sessionId'>Crud Finding</a>";
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
				leftdiv.style.width="180px"
				viewmenu=1
				if (lk=document.getElementById("eclk")) {
					lk.style.visibility="visible"
				}
			} else {
				viewmenu=0
				leftdiv.style.visibility="hidden"
				if (maindiv=document.getElementById("maincontent")) {
					leftdiv.style.width="0px"
					updatelink("hidelk", "View Menu", "javascript:m_hideall()")
				}
				if (lk=document.getElementById("eclk")) {
					lk.style.visibility="hidden"
				}
			}
		}
	}

</script>
';

$menulink='<span class="expandcontract"><a id="hidelk" href="javascript:m_hideall()">Hide</a>
<span id="eclk"> | <a href="javascript:m_expandall()">Expand</a> |
<a href="javascript:m_collapseall()">Contract</a></span>
</span>';

$menuprocessing="";
	foreach((array)$data as $menu) {
		$action=$menu['action'][0];
		$result=$action;
		if ($menu['result'][0]) $result .= ' : '.$menu['result'][0];
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
		// print out the title of the subfunction
		foreach((array)$data as $submenu) {
			if (is_array($submenu)) {
				$text.="<li>".$submenu['name']."</li>";
				// if there are results for the
				// subfunction, print them out
				foreach ((array)$submenu['result'] as $res) {
					$text.=($res) ? "<li class='sub1'>$res</li>" : "";
				}
			}
			else $text.="<li>$submenu</li>\n";
		}
		$text.="</ul>";
		return '<div class="submenu">'.$text.'</div>';
	}

?>
