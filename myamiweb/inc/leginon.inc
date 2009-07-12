<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement see
 *	@licence http://ami.scripps.edu/software/leginon-license
 *	@version $Revision: 1.84 $
 *	@version $Id: leginon.inc,v 1.84 2008-02-05 18:16:12 dfellman Exp $
 */
/**
 *	Query definition to access all leginon data 
 *	
 */

$paths = array( get_include_path(), './processing');
set_include_path(implode(PATH_SEPARATOR, $paths));
require_once "config.php";
require_once "inc/util.inc";
require_once "inc/xmlapplicationimport.inc";
require_once "inc/mysql.inc";

define('DB_HOST', $DB_HOST);
define('DB_USER', $DB_USER);
define('DB_PASS', $DB_PASS);
define('DB', $DB);

class leginondata {

	var $crlf = "\n";
	var $ffttypes = array('focpow', 'fft');
	var $defaulttypes = array('all', 'atlas', 'exemplar', 'hidden');
	var $manualtype = 'manual';
	var $rcttype = 'rct';
	var $calibrationtables = array (
		'CameraSensitivityCalibrationData',
		'MatrixCalibrationData',
		'PixelSizeCalibrationData',
		'StageModelCalibrationData',
		'StageModelMagCalibrationData',
		'EucentricFocusData'
	);
	var $applicationtables = array (
		'ApplicationData',
		'BindingSpecData',
		'NodeSpecData'
	);

	function leginondata() {
		$this->mysql = &new mysql(DB_HOST, DB_USER, DB_PASS, DB);
		if ($this->mysql->checkDBConnection())
			$this->viewer_tables();
	}

	function viewer_tables() {
		$comment_tbl_name = 'viewer_comment';
		$comment_tbl_def  = ''
		.'CREATE TABLE `'.$comment_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`timestamp` timestamp(14) NOT NULL,'
		.'`sessionId` int(11) NOT NULL default "0",'
		.'`type` enum(\'rt\',\'post\') NOT NULL default \'rt\','
		.'`imageId` int(11) NOT NULL default "0",'
		.'`name` text NOT NULL,'
		.'`comment` text NOT NULL,'
		.'PRIMARY KEY  (`id`),'
		.'KEY `timestamp` (`timestamp`),'
		.'KEY `sessionId` (`sessionId`),'
		.'KEY `imageId` (`imageId`)'
		.');';
		if (!$this->mysql->SQLTableExists($comment_tbl_name)) 
			$this->mysql->SQLquery($comment_tbl_def);
		$update_tbl_name = 'viewer_update';
		$update_tbl_def  = ''
		.'CREATE TABLE `'.$update_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`timestamp` timestamp(14) NOT NULL,'
		.'`status` enum(\'N\',\'Y\') NOT NULL default \'N\','
		.'`name` text NOT NULL,'
		.'`update` text NOT NULL,'
		.'PRIMARY KEY  (`id`),'
		.'KEY `timestamp` (`timestamp`)'
		.');';
		$update_tbl_name = 'viewer_update';
		if (!$this->mysql->SQLTableExists($update_tbl_name)) 
			$this->mysql->SQLquery($update_tbl_def);
		$login_tbl_name = 'viewer_login';
		$login_tbl_def  = ''
		.'CREATE TABLE `'.$login_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`username` varchar(50),'
		.'`password` varchar(50),'
		.'`privilege` tinyint(4),'
		.'PRIMARY KEY  (`id`),'
		.'KEY `login` (`username`)'
		.');';
		if (!$this->mysql->SQLTableExists($login_tbl_name)) 
			$this->mysql->SQLquery($login_tbl_def);
		$user_tbl_name = 'viewer_users';
		$user_tbl_def  = ''
		.'CREATE TABLE `'.$user_tbl_name.'` ('
		.'`userid` int(11) NOT NULL auto_increment,'
		.'`login` varchar(50),'
		.'`firstname` text,'
		.'`lasttname` text,'
		.'`title` text,'
		.'`institute` text,'
		.'`dept` text,'
		.'`address` text,'
		.'`city` text,'
		.'`statecountry` text,'
		.'`zip` text,'
		.'`phone` text,'
		.'`fax` text,'
		.'`email` text,'
		.'`url` text,'
		.'PRIMARY KEY  (`userid`),'
		.'KEY `login` (`login`)'
		.');';
		if (!$this->mysql->SQLTableExists($user_tbl_name)) {
			$this->mysql->SQLquery($user_tbl_def);
		}
		$image_status_tbl_name = 'viewer_pref_image';
		$image_status_tbl_def  = ''
		.'CREATE TABLE `'.$image_status_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`timestamp` timestamp(14) NOT NULL,'
		.'`username` varchar(50),'
		.'`sessionId` int(11),'
		.'`imageId` int(11),'
		.'`status` enum(\'hidden\',\'visible\',\'exemplar\'),'
		.'PRIMARY KEY  (`id`),'
		.'KEY `timestamp` (`timestamp`),'
		.'KEY `userId` (`username`),'
		.'KEY `sessionId` (`sessionId`),'
		.'KEY `imageId` (`imageId`),'
		.'KEY `status` (`status`)'
		.');';
		if (!$this->mysql->SQLTableExists($image_status_tbl_name)) {
			$this->mysql->SQLquery($image_status_tbl_def);
		}
		$image_del_tbl_name = 'viewer_del_image';
		$image_del_tbl_def  = ''
		.'CREATE TABLE `'.$image_del_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`timestamp` timestamp(14) NOT NULL,'
		.'`username` varchar(50),'
		.'`sessionId` int(11),'
		.'`imageId` int(11),'
		.'`status` enum(\'deleted\',\'marked\'),'
		.'PRIMARY KEY  (`id`),'
		.'KEY `timestamp` (`timestamp`),'
		.'KEY `userId` (`username`),'
		.'KEY `sessionId` (`sessionId`),'
		.'KEY `imageId` (`imageId`),'
		.'KEY `status` (`status`)'
		.');';
		if (!$this->mysql->SQLTableExists($image_del_tbl_name)) {
			$this->mysql->SQLquery($image_del_tbl_def);
		}
	}

	function query($q) {
		return $this->mysql->SQLQuery($q);
	}

	function getSQLResult($q) {
		return $this->mysql->getSQLResult($q);
	}
	

	function getTotalImgs() {
		$q = "SELECT COUNT(DISTINCT `DEF_id`) as i "
		  ."FROM `AcquisitionImageData`";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['i'];
	}

	function getTotalSessions() {
		$q = "SELECT COUNT(DISTINCT `DEF_id`) as i "
		  ."FROM `SessionData`";
		$r = $this->mysql->getSQLResult($q);
		return $r[0]['i'];
	}

	function getLastSessionId() {
		$q = "select distinct(s.DEF_id) from AcquisitionImageData a "
			."left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) "
			."order by s.DEF_timestamp DESC limit 1";
		$RlastId = $this->mysql->SQLQuery($q) or die ("No session found");
		$lastId=mysql_fetch_array($RlastId);
		$expId=$lastId[0];
		return $expId;
	}

	function sessionIdExists($sessions, $sessionId) {
		$sessionId_exists=false;
		foreach ($sessions as $session)
		if (in_array($sessionId, $session)) {
			$sessionId_exists=true;
				break;
		}
		return $sessionId_exists;
	}

	function getSessions($comment="", $projectId=false, $like="") {
		if ($like)
			$wherelike = "and s.`Name` like '$like' ";
		$selectcomment = ($comment) ? 
				"if (length(s.comment)>0, concat(s.name,' - ',s.comment), s.name)" : "s.name";
		if (is_numeric($projectId)) {
			// --- project database information
			$project = &new project;
			$db  = &$project->mysql;
			$q = "select p.name from ".PROJECT_DB.".projectexperiments p where p.projectId='$projectId'";
			$psessions = $db->getSQLResult($q);
			$ps=array();
			foreach ($psessions as $psession) {
				$ps[$psession['name']] = $psession['name'];
			}
			$sessions = $this->getSessions($comment, false, $like);
			if (!$sessions) return array();
			foreach ($sessions as $session) {
				$s[$session['name_org']] = $session;
			}
			// --- get common sessions 
			$i = array_intersect(array_keys($s), array_keys($ps));
			$ps = array();
			foreach ($i as $d) {
				$ps[] = $s[$d]; 
			}
			return $ps;

		}

		$q="select s.DEF_id as `id`, ".$selectcomment." as `name`, s.Name as `name_org` "
		."from AcquisitionImageData a "
		."left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) "
		."where a.`REF|SessionData|Session` IS NOT NULL "
		.$wherelike
		."group by a.`REF|SessionData|Session` "
		."order by s.DEF_timestamp DESC ";

		return $this->mysql->getSQLResult($q);
	}

	function getSessionInfo($name) {

		if (!is_array($name)) {
			$name = array($name);
		}
		foreach ($name as $n) {
			if (is_numeric($n))
				$ids[] = "s.`DEF_id`='$n'";
			else
				$ids[] = "s.`Name` like '$n'";
		}
		$sqlwhere = "where (".join(" OR ", $ids).")";

		$q="select "
		."s.`DEF_id` as SessionId, "
		."s.Name, "
		."s.comment as Purpose, "
		."unix_timestamp(s.`DEF_timestamp`) as `Begin unixTimestamp`,"
		."unix_timestamp(a.`DEF_timestamp`) as `End unixTimestamp`, "
		."date_format(s.`DEF_timestamp`, '%Y-%d-%m %T') as `Begin Time`,"
		."date_format(a.`DEF_timestamp`, '%Y-%d-%m %T') as `End Time`, "
		."sec_to_time((Dayofyear(a.`DEF_timestamp`)-Dayofyear(s.`DEF_timestamp`))*86400-"
		."time_to_sec(s.`DEF_timestamp`)+time_to_sec(a.`DEF_timestamp`)) as `Total Duration`, "
		."s.`Image path`, "
		."concat(i.name,' - ',ic.name) as Instrument, "
		."i.hostname as `Instrument Host`, "
		."sc.`REF|InstrumentData|tem`  as `InstrumentId`, "
		."c.`REF|InstrumentData|ccdcamera`  as `CameraId`, "
		."u.`DEF_id` as userId, "
		."u.`full name` as User "
		."from `SessionData` s "
		."left join UserData u on (u.`DEF_id`=s.`REF|UserData|user`) "
		."left join AcquisitionImageData a on (a.`REF|SessionData|session`=s.`DEF_id`) "
		."left join ScopeEMData sc on (sc.`DEF_id`=a.`REF|ScopeEMData|scope`)"
		."left join CameraEMData c on (c.`DEF_id`=a.`REF|CameraEMData|camera`)"
		."left join InstrumentData i on (i.`DEF_id`=sc.`REF|InstrumentData|tem`)"
		."left join InstrumentData ic on (ic.`DEF_id`=c.`REF|InstrumentData|ccdcamera`)"
		.$sqlwhere 
		."order by a.`DEF_timestamp` DESC limit 1";
		$sessioninfo = $this->mysql->getSQLResult($q);
		return $sessioninfo[0];
	}

	function getInstrumentInfo($id) {
		return $this->getDataInfo('InstrumentData', $id);
	}

	function getInstruments() {
		return $this->getAll('InstrumentData');
	}

	function getInstrumentHosts() {
		$hosts = array();
		$instruments = $this->getInstruments();
		if ($instruments)
		foreach ($instruments as $instrument) {
			$hosts[] = $instrument['hostname'];
		}
		return array_unique($hosts);
	}

	function getCameras($hostname) {
		$q="select `DEF_id` as id, name from `InstrumentData` "
			." where (type='CCDCamera' or name='SimCCDCamera') and hostname='$hostname'";
		return $this->mysql->getSQLResult($q);
	}

	function getScopes($hostname) {
		$q="select `DEF_id` as id, name from `InstrumentData` "
			." where (type='TEM' or name='SimTEM') and hostname='$hostname'";
		return $this->mysql->getSQLResult($q);
	}

	function getSummary($expId, $presetname=False) {
	/*
		$q="select if (isnull(p.name), '"
			.$this->manualtype."', p.name) as name, count(a.`DEF_id`) as nb from AcquisitionImageData a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			." where a.`REF|SessionData|session` = '$expId' "
			." group by p.name ";
	*/
		$q="SELECT p.name, count(a.`DEF_id`) as nb, p.magnification "
		  ." FROM AcquisitionImageData a "
		  ." LEFT JOIN PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
		  ." WHERE a.`REF|SessionData|session` = '$expId' ";
		if ($presetname) $q .= "AND p.name = '$presetname' ";
		$q.=" GROUP BY p.name "
		  ." ORDER BY p.magnification ";
		return $this->mysql->getSQLResult($q);
	}

	function getUsers() {
		return $this->getAll('UserData');
	}

	function addUser($data) {
	}

	function getGroups() {
		return $this->getAll('GroupData');
	}

	function getComments($sessionId, $type='rt') {
		$q="select "
			."date_format(c.`timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."c.name, c.comment "
			."from `viewer_comment` c " 
			."where `sessionId` = '$sessionId' and `type` = '$type' "
			." ";
		return $this->mysql->getSQLResult($q);
	}

	function getImageComment($imageId, $type='rt') {
		$q="select "
			."comment "
			."from `ImageCommentData` " 
			."where `REF|AcquisitionImageData|image` = '$imageId' "
			." ";
		$result = $this->mysql->getSQLResult($q);
		if ($result) return $result[0][comment];
	}

	function getDatalabels($sessionId) {
		$q="select distinct label FROM AcquisitionImageData a "
			." where a.`REF|SessionData|session` = '$sessionId'";
		return $this->mysql->getSQLResult($q);
	}

	function getDatatypes($sessionId, $allpresets=true) {
		$q="select distinct name FROM AcquisitionImageData a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			." where a.`REF|SessionData|session` = '$sessionId'";
		$Rdatatypes = $this->mysql->getSQLResult($q);
		foreach ($Rdatatypes as $d) {
			if ($d['name'])
				$datatypes[]=$d['name'];
		}
		if ($allpresets)
			$datatypes[]=$this->manualtype; 
		return $datatypes;
	}

