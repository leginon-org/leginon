<?php
$paths = array('.', '..', get_include_path());
set_include_path(implode(PATH_SEPARATOR, $paths));
require_once "../config.php";
require_once "inc/leginon.inc";

class Tomography {
	function Tomography($mysql) {
		$this->mysql = $mysql;
		$this->leginon = new leginondata;
	}

	function getTiltSeriesSessions() {
		$query = 'SELECT DISTINCT(s.`DEF_id`) AS `id`, '
			.'s.name AS name, '
			.'s.comment AS comment '
			.'FROM SessionData s '
			.'LEFT JOIN TiltSeriesData t '
			.'ON (s.`DEF_id` = t.`REF|SessionData|Session`) '
			.'WHERE t.`REF|SessionData|Session` <> "NULL" '
			.'AND t.`tilt step` <> "NULL" '
			.'ORDER BY s.DEF_timestamp DESC;';
		return $this->mysql->getSQLResult($query);
	}

	function getTiltSeriesCount($start=NULL, $stop=NULL) {
		$query = 'SELECT UNIX_TIMESTAMP(DATE(DEF_timestamp)) AS time, '
				.'COUNT(*) AS count '
				.'FROM `TiltSeriesData` ';
		if ($start != NULL || $stop != NULL) {
			$query .= 'WHERE DEF_timestamp ';
		}
		if ($start != NULL && $stop != NULL) {
			$query .= "BETWEEN '$start' AND '$stop' ";
		} else if ($start != NULL) {
			$query .= ">= '$start' ";
		} else if ($stop != NULL) {
			$query .= "<= '$stop' ";
		}
		$query .= 'GROUP BY time ORDER BY time';
		return $this->mysql->getSQLResult($query);
	}

	function getTiltSeriesInfo($start=NULL, $stop=NULL) {
		$query = 'SELECT `DEF_id` as id, '
			.'UNIX_TIMESTAMP(DEF_timestamp) as timestamp '
			.'FROM `TiltSeriesData` ';
		if ($start != NULL || $stop != NULL) {
			$query .= 'WHERE UNIX_TIMESTAMP(DEF_timestamp) ';
		}
		if ($start != NULL && $stop != NULL) {
			$query .= "BETWEEN $start AND $stop ";
		} else if ($start != NULL) {
			$query .= ">= $start ";
		} else if ($stop != NULL) {
			$query .= "<= $stop ";
		}
		$query .= 'ORDER BY DEF_timestamp;';
		return $this->mysql->getSQLResult($query);
	}

	function getTiltSeries($sessionId) {
		if($sessionId == NULL)
			return array();

		$query = 'SELECT `DEF_id` as id, '
			.'UNIX_TIMESTAMP(DEF_timestamp) as timestamp, '
			.'`number` '
			.'FROM `TiltSeriesData` '
			."WHERE `REF|SessionData|session`='$sessionId' "
			.'ORDER BY DEF_timestamp;';
		return $this->mysql->getSQLResult($query);
	}

	function getSessionSelector($sessions, $sessionId=NULL) {
		$selector = '<select name="sessionId" onchange=submit()>';
		foreach ($sessions as $session) {
			$selector .= '<option class="fixed" value='.$session['id'];
			if ($session['id'] == $sessionId)
				$selector .= ' selected ';
			$selector .= '>'.$session['name'].' - '.$session['comment'].'</option>';
		}
		$selector .= '</select>';
		return $selector;
	}

