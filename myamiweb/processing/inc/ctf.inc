<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config_processing.php";
require_once "inc/mysql.inc";

define(PROCESSING_DB_HOST, $PROCESSING_DB_HOST);
define(PROCESSING_DB_USER, $PROCESSING_DB_USER);
define(PROCESSING_DB_PASS, $PROCESSING_DB_PASS);
define(PROCESSING_DB, $PROCESSING_DB);

class ctfdata {

	var $crlf = "\n";

	function ctfdata() {
		$this->mysql = new mysql(
					PROCESSING_DB_HOST,
					PROCESSING_DB_USER,
					PROCESSING_DB_PASS,
					PROCESSING_DB);
	}

	function hasCtfData($sessionId) {
		$d = ($this->getLastCtfRun($sessionId)) ? true : false;
		return $d;
	}

	function getLastCtfRun($sessionId) {
		$q = "select max(DEF_id) as runId "
			."from `ApAceRunData` where `dbemdata|SessionData|session`='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r[runId];
	}

	function getCtfRunIds($sessionId) {
		$q = "SELECT * "
			."FROM `ApAceRunData` AS a "
			."WHERE `dbemdata|SessionData|session` = '$sessionId' "
			."ORDER BY a.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getAceParams($runId) {
		$q = "select *, r.`DEF_id` as acerun "
			."from ApAceParamsData p "
			."left join ApAceRunData r on (p.`DEF_id` = r.`REF|ApAceParamsData|aceparams`) "
			."where r.`DEF_id` = '$runId'";
		$r = $this->mysql->getSQLResult($q);
		return end($r);
	}
	
	function getCtfInfoWithNominal($sessionId, $runId=false) {
		$q =	"select "
			."c.`dbemdata|AcquisitionImageData|image`, "
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
			."c.`graph2` "
			."from ApCtfData c left join ApAceRunData r on (c.`REF|ApAceRunData|acerun` = r.`DEF_id`) "
			."left join dbemdata.AcquisitionImageData i on (c.`dbemdata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join dbemdata.ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and r.`DEF_id`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`dbemdata|AcquisitionImageData|image` = c.`dbemdata|AcquisitionImageData|image`)";
		return $this->mysql->getSQLResult($q);
	}