	function getTruePresets($sessionId) {
		return $this->getDatatypes($sessionId, false); 
	}

	function getAllDatatypes($sessionId) {
		$defaulttypes = $this->defaulttypes;
		$types = $this->getDatatypes($sessionId);
		return array_merge($defaulttypes, $types);
	}

	function getImageStat($name) {
		if (!$name)
			return false;
		$sqljoin = "LEFT JOIN `AcquisitionImageData` AS `a` "
				."ON (`a`.`DEF_id`=`s`.`REF|AcquisitionImageData|image`) ";
		$sqlwhere = "a.`MRC|image`='$name' ";
		if (is_numeric($name)) {
			$sqljoin = "";
			$sqlwhere = "s.`REF|AcquisitionImageData|image`='$name' " ;
		}
		$q="SELECT "
		."`s`.`min`, `s`.`max`, `s`.`stdev`, `s`.`mean` "
		."FROM "
		."`AcquisitionImageStatsData` AS `s` "
		.$sqljoin
		."WHERE "
		.$sqlwhere;
		return $this->mysql->getSQLResult($q);
	}

	function getFilenames($sessionId, $name="", $table="AcquisitionImageData") {
		$has_ImageStatusData = $this->mysql->isTable('ImageStatusData'); 
		$sessionwhere = "a.`REF|SessionData|session`='$sessionId' ";
		if (!is_numeric($sessionId)) {
			$sessionwhere = "s.`Name` like '$sessionId' ";
			$sessionjoin = "left join SessionData s on (s.`DEF_id`=a.`REF|SessionData|session`) ";
		}
		if (in_array($name, $this->defaulttypes)) {
			$defaultname=$name;
			$name="";
		}
			$hiddenjoin = "left join `viewer_pref_image` r on (r.imageId=a.DEF_id) ";
			if ($has_ImageStatus)
				$hiddenjoin .= "left join `ImageStatusData` ir on (ir.`REF|AcquisitionImageData|image`=a.DEF_id) ";
		if ($defaultname=="hidden" || $defaultname=="exemplar") {
			$hiddenwhere = "and  ((r.id is not null and r.status='$defaultname') ";
			if ($has_ImageStatus)
				$hiddenwhere .= "or  (ir.`DEF_id` is not null and ir.status='$defaultname')";
			$hiddenwhere .=")";
		} else {
			$hiddenwhere = "and ((r.id is NULL or r.status <>'hidden') ";
			if ($has_ImageStatus)
				$hiddenwhere .= "and (ir.`DEF_id` is NULL or ir.status <>'hidden')";
			$hiddenwhere .=") ";
		}
		if (in_array($name, $this->ffttypes)) {
		$q = "select a.`DEF_id` as `id`, f.`MRC|Image` as `name` "
				." from `$table` a "
				." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
				." left join AcquisitionFFTData f on (f.`REF|AcquisitionImageData|source`=a.`DEF_id`) "
				.$sessionjoin
				.$hiddenjoin
				." where "
				.$sessionwhere 
				." and f.`MRC|Image`<>'NULL' "
				.$hiddenwhere
		    ." order by a.`DEF_id` DESC ";
		} else {
		$q = "select a.`DEF_id` as `id`, a.`MRC|Image` as `name` "
			." from `$table` a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			.$sessionjoin
			.$hiddenjoin
			." where "
			.$sessionwhere
			.$hiddenwhere;

			if ($name) {
				if ($name == $this->manualtype)
					$q .=" and p.name is null ";
				else
					$q .=" and p.name = '$name' ";
			}
		    $q .=" order by a.`DEF_id` DESC ";
		}

		$filenames = array();
		$Rfile=$this->mysql->SQLQuery($q);
		while ($filename = mysql_fetch_array($Rfile, MYSQL_ASSOC))
			$filenames[] = $filename;

		return $filenames;
	}

	function getPresetFromSessionId($sessionId, $preset) {
		$q="SELECT "
		."`p`.`DEF_id`, `p`.`DEF_timestamp`, "
		."`p`.`name`, `p`.`magnification`, `p`.`spot size`, `p`.`intensity`, "
		."`p`.`SUBD|image shift|x`, `p`.`SUBD|image shift|y`, "
		."`p`.`SUBD|beam shift|x`, `p`.`SUBD|beam shift|y`, "
		."`p`.`defocus`, "
		."`p`.`defocus range min`, `p`.`defocus range max` "
		."FROM `PresetData` p "
		."WHERE "
		."`p`.`REF|SessionData|session`=".$sessionId 
		." and `p`.`name`='".$preset."' ";

		return $this->mysql->getSQLResult($q);
	}

