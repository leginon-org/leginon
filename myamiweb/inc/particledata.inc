<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once('config.php');
require_once('inc/mysql.inc');

define(PARTICLE_DB_HOST, $PARTICLE_DB_HOST);
define(PARTICLE_DB_USER, $PARTICLE_DB_USER);
define(PARTICLE_DB_PASS, $PARTICLE_DB_PASS);
define(PARTICLE_DB, $PARTICLE_DB);

class particledata {

	var $crlf = "\n";

	function particledata () {
		$this->mysql = new mysql(
					PARTICLE_DB_HOST,
					PARTICLE_DB_USER,
					PARTICLE_DB_PASS,
					PARTICLE_DB);
	}
	
	function getTemplatesFromProject ($projectId) {
		$q="select * "
			."from `ApTemplateImageData` where `project|projects|project`='$projectId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getTemplatesFromId ($templateId) {
		$q = "select * " 
			."from ApTemplateImageData where `DEF_id` = '$templateId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlesFromImageId ($runId, $imageId){
		$q = "select p.DEF_id as id, "
			."p.xcoord, p.ycoord, p.correlation "
			."from ApParticleData p "
			."where p.`REF|ApSelectionRunData|selectionrun` = '$runId' "
			."and p.`dbemdata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getLastAssessmentRun ($sessionId){
		$q = "select max(DEF_id) as runId "
			." from ApAssessmentRunData where `dbemdata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId]; 
	}
	
	function getAssessmentRunIds ($sessionId) {
		$q = "select * "
			."from ApAssessmentRun where `dbemdata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		print_r($r);
		return $r;
	}

	function getKeepStatus ($imageId,$runId){
		// returns a boolean value, 0 if rejected, 1 if keeping,
		// null if no status in database
		$q = "select * "
			."from dbappiondata.ApAssessmentData "
			."where `dbemdata|AcquisitionImageData|image` = '$imageId' "
			."and `REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		return $r['selectionkeep'];
	}

