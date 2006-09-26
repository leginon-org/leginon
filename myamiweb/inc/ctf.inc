<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once('config.php');
require_once('inc/mysql.inc');

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
			."from `run` where `dbemdata|SessionData|session`='$sessionId'";
		list($r) = $this->mysql->getSQLResult($q);
		return $r['DEF_id'];
	}

	function getCtfRunIds($sessionId) {
		$q = "select * "
			."from `run` where `dbemdata|SessionData|session`='$sessionId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

	function getAceParams($runId) {
		$q = "select * "
			."from `ace_params` "
			."where `REF|run|runId` = '$runId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}
	
	function getCtfInfoWithNominal($sessionId, $runId=false) {
		$q =	"select "
			."i.`dbemdata|AcquisitionImageData|image`, "
			."i.`dbemdata|ScopeEMData|defocus`, "
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
			."c.`snr` "
			."from image i left join ctf c "
			."on (c.`REF|image|imageId`=i.`DEF_id`) "
			."where i.`dbemdata|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|run|runId`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ctf c2 where c2.`REF|image|imageId` = c.`REF|image|imageId`)";
		return $this->mysql->getSQLResult($q);
	}

	function getCtfInfo($runId) {
		$q =	"select "
			."i.`dbemdata|AcquisitionImageData|image`, "
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
			."c.`snr` "
			."from ctf c , image i where c.`REF|run|runId`='$runId' and c.`REF|image|imageId`=i.`DEF_id`";
		return $this->mysql->getSQLResult($q);
	}

	function getCtfInfoFromImageId($imageId) {
		$q =	"select "
			."c.`DEF_id`, "
			."i.`dbemdata|AcquisitionImageData|image`, "
			."i.`dbemdata|ScopeEMData|defocus`, "
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
			."c.`snr` "
			."from image i left join ctf c "
			."on (c.`REF|image|imageId`=i.`DEF_id`) "
			."where i.`dbemdata|AcquisitionImageData|image`='$imageId' ";
		return $this->mysql->getSQLResult($q);
	}

	function getCTFBlobs($blobfield, $id) {
		if (!$blobfield || !$id)
			return false;
		$q =	"select "
			."`$blobfield`"
			."FROM ctfblob WHERE DEF_id=$id";
		$blobres = $this->mysql->SQLQuery($q);
		list($blob) = mysql_fetch_row($blobres);
		return $blob;
	}

	function getBlobFields() {
		$blobfield = array();
		$fields = $this->mysql->getFieldTypes('ctfblob');
		foreach ($fields as $field=>$type)
			if (eregi('blob', $type))
				$blobfield[] = $field;
		return $blobfield;
	}


	function getStats($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "i.`dbemdata|AcquisitionImageData|image` as id, i.`dbemdata|ScopeEMData|defocus`, "
					. "count(i.DEF_id) as `nb`, "
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
			."from image i left join ctf c "
			."on (c.`REF|image|imageId`=i.`DEF_id`) "
			."left join dbemdata.`AcquisitionImageData` a "
			."on (a.`DEF_id` = i.`dbemdata|AcquisitionImageData|image`) "
			."left join dbemdata.`PresetData` p "
			."on (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
			."where i.`dbemdata|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|run|runId`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ctf c2 where c2.`REF|image|imageId` = c.`REF|image|imageId`)";
			$q .= "group by p.`name`";
			$r = $this->mysql->getSQLResult($q);
			$stats[$k] = $r;
		}
		return $stats;
	}

	function getData($fields, $sessionId, $runId=false) {
		if (!is_array($fields))
			return False;
		foreach ($fields as $field) {
			$selects[$field] = "i.`dbemdata|AcquisitionImageData|image` as id, i.`dbemdata|ScopEMData|defocus`, "
					. "`$field`";
		}
		if (!is_array($selects))
			return False;
		$stats = array();
		foreach ($selects as $k=>$select) {
			$q =	"select ".$select." "
			."from image i left join ctf c "
			."on (c.`REF|image|imageId`=i.`DEF_id`) "
			."where i.`dbemdata|SessionData|session`='$sessionId' ";
			if ($runId)
				$q .= "and c.`REF|run|runId`='$runId' ";
			else
				$q .= "and c.`DEF_id`=(select max(c2.`DEF_id`) from ctf c2 where c2.`REF|image|imageId` = c.`REF|image|imageId`)";
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