	function getPresets($fileId, $presets=array('mag','defocus','pixelsize','dose')) {
				$sqljoin=array();
		if (!$presetfields = $this->mysql->getFields('PresetData'))
			return array();
		if (!is_array($presets) || !$fileId)
			return false;
		if (in_array('tilt', $presets))
			$sqlselect[]="DEGREES(scope.`SUBD|stage position|a`) AS tilt";
		if (in_array('mag', $presets))
			$sqlselect[]="scope.magnification as mag";
		if (in_array('defocus', $presets)) {
			$emtargetId= $this->getId(
					array('DEF_id' => $fileId),
					'AcquisitionImageData',
					'REF|EMTargetData|emtarget'
					);
			if ($emtargetId) {
				$sqlselect[]="scope.defocus-em.`delta z` as `defocus`";
				$sqljoin[]="left join `EMTargetData` em "
				."on (em.`DEF_id` =  a.`REF|EMTargetData|emtarget`)";
			} else {
				$sqlselect[]="scope.defocus";
			}
		}
		if (in_array('pixelsize', $presets))
			$sqlselect[]="pi.pixelsize";
		if (in_array('dose', $presets) && in_array('dose', $presetfields))
			$sqlselect[]="p.dose";
		if (in_array('exposure time', $presets) && in_array('exposure time', $presetfields))
			$sqlselect[]="p.`exposure time`";
		$sqlselectstr=implode(', ',$sqlselect);
		$sqljoinstr=implode(', ',$sqljoin);
		$q='
		select '.$sqlselectstr.'
		from (AcquisitionImageData a , PixelSizeCalibrationData pi)
			left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) 
			left join CameraEMData c on (a.`REF|CameraEMData|camera`=c.`DEF_id`)
		'
		.' left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) '
		.$sqljoinstr
		.' where (scope.`REF|InstrumentData|tem`=pi.`REF|InstrumentData|tem`
				and scope.magnification = pi.magnification 
				and c.`REF|InstrumentData|ccdcamera`=pi.`REF|InstrumentData|ccdcamera`
				and pi.`DEF_timestamp`  < a.`DEF_timestamp` )
				and a.`DEF_id` = '.$fileId.'
		order by pi.`DEF_timestamp` desc limit 1
		';
		list($preset)=$this->mysql->getSQLResult($q);
		return $preset;
	}

	function getPresetFromImageId($imageId) {
		$q	="SELECT "
			."`p`.`DEF_id`, `p`.`DEF_timestamp`, `s`.`DEF_id` as sessionId, `s`.`name` as session, "
			."`p`.`name`, `p`.`magnification`, `p`.`spot size`, `p`.`intensity`, "
			."`p`.`SUBD|image shift|x`, `p`.`SUBD|image shift|y`, `p`.`SUBD|beam shift|x`, "
			."`p`.`SUBD|beam shift|y`, `p`.`defocus`, `p`.`SUBD|dimension|x`, "
			."`p`.`SUBD|dimension|y`, `p`.`SUBD|binning|x`, `p`.`SUBD|binning|y`, "
			."`p`.`SUBD|offset|x`, `p`.`SUBD|offset|y`, `p`.`exposure time`, "
			."`p`.`removed`, `p`.`hasref`, `p`.`dose`, `p`.`number`, "
			."`p`.`film`, `p`.`REF|InstrumentData|tem`, `p`.`REF|InstrumentData|ccdcamera` "
			."FROM "
			."`AcquisitionImageData` AS `a` "
			."LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
			."LEFT JOIN `SessionData` AS `s` ON (`s`.`DEF_id`=`a`.`REF|SessionData|session`) "
			."WHERE `a`.`DEF_id` = '$imageId' ";
		list($r) = $this->mysql->getSQLResult($q);
		return $r;
	}


	function getLastFilenameId($sessionId) {
		$q = "select `DEF_id` as `id` from AcquisitionImageData "
			." where `REF|SessionData|session`='$sessionId' "
			." order by `DEF_timestamp` desc limit 1 ";
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo['id'];
	} 

	function getImagePath($sessionId) {
		$q = "select `image path` as path from `SessionData` "
		    ." where `DEF_id`='$sessionId' ";
		$Rpath=$this->mysql->SQLQuery($q);
		$path = mysql_fetch_array($Rpath);
		return formatPath($path['path']);
	}

	function getImagePathFromImageId($imageId) {
		$q = "select `REF|SessionData|session` as sessionId from AcquisitionImageData "
			."where `DEF_id`=$imageId";
		list($r) = $this->mysql->getSQLResult($q);
		return $this->getImagePath($r['sessionId']);
	}

	function getPolarTransformInfo($imageId) {
	}

	function getLogPolarTransformImageRef($imageId) {
		$q="SELECT "
		."`a`.`DEF_id`, `a`.`filename`, `g`.`grid ID`, `g`.`insertion`, `t`.`number` "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `GridData` AS `g` ON (`g`.`DEF_id`=`a`.`REF|GridData|grid`) "
		."LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."LEFT JOIN `AcquisitionImageTargetData` AS `t` ON "
		."(`t`.`DEF_id`=`a`.`REF|AcquisitionImageTargetData|target`) "
		."WHERE `a`.`DEF_id`=".$imageId;
		list($r) = $this->mysql->getSQLResult($q);
		$gridId = $r['grid ID'];
		$insertion = $r['insertion'];
		
		$q="SELECT "
		."`a`.`DEF_id` as `id`, `a`.`filename`, `g`.`grid ID`, `g`.`insertion`, `t`.`number` "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `GridData` AS `g` ON (`g`.`DEF_id`=`a`.`REF|GridData|grid`) "
		."LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."LEFT JOIN `AcquisitionImageTargetData` AS `t` ON "
		."(`t`.`DEF_id`=`a`.`REF|AcquisitionImageTargetData|target`) "
		."WHERE `g`.`grid ID`=".$gridId." AND "
		."`t`.`number`=0 AND "
		."`g`.`insertion`>$insertion";
		list($r) = $this->mysql->getSQLResult($q);
		$id = $r[id];
		return $id;
	}

	function findField($name) {
	    $result = $this->mysql->SQLQuery("SHOW TABLES");
	    while($row = mysql_fetch_row($result))
		$tables[] = $row[0];
	}

	function getId($where_fields=array(), $table = "AcquisitionImageData", $id="DEF_id") {
		// --- return id from specified table. $where_fields is an array
		// containing the "where" condition:
		//	field1=>value1, field12=>value2, ...
		$parameters['table']=$table;
		$parameters['where']=$where_fields;
		$parameters['id']=$id;
		return $this->mysql->getId($parameters);
	}

	function getAll($table) {
		$q = "select * from `$table`";
		return $this->mysql->getSQLResult($q);
	}

	function getDataInfo($table, $id, $fields=array()) {
		if (!$table)
			return false;
		$data = array();
		$formated_fields = array();
		$acq_fields = $this->mysql->getFields($table); 
		foreach ($acq_fields as $f) {
			if (is_array($fields) && !empty($fields)) { 	
				if (!in_array($f, $fields))
					continue;
			}
			$f = ($f=='DEF_timestamp') ?  "UNIX_TIMESTAMP(`$f`) as `date`" : "`$f`";
			$formated_fields[] = $f;
		}
		$str_fields = implode(', ', $formated_fields);
		$q = 'select '.$str_fields.' from `'.$table.'`'
			.' where `DEF_id`="'.$id.'"';
		$R = $this->mysql->SQLQuery($q);
		while ($r = mysql_fetch_array($R, MYSQL_ASSOC))
			$data[] = $r;
		return $data;
	}

	function getImageAtlas($sessionId) {
		$q = "select `MRC|image` as filename from `MosaicImageData` where "
		    ." `REF|SessionData|Session` =\"$sessionId\"  ";
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo['filename'];
	}

	function getImageList($id) {
		$q="SELECT "
		."`a`.`REF|ImageListData|list` as `list`"
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."WHERE `a`.`DEF_id`=$id";
		list($R) = $this->mysql->getSQLResult($q);
		
		$q="SELECT "
		."`a`.`DEF_id` as `id` "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."WHERE `a`.`REF|ImageListData|list`=".$R['list'];
		$r = $this->mysql->getSQLResult($q);
		$l=array();
		if (is_array($r))
		foreach($r as $ids) {
			$l[] = $ids['id'];
		}
		return $l;

	}

	function getMosaicImages($id) {
		$listId = $this->getId(
				array('REF|AcquisitionImageData|image' => $id),
				'MosaicTileData',
				'REF|ImageListData|list'
				);
		$r= $this->getId(
				array( 'REF|ImageListData|list'  => $listId),
				'MosaicTileData',
				'REF|AcquisitionImageData|image'
				);
		return $r;
	}

	function getRCTfilename($imageId) {
		// --- return RCT filename for a given imageId
		// --- return empty string for no match
		$q="SELECT "
			."a2.DEF_id, a2.`MRC|image` AS filename "
			."FROM AcquisitionImageData AS a1 "
			."LEFT JOIN AcquisitionImageData AS a2 "
			."ON (a1.`REF|TiltSeriesData|tilt series`=a2.`REF|TiltSeriesData|tilt series` "
			."AND a1.DEF_id<>a2.DEF_id) "
			."LEFT JOIN  PresetData AS p1 "
			."ON (a1.`REF|PresetData|preset`=p1.`DEF_id`) "
			."LEFT JOIN  PresetData AS p2 "
			."ON (a2.`REF|PresetData|preset`=p2.`DEF_id`) "
			."WHERE a1.DEF_id=$imageId "
			."AND p1.`name`=p2.`name` ";
		list($r)=$this->mysql->getSQLResult($q);
		if ($r['filename']) {
			return $r['filename'];
		}
		// --- FOR OLDER RCT RUN --- //
		$info=$this->getImageInfo($imageId);
		$name = $info['filename'];
		$p=$info['preset'];
		$pp=$info['parentpreset'];

		// --- change pattern based on parent's preset
		$pattern = ($pp) ? '/'.$pp.'_(\d+)_(.*)'.$p.'_(\d+)/' :
											'/'.$p.'_(\d+)/';
		if (!preg_match($pattern, $name, $result)) {
			// ---try new
			return $this->getRCTfilename_new($imageId);
		}
		$split='/'.$result[0].'/';
		$replacement = ($pp) ? $pp.'_'
									.sprintf("%02d", $result[1]+1)
									.'_'.$result[2]
									.$p.'_'
									.sprintf("%02d", $result[3]+1) : 
									$p.'_'.sprintf("%02d", $result[1]+1);

		$rctfilename=preg_replace($split, $replacement, $name);
		return $rctfilename;
	}

	function getRCTfilename_new($id) {
		$info=$this->getImageInfo($id);
		$name = $info['filename'];
		$p=$info['preset'];
		$pp=$info['parentpreset'];

		if ($pp) {
			$pattern = '/'.$pp.'_v(\d+)_(.*)'.$p.'_v(\d+)_(\d+)/';
		}else
			$pattern = '/'.$p.'_v(\d+)_(\d+)/';

		if (!preg_match($pattern, $name, $result)) {
			// ---try one more
			return $this->getRCTfilename_onemore($id);
		}
		$split='/'.$result[0].'/';
		if ($pp)
		$replacement = $pp.'_v00'
									.'_'.$result[2]
									.$p.'_v00_'
									.sprintf("%02d", $result[4]+1);
		else
		$replacement = $p.'_v00_'
									.sprintf("%02d", $result[2]+1);

		$rctfilename=preg_replace($split, $replacement, $name);
		$rctfilename=preg_replace('/v(\d+)/', 'v__', $rctfilename);
		return $rctfilename;
	}

	function getRCTfilename_onemore($id) {
		$info=$this->getImageInfo($id);
		$name = $info['filename'];
		$p=$info['preset'];
		$pp=$info['parentpreset'];

		if ($pp) {
			$pattern = '/'.$pp.'_v(\d+)_(.*)'.$p.'_(\d+)/';
		}else
			$pattern = '/'.$p.'_v(\d+)_(\d+)/';

		if (!preg_match($pattern, $name, $result))
			return "";
		$split='/'.$result[0].'/';
		if ($pp)
		$replacement = $pp.'_v00'
									.'_'.$result[2]
									.$p.'_'
									.sprintf("%02d", $result[4]+1);
		else
		$replacement = $p.'_'
									.sprintf("%02d", $result[2]+1);

		$rctfilename=preg_replace($split, $replacement, $name);
		$rctfilename=preg_replace('/v(\d+)/', 'v__', $rctfilename);
		return $rctfilename;
	}

	function getFilename($name,$sessionId=Null) {
		$sqlwhere = (is_numeric($name)) ? "where `DEF_id`='$name' " 
				: "where `MRC|image` like '$name' ";
		if ($sessionId) 
			$sqlwhere.="and `REF|SessionData|session`=".$sessionId;
		$q = "select `DEF_id` as id, `MRC|image` as filename, `REF|SessionData|session` as sessionId from `AcquisitionImageData` "
		    .$sqlwhere;
		$filenames = $this->mysql->getSQLResult($q);
		return $filenames;
	}

	function getFilenameFromId($id, $path="") {
			list($filename) = $this->getFilename($id);
			$path = ($path) ? $this->getImagePath($filename['sessionId']) : "";
			return $path.$filename['filename'];
	}

	function getCalibrationIds($calibration, $scopeId=False, $cameraId=False, $limit='', $type='') {
		$calibration_fields = $this->mysql->getFields($calibration); 
		if (in_array('type', $calibration_fields) && $type) {
			$where[] = "cal.`type`='$type'";
		}

		if ($where)
			$sql_where = "where ".implode(' AND ', $where)." ";
		if ($limit)
			$sql_limit = " limit $limit ";

		$select = "cal.`DEF_id` as id ";
		$order  = "order by cal.`DEF_id` DESC ";

		if (in_array('axis', $calibration_fields)) {
			$q = "select distinct axis from `$calibration` cal $sql_where";
			$axis = $this->mysql->getSQLResult($q);
			if ($axis)
				foreach ($axis as $a) {
					$where_axis[] = "cal.`axis`= '".$a['axis']."'";
				}
			if ($where_axis)
				$where[] = '('.implode(' OR ', $where_axis).')';

			$select = "max(cal.`DEF_id`) as id ";
			$group[] = 'cal.`axis`';
			$sql_limit = " ";
		}

		if (in_array('magnification', $calibration_fields)) {
			$q = "select distinct magnification from `$calibration` cal $sql_where";
			$mags = $this->mysql->getSQLResult($q);
			if ($mags)
				foreach ($mags as $mag) {
					$where_mags[] = "cal.magnification = '".$mag['magnification']."'";
				}
			if ($where_mags)
				$where_mag = implode(' OR ', $where_mags);
			$where[] = ' ('.$where_mag.') ';
			$group[] = 'cal.`magnification`';
			$select = "max(cal.`DEF_id`) as id, cal.`magnification` ";
			$order = "order by cal.`magnification` DESC ";
			$sql_limit = " ";
		}


		if (in_array('REF|InstrumentData|tem', $calibration_fields) && is_numeric($scopeId))
			$where[]="cal.`REF|InstrumentData|tem`=$scopeId";

		if (in_array('REF|InstrumentData|ccdcamera', $calibration_fields) && is_numeric($cameraId))
			$where[]="cal.`REF|InstrumentData|ccdcamera`=$cameraId";

		if ($where)
			$sql_where = "where ".implode(' AND ', $where)." ";

		if ($group)
			$sql_group = "group by ".implode(', ', $group)." ";

		$q = "select "
			.$select
			."from ".$calibration." cal "
			.$sql_where
			.$sql_group
			.$order
			.$sql_limit;

		return $this->mysql->getSQLResult($q);
	}

	function itransform($imgId, $type) {
		$m = $this->getImageMatrixCalibration($imgId, $type);
		$matrix = matrix($m[a11],$m[a12],$m[a21],$m[a22]);
		$presetId=$this->getId(
				array('DEF_id'=>$imgId),
				'AcquisitionImageData',
				'REF|PresetData|preset');
		$scopeId=$this->getId(
				array('DEF_id'=>$imgId),
				'AcquisitionImageData',
				'REF|ScopeEMData|scope');
		$cameraId=$this->getId(
				array('DEF_id'=>$imgId),
				'AcquisitionImageData',
				'REF|CameraEMData|camera');
		list($cameraInfo)=$this->getDataInfo('CameraEMData', $cameraId);
		list($scopeInfo)=$this->getDataInfo('ScopeEMData', $scopeId);
		list($presetInfo)=$this->getDataInfo('PresetData', $presetId);
		$binx = $cameraInfo['SUBD|binning|x'];
		$biny = $cameraInfo['SUBD|binning|y'];
		switch ($type) {
			case 'stage position':
				$vector = array($scopeInfo['SUBD|stage position|x'],
					$scopeInfo['SUBD|stage position|y']);
				break;
			case 'image shift':
				$vector = array($scopeInfo['SUBD|image shift|x'],
					$scopeInfo['SUBD|image shift|y']);
				break;
		}
		$matrix_inv = matrix_inverse($matrix);
		$pixvect = matrix_multiply($matrix_inv, $vector);
		$pixpermeterx = hypot($matrix_inv[1][1], $matrix_inv[2][1]);
		$pixpermetery = hypot($matrix_inv[1][2], $matrix_inv[2][2]);
		$transform['angle']=$m['angle'];
		$transform['pixvect']=array(	'row'=>$pixvect[1]/$biny,
						'col'=>$pixvect[2]/$binx);
		$transform['pixpermeter']=array('x'=>$pixpermeterx, 'y'=>$pixpermetery);
		return $transform;

	}

	function getCalibrations($calibration, $scopeId=False, $cameraId=False, $limit='', $type='') {
		$Ids = $this->getCalibrationIds($calibration, $scopeId, $cameraId, $limit, $type);
		if ($Ids) {
			foreach ($Ids as $id) 
				if ($id=$id['id'])
					$where_ids[] = "cal.`DEF_id` = '".$id."'";
			if ($where_ids)
				$sql_where = "where ".implode(' OR ', $where_ids)." ";
		}
		$calibration_fields = $this->mysql->getFields($calibration); 
		if (in_array('magnification', $calibration_fields)) {
			$order = " order by cal.`magnification` DESC ";
		} else {
			$order = " order by cal.`DEF_id` DESC ";
		}

		$q = "select "
			."cal.* "
			."from ".$calibration." cal "
			.$sql_where
			.$order;
		if ($sql_where)
			return $this->mysql->getSQLResult($q);
		else
			return array();
	}

	function getImageMatrixCalibration($imgId, $type='image shift') {
		$q = "select "
			."mcal.`DEF_id`, "
			."mcal.`DEF_timestamp`, "
			."a.`DEF_timestamp`, "
			."mcal.`ARRAY|matrix|1_1` as `a11`,"
			."mcal.`ARRAY|matrix|1_2` as `a12`,"
			."mcal.`ARRAY|matrix|2_1` as `a21`,"
			."mcal.`ARRAY|matrix|2_2` as `a22`,"
			."mcal.`type` as `type`,"
			."atan2(mcal.`ARRAY|matrix|1_1`, mcal.`ARRAY|matrix|2_1`) as angle "
			."from (AcquisitionImageData a, MatrixCalibrationData mcal) "
			."left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) "
			."left join CameraEMData c on (a.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."where "
			."scope.`REF|InstrumentData|tem`=mcal.`REF|InstrumentData|tem` "
			."and "
			."c.`REF|InstrumentData|ccdcamera`=mcal.`REF|InstrumentData|ccdcamera` "
			."and "
			."scope.magnification = mcal.magnification "
			."and "
			."scope.`high tension` = mcal.`high tension` "
			."and "
			."mcal.`type`='".$type."' "
			."and "
			."mcal.`DEF_timestamp` < a.`DEF_timestamp` "
			."and "
			."a.`DEF_id` ='".$imgId."' " 
			."order by mcal.`DEF_id` desc limit 1";

		list($parent) = $this->mysql->getSQLResult($q);
		return $parent;
	}

	function getMatrixCalibration($type, $limit="") {
		if ($limit)
			$limit = " limit ".$limit;
		$q = "select "
			."unix_timestamp(mcal.`DEF_timestamp`) as `unixtimestamp`,"
			."date_format(mcal.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."mcal.type as type, "
			."mcal.`ARRAY|matrix|1_1` as `a11`, "
			."mcal.`ARRAY|matrix|1_2` as `a12`, "
			."mcal.`ARRAY|matrix|2_1` as `a21`, "
			."mcal.`ARRAY|matrix|2_2` as `a22`, "
			."atan2(mcal.`ARRAY|matrix|1_1`, mcal.`ARRAY|matrix|2_1`) as angle "
			."from MatrixCalibrationData mcal "
			."where "
			."mcal.`DEF_timestamp`>'20040222000000' and "
			."mcal.`type`='".$type."' "
			."order by mcal.`DEF_id` ".$limit;

		$Rparent = $this->mysql->SQLQuery($q);
		return $Rparent;
	}

	function getAllMatrixCalibrations() {
		$q = "select "
			."date_format(mcal.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."mcal.type as type, "
			."mcal.`ARRAY|matrix|1_1` as `a11`, "
			."mcal.`ARRAY|matrix|1_2` as `a12`, "
			."mcal.`ARRAY|matrix|2_1` as `a21`, "
			."mcal.`ARRAY|matrix|2_2` as `a22`, "
			."atan2(mcal.`ARRAY|matrix|1_1`, mcal.`ARRAY|matrix|2_1`) as angle "
			."from MatrixCalibrationData mcal "
			."where "
			."1 "
			."order by mcal.`type`, mcal.`DEF_timestamp` "
			."";

		$Rparent = $this->mysql->SQLQuery($q);
		return $Rparent;
	}

	function getMatrixCalibrationTypes() {
		$q="select "
		."distinct mcal.`type` "
		."from MatrixCalibrationData mcal";
		if (!$types=$this->mysql->getSQLResult($q))
			$types = array();
		return $types;
	}

	function getImageFFT($imgId) {
		$q = "select  "
			."fft.`DEF_id` as fftimageId, "
			."fft.`MRC|image` as fftimage "
			."from "
			."AcquisitionFFTData fft "
			."where "
			."fft.`REF|AcquisitionImageData|source` ='".$imgId."' "; 

		list($parent) = $this->mysql->getSQLResult($q);
		return $parent;
	}

	function getParent($imgId) {
		$q = " select "
			."parent.`DEF_id` as parentId, "
			."parent.`MRC|image` as parentimage, "
			."pp.`name` as parentpreset, "
			."parenttarget.`type` as parenttype, "
			."parenttarget.`number` as parentnumber, "
			."p.`name` as preset, "
			."a.`DEF_id` as imageId, "
			."a.`MRC|image` as image "
			."from AcquisitionImageData a "
			."left join PresetData p "
			."on (p.DEF_id=a.`REF|PresetData|preset`) "
			."left join AcquisitionImageTargetData parenttarget "
			."on (parenttarget.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) "
			."left join AcquisitionImageData parent "
			."on (parent.`DEF_id`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."where " 
			."a.`DEF_id` ='".$imgId."' "; 

		if($Rparent = $this->mysql->getSQLResult($q))
			return $Rparent[0];
		else
			return NULL;
	}

	function getImageInfo($imgId) {
		//manual and uploaded images have no parent
		if (!$this->mysql->isTable('PresetData') ||!$this->mysql->isTable('AcquisitionTargetData')) {
			$q = ""
			."select a.`DEF_id` as imageId, "
			."date_format(a.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."a.`REF|SessionData|session` as `sessionId`,"
			."a.`MRC|image` as filename "
			."from AcquisitionImageData a "
			."where "
			."a.`DEF_id` ='".$imgId."' "; 
			list($result) = $this->mysql->getSQLResult($q);
			return $result;
		}
		// --- check if image as a parent
		$parentinfo = $this->getParent($imgId);
		$parentId = ($parentinfo['parentId']) ? $parentinfo['parentId'] : false;
		$parentselect = "";
		$parentjoin = "";
		$gridtable = $this->mysql->isTable('GridData');
		$parenttargetfields = $this->mysql->getFields('AcquisitionImageTargetData');
		$parentcoords = "";
		$parentcoords .= (in_array('delta column', $parenttargetfields)) ?  
			"parenttarget.`delta column`, " : "";
		$parentcoords .= (in_array('delta row', $parenttargetfields)) ?  
			"parenttarget.`delta row`, " : "";
		$parenttargetjoin = 
			"left join AcquisitionImageTargetData parenttarget "
			."on (parenttarget.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) ";
		$parenttargetjoin .= (in_array('REF|CameraEMData|camera', $parenttargetfields)) ?  
			"left join CameraEMData cp "
			."on (parenttarget.`REF|CameraEMData|camera`=cp.`DEF_id`) " : "";
		$gridselect = ($gridtable) ?
			"grid.`grid ID` as gridId, grid.`insertion`, " : "";
		$gridjoin = ($gridtable) ?
			"left join GridData grid "
			."on (grid.`DEF_id`=a.`REF|GridData|grid`) " : '';
		if ($parentId) {
			$parentselect = ""
			."parent.`DEF_id` as parentId, "
			."parent.`MRC|image` as parentimage, "
			."pp.`name` as parentpreset, "
			."parenttarget.`type` as parenttype, "
			."parenttarget.`number` as parentnumber, "
			."floor(parenttarget.`delta column`+cp.`SUBD|dimension|x`/2) as targetx, "
			."floor(parenttarget.`delta row`+cp.`SUBD|dimension|y`/2) as targety, "
			."((c.`SUBD|binning|y`*c.`SUBD|dimension|x`*pi.pixelsize) /  "
			."(cp.`SUBD|binning|y`* ppi.pixelsize)) as targetdim, "
			."((c.`SUBD|binning|y`* pi.pixelsize) /  "
			."(cp.`SUBD|binning|y`* ppi.pixelsize)) as pixelsizeratio, "
			."((c.`SUBD|binning|y`* sqrt(c.`SUBD|dimension|x`*c.`SUBD|dimension|x`  "
			."+ c.`SUBD|dimension|y`*c.`SUBD|dimension|y`) * pi.pixelsize) /  "
			."(cp.`SUBD|binning|y`* ppi.pixelsize)) as targetdiam,  "
			."(pi.pixelsize/ppi.pixelsize) as pixelsizeratio,  "
			."ppi.pixelsize as parentpixelsize,  ";
			$parentjoin = ""
			."left join AcquisitionImageData parent "
			."on (parent.`DEF_id`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."left join ScopeEMData pscope on (pscope.`DEF_id`=parent.`REF|ScopeEMData|scope`) "
			."left join SessionData ps1 on (ps1.`DEF_id`=parent.`REF|SessionData|session`) "
			."cross join PixelSizeCalibrationData ppi on "
			."(pscope.`REF|InstrumentData|tem`= ppi.`REF|InstrumentData|tem` and "
			."pscope.magnification = ppi.magnification and "
			."cp.`REF|InstrumentData|ccdcamera` = ppi.`REF|InstrumentData|ccdcamera` "
			."and ppi.`DEF_timestamp`  < parent.`DEF_timestamp` ) ";
		}
		$q = "select "
			.$gridselect
			.$parentselect
			.$parentcoords
			."a.`DEF_id` as imageId, "
			."date_format(a.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."a.`REF|SessionData|session` as `sessionId`,"
			."a.`MRC|image` as filename, "
			."p.`name` as `preset`, "
			."isc.`name` as `scope`, "
			."ic.`name` as `camera`, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy, "
			."c.`SUBD|binning|y` as binning, "
			."c.`exposure time`, "
			."pi.pixelsize as pixelsize, "
			."scope.magnification, "
			."scope.defocus, "
			."scope.`high tension` "
			."from AcquisitionImageData a "
			."left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) "
			."join InstrumentData isc on (isc.`DEF_id`=scope.`REF|InstrumentData|tem`)"
			."left join CameraEMData c on (a.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."join InstrumentData ic on (ic.`DEF_id`=c.`REF|InstrumentData|ccdcamera`)"
			."left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			.$parenttargetjoin
			.$gridjoin
			."cross join PixelSizeCalibrationData pi on "
			."(scope.`REF|InstrumentData|tem`= pi.`REF|InstrumentData|tem` and "
			."scope.magnification = pi.magnification and "
			."c.`REF|InstrumentData|ccdcamera`=pi.`REF|InstrumentData|ccdcamera` "
			."and pi.`DEF_timestamp`  < a.`DEF_timestamp` ) "
			.$parentjoin
			."where "
			."a.`DEF_id` ='".$imgId."' "
			."order by pi.`DEF_id` desc"; 
		$Rimageinfo = $this->mysql->SQLQuery($q);
		$imageinfo = mysql_fetch_array($Rimageinfo,MYSQL_ASSOC);
		return $imageinfo;
	}

	function getGridId($imgId) {
		if (!$this->mysql->isTable('GridData'))
			return 0;
		$q = "select "
			."grid.`grid ID` as gridId "
			."from AcquisitionImageData a "
			."left join GridData grid "
			."on (grid.`DEF_id`=a.`REF|GridData|grid`) "
			."where "
			."a.`DEF_id` ='".$imgId."' "; 

		$Rgridinfo = $this->mysql->SQLQuery($q);
		$gridinfo = mysql_fetch_array($Rgridinfo);
		return $gridinfo['gridId'];
	}

	function getImageRelation($imgId, $preset='', $matchtargetnb=true) {
		if (!$this->mysql->isTable('PresetData') ||!$this->mysql->isTable('AcquisitionTargetData')) return array();
		if ($matchtargetnb) {
			$targetnbwhere = "siblingtarget.`number`= parenttarget.`number` and ";
		}
			$targetnbjoin  = "left join AcquisitionImageTargetData siblingtarget "
				."on (siblingtarget.`DEF_id`=sibling.`REF|AcquisitionImageTargetData|target`) ";
		$q = "select "  
			."sibling.`DEF_id` as siblingimageId, "
			."sibling.`MRC|image` as siblingimage, "
			."siblingtarget.`type` as siblingtype, "
			."sp.`name` as siblingpreset, "
			."parent.`DEF_id` as parentId, "
			."parent.`MRC|image` as parentimage, "
			."parenttarget.`type` as parenttype, "
			."pp.`name` as parentpreset, "
			."a.`DEF_id` as imageId, "
			."a.`MRC|image` as image, "
			."p.`name` as preset "
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
			."left join AcquisitionImageData sibling "
			."on (targets.`DEF_id`=sibling.`REF|AcquisitionImageTargetData|target`) "
			.$targetnbjoin
			."left join PresetData sp  on (sp.DEF_id=sibling.`REF|PresetData|preset`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."where "
			.$targetnbwhere
			."sibling.`MRC|image` <> 'NULL' "
			."and "
			."sibling.`DEF_id` <> a.`DEF_id` ";
			if ($preset)
				$q .= "and siblingtarget.`type`='".$preset."' ";
				#$q .= "and sp.`name`='".$preset."' ";
			$q .="and "
			."a.`DEF_id` ='".$imgId."' "; 

		$parents = array();
		$Rparent = $this->mysql->SQLQuery($q);
		while ($parent = mysql_fetch_array($Rparent, MYSQL_ASSOC))
			$parents[]=$parent;
		return $parents;
	}


	function getTypeFFT() {
		return $this->ffttypes;
	}

	function findRelation($imgId, $preset, $type='', $matchtargetnb=true) {
		$newimage = array();
		$relations = $this->getImageRelation($imgId, $type, $matchtargetnb);
		foreach ($relations as $relation) {
			if ($relation['siblingpreset']==$preset && $relation['parentId']) {
				$newimage['id'] = $relation['siblingimageId'];
				$newimage['preset'] = $relation['siblingpreset'];
				break;
			}
		}
		return $newimage;
	}

	function findImage($imgId, $preset="") {
	// --- find an image related to an image Id and a preset
		if (!$this->mysql->isTable('PresetData'))
			return array('id'=>$imgId);
		$newimage=array();
		$imageinfo = $this->getImageInfo($imgId);
		if (	empty($preset)
			|| $imageinfo['preset']==$preset 
			|| in_array($preset, $this->defaulttypes)
			|| $preset == $this->manualtype
		) { 
			$newimage['id'] = ($imageinfo['imageId']) ? $imageinfo['imageId'] : $imgId;
			$newimage['preset'] = ($imageinfo['preset']) ? $imageinfo['preset'] : $preset;
			return $newimage;
		}
		if ($preset == $this->rcttype ) {
			$rctfilename = $this->getRCTfilename($imgId);
			// --- get most recent fields
			$filename = end($this->getFilename($rctfilename,$imageinfo['sessionId']));
			$newimage[id] = $filename[id];
			$newimage[preset] = $imageinfo[preset];
			return $newimage;
		}

		// --- search for a parent
		$parentId = $imgId;
		while ($parentId) {
			$parent = $this->getParent($parentId);
			$parentId = $parent['parentId'];
			$parentpreset=$parent['parentpreset'];
			if ($parentpreset==$preset) {
				$newimage['id'] = $parent['parentId'];
				$newimage['preset'] = $parent['parentpreset'];
				$newimage['childid'] = $parent['imageId'];
				break;
			}
		}

		// --- search for siblings from a common target
		if (empty($newimage)) 
			$newimage = $this->findRelation($imgId, $preset);

		// --- search for focus siblings from a different target
		if (empty($newimage)) 
			$newimage = $this->findRelation($imgId, $preset, 'focus', false);

		return $newimage;
		
	}

	function getDefocusStats($imgId, $preset) {
		$newimage = $this->findRelation($imgId, $preset, 'focus', false);
		return $newimage;
	}

	function getImageTargets($imgId, $type="acquisition") {
    $q =  " select "
      ."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
      ."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
      ."t.`delta column` as `delta column`, "
      ."t.`delta row` as `delta row`, "
      ."c.`SUBD|dimension|x` as dimx, "
      ."c.`SUBD|dimension|y` as dimy, "
      ."child.`DEF_id` as childId, "
      ."t.`DEF_id` as tId, "
      ."t.`version` as tversion, "
      ."t.`status` as tstatus, "
      ."t.`number` as tnumber "
      ."from AcquisitionImageData as a "
      ."left join AcquisitionImageTargetData as t "
      ."on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
      ."left join CameraEMData c on (t.`REF|CameraEMData|camera`=c.`DEF_id`) "
      ."left join AcquisitionImageData as child "
      ."on (child.`REF|AcquisitionImageTargetData|target`=t.`DEF_id`) "
      ."where "
      ."t.`type`='$type' and "
      ."a.`DEF_id`='".$imgId."' "
      ."order by `tnumber` ";

		return $this->mysql->getSQLResult($q);
	}

	function getTargetStats($sessionId) {
		$q="SELECT " 
		."count(t.DEF_id) as nb, "
		#."lasttarget.DEF_id, `t`.`REF|AcquisitionImageData|image`, "
		."t.status, t.number "
		."FROM ( "
		."SELECT "
		."max(`t`.DEF_id) as DEF_id "
		."FROM     `AcquisitionImageTargetData` AS `t` "
		."WHERE `t`.type IN ('acquisition', 'focus') "
		."AND `t`.`REF|SessionData|session`=".$sessionId." "
		#."AND `t`.`REF|AcquisitionImageData|image` = $imageId." "
		."GROUP BY t.`REF|AcquisitionImageData|image`, t.version, t.number "
		."  ) lasttarget "
		."LEFT JOIN AcquisitionImageTargetData as t on (t.`DEF_id`=lasttarget.DEF_id) "
		."WHERE 1 "
		."GROUP by t.status ";
		return $this->mysql->getSQLResult($q);
	}

	function matchVersionTargets($targets) {
		$grouptargets = array();
		$ntargets = array();
		if (!is_array($targets)) 
			return false;

		foreach ($targets as $target)
			$grouptargets[$target['tnumber']][] = $target;

		foreach ($grouptargets as $ts) {
			if (!$this->asChildId($ts)) {
				$ntargets[] = $ts[0];
				continue;
			}
			$this->joinChildId($ts, $ntargets);

		}
		return $ntargets;
	}

	function joinChildId($targets, &$ntargets) {
		foreach ($targets as $target) {

			if (!$target['childId']) {
				$tx = $target['x'];
				$ty = $target['y'];
				continue;
			}

			if ($tx)
				$target['x'] = $tx;
			if ($ty)
				$target['y'] = $ty;

			$ntargets[] = $target;
		}
		return true;
	}

	function asChildId($targets) {
		$ret = false;
		foreach ($targets as $target)
			if ($target['childId']) {
				$ret = true;
				break;
			}
		return $ret;
	}

	function getImageFocusTargets($imgId, $all=false) {
		if (!$all)
			$version = "t.`version`='0' and ";
		$q =	" select "
			."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
			."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy, "
			."t.`DEF_id` as tId, "
			."t.`status` as tstatus, "
			."t.`version` as tversion "
			."from AcquisitionImageData as a "
			."left join AcquisitionImageTargetData as t "
			."on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
			."left join CameraEMData c on (t.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."where (t.`delta row` or t.`delta column`)<>'NULL' and "
			.$version 
			."t.`type`='focus' and "
			."a.`DEF_id`='".$imgId."'";
		return $this->mysql->getSQLResult($q);
	}

	function getApplications() {
		$applications = array();
		if ($this->mysql->SQLTableExists("ApplicationData")) {
			$q = "select DEF_Id, name, version from ApplicationData order by name,version";
			$Rapplication = $this->mysql->SQLQuery($q);
			while($application = mysql_fetch_array($Rapplication))
				$applications[] = $application;
		}
		return $applications;
	}

	function getSQLTableDefinitionXML($table) {

	    $crlf = $this->crlf;
	
	    $schema_create = "  <sqltable name=\"".$table."\" >$crlf";
	
	    $result = $this->mysql->SQLQuery("SHOW FIELDS FROM $table"); 
	    while($row = mysql_fetch_array($result))
	    {
	        $schema_create .= "    <field $crlf";
	        $schema_create .= "      name=\"$row[Field]\" $crlf";
	        $schema_create .= "      type=\"$row[Type]\" $crlf";
	
	        if(isset($row["Default"]) && (!empty($row["Default"]) || $row["Default"] == "0"))
	            $schema_create .= "      default=\"DEFAULT '$row[Default]'\" $crlf";
	        if($row["Null"] != "YES")
	            $schema_create .= "      null=\"NOT NULL\" $crlf";
	        if($row["Extra"] != "")
	            $schema_create .= "      extra=\"$row[Extra]\" $crlf";
	        $schema_create .= "    />$crlf";
	    }
	    $schema_create = ereg_replace(",".$crlf."$", "", $schema_create);
	    $result = $this->mysql->SQLQuery("SHOW KEYS FROM $table") ;
	    while($row = mysql_fetch_array($result))
	    {
	        $kname = ($row['Key_name'] == "PRIMARY") ? 
				$row['Key_name'] : $this->addBackquotes($row['Key_name']);
	        if(($kname != "PRIMARY") && ($row['Non_unique'] == 0))
	            $kname="UNIQUE|$kname";
	         if(!isset($index[$kname]))
	             $index[$kname] = array();
						$subpart=($row['Sub_part']) ? '('.$row['Sub_part'].')' : '';
						$index[$kname][] = $this->addBackquotes($row['Column_name']).$subpart;
						$index[$kname]['type'] = $row['Index_type'];
	    }

	    while(list($x, $columns) = @each($index))
	    {
		if ($type=$columns['type'])
			unset($columns['type']);
		$full = ($type=='FULLTEXT') ? 'FULLTEXT ' : '';
	         $schema_create .= "    <key>";
	         if($x == "PRIMARY")
	             $schema_create .= "PRIMARY KEY (" . implode($columns, ", ") . ")";
	         elseif (substr($x,0,6) == "UNIQUE")
	            $schema_create .= "UNIQUE ".substr($x,7)." (" . implode($columns, ", ") . ")";
	         else
	            $schema_create .= $full."KEY ".$x." (" . implode($columns, ", ") . ")";
	         $schema_create .= "</key>$crlf";
	    }
	
	    $schema_create .= "  </sqltable>$crlf";
	    return (stripslashes($schema_create));
	}

	function addBackquotes($field) {
		if (is_array($field)) {
			$formatedfield = array();
			foreach($field as $f)
				$formatedfield[] = '`'.$f.'`';
			return $formatedfield;
		} else {
				return '`'.$field.'`';
		}
	}

	function getXMLData($table, &$buffer, $where="") {
	    $add_query = empty($where) ? "" : " WHERE $where";
	    $local_query = 'SELECT * FROM ' . $table . $add_query;
	    $data = $this->mysql->getSQLResult($local_query);
	    $buffer .= $this->array2XML($data,$table);
	    return $buffer;
	}
	
	function array2XML($data, $table) {
		$crlf = $this->crlf;
		$buffer = '  <!-- ' . $table . ' -->' . $crlf;
		foreach($data as $d) {
			$buffer .= '    <sqltable name="' . $table . '" >' . $crlf;
			foreach ($d as $k=>$v) {
				$buffer .= '        <field name="'.$k.'" >'.htmlspecialchars($v)
					.'</field>'.$crlf;
			}
			$buffer .= '    </sqltable>'.$crlf;
		}
		return $buffer;
	}

	function dumpDeleteSession($sessionId) {
	    $result = $this->mysql->SQLQuery("SHOW TABLES");
	    while($row = mysql_fetch_row($result))
		$tables[] = $row[0];
	    // --- Get Reference Ids
	    $where = " `DEF_id` = $sessionId ";
	    $Rinfo = $this->mysql->SQLQuery("SELECT date_format(DEF_timestamp,'%m/%d/%Y') as date, `name` from SessionData where $where");
	    $result = mysql_fetch_array($Rinfo);
	    $name = $result['name'];
	    $date = $result['date'];

	    $ref_tables[]='SessionData';
	    foreach($tables as $table) {
	    	$result = $this->mysql->SQLQuery("SHOW FIELDS FROM $table"); 
	    	while($row = mysql_fetch_array($result))
			if (ereg("^REF\|SessionData", $row['Field']))
				if(!in_array($table,$ref_tables))
					$ref_tables[]=$table;

	    }

	    $queries = array();
	    foreach($ref_tables as $table) {
		$w = ($table=="SessionData") ? $where : " `REF|SessionData|session` = $sessionId ";
		$q = "select count(DEF_id) as nb from `$table` where $w ";
		list($r) = $this->mysql->getSQLResult($q);
		$nb = $r['nb'];
		if ($nb) {
			// $q = "delete from `$table` where $w ";
			$q = "$nb from $table ";
			echo $q;
			echo "<br>";
			$queries[] = $q;
		}
	    }

	    // $this->mysql->SQLQueries($queries);
	}

	function dumpDefaultTables($tables) {
		$crlf = $this->crlf;
		$dump =  '<!--' . $crlf
			.  '-' . $crlf
			.  '- Default Table XML-Dump' . $crlf
			.  '- http://ami.scripps.edu/ ' . $crlf
			.  '-' . $crlf
			.  '- Tables: ' . $crlf;

		$definition=$content='';
		foreach($tables as $table) {
			$value=false;
			if (is_array($table)) {
				$table=$table[0];
				$value=$table[1];
			}
			if (!$this->mysql->SQLTableExists($table))
				continue;
			$definition .= $this->getSQLTableDefinitionXML($table);
			if ($value) {
				$this->getXMLData($table, $content);
			}
			$dump .=  '-	'.$table. $crlf;
		}

		$dump .=   '-' . $crlf
			.  '-->' . $crlf . $crlf
			.  '<defaulttables>' . $crlf;
		$this->buildXML($definition, $content, $dump);
		$dump .= "</defaulttables>" . $crlf;
		return $dump;
	}

	function dumpCalibrations($tables, $scopeId, $cameraId, $limit, $types=array()) {
		$crlf = $this->crlf;
		list($scopeinfo) = $this->getInstrumentInfo($scopeId);
		list($camerainfo) = $this->getInstrumentInfo($cameraId);
		$dump =  '<!--' . $crlf
			.  '-' . $crlf
			.  '- Calibrations XML-Dump' . $crlf
			.  '- http://ami.scripps.edu/ ' . $crlf
			.  '-' . $crlf
			.  '- Scope:' . $scopeinfo['name'].$crlf
			.  '- Camera:' . $camerainfo['name']. $crlf
			.  '- Date : ' . date("F j, Y, g:i a").$crlf
			.  '-' . $crlf
			.  '- Calibrations: ' . $crlf;

		foreach($tables as $table) {
			if (!$this->mysql->SQLTableExists($table))
				continue;
			$table_fields = $this->mysql->getFields($table); 
			if (in_array('type', $table_fields) && $types) {
				$rall = array();
				foreach ($types as $type) {
					$r = $this->getCalibrations($table, $scopeId, $cameraId, $limit, $type);
					if (!$r[0]['type'])
						continue;
					$rall = array_merge($rall, $r);
					$dump .=  '-		'.$type. $crlf;
				}
				$content .= $this->array2XML($rall, $table);
			} else {
				$r = $this->getCalibrations($table, $scopeId, $cameraId, $limit);
				$content .= $this->array2XML($r, $table);
			}
			$definition .= $this->getSQLTableDefinitionXML($table);
			$dump .=  '-	'.$table. $crlf;
		}
		$dump .=   '-' . $crlf
			.  '-->' . $crlf . $crlf
			.  '<calibrationdump>' . $crlf;
		$this->buildXML($definition, $content, $dump);
		$dump .= "</calibrationdump>" . $crlf;
		return $dump;
	}

	function getApplicationInfo($id) {
		return $this->getDataInfo('ApplicationData', $id);
	}

	function dumpApplicationData($applicationId, $format="xml") {
	    $crlf = $this->crlf;
	    $tbl_applicationdata="ApplicationData";
	    $result = $this->mysql->SQLQuery("SHOW TABLES");
	    while($row = mysql_fetch_row($result))
		$tables[] = $row[0];
	    // --- Get Reference Ids
	    $where = " `DEF_Id` = $applicationId ";
	    $Rinfo = $this->mysql->SQLQuery("SELECT date_format(DEF_timestamp,'%m/%d/%Y') as date, `name`, `version` from $tbl_applicationdata where $where");
	    $result = mysql_fetch_array($Rinfo);
	    $name = $result['name'];
	    $version = $result['version'];
	    $date = $result['date'];

	    $ref_tables=array();
	    foreach($tables as $table) {
		if ($table=="LaunchedApplicationData")
			continue;
	    	$result = $this->mysql->SQLQuery("SHOW FIELDS FROM $table"); 
	    	while($row = mysql_fetch_array($result))
			if (ereg("^REF\|$tbl_applicationdata", $row['Field']))
				if(!in_array($table,$ref_tables))
					$ref_tables[]=$table;
	    }

	    if ($format=="sql") {
		$getdefinition="mysql->getSQLTableDefinition";
		$getdata="mysql->getSQLTableContent";
		$dump      =  '# Leginon Application-SQL-Dump' . $crlf
                           .  '# http://ami.scripps.edu/ ' . $crlf
                           .  '#' . $crlf
                           .  '# Application : ' . $name . $crlf
                           .  '# Version     : ' . $version . $crlf
                           .  '# Date : ' . $date . $crlf
                           .  '#' . $crlf . $crlf;

	    } else if ($format="xml") {
		$getdefinition="getSQLTableDefinitionXML";
		$getdata="getXMLData";
		$dump =  '<!--' . $crlf
                             .  '-' . $crlf
                             .  '- Application XML-Dump' . $crlf
                             .  '- http://ami.scripps.edu/ ' . $crlf
                             .  '-' . $crlf
                             .  '- Application :' . $name . $crlf
                             .  '- Version     :' . $version . $crlf
                             .  '- Date : ' . $date . $crlf
                             .  '-' . $crlf
                             .  '-->' . $crlf . $crlf
                             .  '<applicationdump>' . $crlf;
	    }

	    eval('$table_def='.'$this->'.$getdefinition.'($tbl_applicationdata);');
	    foreach($ref_tables as $table) {
	    	eval('$table_def.='.'$this->'.$getdefinition.'($table);');
	    }
	    


	    eval('$this->'.$getdata.'($tbl_applicationdata, $buffer, $where);');

	    $where = " `REF|ApplicationData|application` = $applicationId";
	    foreach($ref_tables as $table) { 
		    eval('$this->'.$getdata.'($table, $buffer, $where);');
		}

	    if($format=="xml") {
	    	$this->buildXML($table_def, $buffer, $dump);
		$dump .= "</applicationdump>" . $crlf;
	    } else {
		$dump .= $table_def;
		$dump .= $buffer;
	    }

		return $dump;

	}

	function download($filename, $content) {

		$mime_type = (USR_BROWSER_AGENT == 'MSIE' || USR_BROWSER_AGENT == 'OPERA')
		? 'application/octetstream'
		: 'application/octet-stream';

		$now = gmdate('D, d M Y H:i:s') . ' GMT';

		header('Content-Type: ' . $mime_type);
		header('Expires: ' . $now);
		if (USR_BROWSER_AGENT == 'MSIE') {
			header('Content-Disposition: inline; filename="' . $filename . '"');
			header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
			header('Pragma: public');
		} else {
			header('Content-Disposition: attachment; filename="' . $filename . '"');
			header('Pragma: no-cache');
		}
		echo $content;

	}

	function importTables($filename) {
		$app = new XMLApplicationImport($filename);
		$sqldef = $app->getSQLDefinitionQueries();
		$sqldata = $app->getSQLDataQueries();
		$fieldtypes = $app->getFieldTypes();
		if ($this->mysql->checkDBConnection()) {
			$this->mysql->SQLAlterTables($sqldef, $fieldtypes);
			foreach ((array)$sqldata as $table=>$queries) {
				foreach($queries as $query) {
					eval("\$sqlinsert= \"".addslashes($query)."\";");
						$this->mysql->SQLQuery($sqlinsert,true);
				}
			}
		}
			return true;
	}

	function importCalibrations($xmldata, $scopeId, $cameraId) {
		if (!$scopeId && !$cameraId) {
			echo "no instrument found";
			return false;
		}
		$app = new XMLCalibrationImport($xmldata);
		$sqldef = $app->getSQLDefinitionQueries();
		$sqldata = $app->getSQLDataQueries();
		$fieldtypes = $app->getFieldTypes();
		$fieldvalues = $app->getFieldValues();
		if ($changes=$this->mysql->SQLAlterTables($sqldef, $fieldtypes))
			echo "<br>".$changes;

		//--- insert a SessionData to link InstrumentData w/ Calibrations
		$q = "insert into `SessionData` (`name` ) "
			. " VALUES "
			. " ( concat('importcal', DATE_FORMAT(now(), '%Y%m%d%H%i%s')) ) ";

		$sessionId = $this->mysql->SQLQuery($q, True);
		if (!$sessionId) {
			echo "no session table";
			return false;
		}

		//--- insert new Calibrations data;
		if (is_array($sqldata))
		foreach ($sqldata as $table=>$queries) {
			foreach($queries as $query) {
				eval("\$sqlinsert= \"".addslashes($query)."\";");
					$this->mysql->SQLQuery($sqlinsert,true);
			}
		}
		return true;
	}
		
	function importApplication($data) {
		$app = new XMLApplicationImport($data);
		$sqldef = $app->getSQLDefinitionQueries();
		$sqldata = $app->getSQLDataQueries();
		$fieldtypes = $app->getFieldTypes();
		$fieldvalues = $app->getFieldValues();
		$this->sqldefinitions = $sqldef;
		$this->sqlfieldtypes = $fieldtypes;
		$this->sqlfieldvalues = $fieldvalues;

		//--- Generate the tables
		$this->mysql->SQLQueries($sqldef);

		//--- Check if application exits
		$applicationinfo = $fieldvalues['ApplicationData'];
		foreach($applicationinfo as $k=>$v) {
			if (ereg('DEF_',$k)) continue;
			$sqlwhere[] = "`$k`=$v";
		}
		$where = implode(" AND ", $sqlwhere);
		$query = "Select `DEF_id`, name, version from ApplicationData where $where";
		$Rresult = $this->mysql->SQLQuery($query);
		$result = mysql_fetch_array($Rresult);
		if ($result) {
			$msg = 	 "Application $result[name]-$result[version] exists "
				."on sql server ".$this->mysql->getSQLHost();
			return $msg;
		}

		//--- insert new ApplicationData data;
		foreach ($sqldata as $table=>$queries) {
			foreach($queries as $query) {
				if ($table=="ApplicationData")
					$applicationId = $this->mysql->SQLQuery($queries[0], true);
				else {
					eval("\$sqlinsert= \"".addslashes($query)."\";");
					$this->mysql->SQLQuery($sqlinsert,true);
				}
			}
		}

		$msg = "Application "
			.str_replace('"', '', $applicationinfo['name'])
			."-"
			.str_replace('"', '', $applicationinfo['version'])
			." imported successfully"
			." on ".$this->mysql->getSQLHost();
		return $msg;

	}

	function importInfo() {
		return array(	"Definition"=>$this->sqldefinitions,
				"FieldTypes"=>$this->sqlfieldtypes,
				"FieldValues"=>$this->sqlfieldvalues
			);
	}

	function buildXML($definition, $content, &$dump) {
	   $crlf = $this->crlf;
	   $dump .= " <definition>" . $crlf
	   	 . $definition . $crlf
	   	 . " </definition>" . $crlf
	   	 . " <data>" . $crlf
	   	 . $content . $crlf
	   	 . " </data>" . $crlf;
	}

	function handler($value) {
		echo "$value;$this->crlf";
	}

	function getAllGoniometerModels() {
		$models=array();
		$q="SELECT `DEF_id`, concat(date_format(DEF_timestamp,'%d-%b-%Y'), label, axis) as label from StageModelCalibrationData order by `DEF_timestamp` DESC";
		$q="SELECT `DEF_id`, concat(label,' ',axis) as label  from StageModelCalibrationData order by `DEF_timestamp` DESC";
		$result = $this->mysql->SQLQuery($q);
		while ($row= mysql_fetch_array($result, MYSQL_ASSOC))
			$models[] = $row;
		return $models;
	}

	function getGoniometerModelsByHost($hostname) {
		$models=array();

		$q="SELECT s.`DEF_id`, concat(s.label,' ',s.axis) as label "
		." from StageModelCalibrationData s "
		." left join InstrumentData t on s.`REF|InstrumentData|tem` = t.`DEF_id` "
		." left join InstrumentData c on s.`REF|InstrumentData|ccdcamera` = c.`DEF_id` "
		." where t.`hostname` = '$hostname' and c.`hostname` = '$hostname'"
		." order by s.`DEF_timestamp` DESC";
		$result = $this->mysql->SQLQuery($q);
		while ($row= mysql_fetch_array($result, MYSQL_ASSOC))
			$models[] = $row;
		return $models;
	}

	function getGoniometerModelId($label, $axis) {
		$q="SELECT `DEF_id` from StageModelCalibrationData where label=\"$label\" and axis=\"$axis\" order by `DEF_timestamp` DESC limit 1";
		$result = $this->mysql->SQLQuery($q);
		$row = mysql_fetch_array($result);
		return $row['DEF_id'];
	}

	function getGoniometerModel($Id) {
		$q="SELECT * from StageModelCalibrationData where `DEF_id` = \"$Id\"";
		$result = $this->mysql->SQLQuery($q);
		$row = mysql_fetch_array($result, MYSQL_ASSOC);
		return $row;
	}

	function getDriftTime($imageId) {
		$ids = array();
		if (is_array($imageId)) {
			foreach ($imageId as $id) {
				$ids[] = 't.`REF|AcquisitionImageData|image`='.$id;
			}
		} else {
			$ids[] = 't.`REF|AcquisitionImageData|image`='.$imageId;
		}
		$sqlwhere = '('.implode(' OR ', $ids).')';
		$q="select  "
		."t.`REF|AcquisitionImageData|image` as imageId, "
		."t.`DEF_id` as targetId, "
		."t.`version` as `target version`, "
		."sum(time_to_sec((DATE_SUB(d2.`DEF_timestamp`, INTERVAL "
		."date_format(d1.`DEF_timestamp`, '%T') HOUR_SECOND)))) as `total` "
		."from (DriftData d1 , DriftData d2) "
		."left join AcquisitionImageTargetData as t  "
		."on (t.`DEF_id` = d1.`REF|AcquisitionImageTargetData|target`)  "
		."where "
		."d2.`DEF_id`=d1.`DEF_id`+1 and "
		."d2.`REF|AcquisitionImageTargetData|target` = d1.`REF|AcquisitionImageTargetData|target` and "
		.$sqlwhere." and  "
		."t.`type`='focus'   "
		."group by t.`REF|AcquisitionImageData|image` ";
		return $this->mysql->getSQLResult($q);
	}

	function getDriftedImages($id) {
		return $this->getDriftData($id, 'session', true);
	}

	function getDriftDataFromSessionId($id) {
		return $this->getDriftData($id, 'session');
	}

	function getDriftDataFromImageId($id) {
		return $this->getDriftData($id, 'image');
	}
	
	function getDriftData($id, $type, $group=false) {
		switch ($type) {
			case 'image':
				$condition = "`t`.`REF|AcquisitionImageData|image`='$id' and  ";
				break;
			case 'session':
				$condition = "`t`.`REF|SessionData|session` = '$id' and ";
				break;
		} 

		$select =  "UNIX_TIMESTAMP(d1.`DEF_timestamp`) as `unix_timestamp`, "
		."date_format(d1.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`, "
		."a.`MRC|image` as filename, "
		."t.`REF|AcquisitionImageData|image` as imageId, "
		."t.`DEF_id` as targetId, "
		."d1.cols as driftx, "
		."d1.`rows` as drifty, "
		."@val:=sqrt(d1.`rows`*d1.`rows` + d1.`cols`*d1.`cols`) as driftvalue, "
		."d1.interval as `interval`, "
		."@val/d1.interval as `rate` ";

		if ($group) {
			$select = "UNIX_TIMESTAMP(d1.`DEF_timestamp`) as `timestamp`, "
			."t.`REF|AcquisitionImageData|image` as imageId, "
			."t.`DEF_id` as targetId, "
			."count(t.`DEF_id`) as nb_targetId ";
			$sqlgroup = "group by t.`REF|AcquisitionImageData|image`  having nb_targetId > 1 ";
		}

		$q="select  "
		.$select
		."from DriftData d1 "
		."left join AcquisitionImageTargetData as t  "
		."on (t.`DEF_id` = d1.`REF|AcquisitionImageTargetData|target`)  "
		."left join AcquisitionImageData as a on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
		."where "
		.$condition
		." 1 "
//		."t.`type`='focus' "
		.$sqlgroup;
		return $this->mysql->getSQLResult($q);
	}

	function getFocusResultData($id, $correction_type, $method, $status='ok') {

		switch ($correction_type) {
			case 'both':
				$condition1 = "  ";
				break;
			case 'Stage Z':
				$condition1 = "`f`.`defocus correction` = '".$correction_type."' and ";
				break;
			case 'defocus':
				$condition1 = "`f`.`defocus correction` = '".$correction_type."' and ";
				break;
		} 

		switch ($method) {
			case 'Stage Tilt':
				$condition2 = " `f`.`method` = '".$method."' and ";
				break;
			case 'bad':
				$condition2 = " `f`.`method` = '".$method."' and ";
				break;
			case 'all':
				$condition2 = " ";
				break;
		} 

		switch ($status) {
			case 'ok':
				$condition3 = " `f`.`status` = '".$status."' and ";
				break;
			case 'bad':
				$condition3 = " `f`.`status` like '%fit untrusted%' and ";
				break;
			case 'all':
				$condition3 = " ";
				break;
		} 

		$select =  "UNIX_TIMESTAMP(f.`DEF_timestamp`) as `unix_timestamp`, "
		."date_format(f.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`, "
		."a.`MRC|image` as filename, "
		."t.`REF|AcquisitionImageData|image` as imageId, "
		."t.`DEF_id` as targetId, "
		."f.defocus, "
		."f.`stigx`, "
		."f.`stigy`, "
		."f.`min` as fit_residual, "
		."f.status, "
		."f.method ";

		$q="select  "
		.$select
		."from FocuserResultData as f "
		."left join AcquisitionImageTargetData as t  "
		."on (t.`DEF_id` = f.`REF|AcquisitionImageTargetData|target`)  "
		."left join AcquisitionImageData as a on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
		."where "
		.$condition1
		.$condition2
		.$condition3
		." f.`REF|SessionData|session`=".$id." "
		." ";
		return $this->mysql->getSQLResult($q);
	}

	function getMeasurements($label, $axis, $ModelId) {
		$q = " select m.$axis, 
			 sm.mean/(delta/SQRT(m.imagex*m.imagex +  m.imagey*m.imagey)) as norm 
			from StageMeasurementData m 
			left join StageModelMagCalibrationData sm 
			on (sm.axis=m.axis and sm.label = m.label and sm.magnification = m.magnification)  
			left join StageModelCalibrationData s 
			on (s.axis=sm.axis and s.label = sm.label)  
			where m.label='$label' and m.axis='$axis' and s.`DEF_id`='$ModelId'
			and (s.`DEF_timestamp`<= sm.`DEF_timestamp`+30 and s.`DEF_timestamp`>= sm.`DEF_timestamp`-30)";
		return $this->mysql->getSQLResult($q);
	}
	
	function getRelatedIceThicknessFromSession($sessionId, $preset) {
		$q="SELECT "
		."`a`.`MRC|image` as `image`, "
		."`a`.`DEF_id` as imageId, "
		."`hstats`.`mean`, `hstats`.`thickness-mean`, `hstats`.`stdev`, "
		."parent.`MRC|image` as `parent_image`, "
		."`parent`.`DEF_id` as parentId, "
		."`hstatsp`.`mean` as `parent_mean`, `hstatsp`.`thickness-mean` as `parent_thickness-mean`, `hstatsp`.`stdev` as `parent_stdev` "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `AcquisitionImageTargetData` AS `target` "
		."ON (`target`.DEF_id = `a`.`REF|AcquisitionImageTargetData|target`) "
		."LEFT JOIN `AcquisitionImageData` AS `parent` "
		."ON (`parent`.`DEF_id`=`target`.`REF|AcquisitionImageData|image`) "
		."LEFT JOIN `HoleFinderPrefsData` AS `h` "
		."ON (`a`.`DEF_id`=`h`.`REF|AcquisitionImageData|image`) "
		."LEFT JOIN `HoleStatsData` AS `hstats` "
		."ON (`h`.`DEF_id`=`hstats`.`REF|HoleFinderPrefsData|prefs`) "
		."LEFT JOIN `HoleFinderPrefsData` AS `hp` "
		."ON (`parent`.`DEF_id`=`hp`.`REF|AcquisitionImageData|image`) "
		."LEFT JOIN `HoleStatsData` AS `hstatsp` "
		."ON (`hp`.`DEF_id`=`hstatsp`.`REF|HoleFinderPrefsData|prefs`) "
		."LEFT JOIN `AcquisitionImageTargetData` AS `target_parent` "
		."ON (`parent`.`DEF_id`=`target_parent`.`REF|AcquisitionImageData|image` AND `target_parent`.`number`=`target`.`number` AND `target_parent`.`status`='done') "
		."left join CameraEMData cpp "
		."on (target_parent.`REF|CameraEMData|camera`=cpp.`DEF_id`) "
		."LEFT JOIN `PresetData` AS `p` "
		."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."WHERE "
		."`a`.`REF|SessionData|session` = '$sessionId' "
		."AND `p`.`name` ='".$preset."' "
		."AND `hstats`.`mean` IS NOT NULL "
		."AND ABS(floor(target_parent.`delta column`+cpp.`SUBD|dimension|x`/2)-`hstatsp`.`column`) < 2 "
		."AND ABS(floor(target_parent.`delta row`+cpp.`SUBD|dimension|y`/2)-`hstatsp`.`row`) < 2 "
		."group by a.DEF_id";
		return $this->mysql->getSQLResult($q);
	}

	function getIceThicknessFromImage($imageId) {
		$q="SELECT DISTINCT"
			."`h`.`DEF_id`, `h`.`DEF_timestamp`, "
			."`h`.`stats-radius`, `h`.`edge-threshold`, "
			."`h`.`REF|AcquisitionImageData|image`, `h`.`ice-zero-thickness`, "
			."`h`.`edge-lpf-size`, `h`.`threshold-value`, "
			."`h`.`edge-filter-type`, `h`.`lattice-tolerance`, "
			."`h`.`ice-min-thickness`, `h`.`lattice-spacing`, "
			."`h`.`ice-max-stdev`, `h`.`ice-max-thickness`, "
			."`hstats`.`column`, `hstats`.`stdev`, "
			."`hstats`.`mean`, `hstats`.`thickness-mean`, "
			."`hstats`.`REF|HoleFinderPrefsData|prefs`, `hstats`.`row` "
			."FROM "
			."`HoleFinderPrefsData` AS `h` "
			."LEFT JOIN `HoleStatsData` AS `hstats` "
			."ON (`h`.`DEF_id`=`hstats`.`REF|HoleFinderPrefsData|prefs`) "
			."LEFT JOIN `AcquisitionImageData` AS `a` "
			."ON (`a`.`DEF_id`=`h`.`REF|AcquisitionImageData|image`) "
			."WHERE "
			."`h`.`REF|AcquisitionImageData|image` = '$imageId' ";
		return $this->mysql->getSQLResult($q);
	}

	function getIceThicknessPresets($sessionId) {
		$q="SELECT DISTINCT"
			."`p`.`name`, `h`.`REF|SessionData|session` "
			."FROM "
			."`HoleFinderPrefsData` AS `h` "
			."LEFT JOIN `AcquisitionImageData` AS `a` "
			."ON (`a`.`DEF_id`=`h`.`REF|AcquisitionImageData|image`) "
			."LEFT JOIN `PresetData` AS `p` "
			."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
			."WHERE "
			."a.`REF|SessionData|session` = '$sessionId' ";
		return $this->mysql->getSQLResult($q);
	}

	function getImageStats($sessionId="", $preset="") {

		if ($sessionId) {
			$where[] = "`a`.`REF|SessionData|session` = $sessionId";
		}

		if ($preset) {
			$preselect = ", `p`.`name`, `p`.`magnification`";
			$prejoin = "LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`)";
			$where[] = "`p`.`name` = '$preset'"; 
		}

		if ($where)
			$sqlwhere = "WHERE ".implode(' AND ', $where);


		$q="SELECT "
		."UNIX_TIMESTAMP(`s`.`DEF_timestamp`) as `unix_timestamp` , "
		."`s`.`DEF_timestamp` as `timestamp` , `s`.`min`, `s`.`max`, "
		."`s`.`REF|AcquisitionImageData|image` as `imageId`, "
		."`s`.`stdev`, `s`.`mean` "
		.$preselect 
		."FROM "
		."`AcquisitionImageStatsData` AS `s` "
		."LEFT JOIN `AcquisitionImageData` AS `a` "
		."ON (`a`.`DEF_id`=`s`.`REF|AcquisitionImageData|image`) "
		.$prejoin
		.$sqlwhere ;
		return $this->mysql->getSQLResult($q);
	}

	function getSiblingsFromPreset($sessionId, $preset="") {
		if($preset) {
			$sqlpreset="AND `p`.name='$preset' ";
		}
		$q="select a.`DEF_id` as id FROM"
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `PresetData` AS `p` "
		."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."WHERE `a`.`REF|SessionData|session`=$sessionId "
		.$sqlpreset." limit 1";
		list($r) = $this->mysql->getSQLResult($q);
		$imageId = $r['id'];
		return $this->getSiblings($imageId);
	}

	function getSiblings($imageId) {
		$sqlwhere="WHERE a.`DEF_id`=$imageId";
		$q="SELECT "
		."`a`.`DEF_id` as a_id, "
		."`p`.`DEF_id` as a_presetId, "
		."`p`.`name` as a_preset, "
		."`sibling`.`DEF_id` as s_id, "
		."`s_p`.`DEF_id` as s_presetId, "
		."`s_p`.`name` as s_preset "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `PresetData` AS `p` "
		."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."LEFT JOIN `AcquisitionImageTargetData` AS `t` "
		."ON (`t`.`DEF_id`=`a`.`REF|AcquisitionImageTargetData|target`) "
		."LEFT JOIN AcquisitionImageData AS `sibling` "
		."ON (`sibling`.`REF|AcquisitionImageTargetData|target`=`t`.`DEF_id`) "
		."LEFT JOIN `PresetData` AS `s_p` "
		."ON (`s_p`.`DEF_id`=`sibling`.`REF|PresetData|preset`) "
		.$sqlwhere ;
		return $this->mysql->getSQLResult($q);
	}

	function getDefocus($sessionId, $preset="", $stats=false) {
		$wherepreset=($preset) ? "AND `p`.name='$preset'" : "";
		$q="SELECT "
		."UNIX_TIMESTAMP(`a`.`DEF_timestamp`) AS `unix_timestamp`, "
		."`a`.`DEF_timestamp` AS `timestamp`, "
		."`p`.`name`, "
		."`s`.`defocus` "
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `PresetData` AS `p` "
		."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
		."LEFT JOIN `ScopeEMData` AS `s` "
		."ON (`s`.`DEF_id`=`a`.`REF|ScopeEMData|scope`) "
		."WHERE "
		."`a`.`REF|SessionData|session`=$sessionId "
		.$wherepreset;
		if ($stats) {
			return $this->getStats("defocus", $q);
		}
		return $this->mysql->getSQLResult($q);
	}
	
	function getStats($field, $sub_q) {
			$q="select "
				."count(c.`$field`) as `nb`, "
				."min(c.`$field`) as `min`, "
				."max(c.`$field`) as `max`, "
				."avg(c.`$field`) as `avg`, "
				."stddev(c.`$field`) as `stddev` "
				."from ($sub_q) c ";
			list($r)=$this->mysql->getSQLResult($q);
			return $r;
	}

	function getTimingStats($sessionId, $preset="") {
			$sub_q=$this->getTiming($sessionId, $preset="", true);
			$q="select "
				."f.name, count(f.name) as nb, "
				."sum(f.acquisitiontime) as time_in_sec, "
				."sec_to_time(sum(f.acquisitiontime)) as time, "
				."min(f.acquisitiontime) as min, "
				."max(f.acquisitiontime) as max, "
				."avg(f.acquisitiontime) as mean, "
				."stddev(f.acquisitiontime) as stdev "
				."from ($sub_q) f "
				."group by name ";
			return $this->mysql->getSQLResult($q);
	}

	function getPresetTiming($sessionId) {
		$q= "SELECT "
			."UNIX_TIMESTAMP(`a`.`DEF_timestamp`) AS `utime`, "
			."`a`.`DEF_timestamp` AS `timestamp`, "
			."`a`.`filename` AS `filename`, "
			."`a`.`version` AS `version`, "
			."`p`.`name`, "
			."`p`.`magnification` "
			."FROM `AcquisitionImageData` AS `a` "
			."LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id` = `a`.`REF|PresetData|preset`) "
			."WHERE `a`.`REF|SessionData|session` = $sessionId "
			."AND `a`.`version`=0 "
			."ORDER BY `utime` DESC";

		$timearray = $this->mysql->getSQLResult($q);

		foreach($timearray as $i=>$time1) {
			$preset = $time1['name'];
			foreach($timearray as $j=>$vald) {
					$j++;
					if($preset == $timearray[$i+$j]['name']) {
						$tdiff = $time1['utime'] - $timearray[$i+$j]['utime'];
						$diffarray[$preset][] = $tdiff;
						break;
					}
			}
		}

		foreach ((array)$diffarray as $key=>$presetarray) {
			$res1 = array_stats($presetarray);
			$retarray[$key]['name'] = $key;
			$retarray[$key]['time'] = round($res1['mean'],3);
			$retarray[$key]['mean'] = round($res1['mean'],3);
			$retarray[$key]['stdev'] = round($res1['stddev'],3);
			$retarray[$key]['median'] = round($res1['median'],3);
			$retarray[$key]['max'] = round($res1['max'],3);
			$retarray[$key]['min'] = round($res1['min'],3);
		}
		return $retarray;
	}

	function getTiming($sessionId, $preset="", $getquery=false) {
		$datatype=($preset) ? array($preset):$this->getDatatypes($sessionId);
		foreach ($datatype as $preset) {
			$siblings=$this->getSiblingsfrompreset($sessionId, $preset);
			$presetorder=array();
			if ($siblings)
			foreach($siblings as $sibling) {
				$presetorder[]=$sibling['s_preset'];
			}
			$key = array_search($preset, $presetorder);
			$key -=1;
			if ($key<0)
				$key=0;
			$sibling=$siblings[$key];
			$sqlsiblings[]="(`p`.`name` = '".$preset."' AND `s_p`.`name` = '".$sibling['s_preset']."')";
		}

			$where[] = "`a`.`REF|SessionData|session` = $sessionId";
			$where[] = "`sibling`.`version`=0 ";
			$where[] = "`a`.`version`=0 ";
			$where[] = "(".join(" OR ", $sqlsiblings).")";
			// --- quick hack for Square preset --- //
			if ($preset=="sq")
				$where[] = "`a`.`label`='Square' ";

		if ($preset) {
			$preselect = ", `p`.`name`, `p`.`magnification`";
			$prejoin = "LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`)";
			$prejoin .= "LEFT JOIN `PresetData` AS `s_p` ON (`s_p`.`DEF_id`=`sibling`.`REF|PresetData|preset`)";
		}

		if ($where)
			$sqlwhere = "WHERE ".implode(' AND ', $where);

		$sqldiff_a = "TIME_TO_SEC(TIMEDIFF(`a`.`DEF_timestamp`,`t`.`DEF_timestamp`))";
		$sqldiff_s = "TIME_TO_SEC(TIMEDIFF(`sibling`.`DEF_timestamp`,`t`.`DEF_timestamp`))";
		$q="SELECT "
		."UNIX_TIMESTAMP(`a`.`DEF_timestamp`) AS `unix_timestamp`, "
		."`a`.`DEF_timestamp` AS `timestamp`, "
		."`a`.`filename` AS `filename`, "
		."IF ($sqldiff_a > $sqldiff_s, $sqldiff_a-$sqldiff_s, $sqldiff_a) AS acquisitiontime"
		.$preselect 
		."FROM "
		."`AcquisitionImageData` AS `a` "
		."LEFT JOIN `AcquisitionImageTargetData` AS `t` "
		."ON (`t`.`DEF_id`=`a`.`REF|AcquisitionImageTargetData|target`) "
		."LEFT JOIN AcquisitionImageData AS `sibling` "
		."ON (`sibling`.`REF|AcquisitionImageTargetData|target`=`t`.`DEF_id`) "
		.$prejoin
		.$sqlwhere;

		if ($getquery)
			return $q;
		return $this->mysql->getSQLResult($q);
	}

		function getRelatedStats($sessionId, $preset) {
		$q="SELECT "
			."`a`.`DEF_id` as `Id`, "
			."`istats`.`mean`, "
			."`h`.`DEF_id` as `prefId`, "
			."`parent`.`DEF_id` as `parentId`, "
			."`hstats`.`mean` AS `parent mean`, "
			."`hstats`.`thickness-mean` AS `parent thickness-mean` "
			."FROM "
			."`AcquisitionImageData` AS `a` "
			."LEFT JOIN `AcquisitionImageTargetData` AS `target` "
			."ON (`target`.`DEF_id`=`a`.`REF|AcquisitionImageTargetData|target`) "
			."LEFT JOIN `AcquisitionImageData` AS `parent` "
			."ON (`parent`.`DEF_id`=`target`.`REF|AcquisitionImageData|image`) "
			."LEFT JOIN `HoleFinderPrefsData` AS `h` "
			."ON (`target`.`REF|AcquisitionImageData|image`=`h`.`REF|AcquisitionImageData|image`) "
			."LEFT JOIN `HoleStatsData` AS `hstats` "
			."ON (`h`.`DEF_id`=`hstats`.`REF|HoleFinderPrefsData|prefs`) "
			."LEFT JOIN `PresetData` AS `p` "
			."ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) "
			."LEFT JOIN `AcquisitionImageStatsData` AS `istats` "
			."ON (`a`.`DEF_id`=`istats`.`REF|AcquisitionImageData|image`) "
			."WHERE "
			."`a`.`REF|SessionData|session` = '$sessionId' "
			."AND "
			."`parent`.`DEF_id` is not NULL "
			."AND "
			."`p`.`name` = '$preset' "
			."group by `hstats`.`DEF_id`";
		return $this->mysql->getSQLResult($q);
	}

	function getIceThickness($sessionId, $preset) {
		$q = "SELECT "
			."date_format(h.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`, "
			.'`h`.`thickness-mean` '
			.'FROM '
			.'`HoleStatsData` AS `h` '
			.'LEFT JOIN `HoleFinderPrefsData` AS `pref` ON (`pref`.`DEF_id`=`h`.`REF|HoleFinderPrefsData|prefs`) '
			.'LEFT JOIN `AcquisitionImageData` AS `a` ON (`a`.`DEF_id`=`pref`.`REF|AcquisitionImageData|image`) '
			.'LEFT JOIN `PresetData` AS `p` ON (`p`.`DEF_id`=`a`.`REF|PresetData|preset`) '
			.'WHERE '
			."a.`REF|SessionData|session` = '$sessionId' "
			."AND "
			."`p`.`name`='$preset'";
		return $this->mysql->getSQLResult($q);
	}

	function readDataTree(&$arr_node,$Rq,$refname="",$recursive=true) {
		if ($Rq)
		while  ($row  =  mysql_fetch_row($Rq))  {
			for  ($i=0;  $i<mysql_num_fields($Rq);  $i++)  {
				$field = mysql_field_name(($Rq), $i);
				if (ereg("^REF\|",$field)){
					$ref = ereg_replace("^REF\|",'',$field);
					$ref .= '|'.ereg_replace("'","",$row[$i]);
					$refinfo = explode("|", $ref);
					$qref="select * from `$refinfo[0]` where `DEF_id`=".$refinfo[2];
					$Rqref = $this->mysql->SQLQuery($qref);
					if ($recursive)
					$this->readDataTree($arr_node,$Rqref,$refname.'|'.$refinfo[1],false);
				} else if (!ereg("^DEF_|^filename",$field)){
					// filename not a field for image anymore
					$f = $refname.'|'.ereg_replace("SUBD\||ARRAY\||^SEQ\||^MRC\|",'',$field);
					if (strstr($f,'defocus')) 
						$this->formatDefocus($row[$i]); 

					if (strstr($f,'pixelsize')) 
						$this->formatPixelsize($row[$i]); 

					if (strstr($f,'dose')) 
						$this->formatDose($row[$i]);

					$f .= '|'.ereg_replace("'","",$row[$i]);
					if (eregi("\n", $f)) {
						$f = ereg_replace("\n|\r", " ", $f);
					}
					$nodes= explode("|", $f);
					$s="";
					foreach($nodes as $n) {
						$s .="/$n";
						if (!in_array($s, $arr_node)) {
							$arr_node[]=$s;
							continue;
						}
					}
				} else continue;
			}
		}
	}

	function formatDefocus(&$defocus) {
		$defocus = format_micro_number($defocus);
		return $defocus;
	}

	function formatPixelsize(&$pixelsize) {
		$pixelsize = format_nano_number($pixelsize);
		return $pixelsize;
	}

	function formatDose(&$dose) {
		$dose = ($dose) ? number_format(($dose/1e20), 1,'.','').' e<SUP>&ndash;</SUP>/&Aring;<SUP>2</SUP>' : 'none' ;
		return $dose;
	}

	function formatHighTension(&$ht) {
		$ht .= " V";
		return $ht;
	}

	function formatMatrixValue(&$val) {
		$val = (empty($val)) ? $val : format_sci_number($val, 4); 
		return $val;
	}

	function getDataTree($table, $id) {
	/**
	*	Build a javascript tree from a query result
	**/
		// ---  Default node is root
		$arr_node = array('/');
		$jsvar = array();
		$nodeId = array();
		$node = array();
		$nodeparent = array();
		// --- build a tree with '/' as separator

		$q="	select * from $table 
			where  `DEF_id` = \"$id\" ";
		$Rq = $this->mysql->SQLQuery($q);
		$this->readDataTree($arr_node,$Rq); 
//		return $arr_node;
		$tree = "var Tree = new Array; ".$this->crlf;
		while (list($k1, $v1) = each($arr_node)) {
			$jsvar[]="Tree[".($k1-1)."]";
			$nodeId[]=$k1;
			$nodeparent[]=0;
			$node[]=$v1;
		}
		foreach($nodeId as $i) {
			foreach($nodeId as $l) {
				if (ereg ("^".$node[$i].".+", $node[$l])) {
					$nodeparent[$l]=$nodeId[$i];
					continue;
				}
			}
			$file = ereg_replace ($node[$nodeparent[$i]], "", $node[$i]);
			$file = ereg_replace ("^\/","", $file);
			if ($i<>0) 
				$tree .= $jsvar[$i]."=\"".$nodeId[$i]
				."|".$nodeparent[$i]."|".$file."|"
				."javascript:oc($nodeId[$i], $nodeparent[$i])"
				."\";".$this->crlf;
		}
		return $tree;
	}

	function insertBlob($sessionId, $imageId, $filename)  {
		$strfilehex = $this->file2hex($filename);
		$q = 'Insert into `ImageBlob` '
			.'(`sessionId`, `imageId`, `filename`, `imageBlob`) '
			.' Values '
			.'('.$sessionId.', '.$imageId.', "'.$filename.'", '
			.$strfilehex.');'."\n";
		return $q; // $this->mysql->SQLQuery($q, True);
	}

	function file2hex($filename) {
		if (is_file($filename))
			return '0x'.bin2hex(file_get_contents($filename));
		else
			return False;
	}

	function getviewerlog($type, $ip="") {
		if (!$this->mysql->SQLTableExists('viewer_log')) 
			return array();
		$where = array();
		if ($ip) {
			$where[] = "`ip`='".$ip."'";
		}
		$sql_where = ($where) ? "WHERE ".join(' OR ', $where) : "";
		$sql_select = "`l`.`ip`, `l`.`url`, `l`.`sessionId`, `s`.`name`, `s`.`comment`";
		$sql_date = "date_format(max(`l`.`timestamp`), '%d %M %Y') as `timestamp`";
		$sql_order_date = "order by `l`.`timestamp` DESC";
		$sql_nb = "count(`l`.`sessionId`) as `nb`";
		$sql_order_nb = "order by `nb` DESC";
		$sql_limit = " limit 5";
		
		if ($type=="most")

		$q =	"SELECT $sql_select, $sql_nb FROM `viewer_log` AS `l` "
			."LEFT JOIN `SessionData` AS `s` ON (`s`.`DEF_id`=`l`.`sessionId`) "
			.$sql_where
			." group by `l`.`sessionId` "
			.$sql_order_nb.$sql_limit;
		else
		$q =	"SELECT $sql_select, $sql_date FROM `viewer_log` AS `l` "
			."LEFT JOIN `SessionData` AS `s` ON (`s`.`DEF_id`=`l`.`sessionId`) "
			.$sql_where
			." group by `l`.`sessionId` "
			.$sql_order_date.$sql_limit;

		return $this->mysql->getSQLResult($q);
	}

	function getLoggerData($where=array(), $order="", $limit="" ) {
		$field = array ('DEF_id', 'DEF_timestamp','name', 'thread', 'created', 'process', 'module', 'filename', 'levelno', 'pathname', 'lineno', 'message', 'levelname');
		$field = array ('levelname', 'DEF_timestamp','name', 'message' );
		$parameters['field'] = $field;
		$parameters['table'] = 'LoggerRecordData';
		$parameters['where'] = $where;
		$parameters['order'] = $order;
		$parameters['limit'] = $limit;

		return $this->mysql->getData($parameters);
	}

	function setImageDeletionStatus($imageId,$sessionId, $newstatus) {
		$query = 'SELECT status from viewer_del_image '
			.'WHERE `imageId`='.$imageId.' ';
		$results = $this->mysql->getSQLResult($query);
		if ($results) {
			$status = $results[0]['status'];
			# deleted status can not be reverted
			if ($status == 'deleted')
				return;
			$q="delete from `viewer_del_image` where imageId=$imageId ";
			 $this->mysql->SQLQuery($q);
		}
		if ($newstatus != '') {
			//$data['username']=$username;
			$data['imageId']=$imageId;
			$data['sessionId']=$sessionId;
			$data['status']=$newstatus;
			$table='viewer_del_image';
			$this->mysql->SQLInsertIfnotExists($table, $data);
		}
	}

	function getDeletionList($status=1) {
		$query = 'SELECT a.filename, '
			.'s.`image path` as path, '
			.'v.* '
			.' from `AcquisitionImageData` a '
			.'LEFT JOIN `SessionData` s ON a.`REF|SessionData|session`=s.`DEF_id` '
			.'LEFT JOIN `viewer_del_image` v ON v.`imageId`=a.`DEF_id` '
			.'WHERE v.`status`=CONVERT( _utf8 "marked" USING latin1 ) COLLATE latin1_swedish_ci ';
		$results = $this->mysql->getSQLResult($query);
		$filearray = array();
		if ($results) {
			foreach ($results as $r) {
				$filepath = $r['path'].'/'.$r['filename'].'.mrc';
				$r['filepath']=$filepath;
				if (file_exists($filepath) && $status==1) {
					$filearray[] = $r;
				} else {
					if (!file_exists($filepath) && $status==0) 
						$filearray[] = $r;
				}
			}
		}
		return $filearray;
	}	

	function getDeQueuedTargetListIds($sessionId,$qtype) {
		$q="SELECT "
			."dqlist.`REF|ImageTargetListData|list` as doneid "
			."FROM "
			."`DequeuedImageTargetListData` AS `dqlist` "
			."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`dqlist`.`REF|QueueData|queue`) "
			."where "
			."`q`.`REF|SessionData|session`=".$sessionId." "
			."AND "
			."`q`.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE latin1_swedish_ci "
			."";
		return $this->mysql->getSQLResult($q);
	}

	function getTargetListIds($sessionId,$qtype) {
		$q="SELECT "
			."itlist.`DEF_id` as itlid "
			."FROM "
			."`ImageTargetListData` AS `itlist` "
			."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
			."where "
			."`q`.`REF|SessionData|session`=".$sessionId." "
			."AND "
			."`q`.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE latin1_swedish_ci "
			."";
		return $this->mysql->getSQLResult($q);
	}

	function getCountFromTargetListId($targetlistId,$status) {
		$q="SELECT "
			."count(`t`.`DEF_id`) as Count "
			."FROM "
			."`AcquisitionImageTargetData` AS `t` "
			."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
			."WHERE "
			." t.`REF|ImageTargetListData|list` = ".$targetlistId." "
			."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
			."AND t.`status` LIKE CONVERT(_utf8 '".$status."' USING latin1) COLLATE " ."latin1_swedish_ci "
			."";
		$result = $this->mysql->getSQLResult($q);
		if ($result) {
			return $result[0]['Count'];
		} else {
			return;	
		}
	}

	function getCountsFromImageTargetLists($itls) {
		$counts = array();
		foreach ($itls as $itl) {
			$count = $this->getCountFromTargetListId($itl,'new');
			array_push($counts, $count);
		};
		$result = array_reduce($counts,"rsum");
		if (!$result) $result=0;
		return $result;
	}

	function getQueueTimeData($sessionId,$qtype) {
		$q="SELECT "
			."proc.QueueOn as queue,"
			."done.QueueCount as QueueCount, "
			."(done.time-proc.time) as QueueTime "
			."FROM "
			."(SELECT "
			."min(UNIX_timestamp(`t`.`DEF_timestamp`)) as time, "
			."`t`.`REF|AcquisitionImageData|image` as QueueOn, "
			."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
			."FROM "
			."`AcquisitionImageTargetData` AS `t` "
			."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
			."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
			."WHERE "
			." q.`REF|SessionData|session` = ".$sessionId." "
			."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
			."AND t.`status` LIKE CONVERT(_utf8 'processing' USING latin1) COLLATE " ."latin1_swedish_ci "
			."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
			."latin1_swedish_ci "
			."group by t.`REF|AcquisitionImageData|image`) AS proc, "
			."(SELECT "
			."max(UNIX_timestamp(`t`.`DEF_timestamp`)) as time, "
			."`t`.`REF|AcquisitionImageData|image` as QueueOn, "
			."count(`t`.`REF|AcquisitionImageData|image`) as QueueCount "
			."FROM "
			."`AcquisitionImageTargetData` AS `t` "
			."LEFT JOIN `ImageTargetListData` AS `itlist` ON" ."(`itlist`.`DEF_id`=`t`.`REF|ImageTargetListData|list`) "
			."LEFT JOIN `QueueData` AS `q` ON (`q`.`DEF_id`=`itlist`.`REF|QueueData|queue`) "
			."WHERE "
			." q.`REF|SessionData|session` = ".$sessionId." "
			."AND t.`type` LIKE CONVERT(_utf8 'acquisition' USING latin1) COLLATE "."latin1_swedish_ci "
			."AND t.`status` LIKE CONVERT(_utf8 'done' USING latin1) COLLATE "."latin1_swedish_ci "
			."AND q.`label` LIKE CONVERT(_utf8 '".$qtype."' USING latin1) COLLATE "
			."latin1_swedish_ci "
			."group by t.`REF|AcquisitionImageData|image`) AS done "
			."WHERE "
			."proc.QueueOn=done.QueueOn "
			."";
		return $this->mysql->getSQLResult($q);
	}

	function getQueueTypes($sessionId) {
		$q="SELECT "
			."`label` FROM QueueData where `REF|SessionData|session` = ".$sessionId."";
		return $this->mysql->getSQLResult($q);
	}

	function getQueueCountResults($sessionId) {
		$qcounts = array();
		if (!$qtypes = $this->getQueueTypes($sessionId)) {
			return array();
		}
		foreach ((array)$qtypes as $t) {
			$qtype = $t['label'];
			$sqldata_time = $this->getQueueTimeData($sessionId,$qtype);
			$sqldata_dq_list = $this->getDeQueuedTargetListIds($sessionId,$qtype);
			$sqldata_t_list = $this->getTargetListIds($sessionId,$qtype);
			$doneitls = array();
			$allitls = array();
			foreach ($sqldata_dq_list as $d) {
				array_push($doneitls,$d['doneid']);
			};
			foreach ($sqldata_t_list as $d) {
				array_push($allitls,$d['itlid']);
			};
			$activeitls = array_diff($allitls,$doneitls);
			$total_active = $this->getCountsFromImageTargetLists($activeitls);
			$total_new = $this->getCountsFromImageTargetLists($allitls);
			$total_done = 0;
			$total_time = 0;
			$total_done_in_active = 0;
			// Some targets in the active target list may have been processed
			foreach ($activeitls as $d) {
				$total_done_in_active += $this->getCountFromTargetListId($d,'done');
				$total_done_in_active += $this->getCountFromTargetListId($d,'aborted');
			}
			$total_active -= $total_done_in_active;
			// Total Done include only  non-aborted done targets
			foreach ($sqldata_time as $d) {
				$total_done = $total_done + $d['QueueCount'];
				$total_time = $total_time + $d['QueueTime'];
			}
			if ($total_done > 0) {
				$avgtime = ($total_time / $total_done);
				$esttime= ($total_active) * $avgtime;
			} else {
				$avgtime = "unknown";
			}
			$estminute= (int)($esttime / 60);
			$estsecond= (int)($esttime - $estminute * 60);
			if ($total_active)
				$qcounts[] = array($qtype,$total_active,(int)($avgtime),$estminute,$estsecond);
		}
		return $qcounts;
	}

	function getTemplates() {
		$q='select `template-filename` name  from HoleFinderPrefsData where `template-filename` <> "" group by `template-filename` order by DEF_timestamp desc;';
		return $this->mysql->getSQLResult($q);
	}
}

function rsum($v, $w) {
	$v += $w;
	return $v;
}


class MessageLog {

	var $levels = array('ERROR', 'WARNING', 'INFO');
	var $icons = array('ERROR'=>"error.png", 'WARNING'=>"warning.png", 'INFO'=>"info.png");
	var $icon_path = "img/";

	function MessageLog($data) {
		$this->data = $data;
		$content = '<table border="0" cellpadding="1" cellspacing="1">';
		foreach ($data as $row) {
			$content .= "<tr>\n";
			foreach($row as $k=>$v) {
				if ($k=='levelname')
					$v = "<img src='{$this->icon_path}".$this->icons[$v]."'>";
				$content .= "<td>$v</td>";	
			}
			$content .= "</tr>\n";
		}
			$content .= "</table>\n";
		$this->content = $content;
	}

	function display() {
		$html = display_table($title, $this->content);
		return $html;
	}


	// level Time Message

}

$leginondata = new leginondata();

?>