	function updateKeepStatus ($imageId,$runId,$value){
		// update image status : 0 if rejected, 1 if keeping,

		$exists=($this->getKeepStatus($imageId,$runId)) ? true : false;
		if ($exists) {
			$data = array('selectionkeep'=>$value);
			$where = array('dbemdata|AcquisitionImageData|image'=>$imageId);
			$where['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLUpdate('ApAssessmentData',$data,$where); 			
		}
		else {
			$data['selectionkeep']=$value;
			$data['dbemdata|AcquisitionImageData|image']=$imageId;
			$data['REF|ApAssessmentRunData|assessmentrun']=$runId;
			$this->mysql->SQLInsert('ApAssessmentData',$data);
		}
	}
	
	function getAssessmentDataForRun ($runId){
		$q = "select i.filename, a.selectionkeep as keep "
			."from ApAssessmentData a "
			."left join dbemdata.AcquisitionImageData i "
			."on (a.`dbemdata|AcquisitionImageData|image` = i.`DEF_id`) "
			."where a.`REF|ApAssessmentRunData|assessmentrun` = '$runId' ";
		//echo "$q";
		$r=$this->mysql->getSQLResult($q);
		return $r;	
	}

	function getSelectionParams ($runId) {
		$q = "select * from ApSelectionRunData "
			." where `DEF_id` = '$runId' ";
		list($r)=$this->mysql->getSQLResult($q);
		
		//print_r ($r);
		//echo $r['REF|ApSelectionParamsData|params'];
		$q = "select s.*, r.name, r.`dbemdata|SessionData|session` ";
	
		if ($r['REF|ApSelectionParamsData|params']) {
			$selectionparamid=$r['REF|ApSelectionParamsData|params'];
			$q .= "from ApSelectionParamsData s "
			 	."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApSelectionParamsData|params`) ";
		}
		elseif ($r['REF|ApDogParamsData|dogparams']) {
			$dogparamid=$r['REF|ApDogParamsData|dogparams'];
			$q .= "from ApDogParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApDogParamsData|dogparams`) ";
		}
		elseif ($r['REF|ApManualParamsData|manparams']) {
			$manparamid=$r['REF|ApManualParamsData|manparams'];
			$q .= "from ApManualParamsData s "
				."left join ApSelectionRunData r on (s.`DEF_id` = r.`REF|ApManualParamsData|manparams`) ";
		}
		
			$q .= "where r.`DEF_id` = '$runId' ";
		//echo $q;
		$r=$this->mysql->getSQLResult($q);
		//print_r ($r);
		return $r;
	}
	
	function getTemplateRunParams ($runId) {
		$q = "select i.DEF_id as id, i.templatepath as path, i.templatename as tname, i.apix, i.description, "
			."t.range_start, t.range_end, t.range_incr, "
			."r.name "
			."from ApTemplateRunData t "
			."left join ApTemplateImageData i on (t.`REF|ApTemplateImageData|template`=i.`DEF_id`) "
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

	function hasParticleData ($sessionId) {
		$r= ($this->getLastParticleRun($sessionId)) ? true : false;
		return $r;
	}
	
	function getStats ($runId, $inspect=False, $selexval=False){
		$q="select count(p.`DEF_id`) as `totparticles`, "
			."count(distinct p.`dbemdata|AcquisitionImageData|image`) as num, "
			."min(p.correlation) as `min`, "
			."max(p.correlation) as `max`, "
			."avg(p.correlation) as `avg`, "
			."stddev(p.correlation) as `stddev` "
		        ."from ApParticleData p ";
		// use the latest inspection value. This should be changed later 
		if ($inspect) {
		        $q.= "left join ApAssessmentData ad "
				."on (ad.`dbemdata|AcquisitionImageData|image` = p.`dbemdata|AcquisitionImageData|image`) ";
		}
		$q.="WHERE ";
		if ($inspect) {
			$q.= "ad.`DEF_id`=(select max(ad2.`DEF_id`) from ApAssessmentData ad2 where ad2.`dbemdata|AcquisitionImageData|image` = ad.`dbemdata|AcquisitionImageData|image`) "
				."and ad.selectionkeep=1 AND ";
		}
		if ($selexval) $q.="p.`correlation`>='$selexval' AND ";
		$q.="p.`REF|ApSelectionRunData|selectionrun` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
	}
	
	function getNumImgs ($runId){
		$q="SELECT count(distinct `dbemdata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` "
			. "WHERE `REF|ApSelectionRunData|selectionrun`='$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumImgsFromSessionId ($sessionId){
		$q="SELECT count(distinct `dbemdata|AcquisitionImageData|image`) as num "
			. "FROM `ApParticleData` p "
			. "left join `ApSelectionRunData` r on (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id`) "
			. "WHERE r.`dbemdata|SessionData|session`='$sessionId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumAssessedImages ($sessionId) {
		$rid = $this->getLastAssessmentRun($sessionId);
		$q = "select count(DEF_id) as num "
			."from `ApAssessmentData` where "
		        ."`selectionkeep` IS NOT NULL "
 			."and `REF|ApAssessmentRunData|assessmentrun` = '$rid'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}
	
	function getLastParticleRun ($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApSelectionRunData` where `dbemdata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		echo $this->mysql->getError();
		return $r[runId];
	}
	
	function getParticleRunIds ($sessionId) {
		$q = "select * "
			."from `ApSelectionRunData` where `dbemdata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

  function getStackIds ($sessionId) {
    $q = "SELECT r.`REF|ApStackData|stack` as stackid "
        ."FROM ApRunsInStackData as r "
        ."LEFT JOIN ApStackRunData as s ON "
        ."(r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
        ."WHERE s.`dbemdata|SessionData|session` = '$sessionId'"; 
    $r = $this->mysql->getSQLResult($q);
    return $r;
  }
   
  function getNoRefIds ($sessionId) {
    $q = "SELECT r.`REF|ApNoRefRunData|stack` as stackid "
        ."FROM ApRunsInStackData as r "
        ."LEFT JOIN ApStackRunData as s ON "
        ."(r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
        ."WHERE s.`dbemdata|SessionData|session` = '$sessionId'"; 
    $r = $this->mysql->getSQLResult($q);
    return $r;
  }

	function getStackIdsOld ($sessionId) {
	        $q = "select spar.stackid "
				."from ("
				."select `REF|ApParticleData|particle` as pid, `REF|ApStackRunData|stackRun` as stackid "
				."from ApStackParticlesData group by `REF|ApStackRunData|stackRun`) spar "
				."left join ApParticleData p on (p.`DEF_id` = spar.pid) "
				."left join ApSelectionRunData r on  (p.`REF|ApSelectionRunData|selectionrun` = r.`DEF_id` ) "
				."where r.`dbemdata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackParams ($stackId) {
		$q = "SELECT * "
		    ."FROM ApRunsInStackData as r "
		    ."LEFT JOIN ApStackRunData as s "
		    ."ON (r.`REF|ApStackRunData|stackRun`=s.`DEF_id`) "
		    ."LEFT JOIN ApStackData as sd "
		    ."ON (r.`REF|ApStackData|stack`=sd.`DEF_id`) "
		    ."LEFT JOIN `ApStackParamsData` p "
		    ."ON (p.`DEF_id` = s.`REF|ApStackParamsData|stackParams`) "
		    ."WHERE r.`REF|ApStackData|stack` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getNumStackParticles ($stackId) {
		$q= "SELECT count(*) as num "
			."FROM `ApStackParticlesData` "
			."WHERE `REF|ApStackData|stack` = '$stackId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}    

	//////// fix me ////////
  function getStackIdFromReconId ($reconId) {
		$q= "SELECT * "
			."FROM `ApRefinementRunData` "
			."WHERE `DEF_id` = '$reconId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['REF|ApStackData|stack'];
	}    

  function getPixelSizeFromStackId ($stackId) {
	        $q= "SELECT `REF|InstrumentData|tem` t, magnification m, `REF|InstrumentData|ccdcamera` c, a.`DEF_timestamp` time "
                   ."FROM ApStackParticlesData sp "
                   ."left join ApParticleData p on (p.`DEF_id`=sp.`REF|ApParticleData|particle`) "
                   ."left join dbemdata.AcquisitionImageData a on (a.`DEF_id`=p.`dbemdata|AcquisitionImageData|image`) "
                   ."left join dbemdata.PresetData pd on (a.`REF|PresetData|preset`=pd.`DEF_id`) "
                   ."WHERE sp.`REF|ApStackData|stack`='$stackId' "
                   ."GROUP BY `REF|InstrumentData|tem`";
		$r = $this->mysql->getSQLResult($q);
		if (is_array($r[0])) {
		        $tem=$r[0]['t'];
			$mag=$r[0]['m'];
			$ccd=$r[0]['c'];
			$time=$r[0]['time'];
			$q="SELECT pixelsize FROM dbemdata.PixelSizeCalibrationData "
			  ."WHERE `REF|InstrumentData|tem`='$tem' "
			  ."AND `magnification`= '$mag' "
			  ."AND `REF|InstrumentData|ccdcamera`='$ccd' "
			  ."AND `DEF_timestamp`<'$time'";
			$r = $this->mysql->getSQLResult($q);
			return $r[0]['pixelsize'];
		}
		else return;
	}

	function displayParticleStats ($particleruns, $display_keys, $inspect=False, $selexval=False) {
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
			$particlestats = $this->getStats($runId, $inspect, $selexval);
			$html .= "<tr>";
			$numptl=$particlestats['totparticles'];
			$numimg=$particlestats['num'];
			$ppimg = ($numimg > 0) ? (sprintf("%.1f", $numptl/$numimg)) : 0;
			$particlestats['numimgs']=$numimg.'<BR>('.$ppimg.' prtl/img)';
			$particlestats['img'] = '<a href="particlegraph.php?hg=1&run='.$runId.'">'
			        .'<img border="0" '
			        .'src="particlegraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `ApSelectionRunData` where `DEF_id` = $runId";
			$r = $this->mysql->getSQLResult($q);
			$r0 = $r[0];
			$html .= '<td><a href="particlerunreport.php?rId='.$runId.'">'.$r0[name].'</a></td>';
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


#---------RECONSTRUCTION FUNCTIONS---------------#

	function getReconIds ($stackId) {
		$q = "select * "
			."from `ApRefinementRunData` where `REF|ApStackData|stack` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	} 

	function getRefinementRunInfo($refinementRun) {
		$q = "select * "
				."FROM `ApRefinementRunData` WHERE `DEF_id` = '$refinementRun' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getInitModelInfo ($modelId) {
		$q = "SELECT * "
				."FROM `ApInitialModelData` WHERE `DEF_id` = '$modelId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getSymInfo ($symId){
	$q = "SELECT * "
				."FROM `ApSymmetryData` WHERE `DEF_id` = '$symId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getResolutionInfo ($resId) {
		$q = "SELECT * "
			 ."FROM `ApResolutionData` WHERE `DEF_id` = '$resId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getHighestResForRecon ($reconid) {
		$q = "SELECT * " 
			."FROM `ApRefinementData` r "
			."LEFT JOIN `ApResolutionData` res "
			."ON (r.`REF|ApResolutionData|resolution` = res.`DEF_id`) "
			."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconid' "
			."ORDER by res.half ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}
		
	function getIterationInfo ($reconId) {
		$q = "SELECT * "
			."FROM `ApRefinementData` r "
			."LEFT JOIN `ApRefinementParamsData` p "
			."ON (r.`REF|ApRefinementParamsData|refinementParams` = p.`DEF_id`) "
			."WHERE r.`REF|ApRefinementRunData|refinementRun` = '$reconId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getRefinementData ($refinementRun,$iteration) {
		$q = "SELECT DEF_id "
			."FROM `ApRefinementData` "
			."WHERE `REF|ApRefinementRunData|refinementRun` = $refinementRun "
			."AND `iteration` = $iteration";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

	function getNumBadParticles ($refinementDataId) {
		$q = "SELECT count(*) as num "
				."FROM `ApParticleClassificationData` "
				."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
		    ."AND `thrown_out` = 1";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getNumClasses ($refinementDataId) {
		$q = "SELECT count(distinct(`REF|ApEulerData|eulers`)) as num "
				."FROM `ApParticleClassificationData` "
		    ."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getEulerIds ($refinementDataId) {
		$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
				."FROM `ApParticleClassificationData` "
		    ."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticleEuler ($refinementDataId) {
		$q = "SELECT distinct(`REF|ApEulerData|eulers`) as eulers "
			."FROM `ApParticleClassificationData` "
			."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getNumInClass ($refinementDataId,$eulerId) {
		$q = "SELECT count(*) as num "
		  ."FROM `ApParticleClassificationData` "
		  ."WHERE `REF|ApRefinementData|refinement` = '$refinementDataId' "
		  ."AND `REF|ApEulerData|eulers` = $eulerId";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

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
				."euler1.euler1 as euler1_1, "
				."euler1.euler2 as euler1_2, "
				."euler1.euler3 as euler1_3, "
				."euler2.euler1 as euler2_1, "
				."euler2.euler2 as euler2_2, "
				."euler2.euler3 as euler2_3, "
				."cls1.`shiftx` as shiftx1, "
				."cls2.`shiftx` as shiftx2, "
				."cls1.`shifty` as shifty1, "
				."cls2.`shifty` as shifty2, "
				."cls1.`inplane_rotation` as rot1, "
				."cls2.`inplane_rotation` as rot2, "
				."cls1.`quality_factor` as qf1, "
				."cls2.`quality_factor` as qf2 "
				."FROM (`ApParticleClassificationData` as cls1) "
				."LEFT JOIN ( "
				." `ApParticleClassificationData` as cls2, "
				." `ApStackParticlesData` as spd, "
				." `ApEulerData` euler1, `ApEulerData` euler2) "
				."ON ( "
				."cls1.`REF|ApStackParticlesData|particle`=cls2.`REF|ApStackParticlesData|particle` "
				."AND spd.DEF_id=cls1.`REF|ApStackParticlesData|particle` "
				."AND cls1.`thrown_out` is NULL AND cls2.`thrown_out` is NULL "
				."AND euler1.DEF_id=cls1.`REF|ApEulerData|eulers` "
				."AND euler2.DEF_id=cls2.`REF|ApEulerData|eulers` "
				.") "
				."WHERE (cls1.`REF|ApRefinementData|refinement`=$refine1 "
				."AND cls2.`REF|ApRefinementData|refinement`=$refine2 "
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
}
?>
