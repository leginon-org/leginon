<?php

/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see	http://ami.scripps.edu/software/leginon-license
 */

if (DB_HOST == 'DB_HOST') require_once "../config.php";
require_once "config_processing.php";

define('PARTICLE_DB_HOST', $PROCESSING_DB_HOST);
define('PARTICLE_DB_USER', $PROCESSING_DB_USER);
define('PARTICLE_DB_PASS', $PROCESSING_DB_PASS);

class particledata {

	var $crlf="\n";
	var $baseurl=PROCESSING_BASE_URL;

	function particledata () {
		$this->mysql = new mysql(
					PARTICLE_DB_HOST,
					PARTICLE_DB_USER,
					PARTICLE_DB_PASS,
					PARTICLE_DB);
	}

	function getPathFromId ($pathId) {
		$q = "SELECT "
			."p.path AS path "
			."FROM ApPathData as p "
			."WHERE "
			."  p.`DEF_id` = '$pathId' "
			."LIMIT 1 ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		$path = $r[0]['path'];
		//echo "$path<br/><br/>\n";
		return $path;
	}

	function getSessionData ($sessionId) {
		$q = "SELECT "
			."s.* "
			."FROM ".DB_LEGINON.".SessionData as s "
			."WHERE "
			."  s.`DEF_id` = ".$sessionId." ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r[0];
	}

	//------ -------------------- ---------//
	//------ General DB summary functions ---------//
	//------ -------------------- ---------//

	function getTotalAceStats(){
		$q = "SELECT count(DISTINCT `REF|ApAceRunData|acerun`) AS runs, "
			."COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS img "
			."FROM `ApCtfData` ";
		$r = $this->mysql->getSQLResult($q);
		$results = $r[0];
		$q = "SELECT COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) as i "
			."FROM `ApCtfData` "
			."WHERE (`confidence`>=0.8 OR `confidence_d`>=0.8)";
		$r = $this->mysql->getSQLResult($q);
		$results['conf']=$r[0]['i'];
		$q = "SELECT COUNT(DISTINCT `REF|leginondata|SessionData|session`) as i "
			."FROM `ApAceRunData` ";
		$r = $this->mysql->getSQLResult($q);
		$results['sessions']=$r[0]['i'];
		return $results;
	}

	function getTotalParticleStats(){
		$q = "SELECT count(*) AS particles, "
			."COUNT(DISTINCT p.`REF|ApSelectionRunData|selectionrun`) AS runs "
			."FROM `ApSelectionRunData` AS s "
			."LEFT JOIN `ApParticleData` AS p "
			."ON s.`DEF_id` = p.`REF|ApSelectionRunData|selectionrun` ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSloppyTotalParticleStats(){
		$q = "SELECT count(*) AS runs, "
			."COUNT(DISTINCT `REF|ApDogParamsData|dogparams`) AS dog, "
			."COUNT(DISTINCT `REF|ApManualParamsData|manparams`) AS manual, "
			."COUNT(DISTINCT `REF|ApTiltAlignParamsData|tiltparams`) AS tilt, "
			."COUNT(DISTINCT `REF|leginondata|SessionData|session`) AS sessions "
			."FROM `ApSelectionRunData`";
		$r = $this->mysql->getSQLResult($q);
		$results = $r[0];
		$q = "SELECT count(`DEF_id`) AS p, "
			."COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS i "
			."FROM `ApParticleData`";
		$r = $this->mysql->getSQLResult($q);
		$results['particles']=$r[0]['p'];
		$results['imgs']=$r[0]['i'];
		return $results;
	}

	function getTotalStackStats(){
		$q = "SELECT count(*) AS particles, "
			."COUNT(DISTINCT p.`REF|ApStackData|stack`) AS stacks "
			."FROM `ApStackData` AS s "
			."LEFT JOIN `ApStackParticlesData` AS p "
			."ON s.`DEF_id` = p.`REF|ApStackData|stack` ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSloppyTotalStackStats(){
		$q = "SELECT count(*) AS s "
			."FROM `ApStackData`";
		$r = $this->mysql->getSQLResult($q);
		$results=array();
		$results['stacks']=$r[0]['s'];
		$q = "SELECT count(*) AS p "
			."FROM `ApStackParticlesData`";
		$r = $this->mysql->getSQLResult($q);
		$results['particles']=$r[0]['p'];
		return $results;
	}

	function getTotalReconStats(){
		$q = "SELECT count(*) AS particles, "
			."COUNT(DISTINCT p.`REF|ApRefinementData|refinement`) AS iter, "
			."COUNT(DISTINCT i.`REF|ApRefinementRunData|refinementRun`) AS runs "
			."FROM `ApRefinementData` AS i "
			."LEFT JOIN `ApParticleClassificationData` AS p "
			."ON i.`DEF_id` = p.`REF|ApRefinementData|refinement` ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSloppyTotalReconStats(){
		$q = "SELECT count(*) AS i "
			."FROM `ApRefinementData`";
		$r = $this->mysql->getSQLResult($q);
		$results=array();
		$results['iter']=$r[0]['i'];
		$q = "SELECT count(*) AS p "
			."FROM `ApParticleClassificationData`";
		$r = $this->mysql->getSQLResult($q);
		$results['particles']=$r[0]['p'];
		$q = "SELECT count(*) AS r "
			."FROM `ApRefinementRunData`";
		$r = $this->mysql->getSQLResult($q);
		$results['runs']=$r[0]['r'];
		return $results;
	}