	function getCtfInfo($runId) {
		$q =	"select "
			."c.`dbemdata|AcquisitionImageData|image`, "
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

	function getCtfInfoFromImageId($imageId, $order=false) {
		$q =	"select "
			."c.`DEF_id`, "
			."c.`dbemdata|AcquisitionImageData|image`, "
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
			."p.`path`, "
			."c.`graph1` , "
			."c.`graph2` "
			."from ApCtfData c "
			."left join(ApAceRunData r, ApPathData p) "
			."on ( r.DEF_id=c.`REF|ApAceRunData|acerun` and p.DEF_id=r.`REF|ApPathData|path`) "
			."left join dbemdata.AcquisitionImageData i "
			."on (c.`dbemdata|AcquisitionImageData|image` = i.`DEF_id`) "
			."left join dbemdata.ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."where c.`dbemdata|AcquisitionImageData|image`='$imageId' ";
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
			."		c.`dbemdata|AcquisitionImageData|image`, "
			."		i.`DEF_id`, "
			."		p.`name`, "
			."		s.`defocus`, "
			."		c.`defocus1`, c.`defocus2`, c.`defocusinit`, c.`angle_astigmatism`, "
			."		c.`noise1`, c.`noise2`, c.`noise3`, c.`noise4`, "
			."		c.`envelope1`, c.`envelope2`, c.`envelope3`, c.`envelope4`, c.`lowercutoff`, c.`uppercutoff`, c.`snr`, "
			."		c.`confidence`,c.`confidence_d`  "
			."	from dbappiondata.`ApCtfData` c "
			."	left join dbemdata.`AcquisitionImageData` i on (i.`DEF_id` = c.`dbemdata|AcquisitionImageData|image`) "
			."	left join dbemdata.`PresetData` p on (p.DEF_id = i.`REF|PresetData|preset`) "
			."	left join dbemdata.`ScopeEMData` s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."	where "
			."	c.`dbemdata|AcquisitionImageData|image` in  "
			."	( "
			."		select a.`DEF_id` from dbemdata.`AcquisitionImageData` a  "
			."		where a.`REF|SessionData|session`='$sessionId'  "
			."		)  "
			."		order by (if(confidence_d>confidence, confidence_d, confidence)) desc  "
			."	) ctfdata ";
			// if $limit is specified, report only values with confidences > $limit
			if ($limit) {
				$q .= " where ctfdata.confidence > $limit || ctfdata.confidence_d > $limit ";
			}
			$q .= " group by ctfdata.DEF_id ";
		return $this->mysql->getSQLResult($q);
}

	function getStats($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "c.`dbemdata|AcquisitionImageData|image` as id, s.defocus, "
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
			."from ApCtfData c left join dbemdata.AcquisitionImageData i "
			."on (c.`dbemdata|AcquisitionImageData|image`=i.`DEF_id`) "
			."left join dbemdata.`ScopeEMData` s "
			."on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
			."left join dbemdata.`PresetData` p "
			."on (`p`.`DEF_id`=`i`.`REF|PresetData|preset`) "
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|ApAceRunData|acerun`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`dbemdata|AcquisitionImageData|image` = c.`dbemdata|AcquisitionImageData|image`)";
			$q .= "group by p.`name`";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
	}

	function getBestStats($fields, $sessionId, $limit=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] =  " ctfdata.name , "
					. "count(ctfdata.`$field`) as `nb`, "
					. "min(ctfdata.`$field`) as `min`, "
					. "max(ctfdata.`$field`) as `max`, "
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
				."			c.`dbemdata|AcquisitionImageData|image`, "
				."			c.`DEF_id`, "
				."			p.`name`, "
				."			s.`defocus`, "
				."			c.`defocus1`, c.`defocus2`, c.`defocusinit`, c.`angle_astigmatism`, "
				."			c.`noise1`, c.`noise2`, c.`noise3`, c.`noise4`, "
				."			c.`envelope1`, c.`envelope2`, c.`envelope3`, c.`envelope4`, c.`lowercutoff`, c.`uppercutoff`, c.`snr`, "
				."			c.`confidence`,c.`confidence_d`  "
				."		from dbappiondata.`ApCtfData` c "
				."		left join dbemdata.`AcquisitionImageData` i on (i.DEF_id=c.`dbemdata|AcquisitionImageData|image`) "
				."		left join dbemdata.`PresetData` p on (p.DEF_id=i.`REF|PresetData|preset`) "
				."		left join dbemdata.ScopeEMData s on (i.`REF|ScopeEMData|scope` = s.`DEF_id`) "
				."		where "
				."		c.`dbemdata|AcquisitionImageData|image` in  "
				."		( "
				."			select a.`DEF_id` from dbemdata.`AcquisitionImageData` a  "
				."			where a.`REF|SessionData|session`='$sessionId'  "
				."			)  "
				."			order by (if(confidence_d>confidence, confidence_d, confidence)) desc  "
				."		) allctfdata "
				."	group by allctfdata.`dbemdata|AcquisitionImageData|image` "
				."	) ctfdata ";
				// if $limit is specified, report only values with confidences > $limit
				if ($limit){
					$q .= " where sqrt(ctfdata.confidence * ctfdata.confidence_d) > $limit ";
				}
				$q .= " group by ctfdata.name ";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
}

	function getData($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "c.`dbemdata|AcquisitionImageData|image` as id, s.`defocus`, "
					. "`$field`";
		}
		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
			$q =	"select ".$select." "
			."from ctf c left join dbemdata.AcquisitionImageData i"
			."on (c.`dbemdata|AcquisitionImageData|image`=i.`DEF_id`) "
			."left join dbemdata.ScopeEMData s on (s.`DEF_id` = i.`REF|ScopeEMData|scope`) " 
			."where i.`REF|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|ApAceRunData|acerun`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ApCtfData c2 where c2.`dbemdata|AcquisitionImageData|image` = c.`dbemdata|AcquisitionImageData|image`)";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
	}

}

function display_stats($stats, $display_keys) {
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
					if (eregi('defocus', $field)) {
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

function display_data($data, $display_keys) {
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
