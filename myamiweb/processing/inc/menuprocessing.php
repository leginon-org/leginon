<?php
/**
* The Leginon software is Copyright under
* Apache License, Version 2.0
* For terms of the license agreement
* see http://leginon.org
*
*	main menu for processing tools
*/

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/refineJobsMultiModel.inc";
require_once "inc/refineJobsSingleModel.inc";
require_once "inc/alignJobs.inc";


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
		$subclusterjobs = array();
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
	// TODO: getting $totimgs and $assessedimgs are very slow.
	//$totimgs = $particle->getNumImgsFromSessionId($sessionId);
	//$assessedimgs = $particle->getNumTotalAssessImages($sessionId);

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


	// --- Get Helical Data
	if ($hiprunIds = $particle->getHipRunIds($sessionId)) {
		$hipruns=count($hiprunIds);
	}

	// --- Get TiltSeries Data
	if ($tiltseries = $particle->getTiltSeries($sessionId)) {
		$tiltruns=count($tiltseries);
	}
	if ($fulltomograms = $particle->getFullTomogramsFromSession($sessionId)) {
		$fulltomoruns=count($fulltomograms);
	}
	if ($etomoruns = $particle->getUnfinishedETomoRunsFromSession($sessionId)) {
		$etomo_sample=count($etomoruns);
	};
	if ($tomograms = $particle->getTomogramsFromSession($sessionId)) {
		$tomoruns=count($tomograms);
	}
	if ($avgtomograms = $particle->getAveragedTomogramsFromSession($sessionId)) {
		$avgtomoruns=count($avgtomograms);
	}

	// display the direct detector menu
	// TODO: would be nice to hide this if there is a way to see if the data is not DD
	if (true) {
		$action = "Direct Detector Tools";

		// TODO: Add results
		// get tomography auto reconstruction stats:
		$ddresults = array();
		$dddone = count($subclusterjobs['makeddrawframestack']['done']);
		$ddrun = count($subclusterjobs['makeddrawframestack']['running']);
		$ddq = count($subclusterjobs['makeddrawframestack']['queued']);
		$ddresults[] = ($dddone==0) ? "" : "<a href='rawFrameStackReport.php?expId=$sessionId'>$dddone complete</a>";
		$ddresults[] = ($ddrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makeddrawframestack'>$ddrun running</a>";
		$ddresults[] = ($ddq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=makeddrawframestack'>$ddq queued</a>";

		$ddStackform = "MakeDDStackForm";

		$rppresults = array();
		$rppdone = count($subclusterjobs['particlepolishing']['done']);
		$rpprun = count($subclusterjobs['particlepolishing']['running']);
		$rppq = count($subclusterjobs['particlepolishing']['queued']);
		$rppresults[] = ($rppdone==0) ? "" : "<a href='rppReport.php?expId=$sessionId'>$rppdone complete</a>";
		$rppresults[] = ($rpprun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=particlepolishing'>$rpprun running</a>";
		$rppresults[] = ($rppq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=particlepolishing'>$rppq queued</a>";
		$rppform = "rubinsteinParticlePolisher";


		$nruns=array();
		// append (array_push) to nruns
		if (defined('FRAME_TRANSFER_BY_USER') && FRAME_TRANSFER_BY_USER) {
			$nruns[] = array(
				'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=launchFrameTransfer'>Launch Frame Transfer</a>",
			);
		}

		$nruns[] = array(
      'name'=>"<a href='selectFrameAlignment.php?expId=$sessionId'>Select Frame Alignment</a>",
		  'result'=>$ddresults,
		);

		if ($dddone || $ddrun)	{
			$nruns[] = array(
				'name'=>"<a href='runCatchupDDAlign.php?expId=$sessionId'>Launch Alignment Catchup</a>",
			);
		}

		$data[] = array(
			'action' => array($action, $celloption),
			'newrun' => array($nruns, $celloption),
		);
	}

	$action = "Region Mask Creation";
	$result = ($maskruns==0) ? "" :
			"<a href='maskreport.php?expId=$sessionId'>$maskruns</a>";
	$nruns=array();

	// Automated Masking
	$results=array();
	$cruddone = count($subclusterjobs['maskmaker']['done']);
	$crudrun = count($subclusterjobs['maskmaker']['running']);
	$crudqueued = count($subclusterjobs['maskmaker']['queued']);

	// We can get an inflated count for done if the same job was run more than once.
	// Not sure yet if $maskruns is for all methods of mask making or just this one...
	if ( $maskruns < $cruddone )  {
		$cruddone = $maskruns;
	}

	$results[] = ($cruddone==0) ? "" : "<a href='maskreport.php?expId=$sessionId'>$cruddone complete</a>";
	$results[] = ($crudrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=maskmaker'>$crudrun running</a>";
	$results[] = ($crudqueued==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=maskmaker'>$crudqueued queued</a>";

	$nrun = "<a href='manualMaskMaker.php?expId=$sessionId'>Run Manual Masking</a>";
	$nruns[] = $nrun;

	$nruns[] = array(
		'name'=>"<a href='selectMaskingType.php?expId=$sessionId'>Select Automated Masking</a>",
		'result'=>$results,
	);

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nruns, $celloption),
	);

	/*
	**
	** CTF MENU
	**
	*/

	$action = "CTF Estimation";
	// number of CTF runs was determined above and stored in $ctfruns

	$ace1run = count($subclusterjobs['pyace']['running']);
	$ace1run = count($subclusterjobs['pyace']['running']);
	$ace2run = count($subclusterjobs['ace2']['running']);
	$ace2run += count($subclusterjobs['pyace2']['running']);
	$ctffindrun = count($subclusterjobs['ctfestimate']['running']);

	// just add up all queued
	$ctfqueue = count($subclusterjobs['pyace']['queued']);
	$ctfqueue = count($subclusterjobs['ace2']['queued']);
	$ctfqueue = count($subclusterjobs['pyace2']['queued']);
	$ctfqueue = count($subclusterjobs['ctfestimate']['queued']);

	$ctfresults[] = ($ctfq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace'>$ctfq queued</a>";


	$ctfresults = array();
	$ctfresults[] = ($ctfruns==0) ? "" : "<a href='ctfreport.php?expId=$sessionId'>$ctfruns complete</a>";
	$ctfresults[] = ($ace1run==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace'>$ace1run ACE1 running</a>";
	$ctfresults[] = ($ace2run==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=pyace2'>$ace2run ACE2 running</a>";
	$ctfresults[] = ($ctffindrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=ctfestimate'>$ctffindrun running</a>";
	$ctfresults[] = ($ctfqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId'>$ctfqueue queued</a>";

	$nruns = array();

	$nruns[] = array(
		'name'=>"<a href='selectCtfEstimate.php?expId=$sessionId'>Estimate the CTF...</a>",
		'result'=>$ctfresults,
	);

	if ( $ctfruns > 0 ) {
		$nruns[] = array(
			'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=transferCtf'>Transfer results to another preset</a>",
		);
	}

	if ($loopruns > 0) {
		$nruns[] = array(
			'name'=>"<a href='runLoopAgain.php?expId=$sessionId'>Repeat an image loop run</a>",
		);
	}

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($totresult),
		'newrun' => array($nruns, $celloption),
	);

	/*
	**
	** Object selection
	**
	*/

	$action = "Object Selection";

	// get template picking stats:
	$tresults=array();
	$dresults=array();
	$mresults=array();

	$trun = count($subclusterjobs['templatecorrelator']['running']);
	$tq = count($subclusterjobs['templatecorrelator']['queued']);
	$drun = count($subclusterjobs['dogpicker']['running']);
	$dq = count($subclusterjobs['dogpicker']['queued']);
	$srun = count($subclusterjobs['signature']['running']);
	$sq = count($subclusterjobs['signature']['queued']);
	$mrun = count($subclusterjobs['manualpicker']['running']);
	$mq = count($subclusterjobs['manualpicker']['queued']);
	$crun = count($subclusterjobs['contourpicker']['running']);
	$cq = count($subclusterjobs['contourpicker']['queued']);
	$tiltrun = count($subclusterjobs['tiltalign']['running']);
	$tiltqueue = count($subclusterjobs['tiltalign']['queued']);

	$pickresults[] = ($trun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatecorrelator'>$trun running</a>";
	$pickresults[] = ($tq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatecorrelator'>$tq queued</a>";
	$pickresults[] = ($drun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$drun running</a>";
	$pickresults[] = ($dq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=dogpicker'>$dq queued</a>";
	$pickresults[] = ($srun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=signature'>$srun running</a>";
	$pickresults[] = ($sq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=signature'>$sq queued</a>";
	$pickresults[] = ($mrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mrun running</a>";
	$pickresults[] = ($mq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=manualpicker'>$mq queued</a>";
	$pickresults[] = ($crun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=contourpicker'>$crun running</a>";
	$pickresults[] = ($cq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=contourpicker'>$cq queued</a>";
	$pickresults[] = ($tiltrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tiltalign'>$tiltrun running</a>";
	$pickresults[] = ($tiltqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tiltalign'>$tiltqueue queued</a>";

	// in case weren't submitted by web:
	if ($looprundatas = $particle->getLoopProgramRuns()) {
		$loopruns=count($looprundatas);
	}

	$result = ($prtlruns==0) ? "" :
		"<a href='prtlreport.php?expId=$sessionId'>$prtlruns</a>\n";

	$nrun=array();

	$nrun[] = array(
		'name'=>"<a href='selectObjectPicker.php?expId=$sessionId'>Select Particle Picker...</a>",
		'result'=>($prtlruns==0) ? "" : "<a href='prtlreport.php?expId=$sessionId'>$prtlruns complete</a>",
	);

	if ($loopruns > 0) {
		$nrun[] = array(
			'name'=>"<a href='runLoopAgain.php?expId=$sessionId'>Repeat an image loop run</a>",
		);
	}

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nrun, $celloption),
	);

	if (!HIDE_FEATURE)
	{
		$jobtype = 'contouranalysis';
		$cadone = count($subclusterjobs[$jobtype]['done']);
		$carun = count($subclusterjobs[$jobtype]['running']);
		$caq = count($subclusterjobs[$jobtype]['queued']);
		$caresults[] = ($cadone==0) ? "" : "<a href='sizingsummary.php?expId=$sessionId'>$cadone complete</a>";
		$caresults[] = ($carun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=contouranalysis'>$carun running</a>";
		$caresults[] = ($caq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=contouranalysis'>$caq queued</a>";
		$result = ($cadone==0) ? "" :
			"<a href='sizingsummary.php?expId=$sessionId'>$cadone</a>\n";

		if ($cdone || $cadone) {
			$action = "Shape/Size Analysis";
			$nrun=array();
			$nrun[] = array(
				'name'=>"<a href='analyzeTracedObject.php?expId=$sessionId'>Size analysis</a>",
				'result'=>$caresults,
			);
			$data[] = array(
				'action' => array($action, $celloption),
				'result' => array($result),
				'newrun' => array($nrun, $celloption),
			);
		}
	}

	/*
	**
	** STACK MENU
	**
	*/

	// display the stack menu only if have particles picked
	if ($totalprtlruns > 0) {
		$action = "Stacks";

		// get stack stats:
		$sresults=array();
		$sdone = 0; $srun = 0; $sq = 0;
		$stacktypes = array('makestack', 'makestack2', 'filterstack', 'substack', 'centerparticlestack', 'alignsubstack', 'sortjunkstack');
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

		$totresult = ($stackruns==0) ? "" :
			"<a href='stackhierarchy.php?expId=$sessionId'>$stackruns</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='stackTools.php?expId=$sessionId'>Stack Creation...</a>",
			'result'=>$sresults,
		);

		if ($stackruns > 0) {
			$nruns[] = array(
				'name'=>"<a href='selectDDPerParticleAlignment.php?expId=$sessionId'>Select Per Particle Frame Alignment</a>",
				'result'=>$rppresults,
			);
		}

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
		$alignqueue = count($subclusterjobs['partalign']['queued']);

		$alignresults[] = ($aligndone==0) ? "" : "<a href='alignlist.php?expId=$sessionId'>$alignruns complete</a>";
		$alignresults[] = ($alignrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partalign'>$alignrun running</a>";
		$alignresults[] = ($alignqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=partalign'>$alignqueue queued</a>";

		$nruns=array();

		$nruns[] = array(
			'name'=>"<a href='selectParticleAlignment.php?expId=$sessionId'>Select Particle Alignment...</a>",
			'result'=>$alignresults,
		);

		if ($simplejobs=$particle->getFinishedSIMPLEClusteringJobs($projectId)) {
			$nsimplejobs = count($simplejobs);
		}

		if ($cl2djobs=$particle->getFinishedCL2DJobs($projectId)) {
			$ncl2djobs = count($cl2djobs);
		}

		// an exception is made to CL2D & SIMPLE, because it is treated as an alignment & clustering procedure
		if ($aligndone > 0 || $ncl2djobs > 0 || $nsimplejobs > 0) {
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
				'name'=>"<a href='selectFeatureAnalysis.php?expId=$sessionId'>Run Feature Analysis...</a>",
				'result'=>$analysisresults,
			);

//			if ($analysisdone > 0) {
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
				'name'=>"<a href='analysislist.php?expId=$sessionId'>Run Particle Clustering...</a>",
				'result'=>$clusterresults,
			);
//			}
			// Fix Me: This should be move to after particle alignment
			$nruns[] = "<a href='selectLocalClassificationType.php?expId=$sessionId'>Run MaskItOn</a>";

		}
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
		$tsresults[] = ($tsdone_session==0) ? "" : "<a href='selectTemplateStack.php?expId=$sessionId'>$tsdone_session complete</a>";
		$tsresults[] = ($tsruns==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatestack'>$tsruns running</a>";
		$tsresults[] = ($tsqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=templatestack'>$tsqueue queued</a>";

		if ($aligndone > 0 ) {
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

	/* IMAGIC Angular Reconstitution */
	if (($aligndone >= 1 && $clusterdone >=1) || ($tsdone >= 1)) {
		$OptiModRunsTs = $particle->getAutomatedCommonLinesRunsTs($sessionId);
		$OptiModRunsCs = $particle->getAutomatedCommonLinesRunsCs($sessionId);
		$OptiModdone = count(array_merge((array)$OptiModRunsTs, (array)$OptiModRunsCs));
		$OptiModqueue = count($subclusterjobs['optimod']['queued']);
		$OptiModrun = count($subclusterjobs['optimod']['running']);
		$OptiModresults[] = ($OptiModdone > 0) ? "<a href='OptiModSummary.php?expId=$sessionId'>$OptiModdone complete</a>" : '';
		$OptiModresults[] = ($OptiModrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=optimod'>$OptiModrun running</a>";
		$OptiModresults[] = ($OptiModqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=optimod'>$OptiModqueue queued</a>";
		$nruns[] = array(
			'name'=>"<a href='runOptiMod.php?expId=$sessionId'>OptiMod Common Lines</a>",
			'result'=>$OptiModresults,
		);
	}

	/* EMAN Common Lines */
	if ($aligndone >= 1 ) {
		$clinesdone = count($subclusterjobs['createModel']['done']);
		$clinesqueue = count($subclusterjobs['createModel']['queued']);
		$clinesrun = count($subclusterjobs['createModel']['running']);
		$clinesresults[] = ($clinesdone==0) ? "" : "<a href='densitysummary.php?expId=$sessionId&jobtype=createModel'>$clinesdone complete</a>";
		$clinesresults[] = ($clinesrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=createModel'>$clinesrun running</a>";
		$clinesresults[] = ($clinesqueue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=createModel'>$clinesqueue queued</a>";
		$nruns[] = array(
			'name'=>"<a href='createmodel.php?expId=$sessionId'>EMAN Common Lines</a>",
			'result'=>$clinesresults,
		);

	}

	if (!HIDE_FEATURE)
	{
		/* SIMPLE Common Lines */
		// TODO: change the jobtype below for simple
		if ($aligndone >= 1 ) {
			$simpledone = count($subclusterjobs['abinitio']['done']);
			$simplequeue = count($subclusterjobs['abinitio']['queued']);
			$simplerun = count($subclusterjobs['abinitio']['running']);
			$simpleresults[] = ($simpledone==0) ? "" : "<a href='simpleCommonLinesSummary.php?expId=$sessionId&jobtype=abinitio'>$simpledone complete</a>";
			$simpleresults[] = ($simplerun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=abinitio'>$simplerun running</a>";
			$simpleresults[] = ($simplequeue==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=abinitio'>$simplequeue queued</a>";
			$nruns[] = array(
				'name'=>"<a href='runSimple.php?expId=$sessionId'>SIMPLE Common Lines</a>",
				'result'=>$simpleresults,
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

	// --- Refine Reconstruction Menu Section --- //

	// display reconstructions only if there is a stack
	if ($stackruns > 0) {
		$action = "Refine Reconstruction";
		$nruns=array();

		// Single Model Refinement stats

		$refineJobsSM 		= new RefineJobsSingleModel($expId);

		// prep recon stats
		$prepRefineQueue	= $refineJobsSM->countPrepRefineQueue();
		$prepRefineRun		= $refineJobsSM->countPrepRefineRun();
		$prepRefineDone 	= $refineJobsSM->countRefinesReadyToRun();
		$runRefineResults[] = ($prepRefineQueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=single'>$prepRefineQueue preps queued</a>" : "";
		$runRefineResults[] = ($prepRefineRun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$prepRefineRun preps running</a>" : "";
		$runRefineResults[] = ($prepRefineDone>0) ? "<a href='selectPreparedRecon.php?expId=$sessionId&type=single'>$prepRefineDone jobs ready to run</a>" : "";

		// run recon stats
		$refineQueue		= $refineJobsSM->countRunRefineQueue();
		$refineRun			= $refineJobsSM->countRunRefineRun();
		$refineReadyUpload  = $refineJobsSM->countRefinesReadyToUpload();
		$runRefineResults[] = ($refineQueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=single'>$refineQueue jobs queued</a>" : "";
		$runRefineResults[] = ($refineRun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$refineRun jobs running</a>" : "";
		$runRefineResults[] = ($refineReadyUpload>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=single'>$refineReadyUpload ready for upload</a>" : "";

		// upload recon stats
		$uploadQueue		= $refineJobsSM->countUploadRefineQueue();
		$uploadRun			= $refineJobsSM->countUploadRefineRun();
		$refinesComplete	= $refineJobsSM->countUploadRefineDone();
		$runRefineResults[] = ($uploadQueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=single'>$uploadQueue uploads queued</a>" : "";
		$runRefineResults[] = ($uploadRun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$uploadRun uploads running</a>" : "";
		$runRefineResults[] = ($refinesComplete>0) ? "<a href='reconsummary.php?expId=$sessionId'>$refinesComplete complete</a>" : "";

		// insert menu
		$nruns[] = array(
			'name'=>"<a href='selectRefinementType.php?expId=$sessionId'>Run Single-Model Refinement...</a>",
			'result'=> $runRefineResults,
		);

		// Multi Model Refinement stats

		$refineJobsMM = new RefineJobsMultiModel($expId);

		// prep recon stats
		$prepRefineMMQueue		= $refineJobsMM->countPrepRefineQueue();
		$prepRefineMMRun		= $refineJobsMM->countPrepRefineRun();
		$prepRefineMMDone		= $refineJobsMM->countRefinesReadyToRun();
		$runMultiRefineResults[] = ($prepRefineMMQueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=multi'>$prepRefineMMQueue preps queued</a>" : "";
		$runMultiRefineResults[] = ($prepRefineMMRun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$prepRefineMMRun preps running</a>" : "";
		$runMultiRefineResults[] = ($prepRefineMMDone>0) ? "<a href='selectPreparedRecon.php?expId=$sessionId&type=multi'>$prepRefineMMDone jobs ready to run</a>" : "";

		// run recon stats
		$refineMMQueue			= $refineJobsMM->countRunRefineQueue();
		$refineMMRun			= $refineJobsMM->countRunRefineRun();
		$refineReadyUploadMM 	= $refineJobsMM->countRefinesReadyToUpload();
		$runMultiRefineResults[] = ($refineMMQueue>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=multi'>$refineMMQueue jobs queued</a>" : "";
		$runMultiRefineResults[] = ($refineMMRun>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$refineMMRun jobs running</a>" : "";
		$runMultiRefineResults[] = ($refineReadyUploadMM>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=multi'>$refineReadyUploadMM ready for upload</a>" : "";

		// upload recon stats
		$uploadQueueMM			= $refineJobsMM->countUploadRefineQueue();
		$uploadRunMM			= $refineJobsMM->countUploadRefineRun();
		$refinesCompleteMM  	= $refineJobsMM->countUploadRefineDone();
		$runMultiRefineResults[] = ($uploadQueueMM>0) ? "<a href='checkRefineJobs.php?expId=$sessionId&type=multi'>$uploadQueueMM uploads queued</a>" : "";
		$runMultiRefineResults[] = ($uploadRunMM>0) ? "<a href='listAppionJobs.php?expId=$sessionId'>$uploadRunMM uploads running</a>" : "";
		$runMultiRefineResults[] = ($refinesCompleteMM>0) ? "<a href='reconsummarymulti.php?expId=$sessionId'>$refinesCompleteMM complete</a>" : "";

		// Insert Menu
		/*$nruns[] = array(
			'name'=>"<a href='selectMultiModelRefine.php?expId=$sessionId'>Run Multi-Model Refinement...</a>",
			'result'=> $runMultiRefineResults,
		);
		*/

		// This seems to cause terrible things to happen every now and then. Not sure why, but it is not really needed
		// so it is commented out for now.
	
//		$nruns[] = array(
//			'name'=>"<a href='evilClusterUsers.php?expId=$sessionId'>Evil Cluster Users</a>",
//		);


		// --- Get Relion3DRefine Data
		if ($relion3dRefineIds = $particle->getRunIdsFilter($sessionId,'ApSelectionRunData','program','relion',True)) {
			$totalRelion3dRefineRuns=count($relion3dRefineIds);
		}
		if ($relion3dRefineIds = $particle->getRunIdsFilter($sessionId,'ApSelectionRunData','program','relion',False)){
			$relion3dRefineRuns=count($relion3dRefineIds);
		}

		        $form = "uploadRelion3DRefineForm";
		//                echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=$form'>
		$nruns[] = array(
			'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=$form'>Upload Relion 3D Refine</a>",
			'result'=>($relion3dRefineRuns==0) ? "" : "<a href='relion3drefinelistreport.php?expId=$sessionId'>$relion3dRefineRuns complete</a>",
		);


		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array(),
			'newrun' => array($nruns, $celloption),
		);
	}

	//HELICAL PROCESSSING removed in 3.3

	// display the tomography menu only if there are tilt series
	if ($tiltruns > 0) {
		$action = "Tomography (Protomo2)";

		// get tomography auto reconstruction stats:
		$tarresults=array();
		$tardone = count($subclusterjobs['tomoautorecon']['done']);
		$tarrun = count($subclusterjobs['tomoautorecon']['running']);
		$tarq = count($subclusterjobs['tomoautorecon']['queued']);
		$tarresults[] = ($tardone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tardone complete</a>";
		$tarresults[] = ($tarrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoautorecon'>$tarrun running</a>";
		$tarresults[] = ($tarq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoautorecon'>$tarq queued</a>";

		// get tomogram upload stats:
		$utresults=array();
		$utdone = count($subclusterjobs['uploadtomo']['done']);
		$utrun = count($subclusterjobs['uploadtomo']['running']);
		$utq = count($subclusterjobs['uploadtomo']['queued']);
		$utresults[] = ($utdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$utdone complete</a>";
		$utresults[] = ($utrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$utrun running</a>";
		$utresults[] = ($utq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$utq queued</a>";

		// get tilt series alignment stats:

		$projectId   = getProjectId();
		$sessiondata = getSessionList( $projectId, $sessionId );
		$sessioninfo = $sessiondata['info'];
		if (!empty($sessioninfo)) {
			$sessionname = $sessioninfo['Name'];
			$sessionpath = $sessioninfo['Image path'];
			$sessionpath = getBaseAppionPath($sessioninfo);
			$sessionpath = $sessionpath.'/protomo_alignments';
		}
		if (isset($_GET['outdir'])) {
			$sessionpath = $_GET['outdir'];
		} elseif (isset($_POST['outdir'])) {
			$sessionpath = $_POST['outdir'];
		}
		
		$tiltseries_runs = glob("$sessionpath/*/series[0-9][0-9][0-9][0-9].tlt");
		$tadone = count($tiltseries_runs);
		if ($tadone > 0){
			$taresults[] = "<a href='protomoalignrunsummary.php?expId=$sessionId&outdir=$sessionpath'>$tadone runs processing/done (vids)</a>";
			$taresults2[] = "<a href='protomoalignrunsummary.php?expId=$sessionId&outdir=$sessionpath&videos=off'>$tadone runs processing/done (no vids)</a>";
		}
		
		// get full tomogram making stats:
		$tmresults=array();
		$tmdone = $fulltomoruns - $etomo_sample;
		$tmrun = count($subclusterjobs['tomomaker']['running']);
		$tmq = count($subclusterjobs['tomomaker']['queued']);
		$tmresults[] = ($tmdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tmdone complete</a>";
		$tmresults[] = ($tmrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$tmrun running</a>";
		$tmresults[] = ($tmq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$tmq queued</a>";
		$tmresults[] = ($etomo_sample==0) ? "" : "<a href='runETomoMaker.php?expId=$sessionId'>$etomo_sample ready for eTomo</a>";
		// get subtomogram making stats:
		$stresults=array();
		$stdone = $tomoruns;
		$strun = count($subclusterjobs['subtomomaker']['running']);
		$stq = count($subclusterjobs['subtomomaker']['queued']);
		$stresults[] = ($stdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$stdone complete</a>";
		$stresults[] = ($strun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$strun running</a>";
		$stresults[] = ($stq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$stq queued</a>";

		// tomograms being created and completed
		$tottomo = $tmdone+$tmrun+$tmq;

		$tottomo = ($tottomo > $tomoruns+$fulltomoruns) ? $tottomo : $tomoruns+$fulltomoruns;
		$totresult = ($tottomo==0) ? "" :
			"<a href='tomosummary.php?expId=$sessionId'>$fulltomoruns/$tomoruns</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='selectAlignTiltSeries.php?expId=$sessionId'>Align Tilt-Series</a>",
			'result'=>$taresults,
		);
		$nruns[] = array(
			'name'=>"<a href='selectBatchAlignTiltSeries.php?expId=$sessionId'>Batch Align Tilt-Series</a>",
			'result'=>$taresults2,
		);
		$nruns[] = array(
			'name'=>"<a href='selectMoreTiltSeriesProcessing.php?expId=$sessionId''>More Tilt-Series Processing</a>",
		);
		

		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array($totresult),
			'newrun' => array($nruns, $celloption),
		);
	}

	// display the tomography menu only if there are tilt series
	if ($tiltruns > 0) {
		$action = "Tomography(non-Protomo2)";

		// get tomography auto reconstruction stats:
		$tarresults=array();
		$tardone = count($subclusterjobs['tomoautorecon']['done']);
		$tarrun = count($subclusterjobs['tomoautorecon']['running']);
		$tarq = count($subclusterjobs['tomoautorecon']['queued']);
		$tarresults[] = ($tardone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tardone complete</a>";
		$tarresults[] = ($tarrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoautorecon'>$tarrun running</a>";
		$tarresults[] = ($tarq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoautorecon'>$tarq queued</a>";

		// get tomogram upload stats:
		$utresults=array();
		$utdone = count($subclusterjobs['uploadtomo']['done']);
		$utrun = count($subclusterjobs['uploadtomo']['running']);
		$utq = count($subclusterjobs['uploadtomo']['queued']);
		$utresults[] = ($utdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$utdone complete</a>";
		$utresults[] = ($utrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$utrun running</a>";
		$utresults[] = ($utq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$utq queued</a>";

		// get tilt series shift-only alignement stats:
		$tsaresults=array();
		$tsadone = count($subclusterjobs['tomoaligner']['done']);
		$tsadone = count($particle->getTomoAlignmentRunsFromSession($sessionId, False));
		$tsarun = count($subclusterjobs['tomoaligner']['running']);
		$tsaq = count($subclusterjobs['tomoaligner']['queued']);
		$tsaresults[] = ($tsadone==0) ? "" : "<a href='tomoalignrunsummary.php?expId=$sessionId'>$tsadone complete</a>";
		$tsaresults[] = ($tsarun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoaligner'>$tarun running</a>";
		$tsaresults[] = ($tsaq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomoaligner'>$tsaq queued</a>";

		// get full tomogram making stats:
		$tmresults=array();
		$tmdone = $fulltomoruns - $etomo_sample;
		$tmrun = count($subclusterjobs['tomomaker']['running']);
		$tmq = count($subclusterjobs['tomomaker']['queued']);
		$tmresults[] = ($tmdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$tmdone complete</a>";
		$tmresults[] = ($tmrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$tmrun running</a>";
		$tmresults[] = ($tmq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=tomomaker'>$tmq queued</a>";
		$tmresults[] = ($etomo_sample==0) ? "" : "<a href='runETomoMaker.php?expId=$sessionId'>$etomo_sample ready for eTomo</a>";
		// get subtomogram making stats:
		$stresults=array();
		$stdone = $tomoruns;
		$strun = count($subclusterjobs['subtomomaker']['running']);
		$stq = count($subclusterjobs['subtomomaker']['queued']);
		$stresults[] = ($stdone==0) ? "" : "<a href='tomosummary.php?expId=$sessionId'>$stdone complete</a>";
		$stresults[] = ($strun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$strun running</a>";
		$stresults[] = ($stq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=uploadtomo'>$stq queued</a>";

		// tomograms being created and completed
		$tottomo = $tmdone+$tmrun+$tmq;

		$tottomo = ($tottomo > $tomoruns+$fulltomoruns) ? $tottomo : $tomoruns+$fulltomoruns;
		$totresult = ($tottomo==0) ? "" :
			"<a href='tomosummary.php?expId=$sessionId'>$fulltomoruns/$tomoruns</a>";

		$nruns=array();
		$nruns[] = array(
			'name'=>"<a href='runTomoAutoRecon.php?expId=$sessionId'>Auto align+reconstruction</a>",
			'result'=>$tarresults,
		);
		$nruns[] = array(
			'name'=>"<a href='runTomoAligner.php?expId=$sessionId'>Align Tilt-Series(Shift-only)</a>",
			'result'=>$tsaresults,
		);
		$nruns[] = array(
			'name'=>"<a href='runTomoMaker.php?expId=$sessionId'>Create full tomogram</a>",
			'result'=>$tmresults,
		);
		$nruns[] = array(
			'name'=>"<a href='uploadtomo.php?expId=$sessionId'>Upload tomogram</a>",
			'result'=>$utresults,
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

	/* 3d Density Volumes */
	if ($threedvols = $particle->get3dDensitysFromSession($sessionId)) {
		$num3dvols = count($threedvols);
	}
	if ($num3dvols >= 1) {
		$totresult = ($num3dvols>0) ? "<a href='densitysummary.php?expId=$sessionId'>$num3dvols</a>" : "";
		$nruns[] = array(
			'name'=>"<a href='densitysummary.php?expId=$sessionId'>3D Densities</a>",
			'result'=>"<a href='densitysummary.php?expId=$sessionId'>$num3dvols ready to upload</a>",
		);
	}

	if ($leginondata->onlyUploadedImagesInSession($sessionId)) {
	$nruns[] = array(
		'name'=>"<a href='uploadimage.php?expId=$sessionId'>Upload more images</a>",
	);
	}

	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=UploadCtf'>Upload CTF</a>",
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

	$nruns[] = array(
		'name'=> "<a href='uploadTemplateStack.php?expId=$sessionId'>Upload template stack</a>",
		'result'=> ($tsdone_session==0) ? "" : "<a href='selectTemplateStack.php?expId=$sessionId'>$tsdone_session complete</a>",
	);
	
	$nruns[] = array(
		'name'=>"<a href='uploadstack.php?expId=$sessionId'>Upload stack</a>",
	);
	$nruns[] = array(
		'name'=>"<a href='selectStackForm.php?expId=$sessionId&method=external'>Upload reconstruction</a>",
	);

	$nruns[] = array(
		'name'=>"<a href='pdb2density.php?expId=$sessionId'>PDB to map</a>"
	);

	$nruns[] = array(
		'name'=>"<a href='emdb2density.php?expId=$sessionId'>EMDB to map</a>"
	);

	$result = ($models==0) ? "" :
		"<a href='viewmodels.php?expId=$sessionId'>$models available</a>";

	$nruns[] = array(
		'name'=>"<a href='uploadmodel.php?expId=$sessionId'>Upload model</a>",
		'result'=>$result,
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
	$nruns[] = "<a href='runAppionLoop.php?expId=$sessionId&form=imgRejector2Form'>Run Image Rejector</a>";
	$nruns[] = "<a href='imgassessor.php?expId=$sessionId'>Web Img Assessment</a>";
	$nruns[] = "<a href='multiimgassessor.php?expId=$sessionId'>Multi Img Assessment</a>";

	$data[] = array(
		'action' => array($action, $celloption),
		'result' => array($result),
		'newrun' => array($nruns, $celloption),
	);


	// Synthetic Data
	$action = "Synthetic Data";
	if ($models != 0) {
		$synresults=array();
		$syndone = count($subclusterjobs['syntheticdata']['done']);
		$synrun = count($subclusterjobs['syntheticdata']['running']);
		$synq = count($subclusterjobs['syntheticdata']['queued']);

		$synresults[] = ($syndone==0) ? "" : "<a href='stackhierarchy.php?expId=$sessionId&syntheticOnly=True'>$syndone complete</a>";
		$synresults[] = ($synrun==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=syntheticdata'>$synrun running</a>";
		$synresults[] = ($synq==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=syntheticdata'>$synq queued</a>";

		// synthetic stacks being created and stacks completed
		$totsynstack = $syndone+$synrun+$synq;

		$totsynresult = ($totsynstack==0) ? "" :
			"<a href='stackhierarchy.php?expId=$sessionId&syntheticOnly=True'>$totsynstack</a>";

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

	// Clean Data
	$action = "Clean Up";
	$nruns=array();
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=deleteHidden'>Remove Hidden Images</a>",
		);
	
	$data[] = array(
		'action' => array($action, $celloption),
		'newrun' => array($nruns, $celloption),
	);

// FIBSEM Tools
	$action = "FIBSEM Tools";
	$nruns=array();
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=fibsem_MakeStackForm'>Make Inital Stack</a>",
		);
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=fibsem_ClipStackForm'>Select Subtack</a>",
		);
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=fibsem_AlignStackForm'>Align Stack</a>",
		);
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=fibsem_GenerateStackForm'>Generate Aligned Stack</a>",
		);
	$nruns[] = array(
		'name'=>"<a href='runAppionLoop.php?expId=$sessionId&form=fibsem_DewarpStackForm'>Dewarp Stack</a>",
		);
	
	$data[] = array(
		'action' => array($action, $celloption),
		'newrun' => array($nruns, $celloption),
	);


	// Automated Software Testing

	// $TEST_SESSIONS is defined in config.php. It is an array containing the session name
	// of each session that has a test file available. The test files should be named "test_sessionname.py",
	// where sessionname is included in the $TEST_SESSIONS list.
	global $TEST_SESSIONS;
	if ( isset($TEST_SESSIONS) ) {
		$bTestSession = in_array( $sessioninfo["Name"], $TEST_SESSIONS );
	} else {
		$bTestSession = False;
	}

	if ( !HIDE_TEST_TOOLS && $bTestSession ){
		// Add a menu header
		$action = "Testing Tools";

		// Find number of complete, running and queued jobs
		$results=array();

		$done = count($subclusterjobs['testsuite']['done']);
		$running = count($subclusterjobs['testsuite']['running']);
		$queued = count($subclusterjobs['testsuite']['queued']);

		$results[] = ($done==0) ? "" : "<a href='testsuitereport.php?expId=$sessionId'>$done complete</a>";
		$results[] = ($running==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=testsuite'>$running running</a>";
		$results[] = ($queued==0) ? "" : "<a href='listAppionJobs.php?expId=$sessionId&jobtype=testsuite'>$queued queued</a>";

		// Add a menu option
		$nruns = array();
		$nruns[] = array(
			'name' => "<a href='runTestScript.php?expId=$sessionId'>Run Test Script</a>",
			'result' => $results,
		);

		$data[] = array(
			'action' => array($action, $celloption),
			'result' => array(),
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
		$menuprocesing.=addSubmenu($menu['newrun'][0], $expId, $projectId);
	}

	function addMenu($title) {
		$html = '<span class="title" id="top"><img src="../img/lvmenu/expanded.gif" class="arrow" alt="-" />'
		.$title
		.'</span>';
		return $html;
	}

	function addSubmenu($data, $expId, $projectId) {
		//	Deciding on the submenu from ExptAdmin privilege to data
		if ($expId) {
			$allow_process = hasExptAdminPrivilege($expId,'data');
		} elseif ($projectId)
			$allow_process = checkProjectExptAdminPrivilege($projectId,'data');
		else
			$allow_process = false;
		$text="<ul>";
		// print out the title of the subfunction
		foreach((array)$data as $submenu) {
			if (is_array($submenu)) {
				// Users not allowed to process will not get url links
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
