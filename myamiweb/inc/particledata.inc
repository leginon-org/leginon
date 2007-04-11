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

	function particledata() {
		$this->mysql = new mysql(
					PARTICLE_DB_HOST,
					PARTICLE_DB_USER,
					PARTICLE_DB_PASS,
					PARTICLE_DB);
	}
	
	function getTemplatesFromProject($projectId) {
		$q="select * "
			."from `templateImage` where `project|projects|projectId`='$projectId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getTemplatesFromId ($templateId) {
		$q = "select * " 
			."from templateImage where `DEF_id` = '$templateId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getParticlesFromImageId ($runId, $imageId){
		$q = "select p.xcoord, p.ycoord, p.correlation, p.insidecrud "
			."from particle p "
			."left join image i "
			."on (i.`DEF_id` = p.`REF|image|imageId` ) "
			."where p.`REF|run|runId` = '$runId' "
			."and i.`dbemdata|AcquisitionImageData|image` = '$imageId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
        function getKeepStatus($imageId){
	        // returns a boolean value, 0 if rejected, 1 if keeping,
	        // null if no status in database
                $q = "select keep "
		        ."from image "
		        ."where `dbemdata|AcquisitionImageData|image` = '$imageId' ";
		list($r)=$this->mysql->getSQLResult($q);
		return $r['keep'];
	}

        function updateKeepStatus($imageId,$value){
	        // update image status : 0 if rejected, 1 if keeping,
          	$data = array('keep'=>$value);
	        $where = array('dbemdata|AcquisitionImageData|image'=>$imageId);
		$this->mysql->SQLUpdate('image',$data,$where); 
	}

        function getNumAssessedImages($sessionId) {
		$q = "select count(DEF_id) as num "
			."from `image` where "
		        ."`keep` IS NOT NULL "
             	        ."AND `dbemdata|SessionData|session` = '$sessionId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['num'];
	}

	function getSelectionParams($runId) {
		$q = "select s.*, r.name, r.`dbemdata|SessionData|session` "
			."from selectionParams s "
			."left join run r on (s.`REF|run|runId` = r.`DEF_id`) "
			."where s.`REF|run|runId` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getTemplateRunParams($runId) {
		$q = "select i.DEF_id as id, i.templatepath as path, i.apix, i.description, "
			."t.range_start, t.range_end, t.range_incr, "
			."r.name "
			."from templateRun t "
			."left join templateImage i on (t.`REF|templateImage|templateId`=i.`DEF_id`) "
			."left join run r on (t.`REF|run|runId` = r.`DEF_id`) "
			."where t.`REF|run|runId` = '$runId' ";
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}
		
	function getParticles($runId) {
		$q="select p.DEF_id, p.xcoord, p.ycoord, p.correlation, p.insidecrud "
			."from particle p "
			."where p.`REF|run|runId` = '$runId' "; 
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function hasParticleData ($sessionId) {
		$r= ($this->getLastParticleRun($sessionId)) ? true : false;
		return $r;
	}
	
	function getStats ($runId, $inspect=False, $selexval=False){
		$q="select count(p.`DEF_id`) as `totparticles`, "
		        ."count(distinct p.`REF|image|imageId`) as num, "
			."min(p.correlation) as `min`, "
			."max(p.correlation) as `max`, "
			."avg(p.correlation) as `avg`, "
			."stddev(p.correlation) as `stddev` "
		        ."from particle p ";
		if ($inspect) {
		        $q.= "left join image i "
			    ."on (i.`DEF_id` = p.`REF|image|imageId`) ";
		}
		$q.="WHERE ";
		if ($inspect) $q.="i.keep=1 AND ";
		if ($selexval) $q.="p.`correlation`>='$selexval' AND ";
		$q.="p.`REF|run|runId` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
	}
	
        function getNumImgs($runId){
	        $q="SELECT count(distinct `REF|image|imageId`) as num "
		   . "FROM `particle` "
		   . "WHERE `REF|run|runId`='$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

        function getNumInspectedImgs($sessionId){
		$q="select count(*) as `num` "
		        ."FROM image "
		        ."WHERE keep IS NOT NULL AND "
		        ."`dbemdata|SessionData|session`='$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}

	function getLastParticleRun ($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `run` where `dbemdata|SessionData|session` = '$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}
	
	function getParticleRunIds ($sessionId) {
		$q = "select * "
			."from `run` where `dbemdata|SessionData|session` = '$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getStackIds ($sessionId) {
	        $runids=$this->getParticleRunIds($sessionId);
		$stackidlist=array();
		if (!is_array($runids)) return;
		foreach ($runids as $runid) {
		        $run=$runid['DEF_id'];
			$q = "select distinct(`REF|stackParams|stackId`) as stackid "
			    ."from `stackParticles` sp left join particle p on "
			    ."(p.`DEF_id` = sp.`REF|particle|particleId`) "
			    ."WHERE `REF|run|runId` ='$run'";
			$r = $this->mysql->getSQLResult($q);
			if (is_array($r[0]))
			        array_push($stackidlist,$r[0]['stackid']);
		}
		return $stackidlist;
	}

        function getStackParams ($stackId) {
	        $q = "SELECT * "
		    ."FROM `stackParams` "
		  ."WHERE `DEF_id` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

        function getNumStackParticles ($stackId) {
	        $q= "SELECT count(*) as num "
		   ."FROM `stackParticles` "
		   ."WHERE `REF|stackParams|stackId` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['num'];
	}    

        function getStackIdFromReconId ($reconId) {
	        $q= "SELECT * "
		   ."FROM `reconRun` "
		  ."WHERE `DEF_id` = '$reconId'";
		$r = $this->mysql->getSQLResult($q);
	        return $r[0]['REF|stackParams|stackId'];
	}    

        function getPixelSizeFromStackId($stackId) {
	        $q= "SELECT `REF|InstrumentData|tem` t, magnification m, `REF|InstrumentData|ccdcamera` c, a.`DEF_timestamp` time "
                   ."FROM stackParticles sp "
                   ."left join particle p on (p.`DEF_id`=sp.`REF|particle|particleId`) "
                   ."left join image i on (i.`DEF_id`=p.`REF|image|imageId`) "
                   ."left join dbemdata.AcquisitionImageData a on (a.`DEF_id`=i.`dbemdata|AcquisitionImageData|image`) "
                   ."left join dbemdata.PresetData pd on (a.`REF|PresetData|preset`=pd.`DEF_id`) "
                   ."WHERE sp.`REF|stackParams|stackId`='$stackId' "
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
	function displayParticleStats($particleruns, $display_keys, $inspect=False, $selexval=False) {
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
			$ppimg = ($numimg > 0) ? (int)($numptl/$numimg) : 0;
			$particlestats['numimgs']=$numimg.'<BR>('.$ppimg.' prtl/img)';
			$particlestats['img'] = '<a href="particlegraph.php?hg=1&run='.$runId.'">'
			        .'<img border="0" '
			        .'src="particlegraph.php?w=150&hg=1&run='
				.$runId.'"></a>';
			$q = "select name from `run` where `DEF_id` = $runId";
			$r = $this->mysql->getSQLResult($q);
			$r0 = $r[0];
			$html .= '<td><a href="particlerunreport.php?rId='.$runId.'">'.$r0[name].'</a></td>';
			foreach($display_keys as $field) {
			        if (eregi('^min|^max|^avg|^stddev', $particlestats[$field])) $data=format_sci_number($data,4);
				$html .= "<td> $particlestats[$field] </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

#---------RECONSTRUCTION FUNCTIONS---------------#

	function getReconIds ($stackId) {
		$q = "select * "
			."from `reconRun` where `REF|stackParams|stackId` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

        function getInitModelInfo ($modelId) {
	        $q = "SELECT * "
		    ."FROM `initialModel` WHERE `DEF_id` = '$modelId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

        function getSymInfo($symId){
	        $q = "SELECT * "
		    ."FROM `symmetry` WHERE `DEF_id` = '$symId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}

        function getResolutionInfo($resId) {
	        $q = "SELECT * "
		   ."FROM `resolution` WHERE `DEF_id` = '$resId'";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
	}
		
        function getIterationInfo($reconId) {
	        $q = "SELECT * "
		    ."FROM `refinement` r "
		    ."LEFT JOIN `refinementParams` p "
		    ."ON (r.`REF|refinementParams|refinementParamsId` = p.`DEF_id`) "
		    ."WHERE r.`REF|reconRun|reconRunId` = '$reconId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

}
?>