	function getTotalTemplates(){
		$q = "SELECT count(*) AS templates "
			."FROM ApTemplateImageData";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getTotalModels(){
		$q = "SELECT count(*) AS models "
			."FROM ApInitialModelData";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	//------ -------------------- ---------//
	//------ Tomo functions ---------//
	//------ -------------------- ---------//

	function getTomoAlignmentRunsFromSession($sessionId,$showHidden=False){
		if (!$this->mysql->SQLTableExists("ApTomoAlignmentRunData")) return;
		$q =  "SELECT a.`DEF_id` as `alignrunid`, "
			."t.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries "
			."FROM `ApTomoAlignmentRunData` a "
			."LEFT JOIN `ApTiltsInAlignRunData` t "
			."ON t.`REF|ApTomoAlignmentRunData|alignrun` = a.`DEF_id` "
			."WHERE a.`REF|leginondata|SessionData|session` = " .$sessionId." ";
		$fields = $this->mysql->getFields('ApTomoAlignmentRunData');
		if (!$showHidden && in_array('hidden',$fields))
			$q .= " AND ( a.`hidden` = 0 OR a.`hidden` IS NULL ) ";
		$q .= "ORDER BY `tiltseries` ASC ";
		$results = $this->mysql->getSQLResult($q);
		if (count(array($results))) {
			$finalresults = array();
			if ($results) {
				foreach ($results as $result) {
					$info = $this->getTomoAlignmentInfo($result['alignrunid']);
					$result = array_merge($result,$info);
					if ($result['protomoid']) {
						$result['method'] = 'protomo';
					} else {
						if ($result['imodid']) {
							$result['method'] = 'imod';
						} elseif ($result['xleginonid']) {
							$result['method'] = 'leginon';
						} else {
							$result['method'] = 'unknown';
						}
					}
					$finalresults[] = $result;
				}
			}
		} else {
			$finalresults = $results;
		}
		return $finalresults;
	}

	function getTomoAlignmentInfo($alignrunId){
		$q =  "SELECT a.`DEF_id` as `alignrun id`, "
			."a.name as `alignrun name`, "
			."a.bin as bin, "
			."path.`path`, "
			."tilt.`number` as `tilt number`, "
			."tia.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries, ";
		if ($this->mysql->SQLTableExists('ApImodXcorrParamsData')) {
			$q .= "a.`REF|ApImodXcorrParamsData|coarseImodParams` as imodid, "
				."imod.`FilterSigma1` as sigma1, "
				."imod.`FilterSigma2` as sigma2, "
				."imod.`FilterRadius2` as radius2, ";
		}
		$q .= ""
			."a.`REF|leginondata|TomographySettingsData|coarseLeginonParams` as xleginonid, "
			."a.`REF|ApProtomoParamsData|fineProtomoParams` as protomoid, "
			."a.`description`, "
			."a.`hidden` "
			."FROM `ApTomoAlignmentRunData` a "
			."LEFT JOIN `ApPathData` path "
			."ON a.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists('ApImodXcorrParamsData')) {
			$q .= ""
				."LEFT JOIN `ApImodXcorrParamsData` imod "
				."ON a.`REF|ApImodXcorrParamsData|coarseImodParams` = imod.`DEF_id` ";
		}
		$q .= ""
			."LEFT JOIN `ApTiltsInAlignRunData` tia "
			."ON tia.`REF|ApTomoAlignmentRunData|alignrun` = a.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".`TiltSeriesData` tilt ON tia.`REF|leginonData|TiltSeriesData|tiltseries` = tilt.`DEF_id` "
			."WHERE a.`DEF_id` = " .$alignrunId;
		list($r) = $this->mysql->getSQLResult($q);
		if ($r['protomoid']) {
			$r['method'] = 'protomo';
		} else {
			if ($r['imodid']) {
				$r['method'] = 'imod';
				$r['filter sigmas'] = '('.$r['sigma1'].','.$r['sigma2'].')';
				$r['filter radius2'] = $r['radius2'];
				unset($r['sigma1']);
				unset($r['sigma2']);
				unset($r['radius2']);
			} elseif ($r['xleginonid']) {
				$r['method'] = 'leginon';
			} else {
				$r['method'] = 'unknown';
			}
		}
		return $r;
	}

	function getTomoAlignerInfoFromAlignmentRun($alignid,$showiHidden=false) {
		$q = " SELECT a.`DEF_id` as alignerid, "
			." a.`REF|ApTomoAlignmentRunData|alignrun` as `alignrunid`, "
			." a.`REF|ApProtomoRefinementParamsData|refine cycle` as `cycleid`, "
			." a.`REF|ApProtomoRefinementParamsData|good cycle` as `goodid`, "
			." p.`series name`, "
			." f.`cycle` as `refine cycle`, "
			." g.`cycle` as `good cycle`, "
			." f.`alismp` as `align sampling`, "
			." f.`SUBD|alibox|x` as `align box x`, "
			." f.`SUBD|alibox|y` as `align box y`, "
			." f.`cormod`, "
			." f.`imgref`as `refnum`, "
			." f.`REF|leginondata|AcquisitionImageData|reference` as `refimg`, "
			#." f.`imgref` as `imgref number`, "
			." a.* "
			."FROM `ApTomoAlignerParamsData` a "
			."LEFT JOIN `ApProtomoRefinementParamsData` f "
			."ON a.`REF|ApProtomoRefinementParamsData|refine cycle` = f.`DEF_id` "
			."LEFT JOIN `ApProtomoRefinementParamsData` g "
			."ON a.`REF|ApProtomoRefinementParamsData|good cycle` = g.`DEF_id` "
			."LEFT JOIN `ApProtomoParamsData` p "
			."ON a.`REF|ApProtomoParamsData|protomo` = p.`DEF_id` "
			."LEFT JOIN `ApTomoAlignmentRunData` r "
			."ON a.`REF|ApTomoAlignmentRunData|alignrun` = r.`DEF_id` "
			."WHERE r.`DEF_id`=".$alignid." ";
		if (!$showHidden) {
			$q .= " AND ( a.`hidden` = 0 OR a.`hidden` IS NULL ) ";
		}
			$q .= "ORDER BY f.`cycle` ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTomoAlignersFromAlignmentRun($alignid,$showiHidden=false) {
		$q = " SELECT a.`DEF_id` as alignerid "
			."FROM `ApTomoAlignerParamsData` a "
			."LEFT JOIN `ApTomoAlignmentRunData` r "
			."ON a.`REF|ApTomoAlignmentRunData|alignrun` = r.`DEF_id` "
			."WHERE r.`DEF_id`=".$alignid." ";
		if (!$showHidden) {
			$q .= " AND ( a.`hidden` = 0 OR a.`hidden` IS NULL ) ";
		}
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getProtomoAlignmentInfo($alignerid) {
		$q = " SELECT m.`DEF_id` as modelid, "
			." a.`REF|ApTomoAlignerParamsData|aligner` as `alignerid`, "
			." a.`REF|leginondata|AcquisitionImageData|image` as `image`, "
			." a.`number`, "
			." a.`rotation`, "
			." a.`SUBD|shift|x` as `shift x`, "
			." a.`SUBD|shift|y` as `shift y`, "
			." m.`psi`, "
			." m.`theta`, "
			." m.`phi`, "
			." m.`azimuth`, "
			." arun.`DEF_id` as alignrunid, "
			." arun.`name` as runname, "
			." arun.`bin` as bin, "
			." path.`path`, "
			." tilts.`REF|leginondata|TiltSeriesData|tiltseries` as `tiltseries`, "
			." r.* "
			."FROM `ApProtomoAlignmentData` a "
			."LEFT JOIN `ApProtomoModelData` m "
			."ON a.`REF|ApTomoAlignerParamsData|aligner` = m.`REF|ApTomoAlignerParamsData|aligner` "
			."LEFT JOIN `ApTomoAlignerParamsData` ar "
			."ON a.`REF|ApTomoAlignerParamsData|aligner` = ar.`DEF_id` "
			."LEFT JOIN `ApProtomoRefinementParamsData` r "
			."ON ar.`REF|ApProtomoRefinementParamsData|refine cycle` = r.`DEF_id` "
			."LEFT JOIN `ApTomoAlignmentRunData` arun "
			."ON ar.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApTiltsInAlignRunData` tilts "
			."ON tilts.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApPathData` path "
			."ON arun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE ar.`DEF_id`=".$alignerid." "
			."AND tilts.`primary` = 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	function getFullTomogramInfo($tomogramId){
		# check to see if ApFullTomogramRunData is linked.  Old data does not have it.
		$q = "SELECT t.* "
			."FROM `ApFullTomogramData` t "
			."WHERE t.`DEF_id` = " .$tomogramId;
		list($r) = $this->mysql->getSQLResult($q);
		if ($r['REF|ApFullTomogramRunData|reconrun']) $has_run=True;

		$q =  "SELECT t.`DEF_id` as DEF_id, "
			."t.`REF|ApTomoAlignerParamsData|aligner` as aligner, ";
		if ($has_run) {
			$q .= "r.`runname` as runname, ";
			$q .= "r.`method` as `recon method`, ";
		}
		$q .= "t.name as tomofilename, "
			."t.description as description, "
			."t.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries, "
			."tilt.number as 'tiltseries number', "
			." p.`path` as path, "
			." t.`hidden` "
			."FROM `ApFullTomogramData` t ";
		if ($has_run) {
			$q .= "LEFT JOIN `ApFullTomogramRunData` r ON t.`REF|ApFullTomogramRunData|reconrun` = r.`DEF_id` "
				."LEFT JOIN `ApPathData` p ON r.`REF|ApPathData|path` = p.`DEF_id` ";
		} else {
			$q .= "LEFT JOIN `ApPathData` p ON t.`REF|ApPathData|path` = p.`DEF_id` ";
		}
		$q .= "LEFT JOIN ".DB_LEGINON.".`TiltSeriesData` tilt ON t.`REF|leginonData|TiltSeriesData|tiltseries` = tilt.`DEF_id` "
			."WHERE t.`DEF_id` = " .$tomogramId;
		list($r) = $this->mysql->getSQLResult($q);
		if (!$r['runname']) {
			$r['runname'] = array_pop(explode('/',$r['path']));
		}
		return $r;
	}

	function getTomogramInfo($tomogramId){
		$q =  "SELECT t.`DEF_id` as DEF_id, "
			."t.`REF|ApFullTomogramData|fulltomogram` as full, "
			."t.name as name, "
			."t.number as number, "
			."t.pixelsize, "
			."t.description as description, "
			."t.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries, "
			."t.offsetz as offsetz, "
			."t.`SUBD|dimension|x` as dx, "
			."t.`SUBD|dimension|y` as dy, "
			."t.`SUBD|dimension|z` as dz, "
			."tilt.`number` as tiltnumber, "
			."prtl.xcoord as centerx, "
			."prtl.ycoord as centery, "
			."prtl.`REF|leginondata|AcquisitionImageData|image` as prtlimage, "
			." p.`path` "
			."FROM `ApTomogramData` t "
			."LEFT JOIN `ApPathData` p ON t.`REF|ApPathData|path` = p.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".`TiltSeriesData` tilt ON t.`REF|leginonData|TiltSeriesData|tiltseries` = tilt.`DEF_id` "
			."LEFT JOIN `ApParticleData` prtl ON t.`REF|ApParticleData|center` = prtl.`DEF_id` "
			."WHERE t.`DEF_id` = " .$tomogramId;
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTomoCenter($centerx,$centery,$image1id,$tiltseriesid){
		$q = "SELECT "
			.$centerx." + p1.`SUBD|predicted shift|x` - p0.`SUBD|predicted shift|x` as x, "
			.$centery." + p1.`SUBD|predicted shift|y` - p0.`SUBD|predicted shift|y` as y "
			."FROM ".DB_LEGINON.".`TomographyPredictionData` p0 "
			."LEFT JOIN "
			. "(SELECT * "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` image0 "
			."WHERE image0.`REF|TiltSeriesData|tilt series` = ".$tiltseriesid." "
			."ORDER BY image0.`DEF_timestamp` ASC limit 1 ) image0 "
			."ON p0.`REF|AcquisitionImageData|image` = image0.`DEF_id` "
			.", ".DB_LEGINON.".`TomographyPredictionData` p1 "
			."WHERE p1.`REF|AcquisitionImageData|image`=$image1id "
			."";
		list($r) = $this->mysql->getSQLResult($q);
		if (count($r) == 0)
			$r = array(x=>$centerx,y=>$centery);
		return $r;
	}

	function getFullTomogramsFromSession($sessionId,$showHidden=False,$showDummy=False){
		$q =  "SELECT t.`DEF_id` as DEF_id "
			."FROM `ApFullTomogramData` t "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId." ";
		if (!$showDummy)
			$q .= "AND t.name NOT LIKE 'dummy'";
		$fields = $this->mysql->getFields('ApFullTomogramData');
		if (!$showHidden && in_array('hidden',$fields))
			$q .= " AND ( t.`hidden` = 0 OR t.`hidden` IS NULL ) ";
		return $this->mysql->getSQLResult($q);
	}

	function getTomogramsFromSession($sessionId){
		$q =  "SELECT t.`DEF_id` as DEF_id "
			."FROM `ApTomogramData` t "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId;
		return $this->mysql->getSQLResult($q);
	}
	function getSubTomoRunFromStack($stackId){
		$currentstackId = $stackId;
		while (!$r['subtomorunid'] && $currentstackId) {
			$q =  "SELECT `DEF_id` as subtomorunid "
				."FROM `ApSubTomogramRunData` "
				."WHERE `REF|ApStackdata|stack` = " .$currentstackId." "
				."LIMIT 1";
			list($r) = $this->mysql->getSQLResult($q);
			if (!$r['subtomorunid']) {
				$selectionruns = $this->getParticleRunsFromStack($currentstackId);
				if (count($selectionruns) > 1) return;
				$selectionrunid = $selectionruns[0][0]['DEF_id'];
				$q =  "SELECT `DEF_id` as subtomorunid "
					."FROM `ApSubTomogramRunData` "
					."WHERE `REF|ApSelectionRundata|pick` = " .$selectionrunid." "
					."LIMIT 1";
				list($r) = $this->mysql->getSQLResult($q);
			}
			if (!$r['subtomorunid']) {
				$parentstack = $this->getParentStackId($currentstackId);
				$currentstackId = $parentstack['parentid'];
			}
		}
		return $r['subtomorunid'];
	}

	function getOrphanSubTomogramsFromSession($sessionId){
		$q =  "SELECT t.`DEF_id` as DEF_id "
			."FROM `ApTomogramData` t "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId. " "
			."AND t.`REF|ApFullTomogramData|fulltomogram` IS NULL";
		return $this->mysql->getSQLResult($q);
	}

	function getSubTomogramStackIds($sessionId){
		// subtomograms picked by stack
		$q =  "SELECT s.`DEF_id` as stackid, "
			."t.`DEF_id` as subtomorunid, "
			."s.* "
			."FROM `ApSubTomogramRunData` t "
			."LEFT JOIN `ApStackData` s "
			."ON t.`REF|ApStackData|stack` = s.`DEF_id` "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId. " "
			."AND s.`DEF_id` IS NOT NULL "
			." ";
		$r = $this->mysql->getSQLResult($q);
		// subtomograms picked by particle selection (pick)
		$q =  "SELECT s.`DEF_id` as stackid, "
			."sp1.`REF|ApStackData|stack` as oldstackid, "
			."sp1.`REF|ApStackRunData|stackRun` as stackrunid, "
			."pr . `DEF_id` as selectionid, "
			."t. `DEF_id` as subtomorunid, "
			."s.* "
			."FROM ( "
			."SELECT st.*, stpm.`DEF_id` as stackparamsid "
			."FROM `ApStackParticlesData` as st  "
			."LEFT JOIN `ApStackRunData` as str "
			."ON st.`REF|ApStackRunData|stackRun` = str.`DEF_id` "
			."LEFT JOIN `ApStackParamsData` as stpm "
			."ON str.`REF|ApStackParamsData|stackParams` = stpm.`DEF_id` "
			."group by "
			."st.`REF|ApStackRunData|stackRun`  "
			.") sp1  "
			."LEFT JOIN `ApParticleData` p  "
			."ON p .`DEF_id` = sp1 . `REF|ApParticleData|particle`  "
			."LEFT JOIN `ApSelectionRunData` pr ON  "
			."pr . `DEF_id` = p . `REF|ApSelectionRunData|selectionrun` "
			."LEFT JOIN `ApStackData` s "
			."ON s.`REF|ApStackData|oldstack` = sp1.`REF|ApStackData|stack` "
			."LEFT JOIN `ApSubTomogramRunData` t "
			."ON t.`REF|ApSelectionRunData|pick` = pr.`DEF_id` "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId. " "
			."AND s.`DEF_id` IS NOT NULL "
			." ";
		$r1 = $this->mysql->getSQLResult($q);
		$r = array_merge($r,$r1);
		return $r;
	}

	function getAveragedTomogramsFromSession($sessionId,$showHidden=False){
		$q =  "SELECT t.`DEF_id` as `avgid`, "
			."t.`description`, "
			."t.`runname`, "
			."t.`REF|ApStackData|stack` as stackid, "
			."t.`hidden` as hidden, "
			."stack.`substackname` as substackname "
			."FROM `ApTomoAverageRunData` t "
			."LEFT JOIN `ApSubTomogramRunData` sub "
			."ON  t.`REF|ApSubTomogramRunData|subtomorun` = sub.DEF_id "
			."LEFT JOIN `ApStackData` stack "
			."ON  t.`REF|ApStackData|stack` = stack.DEF_id "
			."WHERE sub.`REF|leginondata|SessionData|session` = " .$sessionId." ";
		$fields = $this->mysql->getFields('ApTomoAverageRunData');
		if (!$showHidden && in_array('hidden',$fields))
			$q .= " AND ( t.`hidden` = 0 OR t.`hidden` IS NULL ) ";
		$q .= "ORDER BY `avgid` ASC ";
		return $this->mysql->getSQLResult($q);
	}

	function getAveragedTomogramInfo($avgId){
		$q =  "SELECT avgt.`DEF_id` as `avgid`, "
			."avgt.`description`, "
			."avgt.`runname`, "
			."avgt.`REF|ApStackData|stack` as stackid, "
			."subt.`DEF_id` as `subtomoid`, "
			."sub.`DEF_id` as `subtomorunid`, "
			."path.`path` "
			."FROM `ApTomoAverageRunData` avgt "
			."LEFT JOIN `ApPathData` path "
			."ON avgt.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN `ApSubTomogramRunData` sub "
			."ON  avgt.`REF|ApSubTomogramRunData|subtomorun` = sub.DEF_id "
			."LEFT JOIN `ApStackData` stack "
			."ON  avgt.`REF|ApStackData|stack` = stack.DEF_id "
			."LEFT JOIN `ApStackParticlesData` stackp "
			."ON  stackp.`REF|ApStackData|stack` = stack.DEF_id "
			."LEFT JOIN `ApParticleData` p "
			."ON  stackp.`REF|ApParticleData|particle` = p.DEF_id "
			."LEFT JOIN `ApTomogramData` subt "
			."ON  subt.`REF|ApParticleData|center` = p.DEF_id "
			."LEFT JOIN `ApTomoAvgParticleData` tap "
			."ON  tap.`REF|ApTomoAverageRunData|avgrun` = avgt.DEF_id "
			."WHERE avgt.`DEF_id` = " .$avgId." "
			."AND  tap.`REF|ApTomogramData|subtomo` = subt.DEF_id "
			." ";
		return $this->mysql->getSQLResult($q);
	}

	function getTomoAlignedParticleInfo($avgid,$subtomoid){
		$q =  "SELECT p.`DEF_id` as `alignpid`, "
			."p.`xshift`, "
			."p.`yshift`, "
			."p.`rotation`, "
			."p.`mirror`, "
			."avgtp.`z shift` as zshift, "
			."p.`REF|ApAlignStackData|alignstack` as `alignstack` "
			."FROM `ApTomoAvgParticleData` avgtp "
			."LEFT JOIN `ApTomogramData` sub "
			."ON  avgtp.`REF|ApTomogramData|subtomo` = sub.DEF_id "
			."LEFT JOIN `ApAlignParticlesData` p "
			."ON  avgtp.`REF|ApAlignParticlesData|aligned particle` = p.DEF_id "
			."WHERE avgtp.`REF|ApTomoAverageRunData|avgrun` = " .$avgid." "
			."AND avgtp.`REF|ApTomogramData|subtomo` = ".$subtomoid." ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getsubTomogramsFromFullTomogram($fullId){
		$q =  "SELECT t.`DEF_id` as DEF_id "
			."FROM `ApTomogramData` t "
			."WHERE t.`REF|ApFullTomogramData|fulltomogram` = " .$fullId;
		return $this->mysql->getSQLResult($q);
	}

	function getTiltSeries($sessionId) {
		if($sessionId == NULL)
			return array();
		$query = "SELECT `DEF_id` as id, "
			."UNIX_TIMESTAMP(DEF_timestamp) as timestamp, "
			."`number` "
			."FROM ".DB_LEGINON.".`TiltSeriesData` "
			."WHERE `REF|SessionData|session`=".$sessionId." "
			."ORDER BY DEF_timestamp "
			." ";
		return $this->mysql->getSQLResult($query);
	}

	function getTiltSeriesSelector($tiltSeries, $tiltSeriesId=NULL,$selectname='tiltseriesId') {
		$selector = '<select name="'.$selectname.'" '
				.'size=5 '
				.'onchange=submit()>';
		$length = strlen(count($tiltSeries));
		for ($i = 0; $i < count($tiltSeries); $i++) {
			$series = $tiltSeries[$i];
			# use real series number if exist
			if (!is_null($series['number'])) {
				$number = $series['number'];
			} else {
				$number = $i + 1;
			}
			$selector .= '<option class="fixed" value='.$series['id'];
			if ($series['id'] == $tiltSeriesId) {
				$selector .= ' selected ';
				$selected_number = $number;
			}
			$shownumber = str_pad($number, $length, ' ', STR_PAD_LEFT).'. ';
			$shownumber = str_replace(" ", "&nbsp;", $shownumber);
			$timestamp = date('m/d/y H:i:s', $series['timestamp']);
			$selector .= '>'.$shownumber.$timestamp.'</option>';
		}
		$selector .= '</select>';
		return array($selector,$selected_number);
	}

	function getTomoAlignerSelector($aligners, $alignerId=NULL,$selectname='goodalignerId') {
		$selector = '<select name="'.$selectname.'" '
				.'size=1 '
				.'onchange=submit()>';
		$length = strlen(count($aligners));
		for ($i = 0; $i < count($aligners); $i++) {
			$data = $aligners[$i];
			$aligner = $data['alignerid'];
			$selector .= '<option class="fixed" value='.$i;
			if ($i == $alignerId) {
				$selector .= ' selected ';
				$selected_number = $aligner;
			}
			$shownumber = str_pad($data['refine cycle'], $length, ' ', STR_PAD_LEFT).'. ';
			$shownumber = str_replace(" ", "&nbsp;", $shownumber);
			$selector .= '>'.$shownumber.'sampling@'.$data['align sampling'].'</option>';
		}
		$selector .= '</select>';
		return array($selector,$selected_number);
	}

	function getTomoAlignRunAlignerSelector($aligners, $selectedId=NULL,$selectname='goodalignerId') {
		$selector = '<select name="'.$selectname.'" '
				.'size=1 '
				.'onchange=submit()>';
		$length = strlen(count($aligners));
		for ($i = 0; $i < count($aligners); $i++) {
			$data = $aligners[$i];
			$runinfo = $this -> getTomoAlignmentInfo($data['alignrunid']);
			$alignerid = $data['alignerid'];
			$selector .= '<option class="fixed" value='.$alignerid;
			if ($alignerid == $selectedId) {
				$selector .= ' selected ';
				$selected_aligner = $alignerid;
			}
			if ($runinfo['method'] == 'protomo') {
				if ($data['refine cycle'] != 0) {
					$showmethod = $runinfo['method'];
					$showstr = str_pad(': itr '.$data['refine cycle'], $length, ' ', STR_PAD_LEFT).'. ';
					$showstr = str_replace(" ", "&nbsp;", $showstr);
					$showstr .= ' sampling@'.$data['align sampling'];
				} else {
					$showmethod = 'leginon';
					$showstr = '';
				}
			} else {
				$showmethod = $runinfo['method'];
				$showstr = '';
			}
			$selector .= '>'.$runinfo['alignrun name'].'-'.$showmethod.$showstr.'</option>';
		}
		$selector .= '</select>';
		return array($selector,$selected_aligner);
	}

	function checkforTomogram($tiltseriesId){
		$q =  "SELECT t.name , p.`path` "
			."FROM `ApTomogramData` t "
			."LEFT JOIN `ApPathData` p ON t.`REF|ApPathData|path` = p.`DEF_id` "
			."WHERE t.`REF|leginondata|TiltSeriesData|tiltseries` = " .$tiltseriesId;
		return $this->mysql->getSQLResult($q);
	}

	function checkforFullTomogram($tiltseriesId,$showHidden=False){
		$q =  "SELECT t.`DEF_id`, t.name as `tomofilename` "
			."FROM `ApFullTomogramData` t "
			."WHERE t.`REF|leginondata|TiltSeriesData|tiltseries` = " .$tiltseriesId;
		$r = $this->mysql->getSQLResult($q);
		$result = array();
		if ($r && count($r)) {
			foreach ($r as $full) {
				$fullinfo = $this->getFullTomogramInfo($full['DEF_id']);
				$fullinfo['subtomo'] = $this->countSubTomograms($full['DEF_id']);
				if ($showHidden || !$fullinfo['hidden']) $result[] = $fullinfo;
			}
		}
		return $result;
	}

	function getTiltSeriesInfo($tiltseriesId){
		// get image bin and the most recent pixel calibration
		$q="SELECT pd.`SUBD|binning|x` as imgbin, "
			."pc.`pixelsize` as ccdpixelsize, "
			."a.`REF|SessionData|session` as session, "
			."a.`filename` as filename, "
			."a.`DEF_id` as imageid, "
			."t.`number` as number "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` a "
			."left join ".DB_LEGINON.".`TiltSeriesData` t "
			."on (a.`REF|TiltSeriesData|tilt series`= t.`DEF_id`) "
			."left join ".DB_LEGINON.".`PresetData` pd "
			."on (a.`REF|PresetData|preset`=pd.`DEF_id`) "
			.", ".DB_LEGINON.".`PixelSizeCalibrationData` pc "
			."WHERE a.`REF|TiltSeriesData|tilt series`='$tiltseriesId' "
			."AND pc.`REF|InstrumentData|tem`= pd.`REF|InstrumentData|tem` "
			."AND pc.`magnification`= pd.`magnification` "
			."AND pd.`name` NOT LIKE 'Zproj' "
			."AND "
			."pc.`REF|InstrumentData|ccdcamera`= pd.`REF|InstrumentData|ccdcamera` "
			."AND "
			."pc.`DEF_timestamp`<	a.`DEF_timestamp` "
			."ORDER BY pc.`DEF_timestamp` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;

	}

	function countSubTomograms($fulltomogramId){
		if (!$this->mysql->SQLTableExists("ApTomogramData")) return 0;
		$q="SELECT * "
			."FROM ApTomogramData "
			."WHERE `REF|ApFullTomogramData|fulltomogram`=".$fulltomogramId;
		$r = $this->mysql->getSQLResult($q);
		return count($r);
	}

	function getTomoAlignmentRuns($tiltseriesId){
		$q="SELECT *, "
			."`REF|ApTomoAlignmentRunData|alignrun` as alignrunId "
			."FROM ApTiltsInAlignRunData "
			."WHERE `REF|leginondata|TiltSeriesData|tiltseries`=".$tiltseriesId;
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	function countTomoAlignmentRuns($tiltseriesId){
		$r = $this->getTomoAlignmentRuns($tiltseriesId);
		return ($r)? count($r) : 0;
	}

	function countFullTomograms($tiltseriesId){
		$r = $this->checkforFullTomogram($tiltseriesId,True);
		return ($r)? count($r) : 0;
	}

	function countTomogramsByAlignment($tiltseriesId,$alignrunname){
		$q="SELECT t.* "
			."FROM ApTomoAlignmentRunData a "
			."LEFT JOIN ApFullTomogramData f "
			."on f.`REF|ApTomoAlignmentRunData|alignrun` = a.`DEF_id` "
			."LEFT JOIN ApTomogramData t "
			."on t.`REF|ApFullTomogramData|fulltomogram` = f.`DEF_id` "
			."WHERE a.`REF|leginondata|TiltSeriesData|tiltseries`=".$tiltseriesId." "
			."AND a.name LIKE '".$alignrunname."' ";
		$r = $this->mysql->getSQLResult($q);
		return ($r)? count($r) : 0;
	}

	// --- loads tomo z profile --- //
	function loadTomoZProfile($filename) {
		$data = array();
		if (file_exists($filename)) {
			$lines = file ($filename);
			foreach ($lines as $line) {
				list($k, $v) = explode('	', $line);
				$data[]=trim($v);
			}
		}
		$r = array();
		foreach(array_keys($data) as $i) $r[] = array('z'=>$i,'profile'=>$data[$i]);
		return array($r);
	}

	// ------CTF data functions -------//
	function hasCtfData($sessionId) {
		$d = ($this->getLastCtfRun($sessionId)) ? true : false;
		return $d;
	}

	function hasCtfTiltData($sessionId) {
		$d = ($this->getLastCtfTiltRun($sessionId)) ? true : false;
		return $d;
	}

	function getLastCtfRun($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApAceRunData` where `REF|leginondata|SessionData|session`='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getLastCtfTiltRun($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApCtfTiltRunData` where `REF|leginondata|SessionData|session`='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getCtfRunIds($sessionId, $showHidden=False) {
		$q = "SELECT * "
			."FROM `ApAceRunData` AS a "
			."WHERE "
			."  `REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( a.`hidden` = 0 OR a.`hidden` IS NULL ) ";
		$q .= "ORDER BY a.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getAceParams($acerunId) {
		$q = "SELECT *, path.`path` as path, acerun.`DEF_id` as acerun "
			."FROM ApAceRunData AS acerun "
			."LEFT JOIN ApAceParamsData AS aceparams "
			."  ON (aceparams.`DEF_id` = acerun.`REF|ApAceParamsData|aceparams`) "
			."LEFT JOIN ApCtfTiltParamsData AS ctftilt "
			."  ON (ctftilt.`DEF_id` = acerun.`REF|ApCtfTiltParamsData|ctftilt_params`) "
			."LEFT JOIN ApAce2ParamsData AS ace2params "
			."  ON (ace2params.`DEF_id` = acerun.`REF|ApAce2ParamsData|ace2_params`) "
			."LEFT JOIN ApPathData AS path "
			."  ON (path.`DEF_id` = acerun.`REF|ApPathData|path`) "
			."where acerun.`DEF_id` = '$acerunId'";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		if ($r) return end($r);
	}

	function getCtfInfoWithNominal($sessionId, $runId=false) {
		$q =	"select "
			."c.`REF|leginondata|AcquisitionImageData|image`, "
			."s.`defocus`, "
			."c.`defocus1`, "
			."c.`defocus2`, "
			."c.`defocusinit`, "
			."c.`amplitude_contrast`, "
			."c.`angle_astigmatism`, "
			."c.`noise1`, "
			."c.`noise2`, "
			."c.`noise3`, "
			."c.`noise4`, "
			."c.`envelope1`, "
			."c.`envelope2`, "
			."c.`envelope3`, "
			."c.`envelope4`, "
			."c.`lowercutoff`, "
			."c.`uppercutoff`, "
			."c.`confidence` , "
			."c.`confidence_d` , "
			."c.`snr` , "
			."c.`graph1` , "
			."c.`graph2` , "
			."(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference "
			."from ApCtfData c left join ApAceRunData r on (c.`REF|ApAceRunData|acerun` = r.`DEF_id`) "
			."left join ".DB_LEGINON.".AcquisitionImageData i on (c.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join ".DB_LEGINON.".ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and r.`DEF_id`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`REF|leginondata|AcquisitionImageData|image` = c.`REF|leginondata|AcquisitionImageData|image`)";
		return $this->mysql->getSQLResult($q);
	}

	function getCtfInfo($runId) {
		$q =	"select "
			."c.`REF|leginondata|AcquisitionImageData|image`, "
			."c.`defocus1`, "
			."c.`defocus2`, "
			."c.`defocusinit`, "
			."c.`amplitude_contrast`, "
			."c.`angle_astigmatism`, "
			."c.`noise1`, "
			."c.`noise2`, "
			."c.`noise3`, "
			."c.`noise4`, "
			."c.`envelope1`, "
			."c.`envelope2`, "
			."c.`envelope3`, "
			."c.`envelope4`, "
			."c.`lowercutoff`, "
			."c.`uppercutoff`, "
			."c.`confidence` , "
			."c.`confidence_d` , "
			."c.`snr` , "
			."c.`graph1` , "
			."c.`graph2` "
			."from ApCtfData c where c.`REF|ApAceRunData|acerun`='$runId'";
		return $this->mysql->getSQLResult($q);
	}

	function getCtfInfoFromImageId($imageId, $order=false, $ctffind=False) {
		$q =	"select "
			."c.`DEF_id`, "
			."c.`REF|leginondata|AcquisitionImageData|image`, "
			."s.`defocus`, "
			."c.`defocus1`, "
			."c.`defocus2`, "
			."c.`defocusinit`, "
			."c.`amplitude_contrast`, "
			."c.`angle_astigmatism`, "
			."c.`confidence` , "
			."c.`confidence_d` , "
			."c.`snr` , "
			."p.`path`, "
			."c.`graph1` , "
			."c.`graph2` , "
			."(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference "
			."from ApCtfData c "
			."left join(ApAceRunData r, ApPathData p) "
			."on ( r.DEF_id=c.`REF|ApAceRunData|acerun` and p.DEF_id=r.`REF|ApPathData|path`) "
			."left join ".DB_LEGINON.".AcquisitionImageData i "
			."on (c.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join ".DB_LEGINON.".ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where c.`REF|leginondata|AcquisitionImageData|image`='$imageId' ";
		$q .= " AND c.`graph1` IS NOT NULL ";
		if ($ctffind) $q .= "AND r.`REF|ApCtfTiltParamsData|ctftilt_params` IS NOT NULL ";
		$q .= "ORDER BY (c.`confidence`*c.`confidence_d`) DESC";
		if ($order) {
			$fields = $order['fields'];
			$q .= " order by ".join(", ",$fields);
		}
		return $this->mysql->getSQLResult($q);
	}

	function getBestCtfInfoForSessionId($sessionId, $limit=false) {
		$q = "select  ctfdata.* "
			."from "
			."	( "
			."	select  "
			."		i.`filename`, "
			."		c.`REF|leginondata|AcquisitionImageData|image`, "
			."		i.`DEF_id`, "
			."		p.`name`, "
			."		s.`defocus`, "
			."		c.`defocus1`, c.`defocus2`, c.`defocusinit`, c.`angle_astigmatism`, "
			."		c.`noise1`, c.`noise2`, c.`noise3`, c.`noise4`, "
			."		c.`envelope1`, c.`envelope2`, c.`envelope3`, c.`envelope4`, c.`lowercutoff`, c.`uppercutoff`, c.`snr`, "
			."		c.`confidence`,c.`confidence_d` , "
			."		(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference "
			."	from `ApCtfData` c "
			."	left join ".DB_LEGINON.".`AcquisitionImageData` i on (i.`DEF_id` = c.`REF|leginondata|AcquisitionImageData|image`) "
			."	left join ".DB_LEGINON.".`PresetData` p on (p.DEF_id = i.`REF|PresetData|preset`) "
			."	left join ".DB_LEGINON.".`ScopeEMData` s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."	where "
			."	c.`REF|leginondata|AcquisitionImageData|image` in  "
			."	( "
			."		select a.`DEF_id` from ".DB_LEGINON.".`AcquisitionImageData` a  "
			."		where a.`REF|SessionData|session`='$sessionId'  "
			."	AND  "
			."  ABS(s.`SUBD|stage position|a`) < 0.9  "
			."		)  "
			."		order by (if(confidence_d>confidence, confidence_d, confidence)) desc  "
			."	) ctfdata ";
			// if $limit is specified, report only values with confidences > $limit
			if ($limit) {
				$q .= " where ctfdata.confidence > $limit || ctfdata.confidence_d > $limit ";
			}
			$q .= " group by ctfdata.DEF_id ";
		//echo $q."<br/><br/>\n";
		return $this->mysql->getSQLResult($q);
	}

	function getCTFStats($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "c.`REF|leginondata|AcquisitionImageData|image` as id, s.defocus, "
					. "count(c.DEF_id) as `nb`, "
					. "min(c.`$field`) as `min`, "
					. "max(c.`$field`) as `max`, "
					. "avg(c.`$field`) as `avg`, "
					. "stddev(c.`$field`) as `stddev`";
		}
		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
			$q =	"select ".$select." "
			."from ApCtfData c left join ".DB_LEGINON.".AcquisitionImageData i "
			."on (c.`REF|leginondata|AcquisitionImageData|image`=i.`DEF_id`) "
			."left join ".DB_LEGINON.".`ScopeEMData` s "
			."on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."left join ".DB_LEGINON.".`PresetData` p "
			."on (`p`.`DEF_id`=`i`.`REF|PresetData|preset`) "
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|ApAceRunData|acerun`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`REF|leginondata|AcquisitionImageData|image` = c.`REF|leginondata|AcquisitionImageData|image`)";
			$q .= "group by p.`name`";
			//echo $q."<br/><br/>\n";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
			//echo print_r($r)."<br/><br/>\n";
		}
		return $stats;
	}

	function getAceRunIdFromPath($path){
		$q= "SELECT r.* "
			. "FROM `ApAceRunData` AS r "
			. "LEFT JOIN ApPathData AS p "
			. "ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			. "WHERE p.`path` LIKE '$path%'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getBestStats($fields, $sessionId, $limit=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] =  " ctfdata.name , "
					. "count(ctfdata.`$field`) as `nb`, "
					. "min(abs(ctfdata.`$field`)) as `min`, "
					. "max(abs(ctfdata.`$field`)) as `max`, "
					. "avg(ctfdata.`$field`) as `avg`, "
					. "stddev(ctfdata.`$field`) as `stddev` ";
		}

		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
				$q = "select  $select "
				."from "
				."	( "
				."	select allctfdata.* "
				."	from "
				."		( "
				."		select  "
				."			c.`REF|leginondata|AcquisitionImageData|image`, "
				."			c.`DEF_id`, "
				."			p.`name`, "
				."			s.`defocus`, "
				."			c.`defocus1`, c.`defocus2`, c.`defocusinit`, c.`angle_astigmatism`, "
				."			c.`confidence`,c.`confidence_d` , "
				."			(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference "
				."		from `ApCtfData` c "
				."		left join ".DB_LEGINON.".`AcquisitionImageData` i on (i.DEF_id=c.`REF|leginondata|AcquisitionImageData|image`) "
				."		left join ".DB_LEGINON.".`PresetData` p on (p.DEF_id=i.`REF|PresetData|preset`) "
				."		left join ".DB_LEGINON.".`ScopeEMData` s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
				."		where "
				."		c.`REF|leginondata|AcquisitionImageData|image` in  "
				."			( "
				."			select a.`DEF_id` from ".DB_LEGINON.".`AcquisitionImageData` a  "
				."			where a.`REF|SessionData|session`='$sessionId'  "
				."			)  "
				."			order by (if(confidence_d>confidence, confidence_d, confidence)) desc  "
				."		) allctfdata "
				."	group by allctfdata.`REF|leginondata|AcquisitionImageData|image` "
				."	) ctfdata ";
				// if $limit is specified, report only values with confidences > $limit
				if ($limit){
					$q .= " where sqrt(ctfdata.confidence * ctfdata.confidence_d) > $limit ";
				}
				$q .= " group by ctfdata.name; ";
				//echo $q;
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
	}

	function getData($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "c.`REF|leginondata|AcquisitionImageData|image` as id, s.`defocus`, "
					. "`$field`";
		}
		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
			$q =	"select ".$select." "
			."from ctf c left join ".DB_LEGINON.".AcquisitionImageData i"
			."on (c.`REF|leginondata|AcquisitionImageData|image`=i.`DEF_id`) "
			."left join ".DB_LEGINON.".ScopeEMData s on (s.`DEF_id` = i.`REF|ScopeEMData|scope`) "
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|ApAceRunData|acerun`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`REF|leginondata|AcquisitionImageData|image` = c.`REF|leginondata|AcquisitionImageData|image`)";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
	}

	//------ -------------------- ---------//
	//-------particle functions --------//
	//------ -------------------- ---------//
	function displayParameters ($title,$params,$exclude_fields,$expId,$hide_button_field='',$inform=false) {
		//standard parameter table display

		//Array of $params keys that are shown as a link to another report
		$links=array(
			'stackId'=>"stackreport.php?expId=$expId&sId="
			,'particleSelection'=>"particlerunreport.php?expId=$expId&rId="
		);
		if (count($params) ==0) return;
		echo "<h4>".$title."</h4>";
		echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
		$selection_fields = array_keys($params);
		foreach($selection_fields as $key) {
			$exclude = false;
			foreach($exclude_fields as $bad) {
				if ($key == $bad) {
					$exclude = true;
					break;
				}
			}
			//Display only non-excluded fields
			if (!$exclude) {
				// Clean up referenced key for display
				$displaykeyarray = explode('Data|',$key);
				if (count($displaykeyarray)>1) {
					$displaykey = array_pop($displaykeyarray);
					$refkey = array_pop($displaykeyarray);
				} else {
					$displaykeyarray = explode('DEF_',$key);
					$displaykey = array_pop($displaykeyarray);
					$refkey = $displaykey;
				}
				// Display only non-null params
				if (gettype($params[$key])!='NULL') {
					if (!$hide_button_field) $hide_button_field = $key;
					echo "<tr>\n";
					echo "</td>";
					echo "<td><span class='datafield0'>$displaykey</span></td>";
					echo "<td>";
					$type='text';
					foreach(array_keys($links) as $linkkey) {
						if ($linkkey ==$refkey) {
							$type='link';
							$link = $links[$linkkey];
						}
					}
					if ($type!='link') {
						if (!is_array($params[$key])) {
							//plain display
							echo $params[$key];
						} else {
							//array item display
							$text = '';
							foreach (array_keys($params[$key]) as $akey)
								$text .= ($params[$key][$akey]).',';
							echo trim($text,',');
						}
					} else {
						//Specify different values for the displayed data and link if available
						if (!is_array($params[$key])) {
							$datadisplay = $params[$key];
							$datalink = $datadisplay;
						} else {
							$datadisplay = $params[$key]['display'];
							$datalink = $params[$key]['link'];
						}
						$link = $link.$datalink;
						echo "<a href='".$link."'>".$datadisplay."</a>";
					}
					if ($hide_button_field == $key) {
						$hideid = $params[$hide_button_field];
						if ($params['hidden'] == 1) {
							echo "<font color='#cc0000'>HIDDEN</font>\n";
							if ($inform)
								echo " <input class='edit' type='submit' name='unhideItem".$hideid."' value='unhide'>\n";
						} else {
							if ($inform)
								echo "<input class='edit' type='submit' name='hideItem".$hideid."' value='hide'>\n";
						}
					}
					echo "</td></tr>\n";
				}
			}
		}
		echo "</table>\n";
	}

	function displayParametersInSummary ($params,$display_fields,$expId,$primary_field='DEF_id') {
		//standard parameter row display
		/* Use $params[key] =
				array('link'=>linkid,'display'=>display_string) to create
				a link of a key in $params found in the array $links
			set $primary_field='' to avoid editing/hiding buttons
		*/
		//Array of $params keys that are shown as a link to another report
		$links=array(
			'stackId'=>"stackreport.php?expId=$expId&sId="
			,'stack'=>"stackreport.php?expId=$expId&sId="
			,'particleSelection'=>"particlerunreport.php?expId=$expId&rId="
			,'fulltomoid'=>"fulltomoreport.php?expId=$expId&tomoId="
			,'avgid'=>"tomoavgreport.php?expId=$expId&avgId="
			,'subtomo'=>"subtomosummary.php?expId=$expId&fullId="
			,'alignrun id'=>"tomoalignreport.php?expId=$expId&alignId="
			,'alignerid'=>"protomoreport.php?expId=$expId&aId="
			,'refine cycle'=>"protomoreport.php?expId=$expId&aId="
		);
		$html  = '<tr>';
		foreach($display_fields as $key) {
			// Clean up referenced key for display
			$displaykeyarray = explode('Data|',$key);
			if (count($displaykeyarray)>1) {
				$displaykey = array_pop($displaykeyarray);
				$refkey = array_pop($displaykeyarray);
			} else {
				$displaykeyarray = explode('DEF_',$key);
				$displaykey = array_pop($displaykeyarray);
				$refkey = $displaykey;
			}
			if (!$hide_button_field) $hide_button_field = $key;
			$html .= "<td>\n";
			$type='text';
			foreach(array_keys($links) as $linkkey) {
				if ($linkkey ==$refkey && $params[$key]) {
					$type='link';
					$link = $links[$linkkey];
				}
			}
			if ($type!='link') {
				if (!is_array($params[$key])) {
				//plain display
					$html .= $params[$key];
				} else {
					//array item display
					$text = '';
					foreach (array_keys($params[$key]) as $akey)
						$text .= ($params[$key][$akey]).',';
					$html .= trim($text,',');
				}
			} else {
				//Specify different values for the displayed data and link if available
				if (!is_array($params[$key])) {
					$datadisplay = $params[$key];
					$datalink = $datadisplay;
				} else {
					$datadisplay = $params[$key]['display'];
					$datalink = $params[$key]['link'];
				}
				$link = $link.$datalink;
				$html .= "<a href='".$link."'>".$datadisplay."</a>";
			}
			if ($primary_field == $key && $_SESSION['username']) {
				$primary_id = $params[$key];
				if ($params['hidden'] == 1) {
					$html .= "<font color='#cc0000'>HIDDEN</font>\n";
					$html .= " <input class='edit' type='submit' name='unhideItem".$primary_id."' value='unhide'>\n";
				} else $html .= " <input class='edit' type='submit' name='hideItem".$primary_id."' value='hide'>\n";
			}
			if ('description' == $key && $primary_field) {
				$descDiv = ($_SESSION['username']) ? editButton($primary_id,$t['description']) : $t['description'];
				$html .= "$descDiv\n";
			}
			$html .= "</td>\n";
		}
		$html .= "</tr>";
		return $html;
	}

	function getTemplatesFromProject ($projectId, $getHidden=False) {
		$q="SELECT temp.*, path.path "
			."FROM `ApTemplateImageData` AS temp "
			."LEFT JOIN ApPathData AS path ON "
			."(temp.`REF|ApPathData|path`=path.`DEF_id`) "
			."WHERE `project|projects|project`='$projectId' ";
		if (!$getHidden) $q.= "AND (temp.`hidden` IS NULL OR temp.`hidden` = 0) ";
		$q.= "ORDER BY temp.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTemplatesFromId ($templateId) {
		$q = "SELECT t.*, p.path "
				."FROM `ApTemplateImageData` AS t "
				."LEFT JOIN ApPathData AS p ON "
				."(t.`REF|ApPathData|path`=p.`DEF_id`) "
				."WHERE t.`DEF_id` = '$templateId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRecentTemplateRunFromId ($templateId) {
		$q = "SELECT trun.* "
				."FROM `ApTemplateRunData` AS trun "
				."LEFT JOIN ApTemplateImageData AS timg ON "
				."(trun.`REF|ApTemplateImageData|template` = timg.`DEF_id`) "
				."WHERE timg.`DEF_id` = '$templateId' "
				."ORDER BY trun.`DEF_id` DESC "
				."LIMIT 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getTemplateStacksFromProject ($projectId, $getHidden=False, $type=False) {
		$q = "SELECT stack.*, path.path "
			."FROM ApTemplateStackData as stack "
			."LEFT JOIN ApPathData AS path ON "
			."(stack.`REF|ApPathData|path`=path.`DEF_id`) "
			."WHERE `project|projects|project`='$projectId' ";
		if (!$getHidden) $q.= "AND (stack.`hidden` IS NULL OR stack.`hidden` = 0) ";
		if ($type == "clsavg") $q.= "AND (stack.`cls_avgs` = 1) ";
		if ($type == "forward") $q.= "AND (stack.`forward_proj` = 1) ";
		$q .= "ORDER BY stack.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTemplateStacksFromSession ($expId, $getHidden=False, $type=False) {
		$q = "SELECT stack.*, path.path "
			."FROM ApTemplateStackData as stack "
			."LEFT JOIN ApPathData AS path ON "
								."(stack.`REF|ApPathData|path`=path.`DEF_id`) "
			."WHERE stack.`REF|leginondata|SessionData|session`='$expId' ";
		if (!$getHidden) $q.= "AND (stack.`hidden` IS NULL OR stack.`hidden` = 0) ";
		if ($type == "clsavg") $q.= "AND (stack.`cls_avgs` = 1) ";
		if ($type == "forward") $q.= "AND (stack.`forward_proj` = 1) ";
		$q .= "ORDER BY stack.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getTemplateStackParams ($templateStackId, $getHidden=False, $type=False) {
		$q = "SELECT ts.*, path.path "
			."FROM ApTemplateStackData as ts "
			."  LEFT JOIN ApPathData as path ON "
			."(ts.`REF|ApPathData|path`=path.`DEF_id`) "
			."  WHERE ts.`DEF_id`='$templateStackId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getStackSelector($stackIds,$stackidval,$onchange) {
		/* THIS FUNCTION SHOULD BE MOVED TO summarytables.inc */
		# $stackinfo[0] = stackid
		# $stackinfo[1] = pixel size in angstrums / pixels
		# $stackinfo[2] = stack boxsize (length in either direction) in pixels
		# $stackinfo[3] = number of particles in the stack
		# $stackinfo[4] = appion stackfile path
		# $stackinfo[5] = Imagic stack header file name, including extension but not path
		# $stackinfo[6] = Imagic stack data file name, including extension but not path
		# examples: 
		# $stackinfo[4] = '/your_disk/appion/09aug267/stacks/stack1'
		# $stackinfo[5] = 'start.hed'
		# $stackinfo[6] = 'start.img'
		echo "<SELECT NAME='stackval'";
		if ($onchange) echo "onchange='".$onchange."'";
		echo ">\n";
		foreach ($stackIds as $stackid){
			// get stack parameters from database
			$s=$this->getStackParams($stackid['stackid']);
			// get number of particles in each stack
			$totalp=$this->getNumStackParticles($stackid['stackid']);
			$nump=commafy($totalp);
			// get pixel size of stack
			$apix=($this->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
			// truncated pixel size
			$showapix=sprintf("%.2f",$apix);
			// get box size
			$box=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
			// get stack path with name
			$opvals = "$stackid[stackid]|--|$apix|--|$box|--|$totalp|--|$s[path]|--|$s[name]";
			// if imagic stack, send both hed & img files for dmf
			if (ereg('\.hed', $s['name'])) $opvals.='|--|'.ereg_replace('hed','img',$s['name']);
			if (ereg('\.img', $s['name'])) $opvals.='|--|'.ereg_replace('img','hed',$s['name']);
			echo "<OPTION VALUE='$opvals'";
			// select previously set stack on resubmit
			if ($stackid['stackid']==$stackidval) echo " SELECTED";
			echo">$s[shownstackname] ID: $stackid[stackid] ($nump particles, $showapix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
		}
		echo "</SELECT>\n";
		return $apix;
		/* THIS FUNCTION WAS MOVED TO summarytables.inc */
	}

	function getParticlesFromImageId ($runId, $imageId){
		$q = "select p.DEF_id as id, "
			."p.xcoord, p.ycoord, p.correlation, "
			."p.`REF|ApTemplateImageData|template` as templateId, "
			."p.diameter "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."and p.`REF|leginondata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getLastAssessmentRun ($sessionId){
		$q = "select max(DEF_id) as runId "
			." from ApAssessmentRunData where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}

	function getAssessmentRunIds ($sessionId) {
		$q = "select * "
			."from ApAssessmentRun where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getKeepStatus ($imageId,$runId){
		// returns a boolean value, 0 if rejected, 1 if keeping,
		// null if no status in database
		$q = "select * "
			."from ApAssessmentData "
			."where `REF|leginondata|AcquisitionImageData|image` = '$imageId' "
			."and `REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		if ($r) {
			if ($r['selectionkeep']==0) $keep='no';
			elseif ($r['selectionkeep']==1) $keep='yes';
		}
		return $keep;
		//		return $r['selectionkeep'];
	}

	function updateKeepStatus ($imageId,$runId,$value){
		// update image status : 0 if rejected, 1 if keeping,

		$exists=($this->getKeepStatus($imageId,$runId)) ? true : false;
		if ($exists) {
			$data = array('selectionkeep'=>$value);
			$where = array('REF|leginondata|AcquisitionImageData|image'=>$imageId);
			$where['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLUpdate('ApAssessmentData',$data,$where);
		}
		else {
			$data['selectionkeep']=$value;
			$data['REF|leginondata|AcquisitionImageData|image']=$imageId;
			$data['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLInsert('ApAssessmentData',$data);
		}
	}

	function getAssessmentDataForRun ($runId){
		$q = "select i.filename, a.selectionkeep as keep "
			."from ApAssessmentData a "
			."left join ".DB_LEGINON.".AcquisitionImageData i "
			."on (a.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."where a.`REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		//echo "$q";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getSelectionParams ($runId, $returntype=False) {
		$q = "select * from ApSelectionRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);

		//print_r ($r);
		//echo $r['REF|ApSelectionParamsData|params'];
		$q = "select s.*, r.name, path.path AS path, r.`REF|leginondata|SessionData|session` ";

		if ($r['REF|ApSelectionParamsData|params']) {
			$selectionparamid=$r['REF|ApSelectionParamsData|params'];
			$q .= "from ApSelectionParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApSelectionParamsData|params`) ";
			$type = "Template Correlator";
		}
		elseif ($r['REF|ApDogParamsData|dogparams']) {
			$dogparamid=$r['REF|ApDogParamsData|dogparams'];
			$q .= "from ApDogParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApDogParamsData|dogparams`) ";
			$type = "DOG Picker";
		}
		elseif ($r['REF|ApManualParamsData|manparams']) {
			$manparamid=$r['REF|ApManualParamsData|manparams'];
			$q .= "from ApManualParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApManualParamsData|manparams`) ";
			$type = "Manual Picker";
		}
		elseif ($r['REF|ApTiltAlignParamsData|tiltparams']) {
			$manparamid=$r['REF|ApTiltAlignParamsData|tiltparams'];
			$q .= "from ApTiltAlignParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApTiltAlignParamsData|tiltparams`) ";
			$type = "Tilt Picker";
		}
		$q .= "LEFT JOIN ApPathData AS path "
			." ON (path.`DEF_id` = r.`REF|ApPathData|path`) ";

		if ($returntype) return $type;

		$q .= "where r.`DEF_id` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticleLabels($runId) {
		$q = "select label, count(DEF_id) as `number particle` from ApParticleData where `REF|ApSelectionRunData|selectionrun`=".$runId." and label is not NULL group by `label`";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaxTiltAngle ($sessionId) {
		$q = "SELECT MAX(ABS(s.`SUBD|stage position|a`))*180.0/PI() AS angle "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` AS im "
			."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` AS s "
			."ON s.`DEF_id` = im.`REF|ScopeEMData|scope` "
			."WHERE im.`REF|SessionData|session` = '$sessionId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['angle'];
	}

	function getTemplateRunParams ($runId) {
		$q="SELECT i.DEF_id as id, p.path, i.templatename as tname, i.apix, i.description, "
			."t.range_start, t.range_end, t.range_incr, "
			."r.name "
			."from ApTemplateRunData AS t "
			."left join ApTemplateImageData i on (t.`REF|ApTemplateImageData|template`=i.`DEF_id`) "
			."LEFT JOIN ApPathData AS p ON (i.`REF|ApPathData|path`=p.`DEF_id`) "
			."left join ApSelectionRunData r on (t.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			."where t.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticles ($runId) {
		$q="select p.DEF_id, p.xcoord, p.ycoord, p.correlation "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getImgIdFromSelectionRun ($runId) {
		$q="SELECT "
			."  p.`REF|leginondata|AcquisitionImageData|image` AS imgid "
			."FROM ApParticleData AS p "
			."WHERE "
			."  p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."ORDER BY p.`REF|leginondata|AcquisitionImageData|image` DESC "
			."LIMIT 1 ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0]['imgid'];
	}

	function getParticleCorrelationStats($runId) {
	}

	function hasParticleData ($sessionId) {
		$r= ($this->getLastParticleRun($sessionId)) ? true : false;
		return $r;
	}

	function getStats ($runId, $inspect=false, $selexval=false) {
		$q="select count(p.`DEF_id`) as `totparticles`, "
			."count(distinct p.`REF|leginondata|AcquisitionImageData|image`) as num, "
			."min(p.correlation) as `min`, "
			."max(p.correlation) as `max`, "
			."avg(p.correlation) as `avg`, "
			."stddev(p.correlation) as `stddev` "
			."from ApParticleData p ";
		// use the latest inspection value. This should be changed later
		if ($inspect) {
			$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = p.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 "
				."where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		if ($selexval)
			$q.="p.`correlation`>='$selexval' AND ";
		$q.="p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;

	}

	function getNumImgs ($runId){
		$q="SELECT count(distinct `REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun`='$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumImgsFromSessionId ($sessionId){
		$q= "SELECT "
			. "  COUNT(DISTINCT p.`REF|leginondata|AcquisitionImageData|image`) AS num  "
			. "FROM `ApParticleData` AS p "
			. "LEFT JOIN `ApSelectionRunData` AS r "
			. "  ON (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "WHERE r.`REF|leginondata|SessionData|session`='$sessionId' ";
			#. "  ORDER BY num LIMIT 10";
		#echo $q;
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getSelectionRunIdFromPath($path){
		$q= "SELECT r.* "
			. "FROM `ApSelectionRunData` AS r "
			. "LEFT JOIN ApPathData AS p "
			. "ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			. "WHERE p.`path` LIKE '$path%'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	#--------- IMAGE ASSESSMENT FUNCTIONS ---------------#

	function getNumAssessedImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT COUNT(assess.`DEF_id`) as num "
			."FROM `ApAssessmentData` AS assess "
			."LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			."  ON viewer.`imageId` = assess.`REF|leginondata|AcquisitionImageData|image` "
			."WHERE "
			." ( assess.`selectionkeep` IS NOT NULL "
			."OR "
			."  viewer.`status` IS NOT NULL ) "
			."AND `REF|ApAssessmentRunData|assessmentrun` = '$rid'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumViewerPrefImages ($sessionId) {
		$q = "SELECT "
			. "  COUNT(DISTINCT p.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS p "
			. "LEFT JOIN `ApSelectionRunData` AS r "
			. "  ON (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = p.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE "
			. "  viewer.`status` IS NOT NULL "
			. " AND "
			. "  r.`REF|leginondata|SessionData|session`='$sessionId' ";
		#echo $q.";<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumTotalAssessImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT "
			. "  COUNT(DISTINCT part.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS part "
			. "LEFT JOIN `ApSelectionRunData` AS partrun "
			. "  ON (part.`REF|ApSelectionRunData|selectionrun` = partrun.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "LEFT JOIN `ApAssessmentData` AS assess "
			. "  ON assess.`REF|leginondata|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE ("
			. " ( assess.`selectionkeep` IS NOT NULL AND `REF|ApAssessmentRunData|assessmentrun` = '$rid' )"
			. "OR "
			. "  viewer.`status` IS NOT NULL "
			. ") AND "
			. "  partrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		#echo $q.";<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumRejectAssessedImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT COUNT(assess.`DEF_id`) as num "
			."FROM `ApAssessmentData` AS assess "
			."WHERE "
			." assess.`selectionkeep` = 0 "
			."AND `REF|ApAssessmentRunData|assessmentrun` = '$rid'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumHiddenImages ($sessionId) {
		$q = "SELECT "
			. "  COUNT(DISTINCT p.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS p "
			. "LEFT JOIN `ApSelectionRunData` AS r "
			. "  ON (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = p.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE "
			. "  viewer.`status` = 'hidden' "
			. "AND "
			. "  r.`REF|leginondata|SessionData|session`='$sessionId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumTotalRejectImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT "
			. "  COUNT(DISTINCT part.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS part "
			. "LEFT JOIN `ApSelectionRunData` AS partrun "
			. "  ON (part.`REF|ApSelectionRunData|selectionrun` = partrun.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "LEFT JOIN `ApAssessmentData` AS assess "
			. "  ON assess.`REF|leginondata|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE ("
			. " ( assess.`selectionkeep` = 0 AND `REF|ApAssessmentRunData|assessmentrun` = '$rid' )"
			. "OR "
			. "  viewer.`status` = 'hidden'  "
			. ") AND "
			. "  partrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		#echo $q.";<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumKeepAssessedImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT COUNT(assess.`DEF_id`) as num "
			."FROM `ApAssessmentData` AS assess "
			."LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			."  ON viewer.`imageId` = assess.`REF|leginondata|AcquisitionImageData|image` "
			."WHERE "
			." assess.`selectionkeep` = 1 "
			."AND `REF|ApAssessmentRunData|assessmentrun` = '$rid'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumExemplarImages ($sessionId) {
		$q = "SELECT "
			. "  COUNT(DISTINCT p.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS p "
			. "LEFT JOIN `ApSelectionRunData` AS r "
			. "  ON (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = p.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE "
			. "  viewer.`status` = 'exemplar' "
			. "AND "
			. "  r.`REF|leginondata|SessionData|session`='$sessionId' ";
		#echo $q.";<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumTotalKeepImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "SELECT "
			. "  COUNT(DISTINCT part.`REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` AS part "
			. "LEFT JOIN `ApSelectionRunData` AS partrun "
			. "  ON (part.`REF|ApSelectionRunData|selectionrun` = partrun.`DEF_id`) "
			. "LEFT JOIN ".DB_LEGINON.".`viewer_pref_image` AS viewer"
			. "  ON viewer.`imageId` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "LEFT JOIN `ApAssessmentData` AS assess "
			. "  ON assess.`REF|leginondata|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
			. "WHERE ( "
			. "  ( assess.`selectionkeep` = 1 AND `REF|ApAssessmentRunData|assessmentrun` = '$rid' )"
			. "OR "
			. "  viewer.`status` = 'exemplar' "
			. ") AND "
			. "  partrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		#echo $q.";<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getLastParticleRun ($sessionId) {
		$q = "select DEF_id as runId "
			."from `ApSelectionRunData` "
			."where `REF|leginondata|SessionData|session` = '$sessionId' "
			."order by DEF_id desc limit 1";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getParticleRunData ($partRunId) {
		$q = "SELECT r.*, p.path "
			."FROM `ApSelectionRunData` AS r "
			."LEFT JOIN ApPathData AS p ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$partRunId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getLastRunNumberForType ($sessionId, $table, $field='name') {
		$q = "SELECT r.`".$field."` "
			."FROM `".$table."` AS r "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY r.`".$field."` DESC "
			." ";
		$r = $this->mysql->getSQLResult($q);
		if ($r && count($r) > 0) {
			return count($r);
		}
		return 0;
	}

	function getParticleRunIds ($sessionId,$showHidden=False) {
		$q = "SELECT r.*, p.path "
			."FROM `ApSelectionRunData` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		$q.= "ORDER BY r.`DEF_id` DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	#--------- MAKE STACK FUNCTIONS---------------#

	function getParticleRunsFromStack($stackid) {
		// return all the particle runs contributing to a stack,
		// accounting for multiple runs in 1 stack (combinestack)
		$q = "SELECT `REF|ApStackRunData|stackRun` as stackrun "
			. "FROM `ApRunsInStackData` as rs "
			. "WHERE `REF|ApStackData|stack` = $stackid ";
		$r = $this->mysql->getSQLResult($q);
		$pruns = array();
		foreach ($r as $srun) {
			// get particle run from the first stack particle of
			// each run
			$q = "SELECT `REF|ApSelectionRunData|selectionrun` as DEF_id "
				. "FROM `ApParticleData` as p "
				. "LEFT JOIN `ApStackParticlesData` AS sp "
				. "ON sp.`REF|ApParticleData|particle` = p.`DEF_id` "
				. "WHERE sp.`REF|ApStackRunData|stackRun`=".$srun['stackrun']." "
				. "LIMIT 1 ";
			$pruns[] = $this->mysql->getSQLResult($q);
		}
		return $pruns;
	}

	function getStackRunIdFromPath($path){
		$q= "SELECT sd.* "
			. "FROM `ApStackData` AS sd "
			. "LEFT JOIN ApPathData AS p "
			. "ON (sd.`REF|ApPathData|path` = p.`DEF_id`) "
			. "WHERE p.`path` LIKE '$path%'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackIds ($sessionId, $showHidden=False, $syntheticOnly=False, $noctf=False) {
		$q = "SELECT "
			."  DISTINCT(r.`REF|ApStackData|stack`) as stackid , "
			."  st.*, "
			."  s.`REF|leginondata|SessionData|session` AS sessionid "
			."FROM ApRunsInStackData as r "
			."LEFT JOIN ApStackRunData as s ON "
			."  (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
			."LEFT JOIN ApStackData as st ON "
			."  (r.`REF|ApStackData|stack` = st.`DEF_id`) ";
		if ($noctf) {
			$q.= "LEFT JOIN ApStackParamsData as param ON "
				."  (s.`REF|ApStackParamsData|stackParams` = param.`DEF_id`) ";
		}
		$q.="WHERE "
			."  s.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden)
			$q.= " AND st.`hidden` != 1 ";
		if ($syntheticOnly)
			$q.= " AND s.`REF|ApSyntheticStackParamsData|syntheticStackParams` is NOT NULL ";
		if ($noctf)
			$q.= " AND param.`fliptype` IS NULL ";
		$q.= "ORDER BY stackid DESC";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getPrimaryStackIds ($sessionId) {
		$q = "SELECT "
			."  DISTINCT(r.`REF|ApStackData|stack`) as stackid , "
			."  st.*, "
			."  s.`REF|leginondata|SessionData|session` AS sessionid "
			."FROM ApRunsInStackData as r "
			."LEFT JOIN ApStackRunData as s ON "
			."  (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
			."LEFT JOIN ApStackData as st ON "
			."  (r.`REF|ApStackData|stack` = st.`DEF_id`) "
			."WHERE "
			."  s.`REF|leginondata|SessionData|session` = '$sessionId' "
			." AND st.`REF|ApStackData|oldstack` IS NULL "
			."ORDER BY stackid DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getParentStackId ($substackId) {
		$q = "SELECT "
			." `REF|ApStackData|oldstack` as parentid "
			." FROM ApStackData "
			." WHERE `DEF_id` = ".$substackId." ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSubStackIds ($sessionId, $primarystackid, $showHidden=False) {
		$q = "SELECT "
			."  DISTINCT(r.`REF|ApStackData|stack`) as stackid , "
			."  st.*, "
			."  s.`REF|leginondata|SessionData|session` AS sessionid "
			."FROM ApRunsInStackData as r "
			."LEFT JOIN ApStackRunData as s ON "
			."  (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
			."LEFT JOIN ApStackData as st ON "
			."  (r.`REF|ApStackData|stack` = st.`DEF_id`) "
			."WHERE "
			."  s.`REF|leginondata|SessionData|session` = '$sessionId' "
			." AND st.`REF|ApStackData|oldstack` = '$primarystackid' ";
		if (!$showHidden)
			$q.= " AND st.`hidden` != 1 ";
		$q.= "ORDER BY stackid DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusterRefNumsFromSubStack ($substackid,$clusterstackid) {
		$q = "SELECT "
			."cp.`refnum` as classnum "
			."FROM `ApClusteringParticlesData` as cp "
			."LEFT JOIN `ApAlignParticlesData` as ap "
			."ON cp.`REF|ApAlignParticlesData|alignparticle` = ap.`DEF_id` "
			."LEFT JOIN `ApStackParticlesData` as pst "
			."ON ap.`REF|ApStackParticlesData|stackpart` = pst.`DEF_id` "
			."LEFT JOIN `ApParticleData` as pp "
			."ON pst.`REF|ApParticleData|particle` = pp.`DEF_id` "
			."LEFT JOIN `ApStackParticlesData` as sst "
			."ON sst.`REF|ApParticleData|particle` = pp.`DEF_id` "
			."WHERE "
			."sst.`REF|ApStackData|stack` = ".$substackid." "
			."AND cp.`REF|ApClusteringStackData|clusterstack` = ".$clusterstackid." "
			."GROUP BY cp.`refnum` "
			." ";
		return $this->mysql->getSQLResult($q);
	}

	function getSubStackAlignCluster($substackinfo) {
		$conditions = array(
			'alignsub'=>array('alias'=>'ast','data'=>'ApAlignStackData'),
			'clustersub'=>array('alias'=>'cst','data'=>'ApClausteringStackData')
		);
		$substackname = $substackinfo['substackname'];
		foreach (array_keys($conditions) as $key) {
			if (ereg($key,$substackname)) {
				$conditionid = str_replace($key, '', $substackname);
				$condition = $key;
			} else {
			echo ereg($key,$substackname);
			}
		}
		if ($condition) {
			$q = "SELECT ";
			if ('clustersub' == $condition) {
				$q.= "cst.`DEF_id` as clusterstackid, ";
				$q.= "cr.`DEF_id` as clusterrunid, ";
			}
			$q.= " ast.`REF|ApStackData|stack` as primarystackid , "
				." ast.`DEF_id` as alignstackid, "
				." ar.`DEF_id` as alignrunid "
				."FROM ApAlignStackData as ast "
				."LEFT JOIN ApAlignRunData as ar ON "
				."  (ast.`REF|ApAlignRunData|alignRun`=ar.`DEF_id`) ";
			if ('clustersub' == $condition) {
				$q.= "LEFT JOIN ApClusteringRunData as cr ON "
					."(cr.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
					."LEFT JOIN ApClusteringStackData as cst ON "
					."(cst.`REF|ApClusteringRunData|clusterrun` = cr.`DEF_id`) "
					."WHERE "
					." cst.`DEF_id` = '$conditionid' ";
			} else {
				$q.="WHERE "
					." ast.`DEF_id` = '$conditionid' ";
			}
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
		} else return array();
	}

	function getTiltedStackIds ($sessionId, $showHidden=False) {
		$q = "SELECT "
			."  DISTINCT(stack.`DEF_id`) as stackid "
			."FROM ApRunsInStackData as runs "
			."LEFT JOIN ApStackRunData as stackrun ON "
			."  (runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id`) "
			."LEFT JOIN ApStackData as stack ON "
			."  (runs.`REF|ApStackData|stack` = stack.`DEF_id`) "
			."WHERE "
			."  stack.`REF|leginondata|SessionData|session` = '$sessionId' "
			."AND "
			."  ( stackrun.`tiltangle` != 'notilt' AND stackrun.`tiltangle` != 'all' )";
		if (!$showHidden)
			$q.= " AND st.`hidden` != 1 ";
		$q.= "ORDER BY stackid DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNamedSubStackIds ($sessionId, $primarystackid, $name, $showHidden=False) {
		$q = "SELECT "
			."  DISTINCT(s.`DEF_id`) as stackid, "
			."  s.* "
			."FROM ApStackData as s "
			."WHERE "
			." s.`REF|ApStackData|oldstack` = '$primarystackid' ";
		if ($name)
			$q.= "AND s.`substackname` REGEXP '".$name."' ";
		if (!$showHidden)
			$q.= " AND s.`hidden` != 1 ";
		$q.= "ORDER BY stackid DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackIdsForProject ($projectId, $showHidden=False) {
		$q = "SELECT "
			."  DISTINCT(st.`DEF_id`) as stackid "
			."FROM ApStackData as st ";
		if (!$showHidden)
			$q.= " WHERE st.`hidden` != 1 ";
		$q.= "ORDER BY stackid DESC";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getStackIdsOld ($sessionId) {
		$q = "select spar.stackid "
		."from ("
		."select `REF|ApParticleData|particle` as pid, `REF|ApStackRunData|stackRun` as stackid "
		."from ApStackParticlesData group by `REF|ApStackRunData|stackRun`) spar "
		."left join ApParticleData p on (p.`DEF_id` = spar.pid) "
		."left join ApSelectionRunData r on	(p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id` ) "
		."where r.`REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParams ($stackId) {
		$q = "SELECT DISTINCT(sd.`DEF_id`) as `stackId`, sd.*, pd.`path`"
			."FROM ApStackData as sd "
			."LEFT JOIN ApPathData AS pd ON "
			."(sd.`REF|ApPathData|path` = pd.`DEF_id`) "
			."WHERE sd.`DEF_id` = '$stackId'";
		//echo $q."<br/>\n";
		list($stack_primary_array) = $this->mysql->getSQLResult($q);
		if (!$stack_primary_array) return;
		// Get runs in stack
		$q = "SELECT r.`REF|ApStackRunData|stackRun` as runid "
			."FROM ApRunsInStackData as r "
			."WHERE r.`REF|ApStackData|stack` = '$stackId'";
		//echo $q."<br/>\n";
		$stackrunIds = $this->mysql->getSQLResult($q);
		// Parameters of original stack of the runs in stack
		$selectionstacks = array();
		foreach ($stackrunIds as $runid) {
			$stackrunId = $runid[runid];
			$rstack = $this->getOriginalStackFromStackRun($stackrunId);
			$childstackId = $rstack['stackId'];
			//Get Parameters
			$q = "SELECT DISTINCT(sd.`DEF_id`) as `stackId`, s.`DEF_id` as runid, s.*, p.*,sd.*,"
				."s.`REF|leginondata|SessionData|session` AS sessionid "
				."FROM ApRunsInStackData as r "
				."LEFT JOIN ApStackRunData as s "
				."ON (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
				."LEFT JOIN ApStackData as sd "
				."ON (r.`REF|ApStackData|stack`=sd.`DEF_id`) "
				."LEFT JOIN ApPathData AS pd ON "
				."(sd.`REF|ApPathData|path` = pd.`DEF_id`) "
				."LEFT JOIN `ApStackParamsData` p "
				."ON (p.`DEF_id` = s.`REF|ApStackParamsData|stackParams`) "
				."WHERE r.`REF|ApStackData|stack` = '$childstackId'";
			list($r) = $this->mysql->getSQLResult($q);
			//echo $q."<br/>\n";
			$params[]=$r;
			$selectionstacks[] = $childstackId;
		}
		//handle multiple runs in stack
		if (count($stackrunIds) > 1) {
			$patharray = explode('/',$stack_primary_array[path]);
			$runname = $patharray[count($patharray)-1];
			$extra=0;
		} else {
			$extra=1;
			$runname=$params[0]['stackRunName'];
		}
		//substack has no other parameter but oldstack reference
		if ($stack_primary_array['REF|ApStackData|oldstack']) {
			$r = array();
			$r = array_merge($r, $stack_primary_array);
			$r = array_merge($r,$this->getSubStackAlignCluster($stack_primary_array));
			$r['shownstackname'] = $runname.'-'.$stack_primary_array['substackname'];
			$r['REF|ApStackData|oldstack'] = $stack_primary_array['REF|ApStackData|oldstack'];
			//add needed parent stackrun parameters, but not all since they overwrites the primary values
			$r['bin'] = $params[0]['bin'];
			$r['boxSize'] = $params[0]['boxSize'];
			$r['tiltangle'] = $params[0]['tiltangle'];
			$r['fliptype'] = $params[0]['fliptype'];
			$r['inverted'] = $params[0]['inverted'];
			return $r;
		}
		$runarray = array();
		$runarray['shownstackname'] = $runname;
		$runarray['count'] = count($stackrunIds);
		$runarray = array_merge($runarray,$stack_primary_array);
		//use first run parameters for basic stack info
		if ($extra) {
			//use first run parameters for extra info
			$r = array_merge($params[0],$runarray);
		} else {
			$r = $runarray;
			$r['bin'] = $params[0]['bin'];
			$r['boxSize'] = $params[0]['boxSize'];
			$r['tiltangle'] = $params[0]['tiltangle'];
			$r['fliptype'] = $params[0]['fliptype'];
			$r['inverted'] = $params[0]['inverted'];
			$r['pixelsize'] = $params[0]['pixelsize'];
		}
		$r['selectionstacks'] = $selectionstacks;
		return $r;
	}

	function getOriginalStackFromStackRun($stackrunId) {
	//get the original stack when a stackrun is also used in combined stacks
		$q = "SELECT DISTINCT(rs.`REF|ApStackData|stack`) as stackId from `ApRunsInStackData` rs"
			. " WHERE"
			. " rs.`REF|ApStackRunData|stackRun`=".$stackrunId." "
			. " AND"
			. " rs.`REF|ApStackData|stack` NOT IN"
			. " (SELECT `REF|ApStackData|stack` as stack FROM "
			. " (SELECT count(*) as count ,`REF|ApStackData|stack`"
			. " FROM `ApRunsInStackData`"
			. " WHERE 1"
			. " GROUP BY `REF|ApStackData|stack`) runs"
			. " where runs.`count` > 1)";
		list($rstack) = $this->mysql->getSQLResult($q);
		return $rstack;
	}

	function getStackSelectionRun ($stackId) {
		$q = "SELECT pr . `DEF_id` selectionid , "
		." pr . `name`, "
		." pr . `REF|leginondata|SessionData|session` as sessionId "
		." FROM ( SELECT * FROM `ApStackParticlesData` "
		." WHERE `REF|ApStackData|stack` = ".$stackId." "
		." group by `REF|ApStackRunData|stackRun` ) sp1 "
		." LEFT JOIN `ApParticleData` p "
		." ON p . `DEF_id` = sp1 . `REF|ApParticleData|particle` "
		." LEFT JOIN `ApSelectionRunData` pr "
		." ON pr . `DEF_id` = p . `REF|ApSelectionRunData|selectionrun` "
		." ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStacksFromSelectionRun ($pickrunid) {
		$q = "SELECT DISTINCT(sp1.`REF|ApStackData|stack`) as stackid, "
		."sp1.`REF|ApStackRunData|stackRun` as stackrunid, "
		."pr . `DEF_id` as selectionid  "
		."FROM ( "
		."SELECT st.*, stpm.`DEF_id` as stackparamsid "
		."FROM `ApStackParticlesData` as st  "
		."LEFT JOIN `ApStackRunData` as str "
		."ON st.`REF|ApStackRunData|stackRun` = str.`DEF_id` "
		."LEFT JOIN `ApStackParamsData` as stpm "
		."ON str.`REF|ApStackParamsData|stackParams` = stpm.`DEF_id` "
		."group by "
		."st.`REF|ApStackRunData|stackRun`  "
		.") sp1  "
		."LEFT JOIN `ApParticleData` p  "
		."ON p .`DEF_id` = sp1 . `REF|ApParticleData|particle`  "
		."LEFT JOIN `ApSelectionRunData` pr ON  "
		."pr . `DEF_id` = p . `REF|ApSelectionRunData|selectionrun` "
		."WHERE pr.`DEF_id` =".$pickrunid." "
		." ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackMeanAndStdev ($stackId) {
		$q= "SELECT stackpart.mean AS mean, stackpart.stdev AS stdev "
			."FROM `ApStackParticlesData` AS stackpart "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r[0])."<br/><br/>\n";
		return $r;
	}

	function getNumStackParticles ($stackId) {
		$q= "SELECT count(DEF_id) as num "
			."FROM `ApStackParticlesData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumStackImages ($stackId) {
		$q= "SELECT DISTINCT im.`DEF_id` AS imgid "
			."FROM ApStackParticlesData AS stpart "
			."LEFT JOIN ApParticleData AS part "
			."ON stpart.`REF|ApParticleData|particle` = part.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".`AcquisitionImageData` AS im "
			."ON part.`REF|leginondata|AcquisitionImageData|image` = im.`DEF_id` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return count($r);
	}

	//////// fix me ////////
	function getStackIdFromReconId ($reconId) {
		$q= "SELECT * "
			."FROM `ApRefinementRunData` "
			."WHERE `DEF_id` = '$reconId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['REF|ApStackData|stack'];
	}

	function getStackPixelSizeFromStackId ($stackId) {
		// first see if it's stored in the ApStackData Table (easiest)
		$q="SELECT pixelsize FROM ApStackData WHERE DEF_id=$stackId";
		$r = $this->mysql->getSQLResult($q);
		$apix = $r[0]['pixelsize'];
		if ($apix && $apix != 0) return $apix;
		$preset = $this->getPresetFromStackId($stackId);
		return $preset['stackpixelsize'];
	}

	function getPresetFromStackId ($stackId) {
		//get the first image of the stack assume using defocpair if not specified
		$q="SELECT "
			." IF( ( pimage . `defocpair` IS NULL OR pimage . `defocpair` = 1 ) , "
			." sbimage . image , pimage . image ) as image , "
			." pimage.image as pimage, "
			." pimage.`stackbin` "
			." FROM "
			." ( SELECT "
			." p . `REF|leginondata|AcquisitionImageData|image` as image , pa . `defocpair` ,"
			." pa.`bin` as stackbin "
			." FROM `ApStackParticlesData` sp "
			." LEFT JOIN `ApStackRunData` r ON "
			." ( sp . `REF|ApStackRunData|stackRun` = r . `DEF_id` ) "
			." LEFT JOIN `ApStackParamsData` pa ON "
			." ( pa . `DEF_id` = r . `REF|ApStackParamsData|stackParams` ) "
			." LEFT JOIN `ApParticleData` p ON "
			." sp . `REF|ApParticleData|particle` = p . `DEF_id` "
			." WHERE sp . `REF|ApStackData|stack` = ".$stackId." "
			." limit 1 ) pimage , "
			." ( SELECT "
			." sb . `REF|leginondata|AcquisitionImageData|image2` as image "
			." FROM `ApStackParticlesData` sp "
			." LEFT JOIN `ApStackRunData` r ON "
			." ( sp . `REF|ApStackRunData|stackRun` = r . `DEF_id` ) "
			." LEFT JOIN `ApStackParamsData` pa ON "
			." ( pa . `DEF_id` = r . `REF|ApStackParamsData|stackParams` ) "
			." LEFT JOIN `ApParticleData` p ON "
			." sp . `REF|ApParticleData|particle` = p . `DEF_id` "
			." LEFT JOIN `ApImageTransformationData` sb ON "
			." (sb . `REF|leginondata|AcquisitionImageData|image1` "
			." = p . `REF|leginondata|AcquisitionImageData|image`) "
			." WHERE sp . `REF|ApStackData|stack`= ".$stackId." "
			." limit 1 ) sbimage ";
			list($r1)= $this->mysql->getSQLResult($q);
		//if no sibling image when defocpair param is not specified, use the original image
		$imgId = ($r1['image']) ? $r1['image'] : $r1['pimage'];
		// get image bin and the most recent pixel calibration
		$q="SELECT pd.`SUBD|binning|x` as imgbin, "
			."  pc.`pixelsize` as ccdpixelsize, pd.*, "
			."  pscope.`high tension` as hightension "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` a "
			."left join ".DB_LEGINON.".`PresetData` pd "
			."  on (a.`REF|PresetData|preset`=pd.`DEF_id`) "
			."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` pscope "
			."  ON (pscope.`DEF_id` = a.`REF|ScopeEMData|scope`) "
			.", ".DB_LEGINON.".PixelSizeCalibrationData pc "
			."WHERE a.`DEF_id`='$imgId' "
			."AND pc.`REF|InstrumentData|tem`= pd.`REF|InstrumentData|tem` "
			."AND pc.`magnification`= pd.`magnification` "
			."AND "
			."pc.`REF|InstrumentData|ccdcamera`= pd.`REF|InstrumentData|ccdcamera` "
			."AND "
			."pc.`DEF_timestamp`<	a.`DEF_timestamp` "
			."ORDER BY pc.`DEF_timestamp` DESC ";
		list($r2)=$this->mysql->getSQLResult($q);
		if (!is_null($r1['stackbin']) ) {
			settype($r1['stackbin'],"integer");
			$stackbin = $r1['stackbin'];
		} else {
			$stackbin = 1;
		}
		$r2['stackpixelsize'] = $r2['ccdpixelsize']*$r2['imgbin']*$stackbin;
		return $r2;
	}

	function getPixelSizeFromImgId ($imgid) {
		$q="SELECT pd.`SUBD|binning|x` as imgbin, "
			."  pc.`pixelsize` as ccdpixelsize  "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` AS a "
			."LEFT JOIN ".DB_LEGINON.".`PresetData` AS pd "
			."  ON (a.`REF|PresetData|preset` = pd.`DEF_id`) "
			.", ".DB_LEGINON.".PixelSizeCalibrationData pc "
			."WHERE "
			."  a.`DEF_id`='$imgid' "
			."AND "
			."  pc.`REF|InstrumentData|tem` = pd.`REF|InstrumentData|tem` "
			."AND "
			."  pc.`magnification` = pd.`magnification` "
			."AND "
			."  pc.`REF|InstrumentData|ccdcamera` = pd.`REF|InstrumentData|ccdcamera` "
			."AND "
			."  pc.`DEF_timestamp` <= a.`DEF_timestamp` "
			."ORDER BY pc.`DEF_timestamp` DESC ";
		//echo $q."<br/>\n";
		list($r2)=$this->mysql->getSQLResult($q);
		//echo print_r($r2)."<br/>\n";
		if ($r2['imgbin']) {
			$pixelsize = $r2['ccdpixelsize']*$r2['imgbin'];
		} else {
			$pixelsize = $r2['ccdpixelsize'];
		}
		return $pixelsize;
	}

	function displayParticleStats ($particleruns, $display_keys, $inspect=False, $selexval=False, $dispImg=True) {
		$expId=$_GET['expId'];
		if (!is_array($particleruns))
			return ;
		$html = "\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr> <td><span class='datafield0'>name</span></td>";
		$html .= "<td><span class='datafield0'>dbid</span></td>";
		foreach($display_keys as $key) {
			$html .= "<td> <span class='datafield0'>".$key."</span> </td> ";
		}
		$html .= "</tr>";
		foreach ($particleruns as $particle) {
			$runId=$particle['DEF_id'];
			if ($particle['hidden']) continue;
			$particlestats = $this->getStats($runId, $inspect, $selexval);
			$html .= "<tr>";
			$numptl=$particlestats['totparticles'];
			$numimg=$particlestats['num'];
			$ppimg = ($numimg > 0) ? (sprintf("%.1f", $numptl/$numimg)) : 0;
			$particlestats['numimgs']=$numimg.'<br />('.$ppimg.' prtl/img)';
			if ($dispImg = True)
				$particlestats['img'] = '<a href="'.$this->baseurl.'particlegraph.php?hg=1&run='.$runId.'">'
				.'<img border="0" '
				.'src="'.$this->baseurl.'particlegraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `ApSelectionRunData` where `DEF_id` = $runId";
			list($r0) = $this->mysql->getSQLResult($q);
			$html .= '<td><a href="'.$this->baseurl.'particlerunreport.php?expId='.$expId.'&rId='.$runId.'">'.$r0['name'].'</a></td>';
			$html .= '<td>'.$runId.'</td>';
			foreach($display_keys as $field) {
				$data=$particlestats[$field];
				if (eregi('^min|^max|^avg|^stddev', $field)) $data=format_sci_number($data,4);
				$html .= "<td> $data </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

	#--------- ALIGN STACK FUNCTIONS ---------------#

	function getAlignStackIds ($sessionId, $showHidden=False) {
		//$projectId = (int) getProjectFromExpId($expId);
		$q = "SELECT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApStackData AS st ON "
			."  (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			."  (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			."  (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."WHERE "
			."  strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden)
			$q.= " AND ast.`hidden` != 1 ";
		$q.= "ORDER BY alignstackid DESC";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo $r."<br/>\n";
		return $r;
	}

	function getAlignStackIdsWithAnalysis ($sessionId, $projectId) {
		//$projectId = (int) getProjectFromExpId($expId);
		$q = "SELECT DISTINCT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApAlignAnalysisRunData AS analysis ON "
			."  (analysis.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApStackData AS st ON "
			."  (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			."  (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			."  (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."WHERE "
			."  strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."AND "
			."  ast.`hidden` != 1 "
			."AND "
			."  analysis.`hidden` != 1 "
			."AND "
			."  analysis.`DEF_id` IS NOT NULL "
			."ORDER BY alignstackid DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getAlignStackParams ($alignstackid) {
		$q = "SELECT ar.*, ast.*, "
			."ar.runname AS runname, "
			."pd.`path` AS path "
			."FROM ApAlignStackData as ast "
			."LEFT JOIN ApPathData AS pd ON "
			."(ast.`REF|ApPathData|path` = pd.`DEF_id`) "
			."LEFT JOIN ApAlignRunData AS ar ON "
			."(ast.`REF|ApAlignRunData|alignrun` = ar.`DEF_id`) "
			."WHERE ast.`DEF_id` = '$alignstackid'";
		$r = $this->mysql->getSQLResult($q);
		$packagerefs = array(
			'spidernoref'=>'REF|ApSpiderNoRefRunData|norefrun',
			'spiderefbased'=>'REF|ApRefBasedRunData|refbasedrun',
			'maxlike'=>'REF|ApMaxLikeRunData|maxlikerun',
			'imagicMRA'=>'REF|ApMultiRefAlignRunData|imagicMRA',
			'editerrun'=>'REF|ApEdIterRunData|editerrun',
		);
		foreach (array_keys($packagerefs) as $package) {
			if ($r[0][$packagerefs[$package]]) $r[0]['package'] = $package;
		}
		return $r[0];
	}

	function getNumAlignStackParticles ($alignstackid) {
		$q= "SELECT count(DEF_id) as num "
			."FROM `ApAlignParticlesData` "
			."WHERE `REF|ApAlignStackData|alignstack` = '$alignstackid'";

		//echo $q."<br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumAlignStackReferences ($alignstackid) {
		$q= "SELECT count(aref.`DEF_id`) as num "
			."FROM `ApAlignReferenceData` AS aref "
			."LEFT JOIN ApAlignStackData AS astack ON "
			." (astack.`REF|ApAlignRunData|alignrun` = aref.`REF|ApAlignRunData|alignrun`) "
			."WHERE astack.`DEF_id` = '$alignstackid'"
			." AND "
			." astack.`iteration` = aref.`iteration` ";
		//echo $q."<br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r['num'];
	}

	function getAnalysisRuns ($sessionId, $projectId, $showHidden=False) {
		// This query left join ApCoranRun probably for historical reason
		$q = "SELECT analysis.`DEF_id` AS analysisid, analysis.* ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .= ", coran.* ";
		}
		$q .=	"FROM ApAlignAnalysisRunData AS analysis "
			."LEFT JOIN ApAlignStackData AS ast ON "
			." (analysis.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApStackData AS st ON "
			." (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			." (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			." (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .= "LEFT JOIN ApCoranRunData as coran ON "
			." (analysis.`REF|ApCoranRunData|coranrun` = coran.`DEF_id`) ";
		}
		$q .=	"WHERE "
			." strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden)
			$q.= " AND analysis.`hidden` != 1 AND ast.`hidden` != 1 ";
		$q .= "ORDER BY analysisid DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getAnalysisRunForAlignStack ($alignstackId, $projectId, $showHidden=False) {
		$q = "SELECT analysis.`DEF_id` AS analysisid, analysis.* ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .= ", coran.* ";
		}
		$q .=	"FROM ApAlignAnalysisRunData AS analysis ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .=	"LEFT JOIN ApCoranRunData as coran ON "
			." (analysis.`REF|ApCoranRunData|coranrun`=coran.`DEF_id`) ";
		}
		$q .=	"WHERE "
			."  analysis.`REF|ApAlignStackData|alignstack` = $alignstackId ";
		if (!$showHidden)
			$q.= " AND analysis.`hidden` != 1 ";
		$q .= "ORDER BY analysisid DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getAnalysisParams ($analysisid) {
		$q = "SELECT analysis.`DEF_id` AS analysisid, analysis.*, path.path AS path ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .= ", coran.* ";
		}
		$q .=	"FROM ApAlignAnalysisRunData AS analysis "
			."LEFT JOIN ApAlignStackData AS ast ON "
			." (analysis.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApPathData AS path ON "
			." (analysis.`REF|ApPathData|path` = path.`DEF_id`) ";
		if ($this->mysql->SQLTableExists("ApCoranRunData")) {
			$q .=	"LEFT JOIN ApCoranRunData as coran ON "
			." (analysis.`REF|ApCoranRunData|coranrun`=coran.`DEF_id`) ";
		}
		$q .=	"WHERE "
			."  analysis.`DEF_id` = $analysisid "
			."LIMIT 1 ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r[0];
	}
	function getImagicAnalysisParams ($analysisid) {
		$q = "SELECT analysis.`DEF_id` AS analysisid, analysis.*, data.*, path.path AS path "
			."FROM ApAlignAnalysisRunData AS analysis "
			."LEFT JOIN ApImagicAlignAnalysisData as data ON "
			." (analysis.`REF|ApImagicAlignAnalysisData|imagicMSArun`=data.`DEF_id`) "
			."LEFT JOIN ApPathData AS path ON "
			." (analysis.`REF|ApPathData|path` = path.`DEF_id`) "
								."WHERE "
								."  analysis.`DEF_id` = $analysisid "
								."LIMIT 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getCoranEigenDataFromAnalysis ($analysisid) {
		$q = "SELECT "
			."ce.factor_num AS num, "
			."ce.image_name AS name, "
			."ce.percent_contrib AS contrib, "
			."p.path AS path "
			."FROM ApCoranEigenImageData AS ce "
			."LEFT JOIN ApPathData AS p "
			."  ON (ce.`REF|ApPathData|path` = p.`DEF_id`) "
			."LEFT JOIN ApCoranRunData AS cr "
			."  ON (ce.`REF|ApCoranRunData|coranRun` = cr.`DEF_id`) "
			."LEFT JOIN ApAlignAnalysisRunData AS a "
			."  ON (a.`REF|ApCoranRunData|coranRun` = cr.`DEF_id`) "
			."WHERE "
			."  a.`DEF_id` = '$analysisid' "
			."ORDER BY ce.`factor_num` ASC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getFinishedMaxLikeJobs ($projectId) {
		$q = "SELECT maxjob.*, path.path "
			."FROM ApMaxLikeJobData AS maxjob "
			."LEFT JOIN ApPathData as path ON "
			."  maxjob.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists("ApMaxLikeRunData")) {
			$q .= "LEFT JOIN ApMaxLikeRunData as maxrun ON "
			."  maxrun.`REF|ApMaxLikeJobData|job` = maxjob.`DEF_id` ";
		}
		$q .=	"WHERE "
			."  maxjob.`project|projects|project` = '$projectId' "
			." AND "
			."  maxjob.`finished` = '1' "
			." AND "
			."  maxjob.`hidden` != '1' ";
		if ($this->mysql->SQLTableExists("ApMaxLikeRunData")) {
			$q .= " AND "
			."  maxrun.`REF|ApMaxLikeJobData|job` IS NULL ";
		}
			$q .=	" ORDER BY maxjob.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusteringStacks ($sessionId, $projectId, $showHidden=False) {
		$q = "SELECT cluster.`DEF_id` AS clusterid, clusterrun.*, cluster.*, pd.`path` "
			."FROM ApClusteringStackData AS cluster "
			."LEFT JOIN ApClusteringRunData AS clusterrun ON "
			." (cluster.`REF|ApClusteringRunData|clusterrun` = clusterrun.`DEF_id`) "
			."LEFT JOIN ApAlignStackData AS ast ON "
			." (clusterrun.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApStackData AS st ON "
			." (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			." (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			." (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."LEFT JOIN ApAlignAnalysisRunData AS analysis ON "
			."  (analysis.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApPathData AS pd ON "
			."  (cluster.`REF|ApPathData|path` = pd.`DEF_id`) "
			."WHERE "
			." strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden)
			$q.= " AND cluster.`hidden` != 1 AND ast.`hidden` != 1 AND analysis.`hidden` != 1 ";
		$q .= "ORDER BY clusterid DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getAlignStackIdsWithCluster ($sessionId, $projectId) {
		$q = "SELECT DISTINCT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApClusteringRunData AS clusterrun ON "
			."  (clusterrun.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApClusteringStackData AS cluster ON "
			."  (cluster.`REF|ApClusteringRunData|clusterrun` = clusterrun.`DEF_id`) "
			."LEFT JOIN ApStackData AS st ON "
			."  (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			."  (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			."  (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."LEFT JOIN ApAlignAnalysisRunData AS analysis ON "
			."  (analysis.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."WHERE "
			."  strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."AND "
			."  ast.`hidden` != 1 "
			."AND "
			."  analysis.`hidden` != 1 "
			."AND "
			."  cluster.`hidden` != 1 "
			."AND "
			."  clusterrun.`DEF_id` IS NOT NULL "
			."ORDER BY alignstackid DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getAlignStackIdFromClusterId ($clusterId) {
		$q = "SELECT DISTINCT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApClusteringRunData AS clusterrun ON "
			."  (clusterrun.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApClusteringStackData AS cluster ON "
			."  (cluster.`REF|ApClusteringRunData|clusterrun` = clusterrun.`DEF_id`) "
			."WHERE "
			."  cluster.`DEF_id` = '$clusterId' "
			."ORDER BY alignstackid DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r[0]['alignstackid'];
	}

	function getClusteringStacksForAlignStack ($alignstackId, $showHidden=false) {
		$q = "SELECT cluster.`DEF_id` AS clusterid, path.path AS path, clusterrun.*, cluster.* ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= ", spider.* ";
		}
		$q .=	"FROM ApClusteringStackData AS cluster "
			."LEFT JOIN ApClusteringRunData as clusterrun ON "
			." (cluster.`REF|ApClusteringRunData|clusterrun`=clusterrun.`DEF_id`) "
			."LEFT JOIN ApPathData as path ON "
			." (cluster.`REF|ApPathData|path`=path.`DEF_id`) ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= "LEFT JOIN ApSpiderClusteringParamsData as spider ON "
			." (clusterrun.`REF|ApSpiderClusteringParamsData|spiderparams`=spider.`DEF_id`) ";
		}
		$q .= "WHERE "
			."  clusterrun.`REF|ApAlignStackData|alignstack` = $alignstackId ";
		if (!$showHidden)
			$q.= " AND cluster.`hidden` != 1 ";
		$q .= "ORDER BY clusterid DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getClusteringRunParams ($clusterrunid) {
		$q = "SELECT clustrun.* "
			."FROM ApClusteringRunData AS clustrun "
			."WHERE clustrun.`DEF_id` = '$clusterrunid'";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r[0];
	}

	function getClusteringStackParams ($clusterstackid) {
		$q = "SELECT clustrun.*, cluststack.*, path.`path` AS path "
			."FROM ApClusteringStackData AS cluststack "
			."LEFT JOIN ApPathData AS path ON "
			."  (cluststack.`REF|ApPathData|path` = path.`DEF_id`) "
			."LEFT JOIN ApClusteringRunData AS clustrun ON "
			."  (cluststack.`REF|ApClusteringRunData|clusterrun` = clustrun.`DEF_id`) "
			."WHERE cluststack.`DEF_id` = '$clusterstackid'";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r[0];
	}

	function getClusteringRunsForAlignStack ($alignstackId, $showHidden=false) {
		$q = "SELECT clusterrun.`DEF_id` AS clusterrunid, "
			."  clusterrun.*, analysis.`REF|ApImagicAlignAnalysisData|imagicMSArun` ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= ", spider.* ";
		}
		$q .= "FROM ApClusteringRunData AS clusterrun ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= "LEFT JOIN ApSpiderClusteringParamsData as spider ON "
			." (clusterrun.`REF|ApSpiderClusteringParamsData|spiderparams`=spider.`DEF_id`) ";
		}
		$q .= "LEFT JOIN ApAlignAnalysisRunData as analysis ON "
			." (clusterrun.`REF|ApAlignAnalysisRunData|analysisrun`=analysis.`DEF_id`) "
			."WHERE "
			."  clusterrun.`REF|ApAlignStackData|alignstack` = $alignstackId "
			."ORDER BY clusterrunid DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getClusteringStacksForClusteringRun ($clusterrunId, $showHidden=false) {
		$q = "SELECT cluster.`DEF_id` AS clusterid, path.path AS path, "
			."  clusterrun.*, cluster.*, analysis.`REF|ApImagicAlignAnalysisData|imagicMSArun` ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= ", spider.* ";
		}
		$q .= "FROM ApClusteringStackData AS cluster "
			."LEFT JOIN ApClusteringRunData as clusterrun ON "
			." (cluster.`REF|ApClusteringRunData|clusterrun`=clusterrun.`DEF_id`) "
			."LEFT JOIN ApAlignAnalysisRunData as analysis ON "
			." (clusterrun.`REF|ApAlignAnalysisRunData|analysisrun`=analysis.`DEF_id`) "
			."LEFT JOIN ApPathData as path ON "
			." (cluster.`REF|ApPathData|path`=path.`DEF_id`) ";
		if ($this->mysql->SQLTableExists("ApSpiderClusteringParamsData")) {
			$q .= "LEFT JOIN ApSpiderClusteringParamsData as spider ON "
			." (clusterrun.`REF|ApSpiderClusteringParamsData|spiderparams`=spider.`DEF_id`) ";
		}
		$q .=	"WHERE "
			."  clusterrun.`DEF_id` = $clusterrunId ";
		if (!$showHidden)
			$q.= " AND cluster.`hidden` != 1 ";
		$q .= "ORDER BY clusterid DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	#--------- MAKE MASK FUNCTIONS---------------#

	function getMaskMakerRunIds ($sessionId) {
		$q = "select * "
			."from `ApMaskMakerRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskAssessRunIds ($sessionId) {
		$q = "select * "
			."from `ApMaskAssessmentRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function hasMaskMakerData ($sessionId) {
		$r= ($this->getLastMaskMakerRun($sessionId)) ? true : false;
		return $r;
	}

	function getLastMaskMakerRun ($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApMaskMakerRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}

	function getMaskMakerParams ($runId) {
		$q = "select * from ApMaskMakerRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);

		//print_r ($r);
		//echo $r['REF|ApMaskMakerParamsData|params'];
		$q = "select s.*, r.name, r.`REF|leginondata|SessionData|session` ";

		if ($r['REF|ApMaskMakerParamsData|params']) {
			$maskparamid=$r['REF|ApSelectionParamsData|params'];
			$q .= "from ApMaskMakerParamsData s "
				."left join ApMaskMakerRunData r on (s.`DEF_id` = r.`REF|ApMaskMakerParamsData|params`) "
				."LEFT JOIN ApPathData AS p ON "
				."(r.`REF|ApPathData|path`= p.`DEF_id`) ";
		}

		$q .= "where r.`DEF_id` = '$runId' ";
		//echo $q;
		$r=$this->mysql->getSQLResult($q);
		//print_r ($r);
		return $r;
	}

	function getMaskRegions ($runId) {
		$q="select r.DEF_id, r.x, r.y, r.area, r.mean, r.stdev "
			."from ApMaskRegionData r "
			."where r.`REF|ApMaskMakerRunData|maskrun` = ".$runId." ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskRegionStats ($runId, $inspect=False){
		$q="select count(r.`DEF_id`) as `totregions`, "
			."count(distinct r.`REF|leginondata|AcquisitionImageData|image`) as num, "
			."avg(r.area) as `areamean`, "
			."avg(r.mean) as `Imean`, "
			."avg(r.stdev) as `Istddev` "
						."from ApMaskRegionData r ";
		// use the latest inspection value. This should be changed later
		if ($inspect) {
						$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = r.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		$q.="r.`REF|ApMaskMakerRunData|maskrun` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];

	}

	function displayMaskRegionStats ($expId,$particleruns, $display_keys, $inspect=False, $selexval=False) {
		if (!is_array($particleruns))
			return ;
		$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr> <td> </td>";
		foreach($display_keys as $key) {
			$html .= "<td> <span class='datafield0'>".$key."</span> </td> ";
		}
		$html .= "</tr>";

		foreach ($particleruns as $particle) {
			$runId=$particle['DEF_id'];
			$regionstats = $this->getMaskRegionStats($runId, $inspect);
			$html .= "<tr>";
			$numregn=$regionstats['totregions'];
			$numimg=$regionstats['num'];
			$rpimg = ($numimg > 0) ? (sprintf("%.1f", $numregn/$numimg)) : 0;
			$regionstats['numimgs']=$numimg.'<BR>('.$rpimg.' regions/img)';
			$regionstats['img'] = '<a href="maskregiongraph.php?hg=1&run='.$runId.'">'
							.'<img border="0" '
							.'src="maskregiongraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `ApMaskMakerRunData` where `DEF_id` = $runId";
			$r = $this->mysql->getSQLResult($q);
			$r0 = $r[0];
			$html .= "<td><a target='params' href='maskrunreport.php?expId=$expId&rId=$runId'>".$r0['name']."</a></td>";
			foreach($display_keys as $field) {
							$data=$regionstats[$field];
				if (eregi('^areamean|^Imean|^Istddev', $field)) $data=format_sci_number($data,4);
				$html .= "<td> $data </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

	function getMaskAssessRunByName ($sessionId,$name){
		$q = "select * "
			."from `ApMaskAssessmentRunData` "
			."where "
			."`REF|leginondata|SessionData|session` = '$sessionId' AND "
			." `name` = '$name' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaskAssessNames ($sessionId){
		$q = "select `name` "
			."from `ApMaskAssessmentRunData` "
			."where `REF|leginondata|SessionData|session` = '$sessionId' "
			." group by `name` ";
		$r = $this->mysql->getSQLResult($q);
		if ($r) {
			$names=array();
			foreach ($r as $ra) $names[]=$ra[name];
		}
		return $names;
	}

	function getMaskAssessStats ($runId, $inspect=False){
		$q="select count(m.`keep`) as `totkeeps`, "
			."count(distinct r.`REF|leginondata|AcquisitionImageData|image`) as num "
						."from ApMaskAssessmentData m "
			."left join ApMaskRegionData r "
			." on m.`REF|ApMaskRegionData|region` = r.`DEF_id` ";
		// use the latest inspection value. This should be changed later
		if ($inspect) {
						$q.= "left join ApAssessmentData ad "
				."on (ad.`REF|leginondata|AcquisitionImageData|image` = r.`REF|leginondata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`REF|leginondata|AcquisitionImageData|image` = ad.`REF|leginondata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		$q.="m.`REF|ApMaskAssessmentRunData|run` = '$runId' AND "
			."m.`keep` = 1 ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];

	}

	#---------RECONSTRUCTION FUNCTIONS---------------#

	function getSymmetries($order=true) {
		$q="SELECT * "
			."FROM `ApSymmetryData`";
		if ($order)
			$q.=" order by symmetry ";
		$r=$this->mysql->getSQLResult($q);
		if (!$r) {
			echo "<font size='+2' color='#cc3333'> Major Error: no symmetry info found in database</font>\n";
			exit;
		}
		return $r;
	}

	function getSymInfo ($symId){
		return $this->getSymmetryInfo($symId);
	}

	function getSymmetryInfo($id) {
		$q="SELECT * "
			."FROM `ApSymmetryData` WHERE DEF_id = $id";
		list($r)=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getSymmetryDataFromEmanName($emansym) {
		$q="SELECT * "
			."FROM `ApSymmetryData` "
			."WHERE eman_name = '$emansym' "
			."LIMIT 1 ";
		#echo $q."<br/>";
		$r = $this->mysql->getSQLResult($q);
		#echo print_r($r[0])."<br/>";
		return $r[0];
	}

	function getModelsFromProject ($projectId, $getHidden=False) {
		$q="SELECT i.*, p.path "
			."FROM `ApInitialModelData` i "
			."LEFT JOIN `ApPathData` p "
			." ON (p.`DEF_id` = i.`REF|ApPathData|path`) "
			."WHERE i.`project|projects|project`='$projectId' ";
		if (!$getHidden) $q.= "AND (i.`hidden` IS NULL OR i.`hidden` = 0) ";
		$q.= "ORDER BY i.`DEF_id` DESC";
		//echo $q."\n<BR/>\n";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function updateExemplar($table, $id, $value) {
		$q = "SELECT exemplar "
			."FROM `".$table."` "
			."WHERE `DEF_id`=".$id." ";
		$olddata = $this->mysql->getSQLResult($q);
		if (array_key_exists('exemplar',$olddata[0])) {
			$data = array();
			$data['exemplar']=$value;
			$where = array('DEF_id'=>$id);
			$this->mysql->SQLUpdate($table,$data,$where);
		}
	}

	function getMiscInfoFromProject ($projectId) {
		$q="SELECT i.*, p.path "
			."FROM `ApMiscData` i "
			."LEFT JOIN `ApPathData` p "
			." ON (p.`DEF_id` = i.`REF|ApPathData|path`) "
			."WHERE i.`project|projects|project`='$projectId' "
			."ORDER BY i.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getJobIdsFromSession($expId, $jobtype=False, $status=False, $ignore=True) {
		$q="SELECT j.*, "
			."p.path as appath "
			."FROM `ApClusterJobData` AS j "
			."LEFT JOIN `ApPathData` AS p ON "
			."(j.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE j.`REF|leginondata|SessionData|session` = $expId";
		if ($jobtype) $q.=" AND j.`jobtype` = '$jobtype'";
		if ($status) $q.=" AND j.`status` = '$status'";
		if ($ignore) $q.=" AND j.`status` != 'I'";
		$q.=" ORDER BY j.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getFscFromRefinementDataId ($id) {
		$q = "SELECT * "
			."FROM ApFSCData "
			."WHERE `REF|ApRefinementData|refinementData` = $id "
			."ORDER BY pix";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getJobInfoFromId($jobid) {
		$q="SELECT j.*, "
			."p.path as appath, "
			."d.path as dmfpath, "
			."c.path as clusterpath "
			."FROM `ApClusterJobData` AS j "
			."LEFT JOIN ApPathData AS p ON "
			."(j.`REF|ApPathData|path` = p.`DEF_id`) "
			."LEFT JOIN ApPathData AS d ON "
			."(j.`REF|ApPathData|dmfpath` = d.`DEF_id`) "
			."LEFT JOIN ApPathData AS c ON "
			."(j.`REF|ApPathData|clusterpath` = c.`DEF_id`) "
			."WHERE j.`DEF_id` = $jobid";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getJobFileFromPath($path,$name) {
		$q="SELECT j.*, p.path "
			."FROM `ApClusterJobData` AS j "
			."LEFT JOIN ApPathData AS p ON "
			."(j.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE p.`path` = '$path' AND j.`name` = '$name'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function insertClusterJobData($host,$pathdir,$dmfpathdir,$clusterdir,$name,$expId,$jobtype,$user=NULL) {
		// put appion path in db
		$q = "SELECT DEF_id "
			."FROM `ApPathData` "
			."WHERE `path`='$pathdir'";
		$r = $this->mysql->getSQLResult($q);
		$pathid=$r[0]['DEF_id'];
		if (!$pathid) {
			$pdata['path']=$pathdir;
			$pathid=$this->mysql->SQLInsert('ApPathData',$pdata);
		}
		// put dmf path in db
		$q = "SELECT DEF_id "
			."FROM `ApPathData` "
			."WHERE `path`='$dmfpathdir'";
		$r = $this->mysql->getSQLResult($q);
		$dmfpathid=$r[0]['DEF_id'];
		if (!$dmfpathid) {
			$pdata['path']=$dmfpathdir;
			$dmfpathid=$this->mysql->SQLInsert('ApPathData',$pdata);
		}
		// put cluster path in db
		$q = "SELECT DEF_id "
			."FROM `ApPathData` "
			."WHERE `path`='$clusterdir'";
		$r = $this->mysql->getSQLResult($q);
		$clusterpathid=$r[0]['DEF_id'];
		if (!$clusterpathid) {
			$pdata['path']=$clusterdir;
			$clusterpathid=$this->mysql->SQLInsert('ApPathData',$pdata);
		}
		// find if job is in database
		$q = "SELECT DEF_id "
			."FROM `ApClusterJobData` "
			."WHERE `REF|ApPathData|path` = $pathid AND "
			."`name` = '$name' AND "
			."`REF|leginondata|SessionData|session` = $expId";
		$r = $this->mysql->getSQLResult($q);
		$jid=$r[0]['DEF_id'];
		// if not in database, insert
		if (!$jid) {
			$jdata['REF|ApPathData|path'] = $pathid;
			$jdata['name'] = $name;
			$jdata['jobtype'] = $jobtype;
			$jdata['REF|leginondata|SessionData|session'] = $expId;
			$jdata['REF|ApPathData|dmfpath'] = $dmfpathid;
			$jdata['REF|ApPathData|clusterpath'] = $clusterpathid;
			$jdata['cluster'] = $host;
			$jdata['user'] = $user;
			$jid=$this->mysql->SQLInsert('ApClusterJobData',$jdata);
		}
		return $jid;
	}

	function displayHidingOption($expId,$allruns,$shownruns,$show = False) {
		if (!$_GET['showHidden'] && count($allruns) != count($shownruns)) {
			$numhidden = count($allruns) - count($shownruns);
			$html = "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=1'>[Show ".$numhidden." hidden runs]</a><br/><br/>\n";
		} elseif ($_GET['showHidden']) {
			$html .= "<a href='".$_SERVER['PHP_SELF']."?expId=$expId&showHidden=0'>[Hide hidden runs]</a><br/><br/>\n";
		}
		return $html;
	}

	function updateDescription($table, $id, $newtext) {
		$q = "SELECT description "
			."FROM `".$table."` "
			."WHERE `DEF_id`=".$id." ";
		$olddata = $this->mysql->getSQLResult($q);
		if (array_key_exists('description',$olddata[0])) {
			$data = array();
			$data['description']=$newtext;
			$where = array('DEF_id'=>$id);
			$this->mysql->SQLUpdate($table,$data,$where);
		}
	}

	function updateHide($table, $id, $value) {
		$q = "SELECT hidden "
			."FROM `".$table."` "
			."WHERE `DEF_id`=".$id." ";
		$olddata = $this->mysql->getSQLResult($q);
		if (array_key_exists('hidden',$olddata[0])) {
			$data = array();
			$data['hidden']=$value;
			$where = array('DEF_id'=>$id);
			$this->mysql->SQLUpdate($table,$data,$where);
		}
	}

	function updateTableDescriptionAndHiding($post,$updatetable,$updateid) {
		//update description if posted
		if ($post['updateDesc'.$updateid]) {
			$this->updateDescription($updatetable, $updateid, $post['newdescription'.$updateid]);
		}
		//update hidden if posted
		if ($post['hideItem'.$updateid] == 'hide') {
			$this->updateHide($updatetable, $updateid, '1');
		} elseif ($_POST['unhideItem'.$updateid] == 'unhide') {
			$this->updateHide($updatetable, $updateid, '0');
		}
	}

	function updateClusterQueue($jobid,$queueid,$status) {
		$data = array('clusterjobid'=>$queueid);
		$data['status']=$status;
		$where = array('DEF_id'=>$jobid);
		$this->mysql->SQLUpdate('ApClusterJobData',$data,$where);
	}

	function abortClusterJob($jobid,$user=NULL) {
		$data = array('status'=>'A');
		$where = array('DEF_id'=>$jobid);
		if (!is_null($user)) $where['user'] = $user;
		$this->mysql->SQLUpdate('ApClusterJobData',$data,$where);
	}

	function getSubmittedJobs($expId) {
		$q="SELECT * "
			."FROM `ApClusterJobData` "
			."WHERE `REF|leginondata|SessionData|session`=$expId";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getReconIdFromClusterJobId ($jobid) {
		$q="SELECT * "
			."FROM `ApRefinementRunData` "
			."WHERE `REF|ApClusterJobData|jobfile` = $jobid";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getReconIdsFromSession ($sessionId, $showHidden=False) {
		$q = "SELECT DISTINCT(refrun.`DEF_id`) AS refid, refrun.*, path.path AS path  "
			." FROM `ApRefinementRunData` AS refrun "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			." ON refrun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden) $q.= " AND (refrun.`hidden` IS NULL OR refrun.`hidden` = 0) ";
		$q.= " ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getReconIterIdRelatedToStackid ($stackId, $showHidden=False) {
		// First get a three random particle ids from the stack id
		$q = "SELECT `REF|ApParticleData|particle` AS partid "
			." FROM ApStackParticlesData AS stpart "
			."WHERE `REF|ApStackData|stack` = '$stackId' "
			." ORDER BY RAND() LIMIT 3 ";
		//echo $q."<br/><br/>\n";
		$r1 = $this->mysql->getSQLResult($q);
		//echo print_r($r1)."<br/><br/>\n";
		$partId1 = $r1[0]['partid'];
		$partId2 = $r1[1]['partid'];
		$partId3 = $r1[2]['partid'];

		// Second get all recons using those particles
		$q = "SELECT refrun.* "
			." FROM ApParticleClassificationData AS refpart "
			."LEFT JOIN ApStackParticlesData AS stpart "
			." ON refpart.`REF|ApStackParticlesData|particle` = stpart.`DEF_id` "
			."LEFT JOIN ApRefinementData AS refiter "
			." ON refpart.`REF|ApRefinementData|refinement` = refiter.`DEF_id` "
			."LEFT JOIN ApRefinementRunData AS refrun "
			." ON refiter.`REF|ApRefinementRunData|refinementRun` = refrun.`DEF_id` "
			."WHERE "
			." stpart.`REF|ApParticleData|particle` = '$partId1' "
			."OR "
			." stpart.`REF|ApParticleData|particle` = '$partId2' "
			."OR "
			." stpart.`REF|ApParticleData|particle` = '$partId3' "
			." GROUP BY refrun.`DEF_id` "
			." ORDER BY refrun.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r2 = $this->mysql->getSQLResult($q);
		//echo print_r($r2)."<br/><br/>\n";
		return $r2;
	}

	function getExemplarReconsFromSession ($sessionId, $showHidden=False) {
		$q = "SELECT refdata.`DEF_id` as refdataid, "
			."refrun.`DEF_id` as refrunid, "
			."refdata.*, refrun.*, stackrun.*, runs.*, p.*, params.* "
			." FROM `ApRefinementData` AS refdata "
			."LEFT JOIN `ApRefinementRunData` AS refrun "
			. "ON refdata.`REF|ApRefinementRunData|refinementRun` = refrun.`DEF_id` "
			."LEFT JOIN `ApRefinementParamsData` AS params "
			." ON (refdata.`REF|ApRefinementParamsData|refinementParams` = params.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData as p "
			." ON refrun.`REF|ApPathData|path` = p.`DEF_id` "
			."WHERE refdata.exemplar = 1 "
			."AND stackrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden) $q.= " AND (refrun.`hidden` IS NULL OR refrun.`hidden` = 0) ";
		$q.= " ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	function getReconIds ($stackId, $showHidden=False) {
		$q = "SELECT * "
			."FROM `ApRefinementRunData` AS r ";
		if (!$showHidden)
			$q.= "LEFT JOIN ApStackData AS s "
				." ON r.`REF|ApStackData|stack` = s.`DEF_id` ";
		$q.= "WHERE r.`REF|ApStackData|stack` = '$stackId'";
		if (!$showHidden)
			$q.= " AND (s.`hidden` IS NULL OR s.`hidden` = 0) "
				." AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		$q.= "ORDER BY r.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRefinementRunInfo($refinementRun) {
		$q="select r.*, p.path "
			."FROM `ApRefinementRunData` AS r "
			."LEFT JOIN ApPathData AS p ON "
			."(r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$refinementRun' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getPostProcsFromRefId($refid, $getHidden=False) {
		$q = "SELECT d.*, "
			."p.path as path , a.path as amppath "
			."FROM `Ap3dDensityData` AS d "
			."LEFT JOIN `ApPathData` AS p ON "
			."(d.`REF|ApPathData|path` = p.`DEF_id`) "
			."LEFT JOIN `ApPathData` AS a ON "
			."(d.`REF|ApPathData|ampPath` = a.`DEF_id`) "
			."WHERE d.`REF|ApRefinementData|iterid` = $refid ";
		if (!$getHidden) $q.= "AND (d.`hidden` IS NULL OR d.`hidden` = 0) ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getDensityIdFromFile($rundir,$filename) {
	$q = "SELECT d.`DEF_id` "
			."FROM `Ap3dDensityData` AS d "
			."LEFT JOIN ApPathData AS p ON "
			."(d.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE d.`name` LIKE '$filename' "
			."AND p.`path` LIKE '$rundir' ";
	list($r) = $this->mysql->getSQLResult($q);
		return $r['DEF_id'];
	}

	function get3dDensityInfo ($densityId) {
		$q = "SELECT d.*,p.path "
				."FROM `Ap3dDensityData` AS d "
				."LEFT JOIN ApPathData AS p ON "
				."(d.`REF|ApPathData|path` = p.`DEF_id`) "
				."WHERE d.`DEF_id` = '$densityId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getInitModelInfo ($modelId) {
		$q = "SELECT d.*,p.path "
				."FROM `ApInitialModelData` AS d "
				."LEFT JOIN ApPathData AS p ON "
				."(d.`REF|ApPathData|path` = p.`DEF_id`) "
				."WHERE d.`DEF_id` = '$modelId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getResolutionInfo ($resId) {
		$q = "SELECT * "
				."FROM `ApResolutionData` WHERE `DEF_id` = '$resId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRMeasureInfo ($resId) {
		$q = "SELECT * "
				."FROM `ApRMeasureData` WHERE `DEF_id` = '$resId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHighestResForRecon ($reconid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas "
				."FROM `ApRefinementData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefinementRunData|refinementRun` = '$reconid' "
				//."ORDER by rmeas.rMeasure ";
				."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getHighestRMeasureForRecon ($reconid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas "
				."FROM `ApRefinementData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefinementRunData|refinementRun` = '$reconid' "
				."ORDER by rmeas.rMeasure ";
				//."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getIterationInfo ($reconId,$iteration=0) {
		$q = "SELECT * "
				."FROM `ApRefinementData` r "
				."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconId' "
				."ORDER BY r.`iteration` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($r[0]['REF|ApRefinementParamsData|refinementParams']) {
			$q = "SELECT * "
					."FROM `ApRefinementData` r "
					."LEFT JOIN `ApRefinementParamsData` p "
					."ON (r.`REF|ApRefinementParamsData|refinementParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconId' "
					."ORDER BY r.`iteration` ASC ";
		} elseif ($r[0]['REF|ApXmippRefineIterationParamsData|xmippRefineParams']) {
			$q = "SELECT * "
					."FROM `ApRefinementData` r "
					."LEFT JOIN `ApXmippRefineIterationParamsData` p "
					."ON (r.`REF|ApXmippRefineIterationParamsData|xmippRefineParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconId' "
					."ORDER BY r.`iteration` ASC ";
		}
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		if ($iteration >0) {
			return $r[$iteration-1];
		}
		return $r;
	}

	function getRefinementData ($refinementRun,$iteration=False) {
		$q = "SELECT * "
			."FROM `ApRefinementData` "
			."WHERE `REF|ApRefinementRunData|refinementRun` = $refinementRun ";
		if ($iteration) $q.="AND `iteration` = $iteration";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParamsFromRefinementDataId ($refinementId) {
		$q = "SELECT * "
				."FROM `ApRefinementData` r "
				."LEFT JOIN `ApRefinementParamsData` p "
				."ON (r.`REF|ApRefinementParamsData|refinementParams` = p.`DEF_id`) "
				."WHERE r.`DEF_id` = $refinementId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getStackFromRefinement ($refinementDataId) {
		$q = "SELECT r.*, rr.*, s.*, path.path "
				."FROM `ApRefinementData` r "
				."LEFT JOIN `ApRefinementRunData` rr "
				."ON (r.`REF|ApRefinementRunData|refinementRun` = rr.`DEF_id`) "
				."LEFT JOIN `ApStackData` s "
				."ON (rr.`REF|ApStackData|stack` = s.`DEF_id`) "
				."LEFT JOIN `ApPathData` path "
				."ON (s.`REF|ApPathData|path` = path.`DEF_id`) "
				."WHERE r.`DEF_id` = $refinementDataId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSubsetParticlesInStack ($refinementDataId, $subset, $refinetype='EMAN', $count=False) {
		//check for cached values
		$q = "SELECT * "
			."FROM `ApRefineGoodBadParticleData` gb "
			."WHERE gb.`REF|ApRefinementData|refine` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		if (count($r) && $count) {
			//using cached values
			if ($refinetype == 'SpiCoran') {
				if ($subset=='bad')
					return $r[0]['bad_coran'];
				else
					return $r[0]['good_coran'];
			} elseif ($refinetype == 'MsgP') {
				if ($subset=='bad')
					return $r[0]['bad_msgp'];
				else
					return $r[0]['good_msgp'];
			} else {
				if ($subset=='bad')
					return $r[0]['bad_normal'];
				else
					return $r[0]['good_normal'];
			}
		}
		//Fall back to old method
		$q = "SELECT particleNumber as p ";
		if ($count) $q = "SELECT count(particleNumber) as p ";
		$q .= "FROM `ApParticleClassificationData` apcd "
			."LEFT JOIN `ApStackParticlesData` aspd "
			."ON (apcd.`REF|ApStackParticlesData|particle` = aspd.`DEF_id`) "
			."WHERE apcd.`REF|ApRefinementData|refinement` = '$refinementDataId' ";
		switch ($refinetype) {
			case 'EMAN':
				if ($subset=='bad') $q.="AND `thrown_out` = 1 ";
				elseif ($subset=='good') $q.="AND `thrown_out` is NULL ";
				break;
			case 'SpiCoran':
				if ($subset=='bad') $q.="AND `coran_keep` = 0 ";
				elseif ($subset=='good') $q.="AND `coran_keep` = 1 ";
				break;
			case 'MsgP':
				if ($subset=='bad') $q.="AND `msgp_keep` = 0 ";
				elseif ($subset=='good') $q.="AND `msgp_keep` = 1 ";
				break;
		}
		if (!$count) $q.= "ORDER BY aspd.`DEF_id` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($count) return $r[0]['p'];
		return $r;
	}

	function getPreparedFrealignJobs ($jobid=False, $path=False) {
		$q = "SELECT fre.*, path.path  "
			. " FROM `ApFrealignPrepareData` AS fre "
			. " LEFT JOIN ApPathData AS path ON ( fre.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " LEFT JOIN ApClusterJobData AS job ON ( fre.`REF|ApClusterJobData|job` = job.`DEF_id` ) ";
		if ($jobid) {
			$q .= " WHERE fre.`DEF_id` = '$jobid' ";
		} elseif ($path) {
			$q .= " WHERE path.`path` = '$path' ";
		}
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusterJobByTypeAndPath ($type, $path) {
		$q = "SELECT job.*  "
			. " FROM `ApClusterJobData` AS job "
			. " LEFT JOIN ApPathData AS path "
			. "  ON ( job.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " WHERE "
			. "  path.`path` = '$path' "
			. " AND "
			. "  job.`jobtype` = '$type' ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getRawStackFromCluster ($clusterStackId) {
		$q = "SELECT asd.*, path.path "
			. " FROM `ApClusteringParticlesData` acpd "
			. " LEFT JOIN ApAlignParticlesData aapd ON ( acpd.`REF|ApAlignParticlesData|alignparticle` = aapd.`DEF_id` ) "
			. " LEFT JOIN ApStackParticlesData aspd ON ( aapd.`REF|ApStackParticlesData|stackpart` = aspd.`DEF_id`) "
			. " LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( asd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE acpd.`REF|ApClusteringStackData|clusterstack` = '$clusterStackId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRawStackFromAlign ($alignStackId) {
		$q = "SELECT asd.*, path.path "
			. " FROM ApAlignParticlesData aapd "
			. " LEFT JOIN ApStackParticlesData aspd ON ( aapd.`REF|ApStackParticlesData|stackpart` = aspd.`DEF_id`) "
			. " LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( asd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE aapd.`REF|ApAlignStackData|alignstack` = '$alignStackId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getAlignedStackFromCluster ($clusterStackId) {
		$q = "SELECT aasd.*, path.path "
			. " FROM `ApClusteringParticlesData` acpd "
			. " LEFT JOIN ApAlignParticlesData aapd ON ( acpd.`REF|ApAlignParticlesData|alignparticle` = aapd.`DEF_id` ) "
			. " LEFT JOIN ApAlignStackData aasd ON ( aapd.`REF|ApAlignStackData|alignstack` = aasd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( aasd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE acpd.`REF|ApClusteringStackData|clusterstack` = '$clusterStackId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getAlignedStackFromAlign ($alignStackId) {
		$q = "SELECT aasd.*, path.path "
			. " FROM ApAlignParticlesData aapd "
			. " LEFT JOIN ApAlignStackData aasd ON ( aapd.`REF|ApAlignStackData|alignstack` = aasd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( aasd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE aapd.`REF|ApAlignStackData|alignstack` = '$alignStackId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSubsetParticlesFromCluster ($clusterStackId, $refnums, $count=False) {
		$q = "SELECT particleNumber as p ";
		if ($count) $q = "SELECT count(particleNumber) as p ";
		$q .= "FROM `ApClusteringParticlesData` acpd "
			."LEFT JOIN ApAlignParticlesData aapd ON ( acpd.`REF|ApAlignParticlesData|alignparticle` = aapd.`DEF_id` )"
			."LEFT JOIN ApStackParticlesData aspd ON ( aapd.`REF|ApStackParticlesData|stackpart` = aspd.`DEF_id`)"
			."LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`)"
			."WHERE acpd.`REF|ApClusteringStackData|clusterstack` = '$clusterStackId' AND (";

		foreach ($refnums as $refnum) {
			$refnum = strval(intval($refnum)+1);
			$q .= " acpd.`refnum` = '$refnum' OR ";
		}

		$q = substr($q, 0, -3);
		$q .= ")";

		//if (!$count) $q.= "ORDER BY aspd.`DEF_id` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($count) return $r[0]['p'];
		return $r;
	}

	function getSubsetParticlesFromAlign ($alignStackId, $refnums, $count=False) {
		$q = "SELECT particleNumber as p ";
		if ($count) $q = "SELECT count(particleNumber) as p ";
		$q .= "FROM `ApAlignParticlesData` aapd "
			."LEFT JOIN ApAlignReferenceData aard ON ( aapd.`REF|ApAlignReferenceData|ref` = aard.`DEF_id`)"
			."LEFT JOIN ApStackParticlesData aspd ON ( aapd.`REF|ApStackParticlesData|stackpart` = aspd.`DEF_id`)"
			."LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`)"
			."WHERE aapd.`REF|ApAlignStackData|alignstack` = '$alignStackId' AND (";

		foreach ($refnums as $refnum) {
			$refnum = strval(intval($refnum)+1);
			$q .= " aard.`refnum` = '$refnum' OR ";
		}

		$q = substr($q, 0, -3);
		$q .= ")";

		//if (!$count) $q.= "ORDER BY aspd.`DEF_id` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($count) return $r[0]['p'];
		return $r;
	}

	function getNumBadParticles ($refinementDataId, $refinetype='EMAN' ) {
		$r = $this->getSubsetParticlesInStack($refinementDataId, 'bad',$refinetype);
		return count($r);
	}

	function getNumGoodParticles ($refinementDataId, $refinetype='EMAN' ) {
		$r = $this->getSubsetParticlesInStack($refinementDataId, 'good',$refinetype);
		return count($r);
	}

	function listAllStackParticles ($stackId) {
		$q="SELECT sp.`particleNumber`, db.`MRC|image`, "
			."p.`xcoord` , p.`ycoord` "
			."FROM  `ApStackParticlesData` sp "
			."LEFT JOIN ApParticleData p ON "
			."( sp.`REF|ApParticleData|particle` = p.`DEF_id` ) "
			."LEFT JOIN ".DB_LEGINON.".AcquisitionImageData db ON "
			."( p.`REF|leginondata|AcquisitionImageData|image` = db.`DEF_id` ) "
			."WHERE sp.`REF|ApStackData|stack`=$stackId";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getAverageMedianJump ($refineRunId) {
		$q = "SELECT "
			."COUNT(e.`median`) AS count, "
			."AVG(e.`median`) AS average, "
			."STDDEV(e.`median`) AS stdev "
			."FROM ApEulerJumpData AS e "
			."WHERE "
			."  e.`REF|ApRefinementRunData|refRun` = '$refineRunId' "
			."GROUP BY e.`REF|ApRefinementRunData|refRun` ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getEulerJumps ($refineRunId) {
		$q="SELECT "
			."  e.`DEF_id`, "
			."  e.`median` "
			."FROM ApEulerJumpData AS e "
			."WHERE "
			."  e.`REF|ApRefinementRunData|refRun` = '$refineRunId' ";
			//."ORDER BY e.`median` "
			//."LIMIT 100 ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	// no more ApEulerData tables
	//function getParticleEuler ($refinementDataId) {
	//	$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
	//		."FROM `ApParticleClassificationData` "
	//		."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
	//	$r = $this->mysql->getSQLResult($q);
	//	return $r;
	//}

	//function getNumInClass ($refinementDataId,$eulerId) {
	//	$q = "SELECT count(DEF_id) as num "
	//		."FROM `ApParticleClassificationData` "
	//		."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
	//		."AND `REF|ApEulerData|eulers` = $eulerId";
	//	list($r) = $this->mysql->getSQLResult($q);
	//	return $r['num'];
	//}

	function getEulerAngles ($eulerId) {
		$q = "SELECT * "
			."FROM `ApEulerData` "
			."WHERE `DEF_id` = $eulerId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getCommonParticles ($refine1, $refine2) {
		# compare 2 iterations, get all the particles that were used in both
		# reconstructions (ignore those that were thrown out) and return the eulers"
		$q = "SELECT cls1.`REF|ApStackParticlesData|particle` as prtl, "
				."spd.particleNumber, "
				."cls1.euler1 as euler1_1, "
				."cls1.euler2 as euler1_2, "
				."cls1.euler3 as euler1_3, "
				."cls2.euler1 as euler2_1, "
				."cls2.euler2 as euler2_2, "
				."cls2.euler3 as euler2_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls2.`shiftx` as shiftx2, "
				."cls1.`shifty` as shifty1, "
				."cls2.`shifty` as shifty2, "
				."cls1.`euler3` as rot1, "
				."cls2.`euler3` as rot2, "
				."cls1.`quality_factor` as qf1, "
				."cls2.`quality_factor` as qf2 "
				."FROM (`ApParticleClassificationData` as cls1) "
				."LEFT JOIN ( "
				." `ApParticleClassificationData` as cls2, "
				." `ApStackParticlesData` as spd) "
				//." `ApEulerData` euler1, `ApEulerData` euler2) "
				."ON ( "
				."cls1.`REF|ApStackParticlesData|particle`=cls2.`REF|ApStackParticlesData|particle` "
				."AND spd.DEF_id=cls1.`REF|ApStackParticlesData|particle` "
				."AND cls1.`thrown_out` is NULL AND cls2.`thrown_out` is NULL "
				//."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				//."AND euler2.DEF_id=cls2.`REF|ApEulerData|eulers` "
				.") "
				."WHERE (cls1.`REF|ApRefinementData|refinement`=$refine1 "
				."AND cls2.`REF|ApRefinementData|refinement`=$refine2 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlesFromRefinementId($refine1) {
		# compare 2 iterations, get all the particles that were used in both
		# reconstructions (ignore those that were thrown out) and return the eulers"
		$q = "SELECT cls1.`REF|ApStackParticlesData|particle` as prtl, "
				."spd.particleNumber, "
				."cls1.euler1 as euler1_1, "
				."cls1.euler2 as euler1_2, "
				."cls1.euler3 as euler1_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls1.`shifty` as shifty1, "
				."cls1.`inplane_rotation` as rot1, "
				."cls1.`quality_factor` as qf1 "
				."FROM (`ApParticleClassificationData` as cls1) "
				."LEFT JOIN ( "
				." `ApStackParticlesData` as spd) "
				//." `ApEulerData` euler1) "
				."ON ( "
				."spd.DEF_id=cls1.`REF|ApStackParticlesData|particle` "
				."AND cls1.`thrown_out` is NULL "
				//."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				.") "
				."WHERE ( "
				." cls1.`REF|ApRefinementData|refinement`=$refine1 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParticleNum ($particleId) {
					$q = "SELECT particleNumber "
					."FROM `ApStackParticlesData` "
					."WHERE `DEF_id` = $particleId";
					list($r) = $this->mysql->getSQLResult($q);
					return $r['particleNumber'];
		}

	function getMiscInfoFromReconId ($reconid) {
		$q = "SELECT m.*, p.path "
		."FROM `ApMiscData` AS m "
		."LEFT JOIN ApPathData AS p ON "
		."(m.`REF|ApPathData|path` = p.`DEF_id`) "
		."WHERE m.`REF|ApRefinementRunData|refinementRun` = $reconid";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getEulerStats($reconId, $iterId1, $iterId2) {
		$q = "SELECT difference, eulers, mean from `ApProcEulerData` "
		." WHERE `reconId`=$reconId AND `iter1`=$iterId1 AND `iter2`=$iterId2";
		$r=$this->mysql->getSQLResult($q);

		return $r;
	}

	function getReconInfoFromRefinementId($refineid) {
		$q="SELECT *"
		."FROM "
		."`ApRefinementData` AS `ApRefinementData` "
		."LEFT JOIN `ApRefinementRunData` AS `ApRefinementRunData` "
		."ON (`ApRefinementRunData`.`DEF_id`=`ApRefinementData`.`REF|ApRefinementRunData|refinementRun`) "
		."LEFT JOIN `ApPathData` AS `ApPathData` "
		."ON (`ApPathData`.`DEF_id`=`ApRefinementRunData`.`REF|ApPathData|path`) "
		."WHERE `ApRefinementData`.`DEF_id`=$refineid ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function insertEulerStats($stats) {
		$mean = $stats->myMean;
		$errors = $stats->myData;
		$reconId=$stats->myReconId;
		$iterId1=$stats->myIterId1;
		$iterId2=$stats->myIterId2;
		$eulers=$stats->eulers1;
		$min = $stats->myMin;
		$max = $stats->myMax;
		$stdev = $stats->myStandardDeviation;

		$euler = array_map('simplify',$eulers);

		$table="ApProcEulerData";
		# $this->mysql->SQLInsert($table, $data);
		$q = "SELECT DEF_id from `ApProcEulerData` "
				." WHERE `reconId`=$reconId AND `iter1`=$iterId1 AND `iter2`=$iterId2";
			//--- print_r($r=$this->mysql->SQLQuery($q));
			//--- if (!$r=$this->mysql->getSQLResult($q)) {
					$q = "INSERT INTO `ApProcEulerData` "
							."(`reconId`, `iter1`, `iter2`, `difference`, `eulers`, `mean`, `min`, `max`, `stdev`) "
							." VALUES "
							."($reconId, $iterId1, $iterId2, "
							."'".implode(",",$errors)."',"
							."'".implode(",",$euler)."',"
							."$mean, $min, $max, $stdev)";
					$r=$this->mysql->SQLQuery($q);
					if ($e=$this->mysql->getError()) {
							echo "error -> $e \n";
							exit;
					}
			//--- }
		return $r;

	}

	function getAlignParticleNumber($alignId) {
		$q="SELECT "
			."  ref.`refnum` AS classNumber, "
			."  count(part.`DEF_id`) as number,  "
			."  ROUND(ref.`ssnr_resolution`,3) AS resolution "
			."FROM ApAlignParticlesData AS part "
			."LEFT JOIN ApAlignReferenceData AS ref "
			."  ON (part.`REF|ApAlignReferenceData|ref` = ref.`DEF_id`) "
			."WHERE part.`REF|ApAlignStackData|alignstack` = '$alignId' "
			."GROUP BY ref.`refnum` "
			."ORDER BY ref.`refnum` ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getAlignParticleData ($alignid) {
		$q="SELECT "
			."  a.`partnum`, "
			."  a.`spread`, "
			."  a.`correlation`, "
			."  a.`score` "
			."FROM ApAlignParticlesData AS a "
			."WHERE "
			."  a.`REF|ApAlignStackData|alignstack` = '$alignid' ";
			//."ORDER BY e.`median` "
			//."LIMIT 100 ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusteringParticleNumber($clusterId) {
		$q="SELECT part.`refnum` AS classNumber, "
			."  COUNT(part.`DEF_id`) AS number, "
			."  ROUND(ref.`ssnr_resolution`,3) AS resolution "
			."FROM ApClusteringParticlesData AS part "
			."LEFT JOIN ApClusteringReferenceData AS ref "
			."  ON (part.`REF|ApClusteringReferenceData|clusterreference` = ref.`DEF_id`) "
			."WHERE part.`REF|ApClusteringStackData|clusterstack` = '$clusterId' "
			."GROUP BY part.`refnum` "
			."ORDER BY part.`refnum` ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getNumberOfRctRuns($sessionId, $showHidden=False) {
		$q="SELECT count(rctrun.`DEF_id`) AS number "
			."FROM ApRunsInStackData as runsin "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApRctRunData AS rctrun "
			."  ON rctrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."WHERE strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( rctrun.`hidden` = 0 OR rctrun.`hidden` IS NULL ) ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo $r[0]['number']."<br/><br/>\n";
		return $r[0]['number'];
	}

	function getNumberOfOtrRuns($sessionId, $showHidden=False) {
		$q="SELECT count(otrrun.`DEF_id`) AS number "
			."FROM ApRunsInStackData as runsin "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApOtrRunData AS otrrun "
			."  ON otrrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."WHERE strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( otrrun.`hidden` = 0 OR otrrun.`hidden` IS NULL ) ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo $r[0]['number']."<br/><br/>\n";
		return $r[0]['number'];
	}

	function getRctRunsFromSession($sessionId, $showHidden=False) {
		$q="SELECT rctrun.*, "
			."  path.`path` AS path, "
			."  rmeas.`half` AS rmeas, "
			."  fsc.`half` AS fsc, "
			."  fsc.`fscfile` AS fscfile, "
			."  stparam.`boxSize` AS boxsize "
			."FROM ApRunsInStackData as runsin "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApRctRunData AS rctrun "
			."  ON rctrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackParamsData AS stparam "
			."  ON strun.`REF|ApStackParamsData|stackParams` = stparam.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			."  ON rctrun.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApResolutionData AS rmeas "
			."  ON rctrun.`REF|ApResolutionData|rmeasure_resolution` = rmeas.`DEF_id` "
			."LEFT JOIN ApResolutionData AS fsc "
			."  ON rctrun.`REF|ApResolutionData|fsc_resolution` = fsc.`DEF_id` "
			."WHERE "
			."  rctrun.`DEF_id` IS NOT NULL "
			."AND "
			."  strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( rctrun.`hidden` = 0 OR rctrun.`hidden` IS NULL ) ";
		$q .= "ORDER BY rctrun.`DEF_id` DESC ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getRctRunDataFromId($rctId) {
		$q="SELECT rctrun.*, "
			."  path.`path` AS path, "
			."  rmeas.`half` AS rmeas, "
			."  fsc.`half` AS fsc, "
			."  fsc.`fscfile` AS fscfile, "
			."  stparam.`boxSize` AS boxsize "
			."FROM ApRctRunData as rctrun "
			."LEFT JOIN ApRunsInStackData AS runsin "
			."  ON rctrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApStackParamsData AS stparam "
			."  ON strun.`REF|ApStackParamsData|stackParams` = stparam.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			."  ON rctrun.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApResolutionData AS rmeas "
			."  ON rctrun.`REF|ApResolutionData|rmeasure_resolution` = rmeas.`DEF_id` "
			."LEFT JOIN ApResolutionData AS fsc "
			."  ON rctrun.`REF|ApResolutionData|fsc_resolution` = fsc.`DEF_id` "
			."WHERE "
			."  rctrun.`DEF_id` = '$rctId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getOtrRunsFromSession($sessionId, $showHidden=False) {
		$q="SELECT otrrun.*, "
			."  path.`path` AS path, "
			."  rmeas.`half` AS rmeas, "
			."  fsc.`half` AS fsc, "
			."  fsc.`fscfile` AS fscfile, "
			."  stparam.`boxSize` AS boxsize "
			."FROM ApRunsInStackData as runsin "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApOtrRunData AS otrrun "
			."  ON otrrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackParamsData AS stparam "
			."  ON strun.`REF|ApStackParamsData|stackParams` = stparam.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			."  ON otrrun.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApResolutionData AS rmeas "
			."  ON otrrun.`REF|ApResolutionData|rmeasure_resolution` = rmeas.`DEF_id` "
			."LEFT JOIN ApResolutionData AS fsc "
			."  ON otrrun.`REF|ApResolutionData|fsc_resolution` = fsc.`DEF_id` "
			."WHERE "
			."  otrrun.`DEF_id` IS NOT NULL "
			."AND "
			."  strun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( otrrun.`hidden` = 0 OR otrrun.`hidden` IS NULL ) ";
		$q .= "ORDER BY otrrun.`DEF_id` DESC ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getOtrRunDataFromId($otrId) {
		$q="SELECT otrrun.*, "
			."  path.`path` AS path, "
			."  rmeas.`half` AS rmeas, "
			."  fsc.`half` AS fsc, "
			."  fsc.`fscfile` AS fscfile, "
			."  stparam.`boxSize` AS boxsize "
			."FROM ApOtrRunData as otrrun "
			."LEFT JOIN ApRunsInStackData AS runsin "
			."  ON otrrun.`REF|ApStackData|tiltstack` = runsin.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS strun "
			."  ON (runsin.`REF|ApStackRunData|stackRun` = strun.`DEF_id`) "
			."LEFT JOIN ApStackParamsData AS stparam "
			."  ON strun.`REF|ApStackParamsData|stackParams` = stparam.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			."  ON otrrun.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApResolutionData AS rmeas "
			."  ON otrrun.`REF|ApResolutionData|rmeasure_resolution` = rmeas.`DEF_id` "
			."LEFT JOIN ApResolutionData AS fsc "
			."  ON otrrun.`REF|ApResolutionData|fsc_resolution` = fsc.`DEF_id` "
			."WHERE "
			."  otrrun.`DEF_id` = '$otrId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function get3dDensitysFromSession($sessionId, $showHidden=False) {
		$q="SELECT "
			."  dens.*, "
			."  path.`path` AS path ";
		if ($this->mysql->SQLTableExists('ApRefinementData')) {
			$q .= ", iterid.`REF|ApRefinementRunData|refinementRun` AS refrun ";
		}
		$q .=	"FROM Ap3dDensityData as dens "
			."LEFT JOIN ApPathData AS path "
			."  ON dens.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists('ApRefinementData')) {
			$q .=	"LEFT JOIN ApRefinementData AS iterid "
				."  ON dens.`REF|ApRefinementData|iterid` = iterid.`DEF_id` ";
		}
		$q .= "WHERE "
			."  dens.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( dens.`hidden` = 0 OR dens.`hidden` IS NULL ) ";
		$q .= "ORDER BY dens.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo print_r($r[0])."<br/><br/>\n";
		return $r;
	}

	function get3dDensityFromId($densityId) {
		$q="SELECT "
			."  dens.*, "
			."  path.`path` AS path ";
		if ($this->mysql->SQLTableExists('ApRefinementData')) {
			$q .= ", iterid.`REF|ApRefinementRunData|refinementRun` AS refrun ";
		}
		$q .=	"FROM Ap3dDensityData as dens "
			."LEFT JOIN ApPathData AS path "
			."  ON dens.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists('ApRefinementData')) {
			$q .=	"LEFT JOIN ApRefinementData AS iterid "
				."  ON dens.`REF|ApRefinementData|iterid` = iterid.`DEF_id` ";
		}
		$q .= "WHERE "
			."  dens.`DEF_id` = '$densityId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getAngularReconstitutionRuns($sessionId) {
		$q="SELECT "
			."  ar.*, "
			."  path.`path` AS path "
			."FROM ApBootstrappedAngularReconstitutionRunData as ar "
			."LEFT JOIN ApPathData AS path "
			."  ON ar.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApTemplateStackData AS ts "
			."  ON ar.`REF|ApTemplateStackData|templatestackid` = ts.`DEF_id` "
			."LEFT JOIN ApClusteringStackData AS clusterstack "
			."  ON ar.`REF|ApClusteringStackData|clusterid` = clusterstack.`DEF_id` "
			."LEFT JOIN ApClusteringRunData AS clusterrun ON "
			." (clusterstack.`REF|ApClusteringRunData|clusterrun` = clusterrun.`DEF_id`) "
			."LEFT JOIN ApAlignStackData AS ast ON "
			." (clusterrun.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`) "
			."LEFT JOIN ApStackData AS stack "
			."  ON ast.`REF|ApStackData|stack` = stack.`DEF_id` "
			."LEFT JOIN ApRunsInStackData AS runsinstack "
			."  ON stack.`DEF_id` = runsinstack.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			."  ON stackrun.`DEF_id` = runsinstack.`REF|ApStackRunData|stackRun` "
			."WHERE "
			."  stackrun.`REF|leginondata|SessionData|session` = '$sessionId'";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getImagic3dRefinementRunsFromSessionId($sessionId) {
		$q="SELECT "
			."  refinement.*, "
			."  path.`path` AS path "
			."FROM ApImagic3dRefineRunData as refinement "
			."LEFT JOIN ApPathData AS path "
			."  ON refinement.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApStackData AS stack "
			."  ON refinement.`REF|ApStackData|stackrun` = stack.`DEF_id` "
			."LEFT JOIN ApRunsInStackData AS runsinstack "
			."  ON stack.`DEF_id` = runsinstack.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			."  ON stackrun.`DEF_id` = runsinstack.`REF|ApStackRunData|stackRun` "
			."WHERE "
			."  stackrun.`REF|leginondata|SessionData|session` = '$sessionId'";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getImagic3dRefinementParamsFromRefineId ($refineId) {
		$q = "SELECT param.*, run.*, pd.path, symmetry.symmetry "
			."FROM ApImagic3dRefineRunData as run "
			."LEFT JOIN ApImagic3dRefineIterationData as param "
			."  ON (param.`REF|ApImagic3dRefineRunData|refinement_run`=run.`DEF_id`) "
			."LEFT JOIN ApPathData AS pd ON "
			."  (run.`REF|ApPathData|path` = pd.`DEF_id`) "
			."LEFT JOIN ApSymmetryData as symmetry "
			."  ON param.`REF|ApSymmetryData|symmetry`=symmetry.`DEF_id` "
			."WHERE run.`DEF_id` = '$refineId'";
		$r = $this->mysql->getSQLResult($q);

		return $r;
	}

	//------ -------------------- ---------//
	//------ Loop again functions ---------//
	//------ -------------------- ---------//

	function getLoopProgramRuns () {
		$q = "SELECT DISTINCT "
			."  progrun.`DEF_id` AS id "
			."FROM ScriptProgramRun as progrun "
			."LEFT JOIN ScriptParamValue AS paramvalue "
			."  ON paramvalue.`REF|ScriptProgramRun|progrun` = progrun.`DEF_id` "
			."LEFT JOIN ScriptParamName AS paramname "
			."  ON paramvalue.`REF|ScriptParamName|paramname` = paramname.`DEF_id` "
			."WHERE "
			."  progrun.`REF|ApClusterJobData|job` IS NOT NULL "
			."AND "
			."  paramname.`name` = 'preset' "
			."; ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getProgramRunParams ($progrunid) {
		$q = "SELECT "
			."  progrun.`DEF_id` AS id,  "
			."  progname.`name` AS progname,  "
			."  progrun.`runname` AS runname,  "
			."  session.`name` AS sessionname,  "
			."  username.`name` AS username "
			."FROM ScriptProgramRun as progrun "
			."LEFT JOIN ScriptProgramName AS progname "
			."  ON progrun.`REF|ScriptProgramName|progname` = progname.`DEF_id` "
			."LEFT JOIN ScriptUserName AS username "
			."  ON progrun.`REF|ScriptUserName|username` = username.`DEF_id` "
			."LEFT JOIN ApClusterJobData AS job "
			."  ON progrun.`REF|ApClusterJobData|job` = job.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".SessionData AS session "
			."  ON job.`REF|leginondata|SessionData|session` = session.`DEF_id` "
			."WHERE "
			."  progrun.`DEF_id` = $progrunid "
			."; ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r[0])."<br/><br/>\n";
		return $r[0];
	}

	function getProgramCommands ($progrunid) {
		$q = "SELECT "
			."  paramvalue.*, paramname.*,  "
			."  session.`name` AS sessionname  "
			."FROM ScriptParamValue as paramvalue "
			."LEFT JOIN ScriptParamName AS paramname "
			."  ON paramvalue.`REF|ScriptParamName|paramname` = paramname.`DEF_id` "

			."LEFT JOIN ScriptProgramRun AS progrun "
			."  ON paramvalue.`REF|ScriptProgramRun|progrun` = progrun.`DEF_id` "
			."LEFT JOIN ApClusterJobData AS job "
			."  ON progrun.`REF|ApClusterJobData|job` = job.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".SessionData AS session "
			."  ON job.`REF|leginondata|SessionData|session` = session.`DEF_id` "

			."WHERE "
			."  paramvalue.`REF|ScriptProgramRun|progrun` = $progrunid "
			."ORDER BY LENGTH(paramvalue.`value`) "
			."; ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

}

function simplify($e) {
	return $e['a'].','.$e['b'].','.$e['c'];
}

function displayCTFstats($stats, $display_keys) {
	if (!is_array($stats) || !is_array($display_keys))
		return ;
	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
	foreach($stats as  $field=>$data) {
		if (!$head) {
			$head = true;
			$html .= "<th>\n";
			foreach($display_keys as $kh) {
				$html .= "<td><span class='datafield0'>".$kh."</span></td>";
			}
			$html .= "</th>\n";
		}
		$html .= "<tr>\n";
		$html .= "<td rowspan='".(count($data)+1)."'><span class='datafield0'>".$field."</span></td>\n";
		foreach($data as $row) {
			$html .= "<tr>\n";
			foreach($display_keys as $key) {
				if (!is_array($row))
					continue;
				if (array_key_exists($key, $row))
					$val = $row[$key];
				else
					continue;
				if (eregi('defocus', $key))
						$val = format_micro_number($val);
				if (eregi('^min|^max|^avg|^stddev', $key))
					if (eregi('defocus', $field) || eregi('nominal', $field)) {
							$val = format_micro_number($val);
					} else {
						$val = format_sci_number($val, 3);
					}
				$html .= "<td>";
				$html .= " ".$val."<br>\n";
				$html .= "</td>";
			}
			$html .= "</tr>\n";
		}
		$html .= "</tr>\n";
	}
	$html .= "</table>";
	return $html;
}

function displayCTFdata($data, $display_keys) {
	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
		$html .= "<tr>\n";
		foreach($display_keys as $key) {
			$html .= "<th>";
			$html .= " ".$key."<br>\n";
			$html .= "</th>";
		}
		$html .= "</tr>\n";
		$html .= "<tr>\n";
		foreach($data as $row) {
			foreach($display_keys as $key) {
					$val = $row[$key];
					if (eregi('defocus', $key)) {
							$val = format_micro_number($val);
					}
				$html .= "<td>";
				$html .= " ".$val."<br>\n";
				$html .= "</td>";
			}
			$html .= "</tr>\n";
		}
	$html .= "</table>";
	return $html;
}

?>
