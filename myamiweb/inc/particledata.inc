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
			."on (i.`dbemdata|AcquisitionImageData|image` = p.`REF|image|imageId` ) "
			."where p.`REF|run|runId` = '$runId' "
			."and i.`dbemdata|AcquisitionImageData|image` = '$imageId' ";
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

	function displayParticleStats($stats, $display_keys, $runId) {
		if (!is_array($stats) || !is_array($display_keys))
			return ;
		$html = "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>";
		$html .= "<tr> <td> </td>";
		foreach($stats as  $field=>$data) {
			$html .= "<td> <span class='datafield0'>".$field."</span> </td> ";
		}
		$html .= "</tr> <tr>";
		$q = "select name from `run` where `DEF_id` = $runId";
		$r = $this->mysql->getSQLResult($q);
		$r0 = $r[0];
		$html .= "<td> $r0[name] </td> ";
		foreach($stats as $field=>$data) {
			$html .= "<td> $data </td> ";
		}
		$html .= "</tr> </table>";
		return $html;
	}

}
?>
