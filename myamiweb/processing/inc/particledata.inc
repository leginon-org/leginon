<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see	http://leginon.org
 */

// if the config file is not exist, redirect to setup wizard.
if( !file_exists(dirname(__FILE__).'/../../config.php') ){

	$location = 'location:'.substr($_SERVER['REQUEST_URI'], 0, -11).'setup/index.php';
	header($location);
	exit();
}

define('DS', "/");
require_once dirname(__FILE__).'/../../config.php';
require_once "inc/mysql.inc";
require_once "inc/path.inc";

class particledata {

	var $crlf="\n";
	var $baseurl=PROCESSING_BASE_URL;
	var $ace_method_map=array(
					'ace1'=>array('ApAceParamsData','aceparams'),
					'ace2'=>array('ApAce2ParamsData','ace2_params'),
					'ctffind'=>array('ApCtfTiltParamsData','ctftilt_params'),
					'ctffind4'=>array('ApCtfFind4ParamsData','ctffind4_params'),
					'xmipp'=>array('ApXmippCtfParamsData','xmipp_ctf_params'),
					);

	function particledata () {
		$this->mysql = new mysql(
					DB_HOST,
					DB_USER,
					DB_PASS,
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

	function getSEMDataFromId ($imageId) {
		$q = "SELECT * "
			."FROM ApSEMData"
			." WHERE "
			."`REF|leginondata|AcquisitionImageData|image` = '$imageId' "
			."LIMIT 1 ";
			$r = $this->mysql->getSQLResult($q);
			return $r[0];
	}
	
	function getImageNameFromId ($imageId) {
		$q = "SELECT "
			."img.filename "
			."FROM ".DB_LEGINON.".AcquisitionImageData as img "
			."WHERE "
			."  img.`DEF_id` = '$imageId' "
			."LIMIT 1 ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		$filename = $r[0]['filename'];
		//echo "$filename<br/><br/>\n";
		return $filename;
	}

	function getImageDimensionFromId($imageId) {
		$q = "SELECT "
			."c.`SUBD|dimension|x` dx, c.`SUBD|dimension|y` dy "
			."FROM ".DB_LEGINON.".AcquisitionImageData as img "
			."LEFT JOIN ".DB_LEGINON.".CameraEMData as c "
			."on img.`REF|CameraEMData|camera`=c.`DEF_id` "
			."WHERE "
			."  img.`DEF_id` = '$imageId' "
			."LIMIT 1 ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		$dx = $r[0]['dx'];
		$dy = $r[0]['dy'];
		//echo "$filename<br/><br/>\n";
		return array('x'=>$dx,'y'=>$dy);
	}

	function getPhasePlateInfoFromImageId($imageId) {
		//if (!$this->mysql->SQLTableExists(DB_LEGINON.".PhasePlateUsageData")) return false;
		$q = "SELECT "
			."c.`phase plate number` pp_number, c.`patch position` patch_pos "
			."FROM ".DB_LEGINON.".AcquisitionImageData as img "
			."LEFT JOIN ".DB_LEGINON.".PhasePlateUsageData as c "
			."on img.`REF|PhasePlateUsageData|phase plate`=c.`DEF_id` "
			."WHERE "
			."  img.`DEF_id` = '$imageId' "
			."LIMIT 1 ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		//echo "$filename<br/><br/>\n";
		return $r[0];
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

	function getFilenamesFromLabel($runId, $label) {
		$q = "select "
			."distinct p.`REF|leginondata|AcquisitionImageData|image` as `id`, i.`MRC|Image` as `name` "
			."from ApParticleData p "
			."left join ".DB_LEGINON.".AcquisitionImageData i "
			."on (i.DEF_id = p.`REF|leginondata|AcquisitionImageData|image`) "
			."where "
			."p.`REF|ApSelectionRunData|selectionrun`=".$runId." and "
			."p.label='".$label."'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	//------ -------------------- ---------//
	//------ General DB summary functions ---------//
	//------ -------------------- ---------//

	function getTotalAceStats(){
		// Note: this is only used in procsummary.php and needs to be updated
		$q = "SELECT count(DISTINCT `REF|ApAceRunData|acerun`) AS runs, "
			."COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS img "
			."FROM `ApCtfData` ";
		$r = $this->mysql->getSQLResult($q);
		$results = $r[0];
		// seems weird to have hard coded confidence check
		$q = "SELECT COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) as i "
			.$this->getAppionConfidenceScoreSelect('ApCtfData')." "
			."FROM `ApCtfData` "
			."WHERE (confidence_appion >=0.8)";
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
			."LEFT JOIN `ApStackParticleData` AS p "
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
			."FROM `ApStackParticleData`";
		$r = $this->mysql->getSQLResult($q);
		$results['particles']=$r[0]['p'];
		return $results;
	}

	function getTotalReconStats(){
		$q = "SELECT count(*) AS particles, "
			."COUNT(DISTINCT p.`REF|ApRefineIterData|refineIter`) AS iter, "
			."COUNT(DISTINCT i.`REF|ApRefineRunData|refineRun`) AS runs "
			."FROM `ApRefineIterData` AS i "
			."LEFT JOIN `ApRefineParticleData` AS p "
			."ON i.`DEF_id` = p.`REF|ApRefineIterData|refineIter` ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSloppyTotalReconStats(){
		$q = "SELECT count(*) AS i "
			."FROM `ApRefineIterData`";
		$r = $this->mysql->getSQLResult($q);
		$results=array();
		$results['iter']=$r[0]['i'];
		$q = "SELECT count(*) AS p "
			."FROM `ApRefineParticleData`";
		$r = $this->mysql->getSQLResult($q);
		$results['particles']=$r[0]['p'];
		$q = "SELECT count(*) AS r "
			."FROM `ApRefineRunData`";
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
		// This gives the method and parameter-of-the-method id of an alignment run
		$q =  "SELECT a.`DEF_id` as `alignrun id`, "
			."a.name as `alignrun name`, "
			."a.bin as bin, "
			."a.badAlign as badAlign, "
			."path.`path`, "
			."tilt.`number` as `tilt number`, "
			."tia.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries, ";
		if ($this->mysql->SQLTableExists('ApImodXcorrParamsData')) {
			$q .= "a.`REF|ApImodXcorrParamsData|coarseImodParams` as imodid, "
				."imod.`FilterSigma1` as sigma1, "
				."imod.`FilterSigma2` as sigma2, "
				."imod.`FilterRadius2` as radius2, ";
		}
		if ($this->mysql->SQLTableExists('ApRaptorParamsData')) {
			$q .= "a.`REF|ApRaptorParamsData|raptorParams` as raptorid, "
				 ."";
		}
		if ($this->mysql->SQLTableExists('ApProtomoParamsData')) {
			$q .= "a.`REF|ApProtomoParamsData|fineProtomoParams` as protomoid, "
				 ."";
		}
		$q .= ""
			."a.`REF|leginondata|TomographySettingsData|coarseLeginonParams` as xleginonid, "
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
		if ($this->mysql->SQLTableExists('ApRaptorParamsData')) {
			$q .= ""
				."LEFT JOIN `ApRaptorParamsData` raptor "
				."ON a.`REF|ApRaptorParamsData|raptorParams` = raptor.`DEF_id` ";
		}
		$q .= ""
			."LEFT JOIN `ApTiltsInAlignRunData` tia "
			."ON tia.`REF|ApTomoAlignmentRunData|alignrun` = a.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".`TiltSeriesData` tilt ON tia.`REF|leginonData|TiltSeriesData|tiltseries` = tilt.`DEF_id` "
			."WHERE a.`DEF_id` = " .$alignrunId;
		list($r) = $this->mysql->getSQLResult($q);
		if ($r['protomoid']) {
			$r['method'] = 'protomo';
		} elseif ($r['raptorid']) {
			$r['method'] = 'raptor';
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
		// Workaround the possibility of missing these fields in appion_extra.xml
		// refs #1223
		$refinefields = $this->mysql->getFields('ApProtomoRefinementParamsData');
		$fselect =  (in_array('SUBD|alibox|x',$refinefields)) ? 
			" f.`SUBD|alibox|x` as `align box x`, "
			." f.`SUBD|alibox|y` as `align box y`, "
			:'';
			
		// Protomo has more than one iteration(cycle)
		$q = " SELECT a.`DEF_id` as alignerid, "
			." a.`REF|ApTomoAlignmentRunData|alignrun` as `alignrunid`, "
			." a.`REF|ApProtomoRefinementParamsData|refine_cycle` as `cycleid`, "
			." a.`REF|ApProtomoRefinementParamsData|good_cycle` as `goodid`, "
			." p.`series_name`, "
			." f.`cycle` as `refine cycle`, "
			." g.`cycle` as `good cycle`, "
			." f.`alismp` as `align sampling`, "
			.$fselect
			." f.`cormod`, "
			." f.`imgref`as `refnum`, "
			." f.`REF|leginondata|AcquisitionImageData|reference` as `refimg`, "
			#." f.`imgref` as `imgref number`, "
			." a.* "
			."FROM `ApTomoAlignerParamsData` a "
			."LEFT JOIN `ApProtomoRefinementParamsData` f "
			."ON a.`REF|ApProtomoRefinementParamsData|refine_cycle` = f.`DEF_id` "
			."LEFT JOIN `ApProtomoRefinementParamsData` g "
			."ON a.`REF|ApProtomoRefinementParamsData|good_cycle` = g.`DEF_id` "
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

	function getAlignerInfo($alignerid) {
		$q = " SELECT ar.`DEF_id` as alignerid, "
			." FROM `ApTomoAlignerParamsData` ar "
			."WHERE ar.`DEF_id`=".$alignerid." ";
		$r = $this->mysql->getSQLResult($q);

		if (!$r[0]['REF|ApProtomoParamsData|protomo']) {
			$q = " SELECT ar.`DEF_id` as alignerid, "
			." arun.`DEF_id` as alignrunid, "
			." arun.`name` as runname, "
			." arun.`bin` as bin, "
			." path.`path`, "
			." tilts.`REF|leginondata|TiltSeriesData|tiltseries` as `tiltseries` "
			." FROM `ApTomoAlignerParamsData` ar "
			."LEFT JOIN `ApTomoAlignmentRunData` arun "
			."ON ar.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApTiltsInAlignRunData` tilts "
			."ON tilts.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApPathData` path "
			."ON arun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE ar.`DEF_id`=".$alignerid." "
			."AND tilts.`primary_tiltseries` = 1 ";
			$r = $this->mysql->getSQLResult($q);
			return $r;
		} else {
			return $this->getProtomoAlignmentInfo($alignerid);
		}
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
			."ON ar.`REF|ApProtomoRefinementParamsData|refine_cycle` = r.`DEF_id` "
			."LEFT JOIN `ApTomoAlignmentRunData` arun "
			."ON ar.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApTiltsInAlignRunData` tilts "
			."ON tilts.`REF|ApTomoAlignmentRunData|alignrun` = arun.`DEF_id` "
			."LEFT JOIN `ApPathData` path "
			."ON arun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE ar.`DEF_id`=".$alignerid." "
			."AND tilts.`primary_tiltseries` = 1 ";
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
		if ($r['REF|ApTomoReconParamsData|reconparam']) $has_param=True;

		$q =  "SELECT t.`DEF_id` as DEF_id, ";
		if ($has_run) {
			$q .= "r.`runname` as runname, "
				."r.`method` as `recon method`, ";
		}
		if ($has_param) {
			$q .= "pa.`tilt_angle_offset`, "
				."pa.`z_shift`, "
				."pa.`tilt_axis_tilt_out_xyplane`, "
				."pa.`tilt_axis_rotation_in_xyplane`, ";
		}
		$q .= "t.name as tomofilename, "
			."t.description as description, "
			."t.`REF|leginondata|TiltSeriesData|tiltseries` as tiltseries, "
			."tilt.number as 'tiltseries number', "
			." p.`path` as path, "
			."t.`REF|ApTomoAlignerParamsData|aligner` as aligner, "
			."t.`REF|leginondata|AcquisitionImageData|zprojection` as zproj_id, "
			." t.`hidden` ";
		if ($has_run && $this->mysql->FieldExists('ApFullTomogramRunData','SEQ|excluded'))
			$q .= ", r.`SEQ|excluded` as 'excluded imageIds' ";
		$q .= "FROM `ApFullTomogramData` t ";
		if ($has_run) {
			$q .= "LEFT JOIN `ApFullTomogramRunData` r ON t.`REF|ApFullTomogramRunData|reconrun` = r.`DEF_id` "
				."LEFT JOIN `ApPathData` p ON r.`REF|ApPathData|path` = p.`DEF_id` ";
		} else {
			$q .= "LEFT JOIN `ApPathData` p ON t.`REF|ApPathData|path` = p.`DEF_id` ";
		}
		if ($has_param) {
			$q .= "LEFT JOIN `ApTomoReconParamsData` pa ON t.`REF|ApTomoReconParamsData|reconparam` = pa.`DEF_id` ";
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

	function getUnfinishedETomoRunsFromSession($sessionId) {
		$q =  "SELECT t.* "
			.", p.path as rundir "
			."FROM `ApFullTomogramRunData` t "
			."LEFT JOIN `ApPathData` p "
			."ON p.`DEF_id` = t.`REF|ApPathData|path` "
			."WHERE t.`REF|leginondata|SessionData|session` = " .$sessionId." "
			."AND t.`method` LIKE 'etomo' ";
		$runs = $this->mysql->getSQLResult($q);
		if (!is_array($runs) || count($runs)==0) return array();

		$ready_for_etomo = array();
		// only include ones with no full tomogram record in the database
		foreach ($runs as $r) {
			$q = "SELECT `DEF_id` "
				."FROM `ApFullTomogramData` "
				."WHERE `REF|ApFullTomogramRunData|reconrun`=".$r['DEF_id'];
			$tomos = $this->mysql->getSQLResult($q);
			if ( !is_array($tomos) || count($tomos) == 0)
				$ready_for_etomo[]= $r;
		}
		return $ready_for_etomo;
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
			."FROM `ApStackParticleData` as st  "
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
			."LEFT JOIN `ApStackParticleData` stackp "
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
			."avgtp.`z_shift` as zshift, "
			."p.`REF|ApAlignStackData|alignstack` as `alignstack` "
			."FROM `ApTomoAvgParticleData` avgtp "
			."LEFT JOIN `ApTomogramData` sub "
			."ON  avgtp.`REF|ApTomogramData|subtomo` = sub.DEF_id "
			."LEFT JOIN `ApAlignParticleData` p "
			."ON  avgtp.`REF|ApAlignParticleData|aligned_particle` = p.DEF_id "
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
				if ($data['refine_cycle'] != 0) {
					$showmethod = $runinfo['method'];
					$showstr = str_pad(': itr '.$data['refine_cycle'], $length, ' ', STR_PAD_LEFT).'. ';
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

	function hasLocalCtfData($sessionId) {
		$d = ($this->getLastLocalCtfRun($sessionId)) ? true : false;
		return $d;
	}

	function getLastLocalCtfRun($sessionId) {
		$q = "select max(acerun.DEF_id) as runId "
			."from ApAceRunData AS acerun "
			."LEFT JOIN ApCtfFind4ParamsData AS params "
			."ON (acerun.`REF|ApCtfFind4ParamsData|ctffind4_params` = params.DEF_id) "
			."WHERE acerun.`REF|leginondata|SessionData|session`='$sessionId' "
			."AND params.local_refine=1";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getLastCtfRun($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApAceRunData` where `REF|leginondata|SessionData|session`='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getLastCtfTiltRun($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApAceRunData` where (`REF|leginondata|SessionData|session`='$sessionId' "
			."AND `REF|ApCtfTiltParamsData|ctftilt_params` IS NOT NULL) ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}

	function getCtfRunIds($sessionId, $showHidden=False, $ctffind=False) {
		$q = "SELECT * "
			."FROM `ApAceRunData` AS a "
			."WHERE "
			."  `REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden )
			$q .= " AND ( a.`hidden` = 0 OR a.`hidden` IS NULL ) ";
		if ($ctffind) 
			$q .= " AND `REF|ApCtfTiltParamsData|ctftilt_params` IS NOT NULL ";
		$q .= "ORDER BY a.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	// Note, this method needs to be updated each time a new CTF method is added to the database.
	function getCtfRunMethod( $acerunId )
	{
		$q = "SELECT *, path.`path` as path, acerun.`DEF_id` as acerun "
			."FROM ApAceRunData AS acerun "
			."LEFT JOIN ApPathData AS path "
			."  ON (path.`DEF_id` = acerun.`REF|ApPathData|path`) "
			."where acerun.`DEF_id` = '$acerunId'";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		if ($r) $result = end($r);
		//print_r($r)."<br/><br/>\n";

		foreach ($this->ace_method_map as $k=>$p ) {
			$ref= "REF|$p[0]|$p[1]";
			if (in_array($ref, array_keys($result)) && is_numeric($result[$ref])) {
				$method = $k;
				break;
			}
		}
		if (empty($method)) {
			$method = "unknown";
		}
		
		//echo $method."<br/><br/>\n";
		return $method;
	}
	
	function getAceParams($acerunId) {
		$method = $this->getCtfRunMethod( $acerunId );
		if ($method == 'unknown') {
			$j = '';
		} else {
			$p = $this->ace_method_map[$method];
			$j = "LEFT JOIN $p[0] AS $method "
						."  ON ($method.`DEF_id` = acerun.`REF|$p[0]|$p[1]`) ";
		}
		$q = "SELECT *, path.`path` as path, acerun.`DEF_id` as acerun "
			."FROM ApAceRunData AS acerun "
			.$j
			."LEFT JOIN ApPathData AS path "
			."  ON (path.`DEF_id` = acerun.`REF|ApPathData|path`) "
			."where acerun.`DEF_id` = '$acerunId'";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);

		//echo print_r($r)."<br/><br/>\n";
		if ($r) return end($r);
	}

	function getPhaseShiftString($table_alias='c') {
		//To be back compatible, extra_phase_shift is set to 0.0 if field not exists
		$has_phase_shift = $this->mysql->FieldExists('ApCtfData','extra_phase_shift');
		if ( $has_phase_shift ) {
			$phase_shift_select = "c.`extra_phase_shift`, ";
		} else {
			$phase_shift_select = "'0.0' as `extra_phase_shift`, ";
		}
		return $phase_shift_select;
	}

	function getCtfInfo($runId) {
		// ctf info of all images in a run without sorting
		$phase_shift_select = $this->getPhaseShiftString('c');
		$q =	"select "
			."c.`REF|leginondata|AcquisitionImageData|image` as imageid, "
			// ScopeEMData timestamp is not changed after DD frame alignment
			."unix_timestamp(s.`DEF_timestamp`) as unix_timestamp, "
			."s.`defocus`, "
			."c.`defocus1`, "
			."c.`defocus2`, "
			."c.`defocusinit`, "
			."c.`amplitude_contrast`, "
			."c.`angle_astigmatism`, "
			.$phase_shift_select
			."c.`REF|ApAceRunData|acerun`, "  //Needed in checking if there is result.
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
			."c.`confidence_30_10` , "
			."c.`confidence_5_peak` , "
			."c.`resolution_80_percent` , "
			."c.`resolution_50_percent` , "
			."c.`ctffind4_resolution` , "
			."c.`confidence_d` , "
			.$this->getAppionConfidenceScoreSelect('c')." , "
			."c.`snr` , "
			."c.`graph1` , "
			."c.`graph2` "
			."from ApCtfData c left join ApAceRunData r on (c. `REF|ApAceRunData|acerun` = r.`DEF_id`) "
			."left join ".DB_LEGINON.".AcquisitionImageData i on (c.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join ".DB_LEGINON.".ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where c.`REF|ApAceRunData|acerun`='$runId'";
			
		return $this->mysql->getSQLResult($q);
		
	}

	function getCtfInfoFromImageId($imageId, $order=false, $method='', $acerunId='') {
		$phase_shift_select = $this->getPhaseShiftString('c');
		$local_plot_select = ($this->mysql->FieldExists('ApCtfData','localplot')) ? "c.localplot, ": "";
		$q =	"select "
			."c.`DEF_id`, "
			."c.`REF|leginondata|AcquisitionImageData|image`, "
			."s.`defocus`, "
			."c.`defocus1`, "
			."c.`defocus2`, "
			."c.`defocusinit`, "
			."c.`amplitude_contrast`, "
			."c.`angle_astigmatism`, "
			.$phase_shift_select
			."c.`tilt_angle`, "
			."c.`tilt_axis_angle`, "
			."c.`confidence` , "
			."c.`confidence_d` , "
			."c.`cross_correlation` , "
			.$this->getAppionConfidenceScoreSelect('c')." , "
			."c.`snr` , "
			."r.`DEF_id` as acerunId , "
			."r.`name` as runname , "
			."p.`path`, "
			."c.`graph1` , "
			."c.`graph2` , "
			."c.`graph3` , "
			."c.`graph4` , "
			.$local_plot_select
			."c.`confidence_30_10` , "
			."c.`confidence_5_peak` , "
			."c.`resolution_80_percent` , "
			."c.`resolution_50_percent` , "
			."c.`ctffind4_resolution` , "
			."(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference "
			."from ApCtfData c "
			."left join(ApAceRunData r, ApPathData p) "
			."on ( r.DEF_id=c.`REF|ApAceRunData|acerun` and p.DEF_id=r.`REF|ApPathData|path`) "
			."left join ".DB_LEGINON.".AcquisitionImageData i "
			."on (c.`REF|leginondata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join ".DB_LEGINON.".ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where c.`REF|leginondata|AcquisitionImageData|image`='$imageId' ";
		$q .= " AND c.`graph1` IS NOT NULL ";
		$q .= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		if (is_numeric($acerunId) && $acerunId > 0) {
			$q .= "AND r.`DEF_id`=".$acerunId." ";
		} else {
			if (array_search($method, array_keys($this->ace_method_map))!== false) {
				$p = $this->ace_method_map[$method];
				$q .= "AND r. `REF|$p[0]|$p[1]` IS NOT NULL ";
			}
		}

		// Ordering Results
		if ($order) {
			$fields = $order['fields'];
			$q .= " order by ".join(", ",$fields);
		} else {
			$q .= $this->getBestCTFOrder('c');
		}
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getBestCTFOrder($ctftable_alias='c', $skip_appion=false) {
		// First order by ctffind4_resolution which also records equiphase resolution from gctf.  Then sort by res80. If some entries of res80 are null, they will be sorted as 999 and end up at the end of the list.
		// Then sort by res50. If there was a tie from res80, the tie is broken with res50.
		// Res80 and res50 are only set for newer versions of Appion. For runs that were mase with older versions, we still want to sort by
		// cross_correlation (ctffind) and confidence (ace1 and ace2). After sorting by resolution, old runs should all be tied with 999, so the
		// final sort will sort by whichever is not null, the ctffind correlation or the Appion overall conf.
		$c = (empty($ctftable_alias)) ? '':$ctftable_alias.'.';
		$q .= "	ORDER BY coalesce(".$c."ctffind4_resolution,999) ASC ";
		$q .= "	, coalesce(".$c."resolution_80_percent,999) ASC ";
		$q .= " , coalesce(".$c."resolution_50_percent,999) ASC ";
		$q .= " , coalesce(".$c."`cross_correlation`, ";
		// appion merged values are not available in quick stat query.
		if (!$skip_appion) $q.= "confidence_appion, ";
		$q .= " 0.0) DESC ";
		return $q;
	}

	function getAppionConfidenceScoreSelect($ctftable_alias='c') {
		$c = $ctftable_alias;
		$q = "greatest(coalesce(".$c.".confidence, 0), coalesce(".$c.".confidence_d,0), coalesce(".$c.".confidence_30_10,0), coalesce(".$c.".confidence_5_peak,0)) as confidence_appion ";
		return $q;
	}

	function getAppionResolutionSelect($ctftable_alias='c') {
		//FIX ME:This makes AppionResolution different from the resolution used in ordering.
		$c = $ctftable_alias;
		$q = "least(coalesce(".$c.".resolution_50_percent, 999.0), coalesce(".$c.".resolution_80_percent,999.0), coalesce(".$c.".ctffind4_resolution,999.0)) as resolution_appion ";
		return $q;
	}

	function getBestCtfInfoByResolution($sessionId, $limit=false) {
		// This is used in download, report and aceimage display.
		// This should be the standard. 
		// selection of the result for a image is BestCtfOrder.
		// May put limit to what image result to return,
		// use resolution_appion as limit matrix.
		$q = "SELECT  ctfdata.* "
			."FROM "
			."	( "
			."	SELECT  "
			."		i.`filename`, "
			."		i.`DEF_id` AS imageid, "
			."		p.`name`, "
			."		s.`defocus`, "
			."		s.`defocus` AS nominal_defocus, "
			// ScopeEMData timestamp is not changed after DD frame alignment
			."    unix_timestamp(s.`DEF_timestamp`) as unix_timestamp, "
			."		2*ABS(ctf.defocus1-ctf.defocus2)/(ctf.defocus1+ctf.defocus2) AS difference_from_mean, "
			."		(ctf.`defocus1`+ctf.`defocus2`)/2+s.`defocus` as difference_from_nom, "
			.$this->getAppionConfidenceScoreSelect('ctf').", "
			.$this->getAppionResolutionSelect('ctf').", "
			."		ctf.* "
			."	FROM ".PARTICLE_DB.".`ApCtfData` AS ctf "
			."	LEFT JOIN ".DB_LEGINON.".`AcquisitionImageData` AS i ON (i.`DEF_id` = ctf.`REF|leginondata|AcquisitionImageData|image`) "
			."	LEFT JOIN ".DB_LEGINON.".`PresetData` AS p ON (p.DEF_id = i.`REF|PresetData|preset`) "
			." LEFT JOIN ".DB_LEGINON.".`ScopeEMData` AS s ON (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			." LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer "
			."  ON viewer.`REF|AcquisitionImageData|image` = ctf.`REF|leginondata|AcquisitionImageData|image` "
			."	where "
			."	ctf.`REF|leginondata|AcquisitionImageData|image` IN  "
			."	( "
			."		SELECT a.`DEF_id` from ".DB_LEGINON.".`AcquisitionImageData` AS a  "
			."		WHERE a.`REF|SessionData|session`='$sessionId'  "
			."	AND  "
			."  ABS(s.`SUBD|stage position|a`) < 0.9  "
			."	AND  "
			." ( viewer.status IS NULL OR viewer.status != 'hidden' ) "
			."		)  "
			.$this->getBestCTFOrder('ctf')
			."	) ctfdata ";
		// if $limit is specified, report only values with confidences > $limit
		if ($limit) {
			$q .= " WHERE resolution_appion < $limit ";
		}
		$q .= " GROUP BY ctfdata.imageid ORDER BY ctfdata.unix_timestamp ";
		//echo $q."<br/><br/>\n";
		return $this->mysql->getSQLResult($q);
	}

	function getCTFParameterFields($runId=false) {
		$q = "SELECT *, path.`path` as path, acerun.`DEF_id` as acerun "
			."FROM ApAceRunData AS acerun ";
		foreach ($this->ace_method_map as $k=>$p) {
			if ($this->mysql->SQLTableExists("$p[0]")) {
				$q .= "LEFT JOIN $p[0] AS $p[1] "
				."  ON ($p[1].`DEF_id` = acerun.`REF|$p[0]|$p[1]`) ";
			}
		}
		$q .= "LEFT JOIN ApPathData AS path "
			."  ON (path.`DEF_id` = acerun.`REF|ApPathData|path`) ";
		if ( $runId ) $q .= " where acerun.`DEF_id` = $runId ";
		//$q .= " LIMIT 1; ";
		//echo $q."<br/><br/>\n";
		return $this->mysql->getSQLResult($q);
	}

	function getCTFStats($fields, $sessionId, $runId=false) {
		$dbfields = $this->mysql->getFields('ApCtfData');
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			if (!in_array($field, $dbfields))
				continue;
			$selects[$field] = "c.`REF|leginondata|AcquisitionImageData|image` AS id, "
					//."s.defocus, "
					. "count(c.DEF_id) AS `nb`, "
					. "min(c.`$field`) AS `min`, "
					. "max(c.`$field`) AS `max`, "
					. "avg(c.`$field`) AS `avg`, "
					. "stddev(c.`$field`) AS `stddev`";
		}
		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
			$q =	"SELECT ".$select." "
				."FROM ApCtfData AS c "
				."LEFT JOIN ".DB_LEGINON.".AcquisitionImageData i "
					."ON (c.`REF|leginondata|AcquisitionImageData|image`=i.`DEF_id`) "
				//."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` s "
				//	."ON (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
				//."LEFT JOIN ".DB_LEGINON.".`PresetData` p "
				//	."ON (`p`.`DEF_id`=`i`.`REF|PresetData|preset`) "
				."WHERE i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "AND c.`REF|ApAceRunData|acerun`='$runId' ";
			else {
				$q .= "AND c.`DEF_id`=(".
					"SELECT c2.`DEF_id` FROM ApCtfData AS c2 "
					."WHERE c2.`REF|leginondata|AcquisitionImageData|image` = c.`REF|leginondata|AcquisitionImageData|image` "
					."			".$this->getBestCTFOrder('c', true)
					."LIMIT 1 "
				.")";
			}
			//$q .= "GROUP BY p.`name`";
			//if (!$runId)
			//	echo $q."<br/><br/>\n";
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
		// this function is used to set default values 
		//   for makestack, imgrejector,
		// and gives stats in summary.php, and index.php
		//
		// selection of the result for a image is BestCtfOrder.
		// summary.php may put limit to what image result to return,
		// use resolution_appion as limit matrix.
		// Unlike getBestCtfInfoByResolution, this does consider
		// ImageViewerStatus, nor stage tilt
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

		$phase_shift_select = $this->getPhaseShiftString('c');

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
				."			".$phase_shift_select
				."			c.`confidence`,c.`confidence_d` , c.`cross_correlation` , "
				."			c.`ctffind4_resolution` , "
				.$this->getAppionResolutionSelect('c').", "
				.$this->getAppionConfidenceScoreSelect('c').", "
				."			(c.`defocus1`+c.`defocus2`)/2+s.`defocus` as difference_from_nom "
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
				."			".$this->getBestCTFOrder('c')
				."		) allctfdata "
				."	group by allctfdata.`REF|leginondata|AcquisitionImageData|image` "
				."	) ctfdata ";
				// if $limit is specified, report only values with confidences > $limit
				if ($limit){
					$q .= " where ctfdata.resolution_appion < $limit ";
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

	function removeCtfRunById($ctfId) {
		# count the number of values for CTF run
		$q = "SELECT count(DEF_id) as num "
			. "FROM `ApCtfData` "
			. "WHERE `REF|ApAceRunData|acerun` = $ctfId";
		list($r) = $this->mysql->getSQLResult($q);
		
		# remove the CTF data
		$q = "DELETE from `ApCtfData` "
			. "WHERE `REF|ApAceRunData|acerun` = $ctfId";
		$this->mysql->getSQLResult($q);
		$status.= "Removed ".$r['num']." values from ApCtfData<br/>\n";

		# remove the runid
		$q = "DELETE from `ApAceRunData` "
			. "WHERE `DEF_id` = $ctfId";
		$this->mysql->getSQLResult($q);
		$status.= "Removed CTF Run ID $ctfId from ApAceRunData table<br/>\n";
		return $status;
	}

	//------ -------------------- ---------//
	//-------particle functions --------//
	//------ -------------------- ---------//
	//TODO: the next 2 display functions do not belong in this file!!!
	function displayParameters ($title,$params,$exclude_fields,$expId,$hide_button_field='',$inform=false) {
		//standard parameter table display

		//Array of $params keys that are shown as a link to another report
		$links=array(
			'stackId'=>"stackreport.php?expId=$expId&sId="
			,'particleSelection'=>"particlerunreport.php?expId=$expId&rId="
			,'objectTracing'=>"particlerunreport.php?expId=$expId&rId="
			,'aligner'=>"tomoalignercyclereport.php?expId=$expId&aId="
			,'sizingreport'=>"sizingreport.php?expId=$expId&sizingId="
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
			,'alignrun id'=>"tomoalignercyclesummary.php?expId=$expId&alignId="
			,'alignerid'=>"tomoalignercyclereport.php?expId=$expId&aId="
			,'refine cycle'=>"tomoalignercyclereport.php?expId=$expId&aId="
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
			."WHERE `REF|projectdata|projects|project`='$projectId' ";
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
			."WHERE `REF|projectdata|projects|project`='$projectId' ";
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
	
	// Returns a dictionary of values to be used in stack selector GUI elements
	function getAlignedStackOptions( $stackIds ) 
	{
		$options = array();
		
		foreach ( $stackIds as $stackid ) {
			
			// get stack parameters from database
			$stackParams = $this->getAlignStackParams( $stackid['alignstackid'] );
			
			// get number of particles in each stack
			$totalp = $stackParams['num_particles'];
			if ($totalp == 0)
				continue;
				
			$nump = commafy($totalp);
			
			// get pixel size of stack
			$apix = $stackParams['pixelsize'];
			// truncated pixel size
			$showapix = sprintf("%.2f",$apix);
			// get box size
			$box = $stackParams['boxsize'];
			// get stack path with name
			$opvals = "$stackid[alignstackid]|--|$apix|--|$box|--|$totalp|--|$stackParams[path]|--|$stackParams[name]";
			
			// if imagic stack, send both hed & img files for dmf
			if (preg_match('~.hed~', $s['name'])) $opvals.='|--|'.preg_replace('~hed~','img',$s['name']);
			if (preg_match('~.img~', $s['name'])) $opvals.='|--|'.preg_replace('~img~','hed',$s['name']);
			
			// Add this stack to the options dictionary
			$options[$opvals] = $stackParams[runname]." ID: ".$stackid[alignstackid]." (".$nump." particles, ".$showapix." &Aring;/pix, ".$box."x".$box.")";
		}
		
		return $options;
	}
	
	// Returns a dictionary of values to be used in stack selector GUI elements
	function getStackOptions( $stackIds ) 
	{
		$options = array();
		
		foreach ( $stackIds as $stackid ) {
			
			// get stack parameters from database
			$s = $this->getStackParams( $stackid['stackid'] );
			
			// get number of particles in each stack
			$totalp = $this->getNumStackParticles( $stackid['stackid'] );
			if ($totalp == 0)
				continue;
				
			$nump = commafy($totalp);
			
			// get pixel size of stack
			$apix = ($this->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
			// truncated pixel size
			$showapix = sprintf("%.2f",$apix);
			// get box size
			$box = $s['boxsize'];
			// get stack path with name
			$opvals = "$stackid[stackid]|--|$apix|--|$box|--|$totalp|--|$s[path]|--|$s[name]";
			
			// if imagic stack, send both hed & img files for dmf
			if (preg_match('~.hed~', $s['name'])) $opvals.='|--|'.preg_replace('~hed~','img',$s['name']);
			if (preg_match('~.img~', $s['name'])) $opvals.='|--|'.preg_replace('~img~','hed',$s['name']);
			
			// Add this stack to the options dictionary
			$options[$opvals] = $s[shownstackname]." ID: ".$stackid[stackid]." (".$nump." particles, ".$showapix." &Aring;/pix, ".$box."x".$box.")";
		}
		
		return $options;
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
		
		$options = $this->getStackOptions($stackIds);
		foreach ($options as $key => $value) {
			echo "<OPTION VALUE='$key'";
			// select previously set stack on resubmita
			$stackvals = explode( '|--|', $key );
			if ( $stackvals[0] == $stackidval ) echo " SELECTED";
			echo">$value</OPTION>\n";
		}
		
		echo "</SELECT>\n";
		
		// return the apix value
		return $stackvals ? $stackvals[1] : '';
		/* THIS FUNCTION SHOULD BE MOVED TO summarytables.inc */
	}

	function getParticlesFromImageId ($runId, $imageId){
		$fields = $this->mysql->getFields('ApParticleData');
		$labelselect = (in_array('label',$fields)) ? "p.label, ":" ";
		$q = "select p.DEF_id as id, "
			.$labelselect
			."p.xcoord, p.ycoord, p.correlation, "
			."p.`REF|ApTemplateImageData|template` as templateId, "
			."p.diameter "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."and p.`REF|leginondata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getTracesFromImageId ($runId, $imageId){
		$q = "select p.DEF_id as id, "
			."p.name "
			."from ApContourData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."and p.`REF|leginondata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);

		$allpoints = array();
		if (!empty($r)) {
			foreach ($r as $contour) {
				$q = "select p.x,p.y "
					."from ApContourPointData p "
					."where p.`REF|ApContourData|contour` = ".$contour['id']." ";
				$r=$this->mysql->getSQLResult($q);
				$allpoints[$contour['id']] = $r;
			}
		}
		return $allpoints;
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

	function getSelectionRunData($runId) {
		$q = "select * from ApSelectionRunData "
			." where `DEF_id` = '$runId' ";
		list($r) = $this->mysql->getSQLResult($q);

		return $r;
	}
		
	
	function getSelectionParams ($runId, $returntype=False) {
		$r = $this->getSelectionRunData($runId);

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

	function getObjectTracingRuns($sessionId) {
		if ($this->mysql->SQLTableExists("ApContourData")) {
			$q = "SELECT sr.*, count(*) as total_object_traced "
					." FROM ApSelectionRunData AS sr "
					." LEFT JOIN ApManualParamsData as p "
					." ON sr.`REF|ApManualParamsData|manparams` = p.`DEF_id` "
					." LEFT JOIN ApContourData as c "
					." ON c.`REF|ApSelectionRunData|selectionrun` = sr.`DEF_id` "
					." WHERE sr.`REF|leginondata|SessionData|session` = $sessionId "
					." AND "
					." p.`trace` = 1 "
					." GROUP BY sr.`DEF_id` "
					." ";
			$r=$this->mysql->getSQLResult($q);
			return $r;
		} else {
			return array();
		}
	}

	function getParticleLabels($runId) {
		$q = "select label, count(DEF_id) as `number particle` from ApParticleData where `REF|ApSelectionRunData|selectionrun`=".$runId." and label is not NULL group by `label`";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getMaxTiltAngle ($sessionId,$presetname='') {
		//Issue #4730 handling mixed tomography and untilted data collection with different preset names
		$pjoin = ($presetname) ? "LEFT JOIN ".DB_LEGINON.".`PresetData` AS p ON p.`DEF_id`=im.`REF|PresetData|preset` ": '';
		$pwhere = ($presetname) ? ' and p.name like "'.$presetname.'" ': '';
		$q = "SELECT MAX(ABS(s.`SUBD|stage position|a`))*180.0/PI() AS angle "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` AS im "
			.$pjoin
			."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` AS s "
			."ON s.`DEF_id` = im.`REF|ScopeEMData|scope` "
			."WHERE im.`REF|SessionData|session` = '$sessionId' "
			.$pwhere
			." ";
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
		$q="select p.DEF_id, p.xcoord, p.ycoord, p.correlation, "
			."p.`REF|leginondata|AcquisitionImageData|image`, a.`filename`, p.helixnum "
			."from ApParticleData p "
			."left join ".DB_LEGINON.".`AcquisitionImageData` a "
			."on p.`REF|leginondata|AcquisitionImageData|image` = a.`DEF_id` "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getParticlesDataWithDeforcusPair($runId){
		
		$q="SELECT p.`DEF_id`,p.xcoord, p.ycoord, p.`REF|leginondata|acquisitionImageData|image` as imageNum, "
			."a.`filename`, "
			."t.`REF|leginondata|AcquisitionImageData|image2` as pImage, t.shiftx, t.shifty "
			."FROM ApParticleData as p "
			."LEFT JOIN ApImageTransformationData t "
			."ON (p.`REF|leginondata|acquisitionImageData|image` = t.`REF|leginondata|AcquisitionImageData|image1`) "
			."left join ".DB_LEGINON.".`AcquisitionImageData` a "
			."on p.`REF|leginondata|AcquisitionImageData|image` = a.`DEF_id` "
			."WHERE p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
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
			."max(p.`REF|leginondata|AcquisitionImageData|image`) as lastimage, "
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
		$tracestats = $this->getTraceStats($runId);
		# not to replace $r['lastimage'] if no real trace stats
		if (!$tracestats['lastimage']) $tracestats['lastimge'] = $r['lastimage'];
		$r = array_merge($r,$tracestats);
		$q = "select p.`name` "
			." from ".DB_LEGINON.".AcquisitionImageData a"
			." , ".DB_LEGINON.".PresetData p"
			." where a.`REF|PresetData|preset` = p.`DEF_id`"
			." and a.`DEF_id` = ".$r['lastimage'];
		list($r1) = $this->mysql->getSQLResult($q);
		if ($r1) {
			$r['preset'] = $r1['name'];
		} else {
			$r['preset'] = 'n/a';
		}
		return $r;

	}

	function getTraceStats ($runId) {
		if (!$this->mysql->SQLTableExists("ApContourData"))
			return array();
		$q = "SELECT count(*) as total_object_traced, "
				."c.`REF|leginondata|AcquisitionImageData|image` as lastimage "
				." FROM ApSelectionRunData AS sr "
				." LEFT JOIN ApManualParamsData as p "
				." ON sr.`REF|ApManualParamsData|manparams` = p.`DEF_id` "
				." LEFT JOIN ApContourData as c "
				." ON c.`REF|ApSelectionRunData|selectionrun` = sr.`DEF_id` "
				." WHERE sr.`DEF_id` = $runId "
				." AND "
				." p.`trace` = 1 "
				." AND "
				." c.`DEF_id` is not null "
				." GROUP BY sr.`DEF_id` ";
		list($r)=$this->mysql->getSQLResult($q);
		if (!$r) $r=array('total_object_traced'=>0);
		return $r;
	}

	function getNumImgs ($runId){
		$q="SELECT count(distinct `REF|leginondata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun`='$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getImgIdsFromSessionId ($sessionId){
		$q = "SELECT "
			."img.`DEF_id` "
			."FROM ".DB_LEGINON.".AcquisitionImageData as img "
			."WHERE "
			."  img.`REF|SessionData|session` = '$sessionId' ";
		//echo $q;
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}	

	function isSessionRunning($sessionid) {	
		$q="SELECT "
			."UNIX_TIMESTAMP(img.`DEF_timestamp`) AS `end` "
			.",img.filename "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` AS img "
			."WHERE `REF|SessionData|session` = '$sessionid' "
			."AND (`filename` NOT LIKE '%-%' OR `filename` NOT LIKE 'project')"
			."ORDER BY img.`DEF_timestamp` DESC LIMIT 1";
		$endinfo = $this->mysql->getSQLResult($q);
		$lastsecs = time() - $endinfo[0]['end'];
		$active_time = 60*60;
		return ($lastsecs <= $active_time) ? true:false;
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
	
	function getHighTensionFromSessionId( $sessionId )
	{
		$q= "SELECT `high tension` FROM ".DB_LEGINON.".ScopeEMData AS s "
			. "WHERE s.`REF|SessionData|session`='$sessionId' ";
		//echo $q;
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['high tension'];
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
			."LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			."  ON viewer.`REF|AcquisitionImageData|image` = assess.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = p.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = p.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
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
			."LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			."  ON viewer.`REF|AcquisitionImageData|image` = assess.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = p.`REF|leginondata|AcquisitionImageData|image` "
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
			. "LEFT JOIN ".DB_LEGINON.".`ViewerImageStatus` AS viewer"
			. "  ON viewer.`REF|AcquisitionImageData|image` = part.`REF|leginondata|AcquisitionImageData|image` "
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

	// return the last Def_id value in the provided table
	function getLastDefId($sessionId, $table) 
	{
		$q = "select DEF_id as runId "
			."from `".$table."` "
			."where `REF|leginondata|SessionData|session` = '$sessionId' "
			."order by DEF_id desc limit 1";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['runId'];
	}
	
	function getLastParticleRun($sessionId) 
	{
		return $this->getLastDefId($sessionId, "ApSelectionRunData");
	}

	function getLastDDStackRun($sessionId) 
	{
		return $this->getLastDefId($sessionId, "ApDDStackRunData");
	}
	
	function hasDDstackData($sessionId) 
	{
		$r= ($this->getLastDDStackRun($sessionId)) ? true : false;
		return $r;
	}
		
	function getParticleRunData($partRunId) 
	{
		return getRunData($partRunId, "ApSelectionRunData" );
	}
	
	function getDDStackRunData($ddRunId) 
	{
		return getRunData($ddRunId, "ApDDStackRunData" );
	}

	function getRecentAlignedImage($imgid)
	{
		// check as result
		$q = "SELECT pair.`REF|leginondata|AcquisitionImageData|result` result_imgid "
			."FROM `ApDDAlignImagePairData` pair "
			."WHERE pair.`REF|leginondata|AcquisitionImageData|source` = ".$imgid." "
			."ORDER BY pair.`DEF_timestamp` DESC ";
		$r = $this->mysql->getSQLResult($q);
		if ( is_array($r) && $r ) return $r[0]['result_imgid'];
	}

	function getAlignLogShiftFromDDAlignedImageId($result_imgid,$apix=1)
	{
		// get Alignlog path
		$align_log = $this->getAlignLogPathFromDDAlignedImageId($result_imgid);
		// get shift data
		$data = array();
		if (is_file($align_log)) {
			$text = file_get_contents($align_log);
			$bits = explode('Sum Frame',$text);
			if (count($bits) > 1) {
				$shiftlines = explode("\n",$bits[1]);
				foreach($shiftlines as $shiftline) {
					$shiftbits = explode('with xy shift:',$shiftline);
					if (count($shiftbits) > 1) {
						$shifts = explode(' ',trim($shiftbits[1]));
						$data[] = array('x'=>((float) $shifts[0])*$apix,'y'=> ((float) $shifts[count($shifts)-1])*$apix);
					}
				}
			}
		} else {return $align_log;}
		return $data;
	}

	function getShiftDistancesFromPositions($data)
	{
		$distances = array();
		$i = 0;
		while ( $i < count($data)-1 ) {
			$p0 = $data[$i];
			$p1 = $data[$i+1];
			$distance = hypot($p0['x']-$p1['x'], $p0['y']-$p1['y']);
			$distances[] = $distance;
			$i += 1;
		}
		return $distances;
	}

	function getAlignLogPathFromDDAlignedImageId($result_imgid)
	{
		// get Alignlog path
		$q = "SELECT rundir.path as rundir, pair.`REF|leginondata|AcquisitionImageData|source` as source_imgid, params.bin as bin "
			."FROM `ApDDAlignImagePairData` pair "
			."LEFT JOIN `ApDDStackRunData` run "
			."ON pair.`REF|ApDDStackRunData|ddstackrun`=run.`DEF_id` "
			."LEFT JOIN	`ApPathData` rundir "
			."ON run.`REF|ApPathData|path` = rundir.`DEF_id` "
			."LEFT JOIN `ApDDStackParamsData` params "
			."ON run.`REF|ApDDStackParamsData|params` = params.`DEF_id` "
			."WHERE pair.`REF|leginondata|AcquisitionImageData|result` = ".$result_imgid;
		list($r) = $this->mysql->getSQLResult($q);
		// Log filename depends on the binning
		$bin = ((int) $r['bin'] < 1) ? 1:(int) $r['bin'];
		$bin_text = ($bin == 1) ? '':'_'.$bin.'x';
		$source_image_name = $this->getImageNameFromId($r['source_imgid']);
		// refs #4544 default log without bin_text
		$default_align_log = $r['rundir'].'/'.$source_image_name.'_st_Log.txt';
		if (file_exists ($default_align_log)) return $default_align_log;
		// back compatibility older alignment still use the original binned log
		$align_log = $r['rundir'].'/'.$source_image_name.'_st'.$bin_text.'_Log.txt';
		return $align_log;
	}

	function getRunData($runId, $table) 
	{
		$q = "SELECT r.*, p.path "
			."FROM `".$table."` AS r "
			."LEFT JOIN ApPathData AS p ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$runId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	// Warning: this counts the number of runs, it does not return the 
	// last run id number used. Since a user can modify the runname,
	// this is not a safe number to use for a defualt run name. Try
	// getMaxRunNumber() instead.
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

	function getRunIds($sessionId, $table, $showHidden=False) 

	{
		$q = "SELECT r.*, p.path "
			."FROM `".$table."` AS r "
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

	// Filter Run ID's against a field and field value, 
	function getRunIdsFilter($sessionId,$table,$field,$filtervalue,$showHidden=False)
	{
		$q = "SELECT r.*, p.path "
			."FROM `".$table."` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' "
			."AND r.`".$field."` = '$filtervalue' ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		$q.= "ORDER BY r.`DEF_id` DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}


	function getParticleRunIds($sessionId,$showHidden=False) 
	{
		return $this->getRunIds($sessionId, "ApSelectionRunData", $showHidden);
	}

	function getDDStackRunIds($sessionId,$showHidden=False) 
	{
		return $this->getRunIds($sessionId, "ApDDStackRunData", $showHidden);
	}
	
	function getDDStackRunIdsAlign($sessionId,$showHidden=True) 
	{
		$q = "SELECT r.`DEF_id` as stackid, r.`runname` as runname "
			."FROM `ApDDStackRunData` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."LEFT JOIN `ApDDStackParamsData` AS a "
			."ON (r.`REF|ApDDStackParamsData|params` = a.`DEF_id`) "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' "
			."AND a.`align` = 1 ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		$q.= "ORDER BY r.`DEF_id` DESC ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}	
	


        function getDDStackRunIdsUnAligned($sessionId,$showHidden=True)
        {
                $q = "SELECT r.`DEF_id` as stackid, r.`runname` as runname "
                        ."FROM `ApDDStackRunData` AS r "
                        ."LEFT JOIN ApPathData AS p "
                        ."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
                        ."LEFT JOIN `ApDDStackParamsData` AS a "
                        ."ON (r.`REF|ApDDStackParamsData|params` = a.`DEF_id`) "
                        ."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' "
                        ."AND a.`align` = 0 ";
                if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
                $q.= "ORDER BY r.`DEF_id` DESC ";
                //echo $q."<br/>\n";
                $r = $this->mysql->getSQLResult($q);
                return $r;
        }


	function getDDStackRunName($stackId,$showHidden=True) 
	{
		$q = "SELECT r.`runname` "
			."FROM `ApDDStackRunData` AS r "
			."WHERE r.`DEF_id` = '$stackId' ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		//echo $q."<br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}		

	function getDDStackOutdir($stackId,$showHidden=True) 
	{
		$q = "SELECT p.`path` "
			."FROM `ApDDStackRunData` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$stackId' ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
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
				. "LEFT JOIN `ApStackParticleData` AS sp "
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

	function getVirtualStackData($stackid) {
		$orig_stack = '';
		$working_stackid = $stackid;
		while ($orig_stack == '') {
			# get oldstack from current stackid
			$r = $this->getParentStackId($working_stackid);
			$oldstackid = $r['parentid'];
			if (!$oldstackid) return;

			# find out if stackfile exists
			$stackdata = $this->getStackParams($oldstackid);
			$fname = $stackdata['path']."/".$stackdata['name'];
			if (file_exists($fname)) {
				$orig_stack=$oldstackid;
				$q = "SELECT s1.particleNumber "
					."FROM `ApStackParticleData` as s1 "
					."LEFT JOIN `ApStackParticleData` as s2 "
					."ON s1.`REF|ApParticleData|particle`=s2.`REF|ApParticleData|particle` "
					."WHERE ("
					."s1.`REF|ApStackData|stack`=$oldstackid and "
					."s2.`REF|ApStackData|stack`=$stackid) "
					."ORDER BY s1.particleNumber";
				$r = $this->mysql->getSQLResult($q);
				$parts = array();
				foreach ($r as $val) {$parts[] = $val['particleNumber'];}
			}
			else $working_stackid = $oldstackid;
		}
		return array('stackid'=>$orig_stack,
			'filename'=>$fname,
			'particles'=>$parts);
	}

	function getClusterRefNumsFromSubStack ($substackid,$clusterstackid) {
		$q = "SELECT "
			."cp.`refnum` as classnum "
			."FROM `ApClusteringParticleData` as cp "
			."LEFT JOIN `ApAlignParticleData` as ap "
			."ON cp.`REF|ApAlignParticleData|alignparticle` = ap.`DEF_id` "
			."LEFT JOIN `ApStackParticleData` as pst "
			."ON ap.`REF|ApStackParticleData|stackpart` = pst.`DEF_id` "
			."LEFT JOIN `ApParticleData` as pp "
			."ON pst.`REF|ApParticleData|particle` = pp.`DEF_id` "
			."LEFT JOIN `ApStackParticleData` as sst "
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
			if (preg_match('%'.$key.'%',$substackname)) {
				$conditionid = str_replace($key, '', $substackname);
				$condition = $key;
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
			if (count($r)) return $r[0];
		}
		return array();
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
		."from ApStackParticleData group by `REF|ApStackRunData|stackRun`) spar "
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
		// echo $q."<br/>\n";
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
			$r['tiltangle'] = $params[0]['tiltangle'];
			$r['phaseFlipped'] = $params[0]['phaseFlipped'];
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
			$r['tiltangle'] = $params[0]['tiltangle'];
			$r['phaseFlipped'] = $params[0]['phaseFlipped'];
			$r['fliptype'] = $params[0]['fliptype'];
			$r['inverted'] = $params[0]['inverted'];
			$r['pixelsize'] = $params[0]['pixelsize'];
			$r['boxsize'] = $params[0]['boxsize'];
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
		." FROM ( SELECT * FROM `ApStackParticleData` "
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
		."FROM `ApStackParticleData` as st  "
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
			."FROM `ApStackParticleData` AS stackpart "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r[0])."<br/><br/>\n";
		return $r;
	}
	
	function getParticlesFromStack($stackId){
		$q= "SELECT `REF|ApParticleData|particle` AS particleId, mean, stdev, skew, "
			."kurtosis, edgemean, edgestdev, centermean, centerstdev, min, max "
			."FROM `ApStackParticleData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'"; 
			
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlePicksFromStack($stackId) {
		$q="SELECT s.particleNumber as particle, "
			."p.`REF|leginondata|AcquisitionImageData|image` as imgid, "
			."p.xcoord, p.ycoord, p.helixnum, p.angle "
			."FROM `ApStackParticleData` AS s "
			."LEFT JOIN `ApParticleData` AS p "
			."ON s.`REF|ApParticleData|particle` = p.`DEF_id` "
			."WHERE s.`REF|ApStackData|stack` = '$stackId' "
			."ORDER BY s.particleNumber";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumStackParticles ($stackId) {
		$q= "SELECT count(DEF_id) as num "
			."FROM `ApStackParticleData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getNumStackImages ($stackId) {
		$r = $this->getStackImages($stackId);
		return count($r);
	}

	function getStackImages ($stackId, $limit=null) {
		//Get unique images in the stack
		$q= "SELECT DISTINCT im.`DEF_id` AS imgid "
			."FROM ApStackParticleData AS stpart "
			."LEFT JOIN ApParticleData AS part "
			."ON stpart.`REF|ApParticleData|particle` = part.`DEF_id` "
			."LEFT JOIN ".DB_LEGINON.".`AcquisitionImageData` AS im "
			."ON part.`REF|leginondata|AcquisitionImageData|image` = im.`DEF_id` "
			."WHERE `REF|ApStackData|stack` = '$stackId' ";
		if ($limit) $q .= "LIMIT ".$limit." ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticleMovieRunFromId($movierunid) {
		$q = "SELECT pr . `DEF_id` as runid , "
		." pr . `movieRunName`, "
		." path . `path`, "
		." pr . `REF|leginondata|SessionData|session` as sessionId, "
		." pr . `REF|ApSelectionRunData|selectionrun` as selectionId "
		." FROM `ApParticleMovieRunData` pr "
		." LEFT JOIN `ApPathData` path "
		." ON pr.`REF|ApPathData|path` = path.`DEF_id` "
		." WHERE pr.`DEF_id` = ".$movierunid." "
		." ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumRefImages ($alignrun) {
		$q = "SELECT count(DEF_id) as num "
			."FROM `ApAlignReferenceData` "
			."WHERE `REF|ApAlignRunData|alignrun` = '$alignrun'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function removeSelectionRunById($selectionRunId) {
		# count the number of values for selection run
		$q = "SELECT count(DEF_id) as num "
			. "FROM `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun` = $selectionRunId";
		list($r) = $this->mysql->getSQLResult($q);
		
		# remove the selection data
		$q = "DELETE from `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun` = $selectionRunId";
		$this->mysql->getSQLResult($q);
		$status.= "Removed ".$r['num']." values from ApParticleData<br/>\n";

		# get path from the entry in ApSelectionRunData
		$q = "SELECT `REF|ApPathData|path` as path from ApSelectionRunData "
			."WHERE DEF_id=$selectionRunId";
		$r = $this->mysql->getSQLResult($q);
		$pathid = $r[0]['path'];
		# this path is used to remove the corresponding
		# entry from ApAppionJobData
		$q = "DELETE from ApAppionJobData "
			."WHERE `REF|ApPathData|path`=$pathid ";
		$this->mysql->getSQLResult($q);
		$status.= "Removed associated job from ApAppionJobData<br/>\n";

		# remove the runid
		$q = "DELETE from `ApSelectionRunData` "
			. "WHERE `DEF_id` = $selectionRunId";
		$this->mysql->getSQLResult($q);
		$status.= "Removed Selection Run ID $selectionRunId from ApSelectionRunData table<br/>\n";
		return $status;
	}

	function removeAlignStackById($alignStackId) {
		// Get alignment run for this stack
		$q = "SELECT `REF|ApAlignRunData|alignrun` as alignrun "
			. "FROM `ApAlignStackData` "
			. "WHERE `DEF_id`=$alignStackId ";
		$r = $this->mysql->getSQLResult($q);
		$alignrun = $r[0]['alignrun'];

		// delete entry in ApAlignRunData
		$q = "DELETE from `ApAlignRunData` "
			. "WHERE `DEF_id`=$alignrun ";
		$r = $this->mysql->getSQLResult($q);
		$status = "Removed Alignment ID $alignrun from ApAlignRunData table<br>\n";

		// delete entry in ApAlignReferenceData
		$q = "DELETE from `ApAlignReferenceData` "
			. "WHERE `REF|ApAlignRunData|alignrun`=$alignrun ";
		$r = $this->mysql->getSQLResult($q);
		$status.= "Removed Aligned References from ApAlignReferenceData table<br>\n";

		// get path the Stack entry in ApStackData
		$q = "SELECT `REF|ApPathData|path` as path from ApAlignStackData "
			."WHERE DEF_id=$alignStackId";
		$r = $this->mysql->getSQLResult($q);
		$pathid = $r[0]['path'];
		// this path is used to remove the corresponding
		// entry from ApAppionJobData
		$q = "DELETE from ApAppionJobData "
			."WHERE `REF|ApPathData|path`=$pathid ";
		$this->mysql->getSQLResult($q);
		$status.= "Removed associated job from ApAppionJobData<br/>\n";
	
		// remove stack from ApStackData
		$q = "DELETE from `ApAlignStackData` "
			. "WHERE `DEF_id`=$alignStackId ";
		$r = $this->mysql->getSQLResult($q);
		$status.= "Removed Aligned Stack ID $alignStackId from ApAlignStackData table<br>\n";
		// count the number of particles in ApStackParticleData
		$q = "SELECT count(DEF_id) as num "
			."FROM `ApAlignParticleData` "
			."WHERE `REF|ApAlignStackData|alignstack`=$alignStackId ";
		list($r) = $this->mysql->getSQLResult($q);
		$q = "DELETE FROM `ApAlignParticleData` "
			."WHERE `REF|ApAlignStackData|alignstack`=$alignStackId ";
		$this->mysql->getSQLResult($q);
		$status.= "Removed ".$r['num']." particles from ApAlignParticleData<br/>\n";

		return $status;		
	}

	function removeStackById($stackId) {
		// Now get the stack run(s) used for this stack
		$q = "SELECT `REF|ApStackRunData|stackRun` as stackrun "
			. "FROM `ApRunsInStackData` as rs "
			. "WHERE `REF|ApStackData|stack` = $stackId ";
		$r = $this->mysql->getSQLResult($q);

		// delete entry in ApRunsInStackData
		$q = "delete from `ApRunsInStackData` "
			. "WHERE `REF|ApStackData|stack` = $stackId";
		$this->mysql->getSQLResult($q);
		$status = "Removed Stack ID $stackId from ApRunsInStackData table<br>\n";
		// check if there are still runs for each stack run:
		foreach ($r as $srun) {
			$srunid=$srun['stackrun'];
			$q = "SELECT count(*) as num from `ApRunsInStackData` "
				. "WHERE `REF|ApStackRunData|stackRun` = $srunid";
			$r = $this->mysql->getSQLResult($q);
			// if no entries left, remove entry in ApStackRunData
			if ($r[0]['num']==0 ) {
				$q = "DELETE from `ApStackRunData` "
					. "WHERE `DEF_id` = $srunid";
				$this->mysql->getSQLResult($q);
				$status.= "Removed Stack Run ID $srunid from ApStackRunData table<br/>\n";
			}
			else $status.= "Stack Run ID $srunid is used in other stacks, not removing it from the ApStackRunData table<br/>\n";
		}
		// get path the Stack entry in ApStackData
		$q = "SELECT `REF|ApPathData|path` as path from ApStackData "
			."WHERE DEF_id=$stackId";
		$r = $this->mysql->getSQLResult($q);
		$pathid = $r[0]['path'];
		// this path is used to remove the corresponding
		// entry from ApAppionJobData
		$q = "DELETE from ApAppionJobData "
			."WHERE `REF|ApPathData|path`=$pathid ";
		$this->mysql->getSQLResult($q);
		$status.= "Removed associated job from ApAppionJobData<br/>\n";
		// remove stack from ApStackData
		$q = "DELETE from ApStackData "
			." WHERE DEF_id=$stackId ";
		$this->mysql->getSQLResult($q);
		$status.= "Removed Stack ID $stackId from ApStackData<br/>\n";
		// count the number of particles in ApStackParticleData
		$q = "SELECT count(DEF_id) as num "
			."FROM `ApStackParticleData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		list($r) = $this->mysql->getSQLResult($q);
		$q = "DELETE from `ApStackParticleData` "
			. "WHERE `REF|ApStackData|stack` = '$stackId'";
		$this->mysql->getSQLResult($q);
		$status.= "Removed ".$r['num']." particles from ApStackParticleData<br/>\n";
		return $status;
	}

	//////// fix me ////////
	function getStackIdFromReconId ($reconId) {
		$q= "SELECT * "
			."FROM `ApRefineRunData` "
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
			." FROM `ApStackParticleData` sp "
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
			." FROM `ApStackParticleData` sp "
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

	function getMinimumPixelSizeForSession($sessionid) {
		// for simplicity this ignores any binning..., which may be bad
		$q="SELECT "
			."  MIN(pixelsize) AS val "
			."FROM ".DB_LEGINON.".PixelSizeCalibrationData "
			."WHERE DEF_id IN "
			." ( "
				."SELECT MAX(pix.`DEF_id`) "
				."FROM ".DB_LEGINON.".`AcquisitionImageData` AS a "
				."LEFT JOIN ".DB_LEGINON.".`CameraEMData` AS cam "
				."  ON (a.`REF|CameraEMData|camera` = cam.`DEF_id`) "
				."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` AS scope "
				."  ON (a.`REF|ScopeEMData|scope` = scope.`DEF_id`) "
				.", ".DB_LEGINON.".PixelSizeCalibrationData AS pix "
				."WHERE "
				."  a.`REF|SessionData|session` = '$sessionid' "
				."AND "
				."  pix.`REF|InstrumentData|tem` = scope.`REF|InstrumentData|tem` "
				."AND "
				."  pix.`magnification` = scope.`magnification` "
				."AND "
				."  pix.`REF|InstrumentData|ccdcamera` = cam.`REF|InstrumentData|ccdcamera` "
				."AND "
				."  pix.`DEF_timestamp` <= a.`DEF_timestamp` "
				."GROUP BY a.`DEF_id` "
			." ) ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		$pixelsize = $r[0]['val'];
		//echo $pixelsize."<br/><br/>\n";
		return $pixelsize;
	}

	function getPixelSizeFromImgIdPresetQuery($imgid) {
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
		return $q;
	}

	function getPixelSizeFromImgIdEMQuery($imgid) {
		// This is the more reliable query for pixel size but may take longer?
		$q="SELECT ce.`SUBD|binning|x` as imgbin, "
			."  pc.`pixelsize` as ccdpixelsize,  "
			."  ce.`SUBD|pixel size|x` as physical_pixelsize  "
			."FROM ".DB_LEGINON.".`AcquisitionImageData` AS a "
			."LEFT JOIN ".DB_LEGINON.".`CameraEMData` AS ce "
			."  ON (a.`REF|CameraEMData|camera` = ce.`DEF_id`) "
			."LEFT JOIN ".DB_LEGINON.".`ScopeEMData` AS se "
			."  ON (a.`REF|ScopeEMData|scope` = se.`DEF_id`) "
			.", ".DB_LEGINON.".PixelSizeCalibrationData pc "
			."WHERE "
			."  a.`DEF_id`='$imgid' "
			."AND "
			."  pc.`REF|InstrumentData|tem` = se.`REF|InstrumentData|tem` "
			."AND "
			."  pc.`magnification` = se.`magnification` "
			."AND "
			."  pc.`REF|InstrumentData|ccdcamera` = ce.`REF|InstrumentData|ccdcamera` "
			."AND "
			."  pc.`DEF_timestamp` <= a.`DEF_timestamp` "
			."ORDER BY pc.`DEF_timestamp` DESC ";
		return $q;
	}

	function getPixelSizeFromImgId ($imgid) {
		$q = $this->getPixelSizeFromImgIdPresetQuery($imgid);
		//echo $q."<br/>\n";
		list($r2)=$this->mysql->getSQLResult($q);
		//echo print_r($r2)."<br/>\n";
		if ($r2 === null) {
			// If the session has only manual images, there is no preset.
			$q = $this->getPixelSizeFromImgIdEMQuery($imgid);
			list($r2)=$this->mysql->getSQLResult($q);
		}
		if ($r2['imgbin']) {
			$pixelsize = $r2['ccdpixelsize']*$r2['imgbin'];
		} else {
			$pixelsize = $r2['ccdpixelsize'];
		}
		return $pixelsize;
	}

	function getStackCameraPhysicalPixelSize ($stackId) {
		// return camera physical pixel size in meters
		$r1 = $this->getStackImages ($stackId, $limit=1);
		$q = $this->getPixelSizeFromImgIdEMQuery($r1[0]['imgid']);
		list($r) = $this->mysql->getSQLResult($q);
		return $r['physical_pixelsize'];
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
				if (preg_match('%^min|^max|^avg|^stddev%i', $field)) $data=format_sci_number($data,4);
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
		// get session name, since original stack may be deleted
		$q = "SELECT name from ".DB_LEGINON.".SessionData "
			."WHERE DEF_id=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		$sname = $r[0]['name'];
		$q = "SELECT DISTINCT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApStackData AS st ON "
			."  (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			."  (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			."  (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."LEFT JOIN ApPathData ON "
			."  (ast.`REF|ApPathData|path`=ApPathData.`DEF_id`) "
			."WHERE "
			."  (strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."OR "
			."  ApPathData.`path` LIKE \"%$sname%\") ";
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
		// get session name, since original stack may be deleted
		$q = "SELECT name from ".DB_LEGINON.".SessionData "
			."WHERE DEF_id=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		$sname = $r[0]['name'];
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
			."LEFT JOIN ApPathData ON "
			."  (ast.`REF|ApPathData|path`=ApPathData.`DEF_id`) "
			."WHERE "
			."  (strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."OR "
			."  ApPathData.`path` LIKE \"%$sname%\") "
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
	
	function getAlignStackIdsWithClusterRun ($sessionId, $projectId) {
		$q = "SELECT name from ".DB_LEGINON.".SessionData "
			."WHERE DEF_id=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		$sname = $r[0]['name'];
		$q = "SELECT DISTINCT ast.`DEF_id` AS alignstackid "
			."FROM ApAlignStackData AS ast "
			."LEFT JOIN ApClusteringRunData AS cluster ON "
			."  (cluster.`REF|ApAlignStackData|alignstack` = ast.`DEF_id`)"
			."LEFT JOIN ApStackData AS st ON "
			."  (ast.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApRunsInStackData as runsin ON "
			."  (runsin.`REF|ApStackData|stack` = st.`DEF_id`) "
			."LEFT JOIN ApStackRunData as strun ON "
			."  (runsin.`REF|ApStackRunData|stackRun`=strun.`DEF_id`) "
			."LEFT JOIN ApPathData ON "
			."  (ast.`REF|ApPathData|path`=ApPathData.`DEF_id`) "
			."WHERE "
			."  (strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."OR "
			."  ApPathData.`path` LIKE \"%$sname%\") "
			."AND "
			."  ast.`hidden` != 1 "
			."AND "
			."  cluster.`DEF_id` IS NOT NULL "
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
			'isac'=>'REF|ApSparxISACRunData|isacrun',
			'imagicMRA'=>'REF|ApMultiRefAlignRunData|imagicMRA',
			'editerrun'=>'REF|ApEdIterRunData|editerrun',
			'xmipp2cl2d'=>'REF|ApCL2DRunData|cl2drun',
			'xmipp3cl2d'=>'REF|ApXMIPP3CL2DRunData|xmipp3cl2drun',
		);
		foreach (array_keys($packagerefs) as $package) {
			if ($r[0][$packagerefs[$package]]) $r[0]['package'] = $package;
		}
		return $r[0];
	}

	function getNumAlignStackParticles ($alignstackid) {
		$q= "SELECT count(DEF_id) as num "
			."FROM `ApAlignParticleData` "
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
		// get session name, since original stack may be deleted
		$q = "SELECT name from ".DB_LEGINON.".SessionData "
			."WHERE DEF_id=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		$sname = $r[0]['name'];

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
		$q .=	"LEFT JOIN ApPathData ON "
			."  (ast.`REF|ApPathData|path`=ApPathData.`DEF_id`) "
			."WHERE "
			."  (strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."OR "
			."  ApPathData.`path` LIKE \"%$sname%\") ";
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
			."  maxjob.`REF|projectdata|projects|project` = '$projectId' "
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

	function getFinishedCL2DJobs ($projectId) {
		$q = "SELECT cl2djob.*, path.path "
			."FROM ApCL2DRunData AS cl2djob "
			."LEFT JOIN ApPathData as path ON "
			."  cl2djob.`REF|ApPathData|path` = path.`DEF_id` ";
		$q .=	"WHERE "
			."  cl2djob.`REF|projectdata|projects|project` = '$projectId' "
			." AND "
			."  cl2djob.`finished` = '1' ";
			$q .=	" ORDER BY cl2djob.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getFinishedSIMPLEClusteringJobs ($projectId) {
		$q = "SELECT simplejob.*, path.path "
			."FROM ApSIMPLEClusterRunData AS simplejob "
			."LEFT JOIN ApPathData as path ON "
			."  simplejob.`REF|ApPathData|path` = path.`DEF_id` ";
		$q .=	"WHERE "
			."  simplejob.`REF|projectdata|projects|project` = '$projectId' "
			." AND "
			."  simplejob.`finished` = '1' ";
			$q .=	" ORDER BY simplejob.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusteringStacks ($sessionId, $projectId, $showHidden=False) {
		// get session name, since original stack may be deleted
		$q = "SELECT name from ".DB_LEGINON.".SessionData "
			."WHERE DEF_id=$sessionId";
		$r = $this->mysql->getSQLResult($q);
		$sname = $r[0]['name'];

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
			."LEFT JOIN ApPathData AS pd ON "
			."  (cluster.`REF|ApPathData|path` = pd.`DEF_id`) "
			."LEFT JOIN ApPathData ON "
			."  (ast.`REF|ApPathData|path`=ApPathData.`DEF_id`) "
			."WHERE "
			."  (strun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."OR "
			."  ApPathData.`path` LIKE \"%$sname%\") ";
		if (!$showHidden)
			$q.= " AND cluster.`hidden` != 1 AND ast.`hidden` != 1 ";
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

	#--------- RECIPE BAKING FUNCTIONS---------------#
	function getAllRecipeData() {
		# Return all recipe info
		$q = "SELECT `DEF_id`, `name`, `description`, `ctfrunids`, "
			."`REF|ApStackData|stack` as stackid, "
			."`REF|ApAlignStackData|alignstack` as alignstackid "
			."FROM ApRecipeData";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getRecipeDataFromId($rid,$remove=False) {
		# Return info for recipe, or delete it
		if ($remove) { 
			$q = "DELETE FROM ApRecipeData WHERE `DEF_id`=$rid";
			$r=$this->mysql->SQLQuery($q);
			return;
		}

		$q = "SELECT `DEF_id`, `name`, `description`, `ctfrunids`, "
			."`REF|ApStackData|stack` as stackid, "
			."`REF|ApAlignStackData|alignstack` as alignstackid "
			."FROM ApRecipeData "
			."WHERE `DEF_id`=$rid";
		echo $q;
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRecipeNames() {
		# Return all the names for the recipes in a database
		$q = "SELECT name FROM ApRecipeData";
		$r=$this->mysql->getSQLResult($q);
		if ($r) {
			$names=array();
			foreach ($r as $ra) $names[]=$ra['name'];
		}
		return $names;
	}

	function bakeRecipe($name, $description, $stackid, $alignstackid, $ctfrunids=False) {
		# Make sure row doesn't already exist
		$q = "SELECT * FROM ApRecipeData "
			."WHERE ";
		if ($stackid) $q.="`REF|ApStackData|stack` = $stackid";
		elseif ($alignstackid) $q.="`REF|ApAlignStackData|alignstack` = $alignstackid ";
		$r = $this->mysql->getSQLResult($q);
		if ($r) return("exists");

		$q = "INSERT INTO `ApRecipeData` "
			."(`name`, `description`,`ctfrunids`,`REF|ApStackData|stack`,`REF|ApAlignStackData|alignstack`) "
			."VALUES "
			."('$name','".mysql_real_escape_string($description)."',";
		$q .= ($ctfrunids) ? "'$ctfrunids'," : "NULL,";
		$q .= ($stackid) ? "'$stackid'," : "NULL,";
		$q .= ($alignstackid) ? "'$alignstackid'" : "NULL";
		$q .= ")";
		$r=$this->mysql->SQLQuery($q);
		if ($r) return "ok";
		
	}


	#--------- MAKE MASK FUNCTIONS---------------#

	function getMaskMakerRunIds ($sessionId) {
		return $this->getRunIds($sessionId, "ApMaskMakerRunData", True);
	}

	function getMaskRunPathFromMaskRunId ( $maskRunId ) {
		$q = "select p.`path` "
			."from `ApPathData` p "
			."left join `ApMaskMakerRunData` m "
			."on (p.`DEF_id` = m.`REF|ApPathData|path`) "
			."where m.`DEF_id` = $maskRunId ";
			
		$r = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			//echo "error -> $dberror \n";
			error_log("Error: database error in particledata.inc, getMaskAssessRunIds(): $dberror /n");
		}
		return $r;
	}
	
	function getMaskAssessRunIds ($sessionId) {
		$q = "select * "
			."from `ApMaskAssessmentRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			//echo "error -> $dberror \n";
			error_log("Error: database error in particledata.inc, getMaskAssessRunIds(): $dberror /n");
		}
		return $r;
	}
	
	function getMaskAssessRunId( $sessionId, $maskRunId ) 
	{
		$q = "select `DEF_id` "
			."from `ApMaskAssessmentRunData` where `REF|leginondata|SessionData|session` = '$sessionId' and `REF|ApMaskMakerRunData|maskrun` = $maskRunId";
		$r = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			echo "error -> $dberror \n";
			error_log("Error: database error in particledata.inc, getMaskAssessRunId(): $dberror /n");
		}
		$id = $r[0]["DEF_id"];
		return $id;
	}
	
	function hasMaskMakerData ($sessionId) {
		$r= ($this->getLastMaskMakerRun($sessionId)) ? true : false;
		if ($r === False) {
			$dberror = $this->mysql->getError();
			//echo "error -> $dberror \n";
			error_log("Error: database error in particledata.inc, hasMaskMakerData(): $dberror /n");
		}
		return $r;
	}

	function getLastMaskMakerRun ($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApMaskMakerRunData` where `REF|leginondata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}

	function getMaskMakerRunByPath( $sessionId, $path ) 
	{
		$q = "select m.`DEF_id` as runId "
			."from `ApMaskMakerRunData` m where m.`REF|leginondata|SessionData|session` = $sessionId "
			."and m.`REF|ApPathData|path` in (SELECT p.`DEF_id` from `ApPathData` AS p where p.`path` LIKE \"%$path%\") ";
		list($r) = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			echo "error -> $dberror query -> $q \n";
			error_log("Error: database error in particledata.inc, updateMaskAssessmentByImage(): $dberror /n");
		}
		return $r[runId];
	}
	
	function getMaskMakerParams ($runId) {
		$q = "select * from ApMaskMakerRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);

		//print_r ($r);
		//echo $r['REF|ApMaskMakerParamsData|params'];
		$q = "select s.*, p.path, r.name, r.`REF|leginondata|SessionData|session` ";

		// TODO: does this table even exist?
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
		if (!is_array($particleruns)) {
			return ;
		}
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
				if (preg_match('^areamean^', $field) || preg_match('^Imean^', $field) || preg_match('^Istddev^', $field)) $data=format_sci_number($data,4);
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
	
	// $maskId is the DEF_id of the region in ApMaskAssessmentData
	// $newStatus is boolean True or False
	// True means the region will be considered during stack creation
	// and particles within the region will not be used. 
	// False means this region will be ignored and particles within the 
	// region will still be used for stack creation.
	function updateMaskAssessment( $maskId, $newStatus) 
	{
		$table = "ApMaskAssessmentData";
		$field = "keep";
		// make sure the row and column exists 
		$q = "SELECT `".$field."` "
			."FROM `".$table."` "
			."WHERE `DEF_id`=".$maskId." ";
		$olddata = $this->mysql->getSQLResult($q);
		if ( array_key_exists($field, $olddata[0]) ) {
			$data 			= array();
			$data[$field] 	= $newStatus;
			$where 			= array('DEF_id'=>$maskId);
			$this->mysql->SQLUpdate( $table, $data, $where );
		}
	}	
	
	// Update all the masks for a given image with the new status.
	// Use the $assessRunId to find the ApMaskMakerRunData ID.
	// Use the $imageId with the mask maker run id to find all the mask region ids that should change.
	// Use the mask region id with the assessment run ID to update the status in ApMaskAssessmentData.
	// For now, not using the assessment run ID, I think there is only one per region.
	function updateMaskAssessmentByImage( $imageId, $assessRunId, $newStatus) 
	{
		// Pull the region id from ApMaskRegionData and give it a key of 
		// REF|ApMaskRegionData|region to match what we are looking for in ApMaskAssessmentData.
		$q = "SELECT regions.`DEF_id` as `REF|ApMaskRegionData|region` "
			."FROM `ApMaskRegionData` as regions "
			."LEFT JOIN `ApMaskAssessmentRunData` as assessRun "
			."ON (assessRun.`REF|ApMaskMakerRunData|maskrun` = regions.`REF|ApMaskMakerRunData|maskrun`) "
			."WHERE assessRun.`DEF_id`=".$assessRunId." AND regions.`REF|leginondata|AcquisitionImageData|image`=".$imageId." ";

		$regionIds = $this->mysql->getSQLResult($q);
		if ($regionIds === False) {
			$dberror = $this->mysql->getError();
			//echo "error -> $dberror query -> $q \n";
			error_log("Error: database error in particledata.inc, updateMaskAssessmentByImage(): $dberror /n");
		}
		
		// Update keep status
		$data 			= array();
		$data["keep"] 	= $newStatus;
		foreach ( $regionIds as $regionId ) {
			$this->mysql->SQLUpdate( "ApMaskAssessmentData", $data, $regionId );
		}
	}		

	function getMaskAssessment( $imageId, $maskRunId) 
	{
		// First find the mask region ID
		$q = "SELECT `DEF_id` "
			."FROM `ApMaskRegionData` "
			."WHERE `REF|leginondata|AcquisitionImageData|image`=".$imageId." and `REF|ApMaskMakerRunData|maskrun`=".$maskRunId." ";
			
		$regionIdResult = $this->mysql->getSQLResult($q);
		if ($regionIdResult === False) {
			$dberror = $this->mysql->getError();
			echo "error -> $dberror query -> $q \n";
			//error_log("Error: database error in particledata.inc, updateMaskAssessmentByImage(): $dberror /n");
			return;
		} else if ( empty($regionIdResult) ) {
			//var_dump($q);
			return;
		} else {
			$regionId = $regionIdResult[0]['DEF_id'];
		}
		
		// Now find the keep status from the region id
		$table = "ApMaskAssessmentData";
		$field = "keep";
		// make sure the row and column exists 
		$q = "SELECT `".$field."` "
			."FROM `".$table."` "
			."WHERE `REF|ApMaskRegionData|region`=".$regionId." ";
		
		$r = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			echo "error -> $dberror query -> $q \n";
			//error_log("Error: database error in particledata.inc, updateMaskAssessmentByImage(): $dberror /n");
		}
		return $r[0]['keep'];
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
			."WHERE i.`REF|projectdata|projects|project`='$projectId' ";
		if (!$getHidden) $q.= "AND (i.`hidden` IS NULL OR i.`hidden` = 0) ";
		$q.= "ORDER BY i.`DEF_id` DESC";
		//echo $q."\n<BR/>\n";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getModelsFromRefineID( $refineID )
	{
		$q = "SELECT model.*, refmodel.filename  "
			. " FROM `ApRefineInitModelData` AS refmodel, ApInitialModelData AS model "
			. " WHERE refmodel.`REF|ApPrepRefineData|preprefine` = $refineID "
			. " AND refmodel.`REF|ApInitialModelData|refmodel` = model.`DEF_id` ";

		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
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
			."WHERE i.`REF|projectdata|projects|project`='$projectId' "
			."ORDER BY i.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getJobTypesLike( $expId, $pattern )
	{
		$q="SELECT DISTINCT(j.`jobtype`) "
			."FROM `ApAppionJobData` AS j "
			."WHERE j.`REF|leginondata|SessionData|session` = $expId "
			."AND j.`jobtype` LIKE '$pattern' ";
		
		$r = $this->mysql->getSQLResult($q);
		
		return $r;
	}

	function getJobNameTypesLike( $expId, $name, $pattern )
	{
		$q="SELECT * "
			."FROM `ApAppionJobData` AS j "
			."WHERE j.`REF|leginondata|SessionData|session` = $expId "
			."AND j.`name` LIKE '$name' "
			."AND j.`jobtype` LIKE '$pattern' ";
		$r = $this->mysql->getSQLResult($q);
		
		return $r;
	}

	function getJobIdsFromSession($expId, $jobtype=False, $status=False, $ignore=True) {
		$q="SELECT j.*, "
			."p.path as appath "
			."FROM `ApAppionJobData` AS j "
			."LEFT JOIN `ApPathData` AS p ON "
			."(j.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE j.`REF|leginondata|SessionData|session` = $expId";
		if ($jobtype) $q.=" AND j.`jobtype` = '$jobtype'";
		if ($status) $q.=" AND j.`status` = '$status'";
		if ($ignore) $q.=" AND j.`status` != 'I'";
		$q.=" ORDER BY j.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		if ($r === False) {
			$dberror = $this->mysql->getError();
			error_log("Error: database error in particledata.inc, getJobIdsFromSession(): $dberror /n");
		}
		return $r;
	}

	function getFscFromRefinementDataId ($id) {
		$q = "SELECT * "
			."FROM ApFSCData "
			."WHERE `REF|ApRefineIterData|refineIter` = $id "
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
			."FROM `ApAppionJobData` AS j "
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

	function getJobFileFromPath($path,$name=False) {
		$q="SELECT j.*, p.path "
			."FROM `ApAppionJobData` AS j "
			."LEFT JOIN ApPathData AS p ON "
			."(j.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE p.`path` = '$path'";
			if ($name) $q.= " AND j.`name` = '$name'";
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
			."FROM `ApAppionJobData` "
			."WHERE `REF|ApPathData|path` = $pathid AND "
			."`name` = '$name' AND "
			."`REF|leginondata|SessionData|session` = $expId "
			." AND `jobtype` = $jobtype ";
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
			$jid=$this->mysql->SQLInsert('ApAppionJobData',$jdata);
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
		$this->mysql->SQLUpdate('ApAppionJobData',$data,$where);
	}

	function updateClusterJobStatus($jobid, $status, $user=false) {
		$data = array('status'=>$status);
		$where = array('DEF_id'=>$jobid);
		if ($user)
			$where['user'] = $user;
		$this->mysql->SQLUpdate('ApAppionJobData',$data, $where);
	}

	function abortClusterJob($jobid, $user=false) {
		$this->updateClusterJobStatus($jobid,'A',$user);
	}

	function markDoneAppionJob($jobid, $user=false) {
		$this->updateClusterJobStatus($jobid,'D',$user);
	}

	function getSubmittedJobs($expId) {
		$q="SELECT * "
			."FROM `ApAppionJobData` "
			."WHERE `REF|leginondata|SessionData|session`=$expId";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function abortSimilarJobs($expId,$jobname,$jobtype) {
		/*
		This function is used to change status of the multiple attempts of the
		same job when one of them has been forced by the user to done or abort.
		*/
		$aborted_jobids = array();
		$jobs = $this->getJobNameTypesLike($expId,$jobname,$jobtype);
		foreach ($jobs as $job) {
			if ($job['status'] == 'Q') {
				$this->updateClusterjobStatus($job['DEF_id'],'A',false);
				$aborted_jobids[]=$job['DEF_id'];
			}
		}
		return $aborted_jobids;
	}

	// This tells us if the job has already been uploaded
	function getReconIdFromAppionJobId($jobid) {
		$q="SELECT * "
			."FROM `ApRefineRunData` "
			."WHERE `REF|ApAppionJobData|job` = $jobid";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}
	
	// This tells us if the job has already been uploaded
	function getAlignRunIdFromAppionPathId($pathid) {
		$q="SELECT * "
			."FROM `ApAlignRunData` "
			."WHERE `REF|ApPathData|path` = $pathid";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getJobNamesFromJobType( $jobtype, $sessionId )
	{
		$q = "select name from `ApAppionJobData` "
			."where `REF|leginondata|SessionData|session` = $sessionId "
			."and jobtype = '$jobtype'";
		$r = $this->mysql->getSQLResult($q);

		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			error_log("Error: database error in particledata.inc, getDefaultJobName(): $dberror /n");
		}
		return $r;
	}
	
	// parse the runname into its components
	static function getJobRunIdFromRunname( $runname ) 
	{
		// step 1: strip the jobtype and id from the runname
		
		// check if the runname has a timestamp appended seperated by '-'
		// explode returns an empty array if the delimiter is not found and the limit is negative
		list($baseRunName, $extension) = explode( "-", $runname, -1 );
		
		// check if the jobtype and id are followed by a '.' with other stuff 
		if ( !$baseRunName ) {
			list($baseRunName, $extension) = explode( ".", $runname, -1 );
		}
		if ( !$baseRunName ) {
			error_log("Error: unable to parse the 'runname' in particledata.inc, getJobRunIdFromRunname./n");
		}

		// step 2: match the $baseRunName with letters in the front and id with numbers at the end of the string
		preg_match('/(\D+)(\d+)$/', $baseRunName, $matches);
		$program = $matches[1];
		$runId = $matches[2];
		return $runId;
	}
	
	function getMaxRunNumber( $jobtype, $sessionId )
	{
		// get job names corresponding to the desired type for this session
		$names = $this->getJobNamesFromJobType( $jobtype, $sessionId );
		
		// find the name with the greatest incremental id ex. recon4 is greater than recon3
		$maxRunNumber = 0;
		if ( !empty($names) ) {
			foreach ( $names as $name ) {
				$runNumber = $this->getJobRunIdFromRunname( $name['name'] );
				$maxRunNumber = ( $runNumber > $maxRunNumber ) ? $runNumber : $maxRunNumber;
			}
		}
		
		return $maxRunNumber;
	}
	
	function getDefaultJobName( $jobtype, $sessionId )
	{
		// check input values
		if ( !$jobtype ) {
			error_log("Error: 'jobtype' Parameter in particledata.inc, getDefaultJobName() is not set./n");
			return False;
		} 
		
		if ( !$sessionId ) {
			error_log("Error: 'sessionId' Parameter in particledata.inc, getDefaultJobName() is not set./n");
			return False;
		}
		
		$lastRunNumber = $this->getMaxRunNumber( $jobtype, $sessionId );
		
		// increment the current run number and append it to the jobtype to create new jobname
		$lastRunNumber++;
		$jobName = $jobtype . $lastRunNumber;
		
		return $jobName;
	}
	
	// Warning: do not use this function for counting the number of runs to create a new runname.
	// try getMaxRunNumber instead.
	function getReconIdsFromSession($sessionId, $showHidden=false, $package=false) {
		$q = "SELECT DISTINCT(refrun.`DEF_id`) AS refid, refrun.*, path.path AS path  "
			." FROM `ApRefineRunData` AS refrun "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			." ON refrun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden) $q.= " AND (refrun.`hidden` IS NULL OR refrun.`hidden` = 0) ";
		if ($package) $q.= " AND (refrun.`package` = '$package') ";
		$q.= " ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}

	// Warning: do not use this function for counting the number of runs to create a new runname.
	// try getMaxRunNumber instead.
	function getMultiModelReconIdsFromSession($sessionId, $showHidden=false, $package=false) {
		$q = "SELECT DISTINCT(refrun.`DEF_id`) AS refid, refrun.*, path.path AS path "
			." FROM `ApRefineRunData` AS refrun "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			." ON refrun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' "
			." AND refrun.`REF|ApMultiModelRefineRunData|multiModelRefineRun` IS NOT NULL ";
		if (!$showHidden) $q.= " AND (refrun.`hidden` IS NULL OR refrun.`hidden` = 0) ";
		if ($package) $q.= " AND (refrun.`package` = '$package') ";
		$q.= " ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
		return $r;
	}
	
	// Warning: do not use this function for counting the number of runs to create a new runname.
	// try getMaxRunNumber instead.
	function getSingleModelReconIdsFromSession($sessionId, $showHidden=false, $package=false) {
		$q = "SELECT DISTINCT(refrun.`DEF_id`) AS refid, refrun.*, path.path AS path "
			." FROM `ApRefineRunData` AS refrun "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON refrun.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			." ON refrun.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' "
			." AND refrun.`REF|ApMultiModelRefineRunData|multiModelRefineRun` IS NULL ";
		if (!$showHidden) $q.= " AND (refrun.`hidden` IS NULL OR refrun.`hidden` = 0) ";
		if ($package) $q.= " AND (refrun.`package` = '$package') ";
		$q.= " ORDER BY refrun.`DEF_id` DESC";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//if ($e=$this->mysql->getError()) {
			//echo "error -> $e \n";
		//}
		//echo print_r($r)."<br/>\n";
		return $r;
	}
	
	function getReconIterIdRelatedToStackid($stackId, $showHidden=False) {
		// First get first three particle ids from the stack id
		$q = "SELECT `REF|ApParticleData|particle` AS partid "
			." FROM ApStackParticleData AS stpart "
			."WHERE `REF|ApStackData|stack` = '$stackId' "
			."LIMIT 3 ";
		//echo $q."<br/><br/>\n";
		$r1 = $this->mysql->getSQLResult($q);
		//echo print_r($r1)."<br/><br/>\n";
		$partId1 = $r1[0]['partid'];
		$partId2 = $r1[1]['partid'];
		$partId3 = $r1[2]['partid'];

		// Second get all recons using those particles
		$q = "SELECT refrun.* "
			." FROM ApRefineParticleData AS refpart "
			."LEFT JOIN ApStackParticleData AS stpart "
			." ON refpart.`REF|ApStackParticleData|particle` = stpart.`DEF_id` "
			."LEFT JOIN ApRefineIterData AS refiter "
			." ON refpart.`REF|ApRefineIterData|refineIter` = refiter.`DEF_id` "
			."LEFT JOIN ApRefineRunData AS refrun "
			." ON refiter.`REF|ApRefineRunData|refineRun` = refrun.`DEF_id` "
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

	function getExemplarReconsFromSession($sessionId, $showHidden=False) {
		$q = "SELECT refdata.`DEF_id` as refdataid, "
			."refrun.`DEF_id` as refrunid, "
			."refdata.*, refrun.*, stackrun.*, runs.*, p.*, params.* "
			." FROM `ApRefineIterData` AS refdata "
			."LEFT JOIN `ApRefineRunData` AS refrun "
			. "ON refdata.`REF|ApRefineRunData|refineRun` = refrun.`DEF_id` "
			."LEFT JOIN `ApEmanRefineIterData` AS params "
			." ON (refdata.`REF|ApEmanRefineIterData|emanParams` = params.`DEF_id`) "
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

	function getReconIds($stackId, $showHidden=False) {
		$q = "SELECT * "
			."FROM `ApRefineRunData` AS r ";
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

	function getRefinementRunInfo($refineRunId) {
		$q="select r.*, p.path "
			."FROM `ApRefineRunData` AS r "
			."LEFT JOIN ApPathData AS p ON "
			."(r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$refineRunId' ";
		//echo $q."<br/><br/>\n";
		list($r) = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/>\n";
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
			."WHERE d.`REF|ApRefineIterData|refineIter` = $refid ";
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
				."FROM `ApRefineIterData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefineRunData|refineRun` = '$reconid' "
				//."ORDER by rmeas.rMeasure ";
				."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getHighestRMeasureForRecon ($reconid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas "
				."FROM `ApRefineIterData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApRefineRunData|refineRun` = '$reconid' "
				."ORDER by rmeas.rMeasure ";
				//."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getIterationInfo ($reconId,$iteration=0) {
		$q = "SELECT * "
				."FROM `ApRefineIterData` r "
				."WHERE r.`REF|ApRefineRunData|refineRun` = '$reconId' "
				."ORDER BY r.`iteration` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($r[0]['REF|ApEmanRefineIterData|emanParams']) {
			$q = "SELECT * "
					."FROM `ApRefineIterData` r "
					."LEFT JOIN `ApEmanRefineIterData` p "
					."ON (r.`REF|ApEmanRefineIterData|emanParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefineRunData|refineRun` = '$reconId' "
					."ORDER BY r.`iteration` ASC ";
		} elseif ($r[0]['REF|ApXmippRefineIterData|xmippParams']) {
			$q = "SELECT * "
					."FROM `ApRefineIterData` r "
					."LEFT JOIN `ApXmippRefineIterData` p "
					."ON (r.`REF|ApXmippRefineIterData|xmippParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefineRunData|refineRun` = '$reconId' "
					."ORDER BY r.`iteration` ASC ";
		} elseif ($r[0]['REF|ApFrealignIterData|frealignParams']) {
			$q = "SELECT * "
					."FROM `ApRefineIterData` r "
					."LEFT JOIN `ApFrealignIterData` p "
					."ON (r.`REF|ApFrealignIterData|frealignParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefineRunData|refineRun` = '$reconId' "
					."ORDER BY r.`iteration` ASC ";
		} elseif ($r[0]['REF|ApRelionIterData|relionParams']) {
			$q = "SELECT * "
					."FROM `ApRefineIterData` r "
					."LEFT JOIN `ApRelionIterData` p "
					."ON (r.`REF|ApRelionIterData|relionParams` = p.`DEF_id`) "
					."WHERE r.`REF|ApRefineRunData|refineRun` = '$reconId' "
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

	function getRefinementData ($refineRunId, $iteration=False) {
		$q = "SELECT * "
			."FROM `ApRefineIterData` "
			."WHERE `REF|ApRefineRunData|refineRun` = $refineRunId ";
		if ($iteration) $q.="AND `iteration` = $iteration";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParamsFromRefinementDataId ($refineIterId) {
		$q = "SELECT * "
				."FROM `ApRefineIterData` AS refineIter "
				."LEFT JOIN `ApEmanRefineIterData` emanparams "
				."  ON (refineIter.`REF|ApEmanRefineIterData|emanParams` = emanparams.`DEF_id`) "
				."WHERE refineIter.`DEF_id` = $refineIterId";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r[0];
	}

	function getStackFromRefineIter ($refineIterId) {
		$q = "SELECT r.*, rr.*, s.*, path.path "
				."FROM `ApRefineIterData` r "
				."LEFT JOIN `ApRefineRunData` rr "
				."ON (r.`REF|ApRefineRunData|refineRun` = rr.`DEF_id`) "
				."LEFT JOIN `ApStackData` s "
				."ON (rr.`REF|ApStackData|stack` = s.`DEF_id`) "
				."LEFT JOIN `ApPathData` path "
				."ON (s.`REF|ApPathData|path` = path.`DEF_id`) "
				."WHERE r.`DEF_id` = $refineIterId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRefineParticleCounts($refineIterId) {
		//check for cached values
		$q = "SELECT * "
			."FROM `ApRefineGoodBadParticleData` gb "
			."WHERE gb.`REF|ApRefineIterData|refine` = '$refineIterId' ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		if (!$r)
			return;
		return $r[0];
	}

	function getSubsetParticlesInStack ($refineIterId, $subset, $refinetype='refine') {
		$q = "SELECT particleNumber as p ";
		$q .= "FROM `ApRefineParticleData` AS refinepart "
			."LEFT JOIN `ApStackParticleData` AS stackpart "
			."  ON (refinepart.`REF|ApStackParticleData|particle` = stackpart.`DEF_id`) "
			."WHERE refinepart.`REF|ApRefineIterData|refineIter` = '$refineIterId' ";
		if ($refinetype == 'postRefine') {
			if ($subset=='bad')
				$q.="AND (refinepart.`postRefine_keep` = 0 OR refinepart.`postRefine_keep` IS NULL) ";
			else
				$q.="AND refinepart.`postRefine_keep` = 1 ";
		} else {
			if ($subset=='bad')
				$q.="AND (refinepart.`refine_keep` = 0 OR refinepart.`refine_keep` IS NULL) ";
			elseif (stripos($subset,';')!==false) {
				$bits = explode(';',$subset);
				$threeDref_num = $bits[0];
				$twoDclass_num = $bits[1];
				if (is_numeric($threeDref_num) && is_numeric($twoDclass_num) && $threeDref_num > 0 && $twoDclass_num >= 0) 
					$q.="AND (refinepart.`3Dref_num` = $threeDref_num AND refinepart.`2Dclass_num` = $twoDclass_num) ";
			} else
				$q.="AND refinepart.`refine_keep` = 1 ";
		}
		$q.= "ORDER BY stackpart.`particleNumber` ASC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}
	
	function getNumParticlesFromRefineIter($refineIterId) 
	{
		$q = "SELECT COUNT(*) as num_parts ";
		$q .= "FROM `ApRefineParticleData` AS refinepart "
			."WHERE refinepart.`REF|ApRefineIterData|refineIter` = '$refineIterId' ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}	

	function getPreparedFrealignJobs ($jobid=False, $path=False, $showHidden=true) {
		$q = "SELECT fre.*, path.path, job.`DEF_id` AS jobid  "
			. " FROM `ApFrealignPrepareData` AS fre "
			. " LEFT JOIN ApPathData AS path ON ( fre.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " LEFT JOIN ApAppionJobData AS job ON ( fre.`REF|ApAppionJobData|job` = job.`DEF_id` ) ";
		if ($jobid) {
			$q .= " WHERE fre.`DEF_id` = '$jobid' ";
		} elseif ($path) {
			$q .= " WHERE path.`path` = '$path' ";
		} elseif (!$showHidden) {
			$q .= " WHERE fre.`hidden` != '1' AND job.`status` = 'D' ";
		}
		$q .=  "  ORDER BY fre.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getPreparedRefineJobs ($jobid=False, $path=False, $showHidden=true, $name=False) {
		$q = "SELECT ref.*, path.path, job.`DEF_id` AS jobid  "
			. " FROM `ApPrepRefineData` AS ref "
			. " LEFT JOIN ApPathData AS path ON ( ref.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " LEFT JOIN ApAppionJobData AS job ON ( ref.`REF|ApAppionJobData|job` = job.`DEF_id` ) ";
		if ($jobid) {
			$q .= " WHERE job.`DEF_id` = '$jobid' ";
		} elseif ($path) {
			$q .= " WHERE ref.`REF|ApPathData|path` = '$path' ";
		} elseif ($name) {
			$q .= " WHERE ref.`name` = '$name' ";
		} elseif (!$showHidden) {
			$q .= " WHERE ref.`hidden` != '1' AND job.`status` = 'D' ";
		}
		$q .=  "  ORDER BY ref.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}
	
	function getPreparedRefineStackData ( $refineid ) {
		$q = "SELECT stack.*, stackref.pixelsize AS parent_pixelsize, "
			. "stackref.`DEF_id` AS parent_id "
			. " FROM ApRefineStackData AS stack "
			. " LEFT JOIN ApStackData AS stackref ON ( stackref.`DEF_id` = stack.`REF|ApStackData|stackref` ) "
			. " WHERE stack.`REF|ApPrepRefineData|preprefine` = $refineid ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}
	
	function getUploadFrealignJobs ($jobid=False, $path=False, $showHidden=true) {
		$q = "SELECT fre.*, path.path  "
			. " FROM `ApFrealignPrepareData` AS fre "
			. " LEFT JOIN ApPathData AS path ON ( fre.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " LEFT JOIN ApAppionJobData AS job ON ( fre.`REF|ApAppionJobData|job` = job.`DEF_id` ) ";
		if ($jobid) {
			$q .= " WHERE fre.`DEF_id` = '$jobid' ";
		} elseif ($path) {
			$q .= " WHERE path.`path` = '$path' ";
		} elseif (!$showHidden) {
			$q .= " WHERE fre.`hidden` != '1' ";
		}
		$q .=  "  ORDER BY fre.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getClusterJobByTypeAndPath ($type, $path) {
		$q = "SELECT job.*  "
			. " FROM `ApAppionJobData` AS job "
			. " LEFT JOIN ApPathData AS path "
			. "  ON ( job.`REF|ApPathData|path` = path.`DEF_id` ) "
			. " WHERE "
			. "  path.`path` = '$path' "
			. " AND "
			. "  job.`jobtype` = '$type' "
			. "  ORDER BY job.`DEF_id` DESC ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getRawStackFromCluster ($clusterStackId) {
		$q = "SELECT asd.*, path.path "
			. " FROM `ApClusteringParticleData` acpd "
			. " LEFT JOIN ApAlignParticleData aapd ON ( acpd.`REF|ApAlignParticleData|alignparticle` = aapd.`DEF_id` ) "
			. " LEFT JOIN ApStackParticleData aspd ON ( aapd.`REF|ApStackParticleData|stackpart` = aspd.`DEF_id`) "
			. " LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( asd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE acpd.`REF|ApClusteringStackData|clusterstack` = '$clusterStackId'  LIMIT 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getRawStackFromAlign ($alignStackId) {
		$q = "SELECT asd.*, path.path "
			. " FROM ApAlignParticleData aapd "
			. " LEFT JOIN ApStackParticleData aspd ON ( aapd.`REF|ApStackParticleData|stackpart` = aspd.`DEF_id`) "
			. " LEFT JOIN ApStackData asd ON ( aspd.`REF|ApStackData|stack` = asd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( asd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE aapd.`REF|ApAlignStackData|alignstack` = '$alignStackId' LIMIT 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getAlignedStackFromCluster ($clusterStackId) {
		$q = "SELECT aasd.*, path.path "
			. " FROM `ApClusteringParticleData` acpd "
			. " LEFT JOIN ApAlignParticleData aapd ON ( acpd.`REF|ApAlignParticleData|alignparticle` = aapd.`DEF_id` ) "
			. " LEFT JOIN ApAlignStackData aasd ON ( aapd.`REF|ApAlignStackData|alignstack` = aasd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( aasd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE acpd.`REF|ApClusteringStackData|clusterstack` = '$clusterStackId' LIMIT 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getAlignedStackFromAlign ($alignStackId) {
		$q = "SELECT aasd.*, path.path "
			. " FROM ApAlignParticleData aapd "
			. " LEFT JOIN ApAlignStackData aasd ON ( aapd.`REF|ApAlignStackData|alignstack` = aasd.`DEF_id`) "
			. " LEFT JOIN `ApPathData` path ON ( aasd.`REF|ApPathData|path` = path.`DEF_id`) "
			. " WHERE aapd.`REF|ApAlignStackData|alignstack` = '$alignStackId' LIMIT 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSubsetParticlesFromCluster ($clusterStackId, $refnums, $count=False) {
		$q = "SELECT particleNumber as p ";
		if ($count) $q = "SELECT count(particleNumber) as p ";
		$q .= "FROM `ApClusteringParticleData` acpd "
			."LEFT JOIN ApAlignParticleData aapd ON ( acpd.`REF|ApAlignParticleData|alignparticle` = aapd.`DEF_id` )"
			."LEFT JOIN ApStackParticleData aspd ON ( aapd.`REF|ApStackParticleData|stackpart` = aspd.`DEF_id`)"
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
		$q .= "FROM `ApAlignParticleData` aapd "
			."LEFT JOIN ApAlignReferenceData aard ON ( aapd.`REF|ApAlignReferenceData|ref` = aard.`DEF_id`)"
			."LEFT JOIN ApStackParticleData aspd ON ( aapd.`REF|ApStackParticleData|stackpart` = aspd.`DEF_id`)"
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

	function listAllStackParticles ($stackId) {
		$q="SELECT sp.`particleNumber`, db.`MRC|image`, "
			."p.`xcoord` , p.`ycoord` "
			."FROM  `ApStackParticleData` sp "
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
			."  e.`REF|ApRefineRunData|refineRun` = '$refineRunId' "
			."GROUP BY e.`REF|ApRefineRunData|refineRun` ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r[0];
	}

	function getEulerJumpsMM ($multiModelRefineRunId) {
		$q="SELECT "
			."  e.`DEF_id`, "
			."  e.`median` "
			."FROM ApEulerJumpData AS e "
			."WHERE "
			."  e.`REF|ApMultiModelRefineRunData|multiModelRefineRun` = '$multiModelRefineRunId' ";
			//."ORDER BY e.`median` ASC "
			//."LIMIT 20 ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getAverageMedianJumpMM ($multiModelRefineRunId) {
		$q = "SELECT "
			."COUNT(e.`median`) AS count, "
			."AVG(e.`median`) AS average, "
			."STDDEV(e.`median`) AS stdev "
			."FROM ApEulerJumpData AS e "
			."WHERE "
			."  e.`REF|ApMultiModelRefineRunData|multiModelRefineRun` = '$multiModelRefineRunId' "
			."GROUP BY e.`REF|ApMultiModelRefineRunData|multiModelRefineRun` ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r[0];
	}

	function getEulerJumps ($refineRunId) {
		$q="SELECT "
			."  e.`DEF_id`, "
			."  e.`median` "
			."FROM ApEulerJumpData AS e "
			."WHERE "
			."  e.`REF|ApRefineRunData|refineRun` = '$refineRunId' ";
			//."ORDER BY e.`median` ASC "
			//."LIMIT 20 ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	// no more ApEulerData tables
	//function getParticleEuler ($refinementDataId) {
	//	$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
	//		."FROM `ApRefineParticleData` "
	//		."WHERE `REF|ApRefineIterData|refineIter` = '$refinementDataId' ";
	//	$r = $this->mysql->getSQLResult($q);
	//	return $r;
	//}

	//function getNumInClass ($refinementDataId,$eulerId) {
	//	$q = "SELECT count(DEF_id) as num "
	//		."FROM `ApRefineParticleData` "
	//		."WHERE `REF|ApRefineIterData|refineIter` = '$refinementDataId' "
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
		$q = "SELECT cls1.`REF|ApStackParticleData|particle` as prtl, "
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
				."FROM (`ApRefineParticleData` as cls1) "
				."LEFT JOIN ( "
				." `ApRefineParticleData` as cls2, "
				." `ApStackParticleData` as spd) "
				//." `ApEulerData` euler1, `ApEulerData` euler2) "
				."ON ( "
				."cls1.`REF|ApStackParticleData|particle`=cls2.`REF|ApStackParticleData|particle` "
				."AND spd.DEF_id=cls1.`REF|ApStackParticleData|particle` "
				."AND cls1.`refine_keep`=1 AND cls2.`refine_keep`=1 "
				//."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				//."AND euler2.DEF_id=cls2.`REF|ApEulerData|eulers` "
				.") "
				."WHERE (cls1.`REF|ApRefineIterData|refineIter`=$refine1 "
				."AND cls2.`REF|ApRefineIterData|refineIter`=$refine2 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlesFromRefinementId($refine1) {
		# compare 2 iterations, get all the particles that were used in both
		# reconstructions (ignore those that were thrown out) and return the eulers"
		$q = "SELECT cls1.`REF|ApStackParticleData|particle` as prtl, "
				."spd.particleNumber, "
				."cls1.euler1 as euler1_1, "
				."cls1.euler2 as euler1_2, "
				."cls1.euler3 as euler1_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls1.`shifty` as shifty1, "
				."cls1.`inplane_rotation` as rot1, "
				."cls1.`quality_factor` as qf1 "
				."FROM (`ApRefineParticleData` as cls1) "
				."LEFT JOIN ( "
				." `ApStackParticleData` as spd) "
				//." `ApEulerData` euler1) "
				."ON ( "
				."spd.DEF_id=cls1.`REF|ApStackParticleData|particle` "
				."AND cls1.`refine_keep`=1 "
				//."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				.") "
				."WHERE ( "
				." cls1.`REF|ApRefineIterData|refineIter`=$refine1 "
				.") "
				."ORDER by prtl";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParticleNum ($particleId) {
		$q = "SELECT particleNumber "
			."FROM `ApStackParticleData` "
			."WHERE `DEF_id` = $particleId";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['particleNumber'];
	}

	function getMiscInfoFromReconId ($reconid) {
		$q = "SELECT m.*, p.path "
		."FROM `ApMiscData` AS m "
		."LEFT JOIN ApPathData AS p ON "
		."(m.`REF|ApPathData|path` = p.`DEF_id`) "
		."WHERE m.`REF|ApRefineRunData|refineRun` = $reconid";
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
		."`ApRefineIterData` AS `ApRefineIterData` "
		."LEFT JOIN `ApRefineRunData` AS `ApRefineRunData` "
		."ON (`ApRefineRunData`.`DEF_id`=`ApRefineIterData`.`REF|ApRefineRunData|refineRun`) "
		."LEFT JOIN `ApPathData` AS `ApPathData` "
		."ON (`ApPathData`.`DEF_id`=`ApRefineRunData`.`REF|ApPathData|path`) "
		."WHERE `ApRefineIterData`.`DEF_id`=$refineid ";
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
			."FROM ApAlignParticleData AS part "
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
			."FROM ApAlignParticleData AS a "
			."WHERE "
			."  a.`REF|ApAlignStackData|alignstack` = '$alignid' ";
			//."ORDER BY e.`median` "
			//."LIMIT 100 ";
		//echo $q."<br/><br/>\n";
		$r=$this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function hasHelicalInfo($alignid) {
		$q="SELECT p.helixnum FROM ApAlignParticleData AS a "
			."LEFT JOIN ApStackParticleData as s "
			."ON (a.`REF|ApStackParticleData|stackpart`=s.`DEF_id`) "
			."LEFT JOIN ApParticleData AS p "
			."ON (s.`REF|ApParticleData|particle`=p.`DEF_id`) "
			."WHERE "
			."  a.`REF|ApAlignStackData|alignstack` = '$alignid' "
			."limit 1";
		//echo $q;
		$r = $this->mysql->getSQLResult($q);
		if ($r[0]['helixnum']) return True;
		return False;
	}

	function getNumImagesInAlignment($alignid) {
		$q="SELECT count(*) as img "
			." FROM ApAlignParticleData AS a "
			."LEFT JOIN ApStackParticleData as s "
			."ON (a.`REF|ApStackParticleData|stackpart`=s.`DEF_id`) "
			."LEFT JOIN ApParticleData AS p "
			."ON (s.`REF|ApParticleData|particle`=p.`DEF_id`) "
			."WHERE "
			."  a.`REF|ApAlignStackData|alignstack` = '$alignid' "
			."GROUP BY p.`REF|leginondata|AcquisitionImageData|image` ";
		$r = $this->mysql->getSQLResult($q);
		return count($r);
	}

	function getHelicalInfoForClasses($alignid,$classnums,$onlyNumImgs=False){
		if ($onlyNumImgs) $q = "SELECT count(*) as img ";
		else $q="SELECT a.partnum, "
			." a.xshift, "
			." a.yshift, "
			." a.rotation, "
			." p.`REF|leginondata|AcquisitionImageData|image` as image, "
			." p.angle, "
			." p.helixnum ";
		$q.= " FROM ApAlignParticleData AS a "
			."LEFT JOIN ApStackParticleData as s "
			."ON (a.`REF|ApStackParticleData|stackpart`=s.`DEF_id`) "
			."LEFT JOIN ApParticleData AS p "
			."ON (s.`REF|ApParticleData|particle`=p.`DEF_id`) "
			."LEFT JOIN ApAlignReferenceData as ar "
			."ON (a.`REF|ApAlignReferenceData|ref` = ar.`DEF_id`) "
			."WHERE "
			."  a.`REF|ApAlignStackData|alignstack` = '$alignid' "
			."  AND (";
		foreach ($classnums as $cnum) {
			$refnum = strval(intval($cnum)+1);
			$q .= " ar.`refnum` = '$refnum' OR ";
		}
		$q = substr($q, 0, -3);
		$q .= ")";
		if ($onlyNumImgs) $q.= "GROUP BY p.`REF|leginondata|AcquisitionImageData|image`";
		$r = $this->mysql->getSQLResult($q);
		if ($onlyNumImgs) return count($r);
		return $r;
	}

	function getClusteringParticleNumber($clusterId) {
		$q="SELECT part.`refnum` AS classNumber, "
			."  COUNT(part.`DEF_id`) AS number, "
			."  ROUND(ref.`ssnr_resolution`,3) AS resolution "
			."FROM ApClusteringParticleData AS part "
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
		if ($this->mysql->SQLTableExists('ApRefineIterData')) {
			$q .= ", refineiter.`REF|ApRefineRunData|refineRun` AS refrun ";
		}
		$q .=	"FROM Ap3dDensityData as dens "
			."LEFT JOIN ApPathData AS path "
			."  ON dens.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists('ApRefineIterData')) {
			$q .=	"LEFT JOIN ApRefineIterData AS refineiter "
				."  ON dens.`REF|ApRefineIterData|refineIter` = refineiter.`DEF_id` ";
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
		if ($this->mysql->SQLTableExists('ApRefineIterData')) {
			$q .= ", refineIter.`REF|ApRefineRunData|refineRun` AS refrun ";
		}
		$q .=	"FROM Ap3dDensityData as dens "
			."LEFT JOIN ApPathData AS path "
			."  ON dens.`REF|ApPathData|path` = path.`DEF_id` ";
		if ($this->mysql->SQLTableExists('ApRefineIterData')) {
			$q .=	"LEFT JOIN ApRefineIterData AS refineIter "
				."  ON dens.`REF|ApRefineIterData|refineIter` = refineIter.`DEF_id` ";
		}
		$q .= "WHERE "
			."  dens.`DEF_id` = '$densityId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}
	
	function getAutomatedCommonLinesRunsCs($sessionId) {
		$q="SELECT "
			."  ar.*, "
			."  path.`path` AS path "
			."FROM ApAutomatedCommonLinesRunData as ar "
			."LEFT JOIN ApPathData AS path "
			."  ON ar.`REF|ApPathData|path` = path.`DEF_id` "
			
			### add a session entry to table
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
			."  stackrun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY ar.`DEF_id` DESC";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getAutomatedCommonLinesRunsTs($sessionId) {
		$q="SELECT "
			."  ar.*, "
			."  path.`path` AS path "
			."FROM ApAutomatedCommonLinesRunData as ar "
			."LEFT JOIN ApPathData AS path "
			."  ON ar.`REF|ApPathData|path` = path.`DEF_id` "
			
			### add a session entry to table
			."LEFT JOIN ApTemplateStackData AS ts "
			."  ON ar.`REF|ApTemplateStackData|templatestackid` = ts.`DEF_id` "
			."WHERE "
			."  ts.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY ar.`DEF_id` DESC";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function getAutomatedCommonLinesRunInfo($aclId) {
		$q="SELECT "
			."  ar.*, "
			."  path.`path` AS path "
			."FROM ApAutomatedCommonLinesRunData as ar "
			."LEFT JOIN ApPathData AS path "
			."  ON ar.`REF|ApPathData|path` = path.`DEF_id` "
			
			### add a session entry to table
			."LEFT JOIN ApTemplateStackData AS ts "
			."  ON ar.`REF|ApTemplateStackData|templatestackid` = ts.`DEF_id` "
			."WHERE "
			."  ar.`DEF_id` = '$aclId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getSIMPLEOrigamiRuns($sessionId) {
		$q="SELECT "
			."  sr.*, "
			."  path.`path` AS path "
			."FROM ApSIMPLEOrigamiRunData as sr "
			."LEFT JOIN ApPathData AS path "
			."  ON sr.`REF|ApPathData|path` = path.`DEF_id` "
			."LEFT JOIN ApSIMPLEOrigamiParamsData AS params "
			."  ON sr.`REF|ApSIMPLEOrigamiParamsData|simple_params` = params.`DEF_id` "
			
			### add a session entry to table
			."LEFT JOIN ApStackData AS stack "
			."  ON sr.`REF|ApStackData|stack` = stack.`DEF_id` "
			."LEFT JOIN ApRunsInStackData AS runsinstack "
			."  ON stack.`DEF_id` = runsinstack.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			."  ON stackrun.`DEF_id` = runsinstack.`REF|ApStackRunData|stackRun` "
			."WHERE "
			."  stackrun.`REF|leginondata|SessionData|session` = '$sessionId' "
			."ORDER BY sr.`DEF_id` DESC";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getSIMPLEOrigamiParams($paramId) {
		$q="SELECT "
			." * "
			."FROM ApSIMPLEOrigamiParamsData as sp "
			."WHERE sp.`DEF_id` = $paramId";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	} 

	function getSIMPLEOrigamiRunInfo($runId) {
		$q="SELECT "
			." sr.*, "
			." path.`path` AS path "
			."FROM ApSIMPLEOrigamiRunData as sr "
			."LEFT JOIN ApPathData AS path "
			."  ON sr.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE sr.`DEF_id` = $runId";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
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

	#------------HELICAL FUNCTIONS---------------#

	function getHIPIdsFromSession ($sessionId, $showHidden=false, $package=false) {
		$q = "SELECT DISTINCT (ApHipRunData.`DEF_id`) AS refid, ApHipRunData.*, path.path AS path "
			." FROM `ApHipRunData` "
			."LEFT JOIN ApRunsInStackData AS runs "
			." ON ApHipRunData.`REF|ApStackData|stack` = runs.`REF|ApStackData|stack` "
			."LEFT JOIN ApStackRunData AS stackrun "
			." ON runs.`REF|ApStackRunData|stackRun` = stackrun.`DEF_id` "
			."LEFT JOIN ApPathData AS path "
			." ON ApHipRunData.`REF|ApPathData|path` = path.`DEF_id` "
			."WHERE stackrun.`REF|leginondata|SessionData|session` = '$sessionId' ";
		if (!$showHidden) $q.= " AND (ApHipRunData.`hidden` IS NULL OR ApHipRunData.`hidden` = 0) ";
		$q.= " ORDER BY ApHipRunData.`DEF_id` DESC";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHipRunIds ($sessionId) {
		$q = "SELECT r.*, p.path "
			."FROM `ApHipRunData` AS r "
			."LEFT JOIN ApPathData AS p "
			."ON (r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`REF|leginondata|SessionData|session` = '$sessionId' ";
		//if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		$q.= "ORDER BY r.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHipRunInfo($hipId) {
		$q="select r.*, p.path "
			."FROM `ApHipRunData` AS r "
			."LEFT JOIN ApPathData AS p ON "
			."(r.`REF|ApPathData|path` = p.`DEF_id`) "
			."WHERE r.`DEF_id` = '$hipId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHipParamsInfo($hipId) {
		$q = "SELECT * "
				."FROM `ApHipParamsData` r "
				."WHERE r.`REF|ApHipRunData|hipRun` = '$hipId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackIdFromHipId ($hipId) {
		$q= "SELECT * "
			."FROM `ApHipRunData` "
			."WHERE `DEF_id` = '$hipId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['REF|ApStackData|stack'];
	}

	function getHipInfoFromRefinementId($refineid) {
		$q="SELECT *"
		."FROM "
		."`ApHipIterData` AS `ApHipIterData` "
		."LEFT JOIN `ApHipRunData` AS `ApHipRunData` "
		."ON (`ApHipRunData`.`DEF_id`=`ApHipIterData`.`REF|ApHipRunData|hipRun`) "
		."LEFT JOIN `ApPathData` AS `ApPathData` "
		."ON (`ApPathData`.`DEF_id`=`ApHipRunData`.`REF|ApPathData|path`) "
		."WHERE `ApHipIterData`.`DEF_id`=$refineid ";
		$r=$this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getHipRefinementData ($hipRunId, $iteration=False) {
		$q = "SELECT * "
			."FROM `ApHipIterData` "
			."WHERE `REF|ApHipRunData|hipRun` = $hipRunId ";
		if ($iteration) $q.="AND `iteration` = $iteration";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getHipIterInfo ($hipId,$iteration=0) {
		$q = "SELECT * "
				."FROM `ApHipIterData` r "
				."WHERE r.`REF|ApHipRunData|hipRun` = '$hipId' "
				."ORDER BY r.`iteration` ASC ";
		$r = $this->mysql->getSQLResult($q);
		if ($iteration >0) {
			return $r[$iteration-1];
		}
		return $r;
	}

	function getHighestResForHip ($hipid) {
		$q = "SELECT ref.iteration AS iter, res.half AS half, rmeas.rMeasure AS rmeas "
				."FROM `ApHipIterData` AS ref "
				."LEFT JOIN `ApResolutionData` AS res "
				." ON (ref.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
				."LEFT JOIN `ApRMeasureData` AS rmeas "
				." ON (ref.`REF|ApRMeasureData|rMeasure` = rmeas.`DEF_id`) "
				."WHERE ref.`REF|ApHipRunData|hipRun` = '$hipid' "
				//."ORDER by rmeas.rMeasure ";
				."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getPostProcsFromHipRefId($refid, $getHidden=False) {
		$q = "SELECT d.*, "
			."p.path as path , a.path as amppath "
			."FROM `Ap3dDensityData` AS d "
			."LEFT JOIN `ApPathData` AS p ON "
			."(d.`REF|ApPathData|path` = p.`DEF_id`) "
			."LEFT JOIN `ApPathData` AS a ON "
			."(d.`REF|ApPathData|ampPath` = a.`DEF_id`) "
			."WHERE d.`REF|ApHipIterData|hipIter` = $refid ";
		if (!$getHidden) $q.= "AND (d.`hidden` IS NULL OR d.`hidden` = 0) ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	//------ -------------------- ---------//
	//------ Loop again functions ---------//
	//------ -------------------- ---------//

	function getJobProgramRunsInSession ($sessionid,$jobtype) {
		$q = "SELECT DISTINCT "
			."  progrun.`DEF_id` "
			.", progrun.`runname` "
			.", runpath.`path` AS rundir "
			."FROM ApAppionJobData job "
			."LEFT JOIN ScriptProgramRun as progrun "
			."  ON job.`DEF_id` = progrun.`REF|ApAppionJobData|job` "
			."LEFT JOIN ApPathData as runpath "
			."  ON runpath.`DEF_id` = progrun.`REF|ApPathData|rundir` "
			."WHERE "
			."  job.`REF|leginondata|SessionData|session` = $sessionid "
			."AND "
			."  job.`jobtype` = '".$jobtype."' "
			."; ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getLoopProgramRuns () {
		$q = "SELECT DISTINCT "
			."  progrun.`DEF_id` AS id "
			."FROM ScriptProgramRun as progrun "
			."LEFT JOIN ScriptParamValue AS paramvalue "
			."  ON paramvalue.`REF|ScriptProgramRun|progrun` = progrun.`DEF_id` "
			."LEFT JOIN ScriptParamName AS paramname "
			."  ON paramvalue.`REF|ScriptParamName|paramname` = paramname.`DEF_id` "
			."WHERE "
			."  progrun.`REF|ApAppionJobData|job` IS NOT NULL "
			."AND "
			."  paramname.`name` = 'preset' "
			."; ";
		//echo $q."<br/><br/>\n";
		$r = $this->mysql->getSQLResult($q);
		//echo print_r($r)."<br/><br/>\n";
		return $r;
	}

	function getProgramRunFromJob ($jobid) {
		$q = "SELECT "
			."  progrun.`DEF_id` AS id "
			."FROM ScriptProgramRun as progrun "
			."WHERE `REF|ApAppionJobData|job` = ".$jobid." "
			."ORDER BY progrun.`DEF_timestamp` DESC "
			."LIMIT 1 ";
		list($r) = $this->mysql->getSQLResult($q);
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
			."LEFT JOIN ApAppionJobData AS job "
			."  ON progrun.`REF|ApAppionJobData|job` = job.`DEF_id` "
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
			."LEFT JOIN ApAppionJobData AS job "
			."  ON progrun.`REF|ApAppionJobData|job` = job.`DEF_id` "
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

	function getJobCommandParams($jobid) {
		$progrun = $this-> getProgramRunFromJob ($jobid);
		$samplecommand = $this->getProgramCommands ($progrun['id']);
		$s = array();
		if (is_array($samplecommand) && count($samplecommand) > 0)
			foreach ($samplecommand as $c) $s[$c['name']] = $c['value'];
		return $s;
	}
}

// For euler angles, takes alpha beta gamma and returns a,b,c, maybe?
function simplify($e) {
	return $e['a'].','.$e['b'].','.$e['c'];
}

//TODO: the following functions should not be in this file!
function displayCTFstats($stats, $display_keys) {
	if (!is_array($stats) || !is_array($display_keys))
		return ;
	$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
	foreach($stats as  $field=>$data) {
		$field_shown = ($field == 'resolution_appion') ? "resolution<br/><br>highest of res(pkg),<br/>res(0.5),res(0.8)": $field;
		$field_shown = ($field == 'ctffind4_resolution') ? "package resolution": $field;
		if (!$head) {
			$head = true;
			$html .= "<th>\n";
			foreach($display_keys as $kh) {
				$html .= "<td><span class='datafield0'>".$kh."</span></td>";
			}
			$html .= "</th>\n";
		}
		if ( !is_array($data) || count($data) < 1) {
			$html .= "</table>\n";
			return $html;
		}
		$html .= "<tr>\n";
		$html .= "<td rowspan='".(count($data)+1)."'><span class='datafield0'>".$field_shown."</span></td>\n";
		foreach($data as $row) {
			$html .= "<tr>\n";
			foreach($display_keys as $key) {
				if (!is_array($row))
					continue;
				if (array_key_exists($key, $row))
					$val = $row[$key];
				else
					continue;
				if (preg_match('%defocus%i', $key))
						$val = format_micro_number($val);
				if (preg_match('%^min|^max|^avg|^stddev%i', $key))
					if (preg_match('%defocus%i', $field) || preg_match('%nominal%i', $field) || preg_match('%difference_from_nom%', $field)) {
						$val = format_micro_number($val);
					} elseif (preg_match('%resolution%', $field)) {
						$val = format_angstrom_number($val*1e-10);
					} else {
						$val = format_sci_number($val, 3);
					}
				$html .= "<td>";
				$html .= " ".$val."<br/>\n";
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
					if (preg_match('%defocus%i', $key)) {
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

function getBaseAppionPath($sessioninfo,$new_base='appion') {
	if (!is_array($sessioninfo)) {
		if (!is_string($sessioninfo) && !empty($sessioninfo)) {
			echo "ERROR: NO session information";
		} else {
			echo "ERROR: string input option not yet implemented";
		}
	}

	// get from leginon session image path
	$leginon_imagepath = $sessioninfo['Image path'];
	if (defined('DEFAULT_APPION_PATH') && DEFAULT_APPION_PATH !='') {
		$appion_path = Path::formatEndPath(DEFAULT_APPION_PATH);
		$parts = explode(DS,PATH::formatEndPath($leginon_imagepath));
		$session_index = array_search($sessioninfo['Name'],$parts);
		$leginon_index = lastPathMatchIndex($leginon_imagepath,'leginon');
		$appion_index = lastPathMatchIndex($appion_path,$new_base);
		$parent_addition_number = (defined('APPION_PARENT_ADDITION') && APPION_PARENT_ADDITION > 0) ? APPION_PARENT_ADDITION:0;
		if ($session_index !== false) {
			if (defined('APPION_PARENT_REPLACEMENT') && APPION_PARENT_REPLACEMENT < 0) {
				# replace one part into DEFAULT_APPION_PATH
				$replace_part = $parts[$leginon_index+APPION_PARENT_REPLACEMENT];
				$appion_parts = explode(DS,$appion_path);
				array_splice($appion_parts,$appion_index+APPION_PARENT_REPLACEMENT,1,array($replace_part));
				$appion_path = Path::formatEndPath(implode(DS,$appion_parts));
			}
			if ($parent_addition_number > 0) {
				// add extra directory division prior to sessionname
				$addition_parts = array_splice($parts,$session_index-APPION_PARENT_ADDITION,APPION_PARENT_ADDITION);
				$appion_path = Path::formatEndPath(Path::formatEndPath($appion_path).implode(DS,$addition_parts));
			}
		} else {
			// use default alone
			$appion_path = Path::formatEndPath(DEFAULT_APPION_PATH);
		}
		return $appion_path.$sessioninfo['Name'];
	} else {
		// use this in case that the word leginon is used in two parts of the path
		preg_match("%leginon(.*)rawdata%", $leginon_imagepath, $reg_match);
		if (!empty($reg_match)) {
			$path_pieces = explode('leginon',$leginon_imagepath);
			$pieces_count = count($path_pieces);
			// part before appion
			$appion_basepath = implode('leginon',array_slice($path_pieces,0,$pieces_count-1)).$new_base.$path_pieces[$pieces_count-1]; 
			$appion_basepath=preg_replace("%/rawdata%","",$appion_basepath);		
			$appion_basepath=preg_replace("%/".$new_base."\d/%","/".$new_base."/",$appion_basepath);		
		} else {
			$extra="ERROR: could not determine Appion Path directory automatically. Please enter manually";
			echo $extra;
		}
	}
	return $appion_basepath;
}

function lastPathMatchIndex($haypath, $needle) {
	// gives equivalent result of array_search in directory_separated array
	// but search for the last match
	$path_pieces = explode($needle,$haypath);
	$pieces_count = count($path_pieces);
	if ($pieces_count > 1) {
		$last_needle_parts = explode(DS,$path_pieces[$pieces_count-1]);
		$hay_parts = explode(DS,$haypath);
		$last_needle_index = count($hay_parts) - count($last_needle_parts);
		return $last_needle_index;
	} else {
		return false;
	}
}
?>
