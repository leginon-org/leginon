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
		$q = "select * "
			."from selectionParams s "
			."where s.`REF|run|runId` = '$runId' ";
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
	
	function getStats ($runId){
		$q="select count(p.DEF_id) as `totparticles`, "
			."min(p.correlation) as `min`, "
			."max(p.correlation) as `max`, "
			."avg(p.correlation) as `avg`, "
			."stddev(p.correlation) as `stddev` "
			."from particle p "
			."where p.`REF|run|runId` = '$runId' ";
		$r = $this->mysql->getSQLResult($q);
		return $r[0];
			
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

	function displayParticleStats($particleruns, $display_keys) {
		if (!is_array($particleruns))
			return ;
		$html = "<BR>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
		$html .= "<tr> <td> </td>\n";
		foreach($display_keys as $key) {
			$html .= "<td> <span class='datafield0'>".$key."</span> </td> ";
		}
		$html .= "</tr>";

		foreach ($particleruns as $particle) {
		        $html .= "<tr>";
			$runId=$particle['DEF_id'];
		        $particlestats=$this->getStats($runId);
		        $particlestats['img'] = '<a href="particlegraph.php?hg=1&run='.$runId.'">'
		                .'<img border="0" '
		                .'src="particlegraph.php?w=150&hg=1&run='
		                .$runId.'"></a>';
			$q = "select name from `run` where `DEF_id` = $runId";
			$r = $this->mysql->getSQLResult($q);
			$r0 = $r[0];
			$html .= "<td> $r0[name] </td>\n";
			foreach($particlestats as $field=>$data) {
			        if (eregi('^min|^max|^avg|^stddev', $field)) {
				        $data=format_sci_number($data,4);
				}
				$html .= "<td> $data </td> \n";
			}
			$html .= "</tr>\n";
		}
		$html .= "</table>\n";
		return $html;
	}

}
?>