	function getTiltSeriesSelector($tiltSeries, $tiltSeriesId=NULL) {
		$selector = '<select name="tiltSeriesId" '
				.'size=32 '
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

	function getPredictionData($tiltSeriesId) {
		$query = "SELECT a.DEF_id AS id, "
			."a.`REF|ScopeEMData|scope` as scope_em_id, "
			."s.`SUBD|stage position|a` as stage_alpha, "
			."p.* "
			."FROM AcquisitionImageData a "
			."LEFT JOIN ScopeEMData s "
			."ON (s.DEF_id = a.`REF|ScopeEMData|scope`) "
			."LEFT JOIN TomographyPredictionData p "
			."ON (a.DEF_id = p.`REF|AcquisitionImageData|image`) "
			."WHERE a.`REF|TiltSeriesData|tilt series`=$tiltSeriesId "
			."AND a.`label` IS NULL "
			."ORDER BY stage_alpha";

		return $this->mysql->getSQLResult($query);
	}

	function sortPredictionData($predictionData) {
		$info = array();
		$count = count($predictionData);
		for ($i = 0; $i < $count; $i++) {
		if (is_array($predictionData[$i]))
			foreach ($predictionData[$i] as $key => $value) {
			$info[$key][$i] = $value;
			}
		}
		return $info;
	}

	function getTiltSeriesSession($tiltSeriesId) {
		if($tiltSeriesId == NULL)
			return array();
		$query = "SELECT s.* FROM TiltSeriesData t "
			."LEFT JOIN SessionData s "
			."ON t.`REF|SessionData|session`=s.DEF_id "
			."WHERE t.DEF_id=$tiltSeriesId "
			."ORDER BY s.DEF_timestamp "
			."ASC LIMIT 1;";
		$result = $this->mysql->getSQLResult($query);
		return $result[0];
	}

	function getTiltSeriesData($tiltSeriesId) {
		if($tiltSeriesId == NULL)
			return array();

		$query = 'SELECT '
			.'a.DEF_id AS id, '
			.'DEGREES(s.`SUBD|stage position|a`) AS alpha, '
			#.'DEGREES(s.`SUBD|stage position|b`) AS beta '
			.'s.`SUBD|stage position|x` AS stage_x, '
			.'s.`SUBD|stage position|y` AS stage_y, '
			.'s.`SUBD|stage position|z` AS stage_z, '
			.'s.`SUBD|image shift|x` AS shift_x, '
			.'s.`SUBD|image shift|y` AS shift_y, '
			.'s.defocus AS defocus, '
			.'s.magnification AS magnification, '
			.'c.`SUBD|dimension|x` AS dimension_x, '
			.'c.`SUBD|dimension|y` AS dimension_y, '
			.'c.`SUBD|binning|x` AS binning_x, '
			.'c.`SUBD|binning|y` AS binning_y, '
			.'c.`exposure time` AS exposure_time, '
			#.'DEGREES(TomographyPredictionData.`SUBD|predicted position|theta`) AS tilt_axis, '
			.'AcquisitionImageStatsData.mean AS mean, '
			.'a.filename, '
			.'a.DEF_id AS imageId, '
			.'p1.pixelsize AS pixel_size '
			.'FROM AcquisitionImageData a '
			.'LEFT JOIN ScopeEMData s '
			.'ON s.DEF_id=a.`REF|ScopeEMData|scope` '
			.'LEFT JOIN CameraEMData c '
			.'ON c.DEF_id=a.`REF|CameraEMData|camera` '
			.'LEFT JOIN TomographyPredictionData '
			.'ON TomographyPredictionData.`REF|AcquisitionImageData|image`=a.DEF_id '
			.'LEFT JOIN AcquisitionImageStatsData '
			.'ON AcquisitionImageStatsData.`REF|AcquisitionImageData|image`=a.DEF_id '
			.'LEFT JOIN PixelSizeCalibrationData p1 '
			.'ON p1.magnification=s.magnification '
			.'AND p1.`REF|InstrumentData|tem`=s.`REF|InstrumentData|tem` '
			.'AND p1.`REF|InstrumentData|ccdcamera`=c.`REF|InstrumentData|ccdcamera` '
			.'AND p1.DEF_timestamp <= a.DEF_timestamp '
			."WHERE a.`REF|TiltSeriesData|tilt series`=$tiltSeriesId "
			."AND a.`label` IS NULL "
			.'AND '
			.'p1.DEF_timestamp=(SELECT MAX(p2.DEF_timestamp) '
			.'FROM PixelSizeCalibrationData p2 '
			.'WHERE p2.DEF_timestamp <= a.DEF_timestamp '
			.'AND p1.magnification=p2.magnification '
			.'AND p1.`REF|InstrumentData|tem`=p2.`REF|InstrumentData|tem` '
			.'AND p1.`REF|InstrumentData|ccdcamera`=p2.`REF|InstrumentData|ccdcamera`) '
			.'ORDER BY s.`SUBD|stage position|a`;';

		return $this->mysql->getSQLResult($query);
	}

	function getImageParent($imgId) {
		$q = "select "  
			."parent.`DEF_id` as parentId, "
			."parent.`MRC|image` as parentimage, "
			."parenttarget.`type` as parenttype, "
			."pp.`name` as parentpreset "
			."from "
			."AcquisitionImageData a "
			."left join PresetData p "
			."on (p.DEF_id=a.`REF|PresetData|preset`) "
			."left join AcquisitionImageTargetData parenttarget "
			."on (parenttarget.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) "
			."left join AcquisitionImageData parent "
			."on (parent.`DEF_id`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join AcquisitionImageTargetData targets "
			."on (targets.`REF|AcquisitionImageData|image`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."where "
			."a.`DEF_id` ='".$imgId."' "; 
		$parents = array();
		$Rparent = $this->mysql->SQLQuery($q);
		while ($parent = mysql_fetch_array($Rparent, MYSQL_ASSOC))
			$parents[]=$parent;
		return $parents;
	}

	function getAtlasName($imageId) {
		$query = 'SELECT '
			.'tlist.`label` AS label '
			.'FROM ImageTargetListData tlist '
			.'LEFT JOIN AcquisitionImageTargetData t '
			.'ON tlist.`DEF_id` = t.`REF|ImageTargetListData|list` '
			.'LEFT JOIN AcquisitionImageData a '
			.'ON t.`DEF_id` = a.`REF|AcquisitionImageTargetData|target` '
			.'WHERE a.`DEF_id`='.$imageId.' '
			.';';
		$results = $this->mysql->getSQLResult($query);
		if ($results)
			return $results[0]['label'];
		}

	function getMeanValues($tilt_series_id) {
		if($tilt_series_id == NULL)
			return array();
	# BUG: for position tilt increment...
		$query = 'SELECT image_data.DEF_id as id, '
			.'stats_data.mean AS mean, '
			.'ROUND(DEGREES(scope_data.`SUBD|stage position|a`), 1) AS alpha '
			.'from AcquisitionImageData image_data '
			.'LEFT JOIN AcquisitionImageStatsData stats_data '
			.'ON stats_data.`REF|AcquisitionImageData|image`=image_data.DEF_id '
			.'LEFT JOIN ScopeEMData scope_data '
			.'ON image_data.`REF|ScopeEMData|scope`=scope_data.DEF_id '
			.'WHERE `REF|TiltSeriesData|tilt series`='.$tilt_series_id.' '
			.' ORDER BY alpha ASC, id DESC;';
		$results = $this->mysql->getSQLResult($query);
		return $results;
	}

	function getTiltSeriesDeletionStatus($tilt_series_id) {
		if($tilt_series_id == NULL)
			return;
		$query = 'SELECT v.status from viewer_del_image v '
			.'LEFT JOIN `AcquisitionImageData` a '
			.'ON v.imageId = a.`DEF_id` '
			.'WHERE a.`REF|TiltSeriesData|tilt series`='.$tilt_series_id.' '
			.'GROUP BY v.`status`;';
		$results = $this->mysql->getSQLResult($query);
		if ($results) 
			return $results[0]['status'];
		return;
	}

	function setTiltSeriesDeletionStatus($tilt_series_id,$status) {
		if($tilt_series_id == NULL)
			return array();
		$query = 'SELECT DEF_id as imageId, `REF|SessionData|session` as sessionId '
			.'from `AcquisitionImageData` '
			.'WHERE `REF|TiltSeriesData|tilt series`='.$tilt_series_id.' '
			.'';
		$results = $this->mysql->getSQLResult($query);
		if ($results) {
			foreach ($results as $r) {
				$this->leginon->setImageDeletionStatus($r['imageId'],$r['sessionId'],
					$status);
			}
		}
		return;
	}

	function getDose($session_id, $preset_name) {
		if($session_id == NULL or $preset_name == NULL)
			return array();
		$query = 'SELECT p.dose/1e20 AS dose, '
			.'p.`exposure time`/1e3 as exposure_time, '
			.'p.DEF_timestamp AS timestamp, '
			.'UNIX_TIMESTAMP(p.DEF_timestamp) AS unix_timestamp '
			.'FROM PresetData p '
			.'WHERE p.name="'.$preset_name.' '
			.'AND `REF|SessionData|session`='.$session_id.' '
			.'ORDER BY timestamp;';
		$results = $this->mysql->getSQLResult($query);
		return $results;
	}

	function getEnergyShift($session_id) {
		if($session_id == NULL)
			return array();
		$query = 'SELECT `before`, `after`, '
			.'DEF_timestamp AS timestamp, '
			.'UNIX_TIMESTAMP(DEF_timestamp) AS unix_timestamp '
			.'FROM InternalEnergyShiftData '
			.'WHERE `REF|SessionData|session`='.$session_id.' '
			.'ORDER BY timestamp;';
		$results = $this->mysql->getSQLResult($query);
		return $results;
	}
}

$mysql = &new mysql($DB_HOST, $DB_USER, $DB_PASS, $DB);
$tomography = new Tomography($mysql);
?>
