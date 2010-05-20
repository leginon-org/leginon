<?php
/**
* The Leginon software is Copyright 2003
* The Scripps Research Institute, La Jolla, CA
* For terms of the license agreement
* see http://ami.scripps.edu/software/leginon-license
*
*	main menu for processing tools
*/

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";


$expId=$_GET['expId'];
$projectId = getProjectId();

// check if coming directly from a session
if (!is_numeric($expId) && is_numeric($_POST['sessionId'])) {
	$sessionId=$_POST['sessionId'];
	$expId = $sessionId;
}
if (is_numeric($expId)) {
	$sessionId=$expId;
	$formAction=$_SERVER['PHP_SELF']."?expId=$expId";;
} elseif (is_numeric($projectId)) {
	$sessionId=$_POST['sessionId'];
	$formAction=$_SERVER['PHP_SELF']."?projectId=$projectId";;
}

// Collect session info from database
$sessiondata=getSessionList($projectId, $sessionId);
$sessioninfo=$sessiondata['info'];
$sessions=$sessiondata['sessions'];

$particle = new particledata();

if (is_numeric($expId)) {
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
	// --- Get CTF Data
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

	// --- Get Alignment Data
	if ($stackruns>0) {
		if ($alignIds = $particle->getAlignStackIds($sessionId)) {
			$alignruns=count($alignIds);
		}
	}
	else {
		$alignruns=0;
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

	$tdone = count($subclusterjobs['templatecorrelator']['done']);
	$trun = count($subclusterjobs['templatecorrelator']['running']);
	$tq = count($subclusterjobs['templatecorrelator']['queued']);

	$ddone = count($subclusterjobs['dogpicker']['done']);
	$drun = count($subclusterjobs['dogpicker']['running']);
	$dq = count($subclusterjobs['dogpicker']['queued']);

	$sdone = count($subclusterjobs['signaturepicker']['done']);
	$srun = count($subclusterjobs['signaturepicker']['running']);
	$sq = count($subclusterjobs['signaturepicker']['queued']);
	
	$mdone = count($subclusterjobs['manualpicker']['done']);
	$mrun = count($subclusterjobs['manualpicker']['running']);
	$mq = count($subclusterjobs['manualpicker']['queued']);

	$tiltdone = count($subclusterjobs['tiltalign']['done']);
	$tiltrun = count($subclusterjobs['tiltalign']['running']);
	$tiltqueue = count($subclusterjobs['tiltalign']['queued']);

	$tresults[] = ($tdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$tdone complete</a>";
	$tresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatecorrelator'>$trun running</a>";
	$tresults[] = ($tq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatecorrelator'>$tq queued</a>";

	$dresults[] = ($ddone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$ddone complete</a>";
	$dresults[] = ($drun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$drun running</a>";
	$dresults[] = ($dq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$dq queued</a>";

	$sresults[] = ($sdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$sdone complete</a>";
	$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=signaturepicker'>$srun running</a>";
	$sresults[] = ($sq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=signaturepicker'>$sq queued</a>";

	$mresults[] = ($mdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$mdone complete</a>";
	$mresults[] = ($mrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mrun running</a>";
	$mresults[] = ($mq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mq queued</a>";

	$tiltresults[] = ($tiltdone==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$tiltdone complete</a>";
	$tiltresults[] = ($tiltrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tiltalign'>$tiltrun running</a>";
	$tiltresults[] = ($tiltqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tiltalign'>$tiltqueue queued</a>";

	// in case weren't submitted by web:
	$totruns = $tdone+$trun+$tq+$ddone+$drun+$dq+$mdone+$mrun+$mq;
	if ($prtlruns > $totruns) $totruns = $prtlruns;
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
	// The signature feature is added with issue #368, however was not tested prior to 2.0 release.
	// It should be hidden until it can be tested at AMI. The HIDE_FEATURE flag can be set
	// in config.php in the myamiweb directory.
	if (!HIDE_FEATURE)
	{
		$nrun[] = array(
			'name'=>"<a href='runSignature.php?expId=$sessionId'>Signature</a>",
			'result'=>$sresults,
		);
	}
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

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nrun, $celloption),
	);


	$action = "CTF Estimation";

	// get ctf estimation stats:
	$ctfresults=array();
	$ctfdone = count($subclusterjobs['pyace']['done']);
	$ctfrun = count($subclusterjobs['pyace']['running']);
	$ctfq = count($subclusterjobs['pyace']['queued']);

	$ctfresults[] = ($ctfdone==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ctfdone complete</a>";
	$ctfresults[] = ($ctfrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace'>$ctfrun running</a>";
	$ctfresults[] = ($ctfq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace'>$ctfq queued</a>";

	$ace2done = count($subclusterjobs['ace2']['done']);
	$ace2run = count($subclusterjobs['ace2']['running']);
	$ace2q = count($subclusterjobs['ace2']['queued']);
	$ace2done+= count($subclusterjobs['pyace2']['done']);
	$ace2run = count($subclusterjobs['pyace2']['running']);
	$ace2q = count($subclusterjobs['pyace2']['queued']);

	$ace2results[] = ($ace2done==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ace2done complete</a>";
	$ace2results[] = ($ace2run==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace2'>$ace2run running</a>";
	$ace2results[] = ($ace2q==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace2'>$ace2q queued</a>";

	$ctffinddone = count($subclusterjobs['ctfestimate']['done']);
	$ctffindrun = count($subclusterjobs['ctfestimate']['running']);
	$ctffindq = count($subclusterjobs['ctfestimate']['queued']);

	$ctffindresults[] = ($ctffinddone==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ctffinddone complete</a>";
	$ctffindresults[] = ($ctffindrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ctfestimate'>$ctffindrun running</a>";
	$ctffindresults[] = ($ctffindq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ctfestimate'>$ctffindq queued</a>";

	// TO DO: Currently ctffind results shows all ctffind & ctftilt runs, since the same program launches both
	// need to figure out how to get ctftilt runs specifically, and decrement from ctffind runs


	// number running and number finished:
	$totruns=$ctfdone+$ctfrun+$ctfq;

	// in case weren't submitted by web:
	if ($ctfruns > $totruns) $totruns = $ctfruns;
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
		'name'=>"<a href='runCtfEstimate.php?expId=$sessionId'>CtfFind Estimation</a>",
		'result'=>$ctffindresults,
	);
	
	//CTFTilt Estimation works and uploads, but fails alot; there is a warning
	if (!HIDE_FEATURE)
	{
		if ($maxangle > 5) {
			$nruns[] = array(
				'name'=>"<a href='runCtfEstimate.php?expId=$sessionId&ctftilt=True'>CtfTilt Estimation</a>",
				'result'=>$ctftiltresults,
			);
		}
	}
	
	if ($loopruns > 0) {
		$nruns[] = array(
			'name'=>"<a href='runLoopAgain.php?expId=$sessionId'>Repeat from other session</a>",
		);
	}

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($totresult),
		'newrun' => array($nruns, $celloption),
	);

	// display the stack menu only if have particles picked
	if ($totalprtlruns > 0) {
		$action = "Stacks";

		// get stack stats:
		$sresults=array();
		$sdone = 0; $srun = 0; $sq = 0;
		$stacktypes = array('makestack', 'makestack2', 'filterstack', 'substack', 'centerparticlestack', 'alignsubstack');
		foreach ($stacktypes as $stacktype) {
			$sdone += count($subclusterjobs[$stacktype]['done']);
			$srun += count($subclusterjobs[$stacktype]['running']);
			$sq += count($subclusterjobs[$stacktype]['queued']);
		}

		$totstack = ($sdone > $stackruns-$srun) ? $sdone : $stackruns-$srun;

		// for each stack running, decrement complete stacks
		// since they are counted twice
		$sresults[] = ($totstack==0) ? "" : "<a href='stackhierarchy.php?expId=$sessionId'>".($totstack)." complete</a>";
		$sresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makestack'>$srun running</a>";
		$sresults[] = ($sq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makestack'>$sq queued</a>";

		$totresult = ($totstack==0) ? "" :
			"<a href='stackhierarchy.php?expId=$sessionId'>$totstack</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='runMakeStack2.php?expId=$sessionId'>Stack creation</a>",
			'result'=>$sresults,
		);
		$nruns[] = array(
			'name'=>"<a href='moreStackTools.php?expId=$sessionId'>more stack tools</a>",
		);

		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totresult),
			'newrun' => array($nruns, $celloption),
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
		
		$alignqueue = count($subclusterjobs['partalign']['queued']);

		$alignresults[] = ($aligndone==0) ? "" : "<a href='alignlist.php?expId=$sessionId'>$alignruns complete</a>";
		$alignresults[] = ($alignrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partalign'>$alignrun running</a>";
		$alignresults[] = ($nmaxlikejobs==0) ? "" : "<a href='runUploadMaxLike.php?expId=$sessionId'>$nmaxlikejobs ready to upload</a>";
		$alignresults[] = ($alignqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partalign'>$alignqueue queued</a>";

		$nruns=array();

		$nruns[] = array(
			'name'=>"<a href='selectParticleAlignment.php?expId=$sessionId'>Run Alignment</a>",
			'result'=>$alignresults,
		);
		if ($aligndone > 0) {
			// alignment analysis
			$analysisresults=array();
			if ($analysisruns=$particle->getAnalysisRuns($expId, $projectId)) {
				$analysisdone = count($analysisruns);
			}
			$analysisrun = count($subclusterjobs['alignanalysis']['running']);
			$analysisqueue = count($subclusterjobs['alignanalysis']['queued']);
			$analysisresults[] = ($analysisdone==0) ? "" : "<a href='analysislist.php?expId=$sessionId'>$analysisdone complete</a>";
			$analysisresults[] = ($analysisrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=alignanalysis'>$analysisrun running</a>";
			$analysisresults[] = ($analysisqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=alignanalysis'>$analysisqueue queued</a>";
			$nruns[] = array(
				'name'=>"<a href='selectFeatureAnalysis.php?expId=$sessionId'>Run Feature Analysis</a>",
				'result'=>$analysisresults,
			);

			if ($analysisdone > 0) {
				// particle clustering
				$clusterresults=array();
				if ($clusterstack=$particle->getClusteringStacks($expId, $projectId)) {
					$clusterdone = count($clusterstack);
				}
				$clusterrun = count($subclusterjobs['partcluster']['running']);
				$clusterqueue = count($subclusterjobs['partcluster']['queued']);
				$clusterresults[] = ($clusterdone==0) ? "" : "<a href='clusterlist.php?expId=$sessionId'>$clusterdone complete</a>";
				$clusterresults[] = ($clusterrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partcluster'>$clusterrun running</a>";
				$clusterresults[] = ($clusterqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partcluster'>$clusterqueue queued</a>";
				$nruns[] = array(
					'name'=>"<a href='analysislist.php?expId=$sessionId'>Run Particle Clustering</a>",
					'result'=>$clusterresults,
				);
			}
		}
		if (!HIDE_IMAGIC && !HIDE_FEATURE) {
			// ===================================================================
			// template stacks (class averages & forward projections)
			// ===================================================================

			$tsresults=array();
			if ($tstacks=$particle->getTemplateStacksFromProject($projectId)) {
				$tsdone = count($tstacks);
			}
			if ($tstacks_session=$particle->getTemplateStacksFromSession($sessionId)) {
				$tsdone_session = count($tstacks_session);
			}
			$tsruns = count($subclusterjobs['templatestack']['running']);
			$tsqueue = count($subclusterjobs['templatestack']['queued']);
			$tsresults[] = ($tsdone==0) ? "" : "<a href='selectTemplateStack.php?expId=$sessionId'>$tsdone complete</a>";
			$tsresults[] = ($tsruns==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatestack'>$tsruns running</a>";
			$tsresults[] = ($tsqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatestack'>$tsqueue queued</a>";
			$nruns[] = array(
				'name'=>"<a href='selectTemplateStack.php?expId=$sessionId'>Template Stacks</a>",
				'result'=>$tsresults,
			);
		}

		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array(""),
			'newrun' => array($nruns, $celloption),
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
		$rctresults[] = ($rctqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=rctvolume'>$rctqueue queued</a>";
		$nruns[] = array(
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
		$otrresults[] = ($otrqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=otrvolume'>$otrqueue queued</a>";
		$nruns[] = array(
			'name'=>"<a href='runOtrVolume.php?expId=$sessionId'>OTR Volume</a>",
			'result'=>$otrresults,
		);
	}

	/* EMAN Common Lines */
	if ($aligndone >= 1 ) {
		$clinesqueue = count($subclusterjobs['createModel']['queued']);
		$clinesrun = count($subclusterjobs['createModel']['running']);
		$clinesresults[] = ($clinesrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=createModel'>$clinesrun running</a>";
		$clinesresults[] = ($clinesqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=createModel'>$clinesqueue queued</a>";
		$nruns[] = array(
			'name'=>"<a href='createmodel.php?expId=$sessionId'>EMAN Common Lines</a>",
			'result'=>$clinesresults,
		);

	}

	/* IMAGIC Angular Reconstitution */
	if (!HIDE_IMAGIC) {
		if (($aligndone >= 1 && $clusterdone >=1) || ($tsdone >= 1)) {
			$angrecondone = count($particle->getAngularReconstitutionRuns($sessionId));
			$angreconqueue = count($subclusterjobs['angrecon']['queued']);
			$angreconrun = count($subclusterjobs['angrecon']['running']);
			$angreconresults[] = ($angrecondone > 0) ? "<a href='angreconsummary.php?expId=$sessionId'>$angrecondone complete</a>" : '';
			$angreconresults[] = ($angreconrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=angrecon'>$angreconrun running</a>";
			$angreconresults[] = ($angreconqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=angrecon'>$angreconqueue queued</a>";
			$nruns[] = array(
				'name'=>"<a href='bootstrappedAngularReconstitution.php?expId=$sessionId'>IMAGIC Angular Reconstitution</a>",
				'result'=>$angreconresults,
			);
		}
	}

	if ( (array)$nruns ) {
		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array(),
			'newrun' => array($nruns, $celloption),
		);
	}

	// display reconstructions only if there is a stack
	if ($stackruns > 0) {
		$reconruns = $particle->getReconIdsFromSession($sessionId, false);
		$allreconruns = $particle->getReconIdsFromSession($sessionId, true);
		$emanreconswithjob = 0;
		if ($allreconruns) {
			$emanreconruns = count($reconruns);
			foreach ($allreconruns as $reconrun) {
				if ($reconrun['REF|ApAppionJobData|job']) {
					$emanreconswithjob++;
				}
			}
		}

		// get num of jubs queued, submitted or done
		$emanjobqueue=count($subclusterjobs['emanrecon']['queued']);
		$emanjobrun=count($subclusterjobs['emanrecon']['running']);
		$emanjobdone=count($subclusterjobs['emanrecon']['done']);

		// for every uploaded job, subtract a submitted job
		// if all submitted jobs are uploaded, it should be 0
		$emanjobincomp = $emanjobdone-$emanreconswithjob; //incomplete

		$action = "Refine Reconstruction";
		$totresult = ($reconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$emanreconruns</a>" : "";

		$emanreconresults = array();

		// check for euler jumper filter jobs
		$ejdone = count($subclusterjobs['removeJumpers']['done']);
		$ejq = count($subclusterjobs['removeJumpers']['queued']);
		$ejrun = count($subclusterjobs['removeJumpers']['running']);

		// check for how many EMAN reconstructions have finished / running / queued
		$emanreconresults[] = ($emanjobqueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId'>$emanjobqueue queued</a>" : "";
		$emanreconresults[] = ($emanjobrun>0) ? "<a href='checkRefineJobs.php?expId=$sessionId'>$emanjobrun running</a>" : "";
		$emanreconresults[] = ($emanjobincomp>0) ? "<a href='checkRefineJobs.php?expId=$sessionId'>$emanjobincomp ready for upload</a>" : "";
		$emanreconresults[] = ($emanreconruns>0) ? "<a href='reconsummary.php?expId=$sessionId'>$emanreconruns complete</a>" : "";
		$emanreconresults[] = ($ejrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=removeJumpers'>$ejrun reclassifying</a>";


		// check for how many FREALIGN reconstructions are upload / ready to upload / ready to run / running / queued
		$frealigndone = count($particle->getReconIdsFromSession($sessionId, false, 'frealign'));

		$prepfrealignqueue = count($subclusterjobs['prepfrealign']['queued']);
		$prepfrealignrun = count($subclusterjobs['prepfrealign']['running']);
		//$prepfrealigndone = count($subclusterjobs['prepfrealign']['done']);
		$prepfrealigndone = count($particle->getPreparedFrealignJobs(false, false, false));
		$runfrealignqueue = count($subclusterjobs['runfrealign']['queued']);
		$runfrealignrun = count($subclusterjobs['runfrealign']['running']);
		$runfrealigndone = count($subclusterjobs['runfrealign']['done']);
		$uploadfrealignqueue = count($subclusterjobs['uploadfrealign']['queued']);
		$uploadfrealignrun = count($subclusterjobs['uploadfrealign']['running']);

		// summed fields
		$runfrealign = $runfrealignqueue + $runfrealignrun + $runfrealigndone;
		$uploadfrealign = $uploadfrealignqueue + $uploadfrealignrun + $frealigndone;
		$frealignprepared = $prepfrealigndone - $runfrealign;
		$frealignran = $runfrealigndone - $uploadfrealign;

		// QUEUED
		$frealignresults[] = ($prepfrealignqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=prepfrealign'>$prepfrealignqueue preps queued</a>" : "";
		$frealignresults[] = ($runfrealignqueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId'>$runfrealignqueue jobs queued</a>" : "";
		$frealignresults[] = ($uploadfrealignqueue>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadfrealign'>$uploadfrealignqueue uploads queued</a>" : "";

		// RUNNING
		$frealignresults[] = ($prepfrealignrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=prepfrealign'>$prepfrealignrun preps running</a>" : "";
		$frealignresults[] = ($runfrealignrun>0) ? "<a href='checkRefineJobs.php?expId=$sessionId'>$runfrealignrun jobs running</a>" : "";
		$frealignresults[] = ($uploadfrealignrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadfrealign'>$uploadfrealignrun uploads running</a>" : "";

		// PREPARED
		$frealignresults[] = ($frealignprepared>0) ? "<a href='runFrealign.php?expId=$sessionId'>$frealignprepared prepared</a>" : "";

		// READY TO UPLOAD
		$frealignresults[] = ($frealignran>0) ? "<a href='uploadFrealign.php?expId=$sessionId'>$frealignran ready to upload</a>" : "";

		// COMPLETE
		$frealignresults[] = ($frealigndone>0) ? "<a href='frealignSummary.php?expId=$sessionId'>$frealigndone complete</a>" : "";


		if (!HIDE_IMAGIC) {
			// check for how many IMAGIC reconstructions have finished / running / queued
			$imq = count($subclusterjobs['imagic3dRefine']['queued']);
			$imrun = count($subclusterjobs['imagic3dRefine']['running']);
			$imrefruns = $particle->getImagic3dRefinementRunsFromSessionId($sessionId);
			$imdone = (!empty($imrefruns)) ? count($imrefruns) : 0;
			$imreconresults = array();
			$imreconresults[] = ($imq>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=imagic3dRefine'>$imq queued</a>" : "";
			$imreconresults[] = ($imrun>0) ? "<a href='listAppionJobs.php?expId=$sessionId&jobtype=imagic3dRefine'>$imrun running</a>" : "";
			$imreconresults[] = ($imdone>0) ? "<a href='imagic3dRefineSummary.php?expId=$sessionId'>$imdone complete</a>" : "";
		}

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
		$nruns[] = array(
			'name'=>"<a href='emanJobGen.php?expId=$sessionId'>EMAN Refinement</a>",
			'result'=>$emanreconresults,
		);
		$nruns[] = array(
			'name'=>"<a href='prepareFrealign.php?expId=$sessionId'>Frealign Refinement</a>",
			'result'=> $frealignresults,
		);
		if (!HIDE_FEATURE)
		{
			$nruns[] = array(
				'name'=>"<a href='spiderJobGen.php?expId=$sessionId'>SPIDER Refinement</a>",
				'result'=> "<i>(incomplete)</i>", //$spiderreconresults,
			);
		}
		if (!HIDE_FEATURE)
		{
			$nruns[] = array(
				'name'=>"<a href='runXmippRefineJobGen.php?expId=$sessionId'>Xmipp Refinement</a>",
				'result'=> "<i>(incomplete)</i>", //$xmippreconresults,
			);
		}
		if (!HIDE_IMAGIC && !HIDE_FEATURE) {
			$nruns[] = array(
				'name'=>"<a href='imagic3dRefine.php?expId=$sessionId'>IMAGIC Refinement</a>",
				'result'=> "<i>(incomplete)</i>", //$imreconresults,
			);
		}
		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totresult),
			'newrun' => array($nruns, $celloption),
		);
	}

	/* 3d Density Volumes */
	$action = "3d Density Volumes";
	$nruns=array();
	if ($threedvols = $particle->get3dDensitysFromSession($sessionId)) {
		$num3dvols = count($threedvols);
	}
	if ($num3dvols >= 1) {
		$nruns[] = array(
			'result'=>"<a href='densitysummary.php?expId=$sessionId'>$num3dvols complete</a>",
		);
	}
	$totresult = ($num3dvols>0) ? "<a href='densitysummary.php?expId=$sessionId'>$num3dvols</a>" : "";
	if ( (array)$nruns ) {
		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totresult),
			'newrun' => array($nruns, $celloption),
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
		$sresults[] = ($sq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$sq queued</a>";

		// get tilt series alignement stats:
		$aresults=array();
		$adone = count($subclusterjobs['tomoaligner']['done']);
		$adone = count($particle->getTomoAlignmentRunsFromSession($sessionId, False));
		$arun = count($subclusterjobs['tomoaligner']['running']);
		$aq = count($subclusterjobs['tomoaligner']['queued']);
		$aresults[] = ($adone==0) ? "" : "<a href='tomoalignsummary.php?expId=$sessionId'>$adone complete</a>";
		$aresults[] = ($arun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoaligner'>$arun running</a>";
		$aresults[] = ($aq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoaligner'>$aq queued</a>";
		
		// get full tomogram making stats:
		$tresults=array();
		$tdone = $fulltomoruns;
		$trun = count($subclusterjobs['tomomaker']['running']);
		$tq = count($subclusterjobs['tomomaker']['queued']);
		$tresults[] = ($tdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tdone complete</a>";
		$tresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$trun running</a>";
		$tresults[] = ($tq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$tq queued</a>";
		// get subtomogram making stats:
		$stresults=array();
		$stdone = $tomoruns;
		$strun = count($subclusterjobs['subtomomaker']['running']);
		$stq = count($subclusterjobs['subtomomaker']['queued']);
		$stresults[] = ($stdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$stdone complete</a>";
		$stresults[] = ($strun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$strun running</a>";
		$stresults[] = ($stq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$stq queued</a>";

		// tomograms being created and completed
		$tottomo = $tdone+$trun+$tq;

		$tottomo = ($tottomo > $tomoruns+$fulltomoruns) ? $tottomo : $tomoruns+$fulltomoruns;
		$totresult = ($tottomo==0) ? "" :
			"<a href='tomosummary.php?expId=$sessionId'>$fulltomoruns/$tomoruns</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='runTomoAligner.php?expId=$sessionId'>Align tilt series</a>",
			'result'=>$aresults,
		);
		$nruns[] = array(
			'name'=>"<a href='runTomoMaker.php?expId=$sessionId'>Create full tomogram</a>",
			'result'=>$tresults,
		);
		$nruns[] = array(
			'name'=>"<a href='uploadtomo.php?expId=$sessionId'>Upload tomogram</a>",
			'result'=>$sresults,
		);
		$nruns[] = array(
			'name'=>"<a href='runSubTomogram.php?expId=$sessionId'>Create tomogram subvolume</a>",
			'result'=>$stresults,
		);
		$nruns[] = array(
			'name'=>"<a href='runTomoAverage.php?expId=$sessionId'>Average subvolumes</a>",
			'result'=> ($avgtomoruns>0) ? "<a href='tomoavgsummary.php?expId=$sessionId'>$avgtomoruns complete</a>" : "",
		);


		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totresult),
			'newrun' => array($nruns, $celloption),
		);
	}

	// upload model & template tools
	$action = "Import tools";

	$nruns=array();
	$nruns[] = array(
		'name'=>"<a href='pdb2density.php?expId=$sessionId'>PDB to Model</a>"
	);

	$nruns[] = array(
		'name'=>"<a href='emdb2density.php?expId=$sessionId'>EMDB to Model</a>"
	);

	$nruns[] = array(
		'name'=>"<a href='uploadParticles.php?expId=$sessionId'>Upload particles</a>",
	);

	$result = ($templates==0) ? "" :
		"<a href='viewtemplates.php?expId=$sessionId'>$templates available</a>";

	$nruns[] = array(
		'name'=>"<a href='uploadtemplate.php?expId=$sessionId'>Upload template</a>",
		'result'=>$result,
	);

	$result = ($models==0) ? "" :
		"<a href='viewmodels.php?expId=$sessionId'>$models available</a>";

	$nruns[] = array(
		'name'=>"<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>",
		'result'=>$result,
	);

	$nruns[] = array(
		'name'=>"<a href='uploadimage.php?expId=$sessionId'>Upload more images</a>",
	);

	$nruns[] = array(
		'name'=>"<a href='uploadstack.php?expId=$sessionId'>Upload stack</a>",
	);

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array(),
		'newrun' => array($nruns, $celloption),
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

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nruns, $celloption),
	);

	$action = "Region Mask Creation";
	$result = ($maskruns==0) ? "" :
			"<a href='maskreport.php?expId=$sessionId'>$maskruns</a>";
	$nruns=array();
	
	//Crud Finding is not yet working for 2.0 release
	if (!HIDE_FEATURE)
	{
		$nrun = "<a href='runMaskMaker.php?expId=$sessionId'>Crud Finding</a>";
		$nruns[]=$nrun;
	}
	$nrun = "<a href='manualMaskMaker.php?expId=$sessionId'>";
	$nrun .= "Manual Masking";
	$nrun .= "</a>";
	$nruns[]=$nrun;

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nruns, $celloption),
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
		$synresults[] = ($synq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=syntheticData'>$synq queued</a>";

		// synthetic stacks being created and stacks completed
		$totsynstack = $syndone+$synrun+$synq;

		$totsynresult = ($totsynstack==0) ? "" :
			"<a href='stacksummary.php?expId=$sessionId&syntheticOnly=True'>$totsynstack</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='createSyntheticDataset.php?expId=$sessionId'>Synthetic Dataset Creation</a>",
			'result'=>$synresults,
		);
		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totsynresult),
			'newrun' => array($nruns, $celloption),
		);		
	}
} elseif (is_numeric($projectId)) {
	$action = "Upload images";
	$nruns[] = array(
		'name'=>"<a href='uploadimage.php?projectId=$projectId'>Upload images</a>",
	);
	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array(),
		'newrun' => array($nruns, $celloption),
	);
};

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
