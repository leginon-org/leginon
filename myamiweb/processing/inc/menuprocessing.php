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
	if ($clusterjobs = $particle->getJobIdsFromSession($expId)) {
		$subclusterjobs=array();
		foreach ($clusterjobs as $job) {
			$jobtype = $job['jobtype'];
			if ($job['status']=='D') $subclusterjobs[$jobtype]['done'][]=$job['DEF_id'];
			elseif ($job['status']=='R') $subclusterjobs[$jobtype]['running'][]=$job['DEF_id'];
			elseif ($job['status']=='Q') $subclusterjobs[$jobtype]['queued'][]=$job['DEF_id'];
		}
	}
	// ---  Get CTF Data
	if ($ctfrunIds = $particle->getCtfRunIds($expId, False)) {
		$ctfruns=count($ctfrunIds);
	}

	// --- Get Particle Selection Data
	if ($prtlrunIds = $particle->getParticleRunIds($sessionId, True)) {
		$totalprtlruns=count($prtlrunIds);
	}
	if ($prtlrunIds = $particle->getParticleRunIds($sessionId, False)) {
		$prtlruns=count($prtlrunIds);
	}

	// --- retrieve template info from database for this project
	$projectId=getProjectFromExpId($expId);
	//echo "PROJECT ID: ".$projectId."<br/>\n";

	if ($projectId) {
		if ($templatesData=$particle->getTemplatesFromProject($projectId)) {
			$templates = count($templatesData);
		}
		if ($modelData=$particle->getModelsFromProject($projectId)) {
			$models = count($modelData);
		}
	}

	// --- Get Mask Maker Data
	if ($maskrunIds = $particle->getMaskMakerRunIds($sessionId)) {
		$maskruns=count($maskrunIds);
	}

	// --- Get Micrograph Assessment Data
	$totimgs = $particle->getNumImgsFromSessionId($sessionId);
	$assessedimgs = $particle->getNumTotalAssessImages($sessionId);

	// --- Get Stack Data
	if ($stackIds = $particle->getStackIds($sessionId)) {
		$stackruns=count($stackIds);
	}

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
		if ($alignIds = $particle->getAlignStackIds($sessionId)) {
			$alignruns=count($alignIds);
		}
	}
	else {
		$alignruns=0;
	}

	// --- Get Reconstruction Data
	if ($stackruns>0) {
		$reconswithjob = 0;
		foreach ((array)$stackIds as $stackid) {
			$reconIds = $particle->getReconIds($stackid['stackid']);
			if ($reconIds) {
				$reconruns+=count($reconIds);
				foreach ($reconIds as $reconId) {
					if ($reconId['REF|ApClusterJobData|jobfile']) {
						$reconswithjob++;
					}
				}
			}
		}
		// get number of jobs submitted
		$subjobs = $particle->getSubmittedJobs($sessionId);

		// get num of jubs queued, submitted or done
		$jobqueue=count($subclusterjobs['recon']['queued']);
		$jobrun=count($subclusterjobs['recon']['running']);
		$jobdone=count($subclusterjobs['recon']['done']);
	}

	// --- Get TiltSeries Data
	if ($tiltseries = $particle->getTiltSeries($sessionId)) {
		$tiltruns=count($tiltseries);
	}
	if ($fulltomograms = $particle->getFullTomogramsFromSession($sessionId)) {
		$fulltomoruns=count($fulltomograms);
	}
	if ($tomograms = $particle->getTomogramsFromSession($sessionId)) {
		$tomoruns=count($tomograms);
	}
	if ($avgtomograms = $particle->getAveragedTomogramsFromSession($sessionId)) {
		$avgtomoruns=count($avgtomograms);
	}

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

	$tiltdone = count($subclusterjobs['tiltalign']['done']);
	$tiltrun = count($subclusterjobs['tiltalign']['running']);
	$tiltqueue = count($subclusterjobs['tiltalign']['queued']);

	$tresults[] = ($tdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$tdone complete</a>";
	$tresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatepicker'>$trun running</a>";
	$tresults[] = ($tq==0) ? "" : "$tq queued";

	$dresults[] = ($ddone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$ddone complete</a>";
	$dresults[] = ($drun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$drun running</a>";
	$dresults[] = ($dq==0) ? "" : "$dq queued";

	$mresults[] = ($mdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$mdone complete</a>";
	$mresults[] = ($mrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mrun running</a>";
	$mresults[] = ($mq==0) ? "" : "$mq queued";

	$tiltresults[] = ($tiltdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$tiltdone complete</a>";
	$tiltresults[] = ($tiltrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tiltalign'>$tiltrun running</a>";
	$tiltresults[] = ($tiltqueue==0) ? "" : "$tiltqueue queued";

	// in case weren't submitted by web:
	$totruns = $tdone+$trun+$tq+$ddone+$drun+$dq+$mdone+$mrun+$mq;
	if  ($prtlruns > $totruns) $totruns = $prtlruns;
	if ($looprundatas = $particle->getLoopProgramRuns()) {
		$loopruns=count($looprundatas);
	}


	$result = ($prtlruns==0) ? "" :
		"<a href='prtlreport.php?expId=$sessionId'>$prtlruns</a>\n";

	$nrun=array();
	$nrun[] = array(
			'name'=>"<a href='runTemplateCorrelator.php?expId=$sessionId'>Template Picking</a>",
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
	if ($loopruns > 0) {
		$nrun[] = array(
				'name'=>"<a href='runLoopAgain.php?expId=$sessionId'>Repeat from other session</a>",
				);
	}
	$maxangle = $particle->getMaxTiltAngle($sessionId);
	if ($maxangle > 5) {
		$nrun[] ="<a href='runTiltAligner.php?expId=$sessionId'>Align and Edit Tilt Pairs</a>";
		$nrun[] = array(
			'name'=>"<a href='runTiltAutoAligner.php?expId=$sessionId'>Auto Align Tilt Pairs</a>",
			'result'=>$tiltresults,
		);
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($result),
		'newrun'=>array($nrun, $celloption),
	);


	$action = "CTF Estimation";

	// get ctf estimation stats:
	$ctfresults=array();
	$ctfdone = count($subclusterjobs['pyace']['done']);
	$ctfrun = count($subclusterjobs['pyace']['running']);
	$ctfq = count($subclusterjobs['pyace']['queued']);

	$ctfresults[] = ($ctfdone==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ctfdone complete</a>";
	$ctfresults[] = ($ctfrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ace'>$ctfrun running</a>";
	$ctfresults[] = ($ctfq==0) ? "" : "$ctfq queued";

	$ace2done = count($subclusterjobs['ace2']['done']);
	$ace2run = count($subclusterjobs['ace2']['running']);
	$ace2q = count($subclusterjobs['ace2']['queued']);
	$ace2done+= count($subclusterjobs['pyace2']['done']);
	$ace2run = count($subclusterjobs['pyace2']['running']);
	$ace2q = count($subclusterjobs['pyace2']['queued']);

	$ace2results[] = ($ace2done==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ace2done complete</a>";
	$ace2results[] = ($ace2run==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace2'>$ace2run running</a>";
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
	if ($loopruns > 0) {
		$nruns[] = array(
				'name'=>"<a href='runLoopAgain.php?expId=$sessionId'>Repeat from other session</a>",
				);
	}

	$data[]=array(
		'action'=>array($action, $celloption),
		'result'=>array($totresult),
		'newrun'=>array($nruns, $celloption),
	);

	// display the stack menu only if have particles picked
	if ($totalprtlruns > 0) {
		$action = "Stacks";

		// get stack stats:
		$sresults=array();
		$sdone = count($subclusterjobs['makestack']['done']);
		$srun = count($subclusterjobs['makestack']['running']);
		$sq = count($subclusterjobs['makestack']['queued']);

		$sdone += count($subclusterjobs['makestack2']['done']);
		$srun += count($subclusterjobs['makestack2']['running']);
		$sq += count($subclusterjobs['makestack2']['queued']);

		$sdone += count($subclusterjobs['stackfilter']['done']);
		$srun += count($subclusterjobs['stackfilter']['running']);
		$sq += count($subclusterjobs['stackfilter']['queued']);

		$sresults[] = ($sdone==0) ? "" : "<a href='stackhierarchy.php?expId=$sessionId'>$sdone complete</a>";
		$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makestack'>$srun running</a>";
		$sresults[] = ($sq==0) ? "" : "$sq queued";

		// stacks being created and stacks completed
		$totstack = $sdone+$srun+$sq;

		$totstack = ($totstack > $stackruns) ? $totstack : $stackruns;
		$totresult = ($totstack==0) ? "" :
			"<a href='stackhierarchy.php?expId=$sessionId'>$totstack</a>";

		$nruns=array();
		$nruns[]=array (
				'name'=>"<a href='runMakeStack2.php?expId=$sessionId'>Stack creation</a>",
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

		// get alignment stats:
		$alignresults=array();
		if ($alignstackids=$particle->getAlignStackIds($expId)) {
			$aligndone = count($alignstackids);
		}
		$alignrun = count($subclusterjobs['partalign']['running']);
		if ($maxlikejobs=$particle->getFinishedMaxLikeJobs($projectId)) {
			$nmaxlikejobs = count($maxlikejobs);
		}
		
		$alignqueue  = count($subclusterjobs['partalign']['queued']);

		$alignresults[] = ($aligndone==0) ? "" : "<a href='alignlist.php?expId=$sessionId'>$alignruns complete</a>";
		$alignresults[] = ($alignrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partalign'>$alignrun running</a>";
		$alignresults[] = ($nmaxlikejobs==0) ? "" : "<a href='runUploadMaxLike.php?expId=$sessionId'>$nmaxlikejobs ready to upload</a>";
		$alignresults[] = ($alignqueue==0) ? "" : "$alignqueue queued";

		$nruns=array();

		$nruns[] = array(
			'name'=>"<a href='selectParticleAlignment.php?expId=$sessionId'>Run Alignment</a>",
			'result'=>$alignresults,
		);
		if ($aligndone > 0) {
			// alignment analysis
			$analysisresults=array();
			if ($analysisruns=$particle->getAnalysisRuns($expId, $projectId)) {
				$analysisdone  = count($analysisruns);
			}
			$analysisrun  = count($subclusterjobs['alignanalysis']['running']);
			$analysisqueue  = count($subclusterjobs['alignanalysis']['queued']);
			$analysisresults[] = ($analysisdone==0) ? "" : "<a href='analysislist.php?expId=$sessionId'>$analysisdone complete</a>";
			$analysisresults[] = ($analysisrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=alignanalysis'>$analysisrun running</a>";
			$analysisresults[] = ($analysisqueue==0) ? "" : "$analysisqueue queued";
			$nruns[] = array (
				'name'=>"<a href='selectFeatureAnalysis.php?expId=$sessionId'>Run Feature Analysis</a>",
				'result'=>$analysisresults,
			);

			if ($analysisdone > 0) {
				// particle clustering
				$clusterresults=array();
				if ($clusterstack=$particle->getClusteringStacks($expId, $projectId)) {
					$clusterdone  = count($clusterstack);
				}
				$clusterrun  = count($subclusterjobs['partcluster']['running']);
				$clusterqueue  = count($subclusterjobs['partcluster']['queued']);
				$clusterresults[] = ($clusterdone==0) ? "" : "<a href='clusterlist.php?expId=$sessionId'>$clusterdone complete</a>";
				$clusterresults[] = ($clusterrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partcluster'>$clusterrun running</a>";
				$clusterresults[] = ($clusterqueue==0) ? "" : "$clusterqueue queued";
				$nruns[] = array (
					'name'=>"<a href='analysislist.php?expId=$sessionId'>Run Particle Clustering</a>",
					'result'=>$clusterresults,
				);
			}
		}

		// ===================================================================
		// template stacks (class averages & forward projections)
		// ===================================================================

		$tsresults=array();
		if ($tstacks=$particle->getTemplateStacksFromProject($projectId)) {
			$tsdone  = count($tstacks);
		}
		if ($tstacks_session=$particle->getTemplateStacksFromSession($sessionId)) {
			$tsdone_session = count($tstacks_session);
		}
		$tsruns  = count($subclusterjobs['templatestack']['running']);
		$tsqueue  = count($subclusterjobs['templatestack']['queued']);
		$tsresults[] = ($tsdone==0) ? "" : "<a href='selectTemplateStack.php?expId=$sessionId'>$tsdone complete</a>";
		$tsresults[] = ($tsrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatestack'>$tsruns running</a>";
		$tsresults[] = ($tsqueue==0) ? "" : "$analysisqueue queued";
		$nruns[] = array (
			'name'=>"<a href='selectTemplateStack.php?expId=$sessionId'>Template Stacks</a>",
			'result'=>$tsresults,
		);


		// =======================
		// old spider alignment
		// =======================

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

		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array(""),
			      'newrun'=>array($nruns, $celloption),
			      );

	}

	// ab initio reconstruction tools
	$action = "Ab Initio Reconstruction";
	$nruns=array();

	/* RCT Volumes */
	if ($maxangle > 5 && $aligndone >= 1 && $stackruns >= 2 ) {
		$rctdone = $particle->getNumberOfRctRuns($sessionId);
		$rctrun = count($subclusterjobs['rctvolume']['running']);
		$rctqueue = count($subclusterjobs['rctvolume']['queued']);
		$rctresults[] = ($rctdone > 0) ? "<a href='rctsummary.php?expId=$sessionId'>$rctdone complete</a>" : '';
		$rctresults[] = ($rctrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=rctvolume'>$rctrun running</a>";
		$rctresults[] = ($rctqueue==0) ? "" : "$rctqueue queued";
		$nruns[]=array(
			'name'=>"<a href='runRctVolume.php?expId=$sessionId'>RCT Volume</a>",
			'result'=>$rctresults,
		);
	}

	/* OTR Volumes */
	if ($maxangle > 5 && $aligndone >= 1 && $stackruns >= 2 ) {
		$otrdone = $particle->getNumberOfOtrRuns($sessionId);
		$otrrun = count($subclusterjobs['otrvolume']['running']);
		$otrqueue = count($subclusterjobs['otrvolume']['queued']);
		$otrresults[] = ($otrdone > 0) ? "<a href='otrsummary.php?expId=$sessionId'>$otrdone complete</a>" : '';
		$otrresults[] = ($otrrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=otrvolume'>$otrrun running</a>";
		$otrresults[] = ($otrqueue==0) ? "" : "$otrqueue queued";
		$nruns[]=array(
			'name'=>"<a href='runOtrVolume.php?expId=$sessionId'>OTR Volume</a>",
			'result'=>$otrresults,
		);
	}

	/* EMAN Common Lines */
	if ($aligndone >= 1 || $norefdone >= 1 ) {
		$clinesqueue = count($subclusterjobs['createModel']['queued']);
		$clinesrun = count($subclusterjobs['createModel']['running']);
		$clinesresults[] = ($clinesrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=createModel'>$clinesrun running</a>";
		$clinesresults[] = ($clinesqueue==0) ? "" : "$clinesqueue queued";
		$nruns[]=array(
			'name'=>"<a href='createmodel.php?expId=$sessionId'>EMAN Common Lines</a>",
			'result'=>$clinesresults,
		);

	}

	/* IMAGIC Common Lines */
	$imagiccluster3d0=$particle->get3d0ClusterModelsFromSessionId($sessionId);
	$imagicts3d0=$particle->get3d0TemplateStackModelsFromSessionId($sessionId);
	if ($clusterdone > 0 || $tsdone_session > 0) {
		if (is_array($imagiccluster3d0) && is_array($imagicts3d0)) $imagic3d0data = array_merge($imagiccluster3d0,$imagicts3d0);
		elseif (is_array($imagiccluster3d0) && !is_array($imagicts3d0)) $imagic3d0data = $imagiccluster3d0;
		else $imagic3d0data = $imagicts3d0;
		$numimagic3d0 = count($imagic3d0data);
		$threed0done = count($subclusterjobs['create3d0']['done']);
		$threed0run = count($subclusterjobs['create3d0']['running']);
		$threed0queue = count($subclusterjobs['create3d0']['queued']);
		$threedresults[] = ($numimagic3d0 == 0) ? "" : "<a href='imagic3dRefine.php?expId=$sessionId&3d0=true'>$numimagic3d0 complete</a>";
		$threedresults[] = ($threed0run == 0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=create3d0'>$threed0run running</a>";
		
		$nruns[]=array(
			'name'=>"<a href='selectClassAveragesFor3d0.php?expId=$sessionId'>IMAGIC Common Lines</a>",
			'result'=>$threedresults
		);
	}

	if ( (array)$nruns ) {
		$data[]=array(
		      'action'=>array($action, $celloption),
		      'result'=>array(),
		      'newrun'=>array($nruns, $celloption),
		      );
	}

	// display reconstructions only if there is a stack
	if ($stackruns > 0) {
		// for every uploaded job, subtract a submitted job
		// if all submitted jobs are uploaded, it should be 0
		$jobincomp = $jobdone-$reconswithjob; //incomplete

		$action = "Refine Reconstruction";

		$emanreconresults = array();

		// check for euler jumper filter jobs
		$ejdone = count($subclusterjobs['removeJumpers']['done']);
		$ejq = count($subclusterjobs['removeJumpers']['queued']);
		$ejrun = count($subclusterjobs['removeJumpers']['running']);

		// check for how many EMAN reconstructions have finished / running / queued
		$emanreconresults[] = ($jobqueue>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobqueue queued</a>" : "";
		$emanreconresults[] = ($jobrun>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobrun running</a>" : "";
		$emanreconresults[] = ($jobincomp>0) ? "<a href='checkjobs.php?expId=$sessionId'>$jobincomp ready for upload</a>" : "";
		$emanreconresults[] = ($reconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$reconruns complete</a>" : "";
		$emanreconresults[] = ($ejrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=removeJumpers'>$ejrun reclassifying</a>";

		$totresult = ($reconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$reconruns</a>" : "";

		// check for how many FREALIGN reconstructions are upload / ready to upload / ready to run / running / queued
		$prepfrealignqueue = count($subclusterjobs['prepfrealign']['queued']);
		$prepfrealignrun = count($subclusterjobs['prepfrealign']['running']);
		$prepfrealigndone = count($subclusterjobs['prepfrealign']['done']);
		$runfrealignqueue = count($subclusterjobs['runfrealign']['queued']);
		$runfrealignrun = count($subclusterjobs['runfrealign']['running']);
		$runfrealigndone = count($subclusterjobs['runfrealign']['done']);
		$uploadfrealignqueue = count($subclusterjobs['uploadfrealign']['queued']);
		$uploadfrealignrun = count($subclusterjobs['uploadfrealign']['running']);
		$uploadfrealigndone = count($subclusterjobs['uploadfrealign']['done']);

		$runfrealign = $runfrealignqueue + $runfrealignrun + $runfrealigndone;
		$uploadfrealign = $uploadfrealignqueue + $uploadfrealignrun + $uploadfrealigndone;
		$frealignprepared = $prepfrealigndone - $runfrealign;
		$frealignran = $runfrealigndone - $uploadfrealign;

		// QUEUED
		$frealignresults[] = ($prepfrealignqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=prepfrealign'>$prepfrealignqueue preps queued</a>" : "";
		$frealignresults[] = ($runfrealignqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=runfrealign'>$runfrealignqueue jobs queued</a>" : "";
		$frealignresults[] = ($uploadfrealignqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadfrealign'>$uploadfrealignqueue uploads queued</a>" : "";

		// RUNNING
		$frealignresults[] = ($prepfrealignrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=prepfrealign'>$prepfrealignrun preps running</a>" : "";
		$frealignresults[] = ($runfrealignrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=runfrealign'>$runfrealignrun jobs running</a>" : "";
		$frealignresults[] = ($uploadfrealignrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadfrealign'>$uploadfrealignrun uploads running</a>" : "";

		// PREPARED
		$frealignresults[] = ($frealignprepared>0) ? "<a href='runFrealign.php?expId=$sessionId'>$frealignprepared prepared</a>" : "";

		// READY TO UPLOAD
		$frealignresults[] = ($frealignran>0) ? "<a href='uploadFrealign.php?expId=$sessionId'>$frealignran ready to upload</a>" : "";

		// COMPLETE
		$frealignresults[] = ($uploadfrealigndone>0) ? "<a href='frealignSummary.php?expId=$sessionId'>$uploadfrealigndone complete</a>" : "";

		// check for how many IMAGIC reconstructions have finished / running / queued
		$imq = count($subclusterjobs['imagic3dRefine']['queued']);
		$imrun = count($subclusterjobs['imagic3dRefine']['running']);
		$imrefruns = $particle->getImagic3dRefinementRunsFromSessionId($sessionId);
		$imdone = (!empty($imrefruns)) ? count($imrefruns) : 0;
		$imreconresults = array();
		$imreconresults[] = ($imq>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=imagic3dRefine'>$imq queued</a>" : "";
		$imreconresults[] = ($imrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=imagic3dRefine'>$imrun running</a>" : "";
		$imreconresults[] = ($imdone>0) ? "<a href='imagic3dRefineSummary.php?expId=$sessionId'>$imdone complete</a>" : "";

		// check for how many Xmipp reconstructions have finished / running / queued
		$xmippreconqueue = count($subclusterjobs['xmipprecon']['queued']);
		$xmippreconrun = count($subclusterjobs['xmipprecon']['running']);
		$xmipprecondone = count($subclusterjobs['xmipprecon']['done']);
		$numxmipprecon = 0;
		$xmippreconupload = $xmipprecondone - $numxmipprecon;
		$xmippreconresults[] = ($xmippreconqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$xmippreconqueue queued</a>" : "";
		$xmippreconresults[] = ($xmippreconrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$xmippreconrun running</a>" : "";
		$xmippreconresults[] = ($xmippreconupload>0) ? "<a href='uploadXmippRecon.php?expId=$sessionId'>$xmippreconupload ready for upload</a>" : "";
		$xmippreconresults[] = ($numxmipprecon>0) ? "<a href='reconsummary.php?expId=$sessionId'>$numxmipprecon complete</a>" : "";

		// list out refinement jobs in the web menu
		$nruns=array();
//		if ($_SESSION['loggedin']) {
		if (TRUE) {
			$nruns[] = array(
					 'name'=>"<a href='emanJobGen.php?expId=$sessionId'>EMAN Refinement</a>",
					 'result'=>$emanreconresults,
					 );
			$nruns[] = array(
					 'name'=>"<a href='prepareFrealign.php?expId=$sessionId'>Frealign Refinement</a>",
					 'result'=>$frealignresults,
					 );
			$nruns[] = "<a href='spiderJobGen.php?expId=$sessionId'>SPIDER Refinement</a>";
			$nruns[] = array(
					 'name'=>"<a href='runXmippRefineJobGen.php?expId=$sessionId'>Xmipp Refinement</a>",
					 'result'=>$xmippreconresults,
					 );
			$nruns[] = array(
					 'name'=>"<a href='imagic3dRefine.php?expId=$sessionId'>IMAGIC Refinement</a>",
					 'result'=>$imreconresults,
					 );
			} else {
			$nruns[] = "<font color='888888'><i>please login first</i></font>";
		}
		$data[]=array(
	      'action'=>array($action, $celloption),
	      'result'=>array($totresult),
	      'newrun'=>array($nruns, $celloption),
	      );
	}

	/* 3d Density Volumes */
	$action = "3d Density Volumes";
	$nruns=array();
	if ($threedvols = $particle->get3dDensitysFromSession($sessionId)) {
		$num3dvols = count($threedvols);
	}
	if ($num3dvols >= 1) {
		$nruns[]=array(
			'result'=>"<a href='densitysummary.php?expId=$sessionId'>$num3dvols complete</a>",
		);
	}
	$totresult = ($num3dvols>0) ? "<a href='densitysummary.php?expId=$sessionId'>$num3dvols</a>" : "";
	if ( (array)$nruns ) {
		$data[]=array(
	      'action'=>array($action, $celloption),
	      'result'=>array($totresult),
	      'newrun'=>array($nruns, $celloption),
	   );
	}

	// display the tomography menu only if there are tilt serieses
	if ($tiltruns > 0) {
		$action = "Tomography";

		// get tomogram upload stats:
		$sresults=array();
		$sdone = count($subclusterjobs['uploadtomo']['done']);
		$srun = count($subclusterjobs['uploadtomo']['running']);
		$sq = count($subclusterjobs['uploadtomo']['queued']);
		$sresults[] = ($sdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$sdone complete</a>";
		$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$srun running</a>";
		$sresults[] = ($sq==0) ? "" : "$sq queued";

		// get tilt series alignement stats:
		$aresults=array();
		$adone = count($subclusterjobs['tomoaligner']['done']);
		$adone = count($particle->getTomoAlignmentRunsFromSession($sessionId, False));
		$arun = count($subclusterjobs['tomoaligner']['running']);
		$aq = count($subclusterjobs['tomoaligner']['queued']);
		$aresults[] = ($adone==0) ? "" : "<a href='tomoalignsummary.php?expId=$sessionId'>$adone complete</a>";
		$aresults[] = ($arun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoalign'>$srun running</a>";
		$aresults[] = ($aq==0) ? "" : "$aq queued";
		
		// get full tomogram making stats:
		$tresults=array();
		$tdone = $fulltomoruns;
		$trun = count($subclusterjobs['tomomaker']['running']);
		$tq = count($subclusterjobs['tomomaker']['queued']);
		$tresults[] = ($tdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tdone complete</a>";
		$tresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$trun running</a>";
		$tresults[] = ($tq==0) ? "" : "$tq queued";
		// get subtomogram making stats:
		$stresults=array();
		$stdone = $tomoruns;
		$strun = count($subclusterjobs['subtomomaker']['running']);
		$stq = count($subclusterjobs['subtomomaker']['queued']);
		$stresults[] = ($stdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$stdone complete</a>";
		$stresults[] = ($strun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$strun running</a>";
		$stresults[] = ($stq==0) ? "" : "$stq queued";

		// tomograms being created and completed
		$tottomo = $tdone+$trun+$tq;

		$tottomo = ($tottomo > $tomoruns+$fulltomoruns) ? $tottomo : $tomoruns+$fulltomoruns;
		$totresult = ($tottomo==0) ? "" :
			"<a href='tomosummary.php?expId=$sessionId'>$fulltomoruns/$tomoruns</a>";

		$nruns=array();
		$nruns[]=array (
			'name'=>"<a href='runTomoAligner.php?expId=$sessionId'>Align tilt series</a>",
			'result'=>$aresults,
			);
		$nruns[]=array (
			'name'=>"<a href='runTomoMaker.php?expId=$sessionId'>Create full tomogram</a>",
			'result'=>$tresults,
			);
		$nruns[]=array (
			'name'=>"<a href='uploadtomo.php?expId=$sessionId'>Upload tomogram</a>",
			'result'=>$sresults,
			);
		$nruns[]=array (
			'name'=>"<a href='runSubTomogram.php?expId=$sessionId'>Create tomogram subvolume</a>",
			'result'=>$stresults,
			);
		$nruns[]=array (
			'name'=>"<a href='runTomoAverage.php?expId=$sessionId'>Average subvolumes</a>",
			'result'=> ($avgtomoruns>0) ? "<a href='tomoavgsummary.php?expId=$sessionId'>$avgtomoruns complete</a>" : "",
			);


		$data[]=array(
	      'action'=>array($action, $celloption),
	      'result'=>array($totresult),
	      'newrun'=>array($nruns, $celloption),
	      );
	}

	// upload model & template tools
	$action = "Import tools";

	$nruns=array();
	$nruns[]=array(
		'name'=>"<a href='pdb2density.php?expId=$sessionId'>PDB to Model</a>"
	);

	$nruns[]=array(
		'name'=>"<a href='emdb2density.php?expId=$sessionId'>EMDB to Model</a>"
	);

	$nruns[]=array(
		'name'=>"<a href='uploadParticles.php?expId=$sessionId'>Upload particles</a>",
	);

	$result = ($templates==0) ? "" :
	  "<a href='viewtemplates.php?expId=$sessionId'>$templates available</a>";

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

	$nruns[]=array(
		'name'=>"<a href='uploadimage.php?expId=$sessionId'>Upload more images</a>",
	);

	$nruns[]=array(
		'name'=>"<a href='uploadstack.php?expId=$sessionId'>Upload stack</a>",
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

	$nruns=array();
	$nruns[] = "<a href='imgassessor.php?expId=$sessionId'>Web Img Assessment</a>";
	$nruns[] = "<a href='multiimgassessor.php?expId=$sessionId'>Multi Img Assessment</a>";
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

	// Synthetic Data
	$action = "Synthetic Data";
	if ($models != 0) {
		$synresults=array();
		$syndone = count($subclusterjobs['syntheticData']['done']);
		$synrun = count($subclusterjobs['syntheticData']['running']);
		$synq = count($subclusterjobs['syntheticData']['queued']);

		$synresults[] = ($syndone==0) ? "" : "<a href='stacksummary.php?expId=$sessionId&syntheticOnly=True'>$syndone complete</a>";
		$synresults[] = ($synrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=syntheticData'>$synrun running</a>";
		$synresults[] = ($synq==0) ? "" : "$synq queued";

		// synthetic stacks being created and stacks completed
		$totsynstack = $syndone+$synrun+$synq;

		$totsynresult = ($totsynstack==0) ? "" :
			"<a href='stacksummary.php?expId=$sessionId&syntheticOnly=True'>$totsynstack</a>";

		$nruns=array();
		$nruns[]=array (
				'name'=>"<a href='createSyntheticDataset.php?expId=$sessionId'>Synthetic Dataset Creation</a>",
				'result'=>$synresults,
				);
		$data[]=array(
			      'action'=>array($action, $celloption),
			      'result'=>array($totsynresult),
			      'newrun'=>array($nruns, $celloption),
			      );		
	}
	

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
		global $expId;
		$allow_process = checkExptAdminPrivilege($expId,'data');
		$text="<ul>";
		// print out the title of the subfunction
		foreach((array)$data as $submenu) {
			if (is_array($submenu)) {
				$submenuname = ($allow_process) ? $submenu['name']:removeLink($submenu['name']);
				$text.="<li>".$submenuname."</li>";
				// if there are results for the
				// subfunction, print them out
				foreach ((array)$submenu['result'] as $res) {
					$text.=($res) ? "<li class='sub1'>$res</li>" : "";
				}
			}
			else {
				$submenuname = ($allow_process) ? $submenu:removeLink($submenu);
				$text.="<li>$submenuname</li>\n";
			}
		}
		$text.="</ul>";
		return '<div class="submenu">'.$text.'</div>';
	}

	function removeLink($name) {
		$namearray = explode("<a",$name);
		if (count($namearray) < 2) return $name;
		$namearray = explode(">",$namearray[1]);
		$newname = $namearray[1];
		return $newname;
	}
?>
