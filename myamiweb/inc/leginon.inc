<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement see
 *	@licence http://ami.scripps.edu/software/leginon-license
 *	@version $Revision: 1.23 $
 *	@version $Id: leginon.inc,v 1.23 2004-09-10 23:02:36 dfellman Exp $
 */
/**
 *	Query definition to access all leginon data 
 *	
 */

require_once("config.php");
require_once("inc/util.inc");
require_once('inc/xmlapplicationimport.inc');
require_once('inc/mysql.inc');

class leginondata {

	var $crlf = "\n";
	var $format = "sql";
	var $saveasfile = false;
	var $ffttypes = array('focpow', 'fft');
	var $defaulttypes = array('all'=>'all', 'atlas'=>'atlas');
	var $manualtype = 'manual';

	function leginondata() {
		require("config.php");
		$this->mysql = new mysql($HOSTNAME, $DBUSER, $DBPASSWORD, $DATABASE);
		$this->viewer_tables();
	}

	function viewer_tables() {
		$comment_tbl_name = 'viewer_comment';
		$comment_tbl_def  = ''
		.'CREATE TABLE `'.$comment_tbl_name.'` ('
		.'`id` int(11) NOT NULL auto_increment,'
		.'`timestamp` timestamp(14) NOT NULL,'
		.'`sessionId` int(11) NOT NULL default "0",'
		.'`imageId` int(11) NOT NULL default "0",'
		.'`name` text NOT NULL,'
		.'`comment` text NOT NULL,'
		.'PRIMARY KEY  (`id`),'
		.'KEY `timestamp` (`timestamp`),'
		.'KEY `sessionId` (`sessionId`),'
		.'KEY `imageId` (`imageId`)'
		.');';
		if (!$this->mysql->SQLTableExists($comment_tbl_name)) 
			$this->mysql->SQLQuery($comment_tbl_def);

	}

	function query($q) {
		return $this->mysql->SQLQuery($q);
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

	function getSessions($comment="", $projectId=false) {
		$selectcomment = ($comment) ? 
				"if (length(s.comment)>0, concat(s.name,' - ',s.comment), s.name)" : "s.name";
		if (is_numeric($projectId)) {
			$projectjoin = (is_numeric($projectId)) ? 
				"left join project.projectexperiments p on (p.name = s.name) " : "";
			$projectwhere = (is_numeric($projectId)) ? 
				" and p.projectId='$projectId' " : "";
		}

		$q="select distinct(s.DEF_id) as `id`, ".$selectcomment." as `name` "
		."from SessionData s "
		."left join AcquisitionImageData a on (s.`DEF_id` = a.`REF|SessionData|Session`) "
		.$projectjoin
		."where a.`REF|SessionData|Session` <> 'NULL' "
		.$projectwhere
		."order by s.DEF_timestamp DESC ";
		$result = $this->mysql->SQLQuery($q);
		$sessions = array();
		if ($result)
			while($session = mysql_fetch_array($result, MYSQL_ASSOC))
				$sessions[] = $session;
		return $sessions;
	}

	function getSessionInfo($expId) {
		$sessioninfo = array();
		$q="select "
		."s.Name, "
		."s.comment as Purpose, "
		."date_format(s.`DEF_timestamp`, '%Y-%d-%m %T') as `Begin Time`,"
		."date_format(a.`DEF_timestamp`, '%Y-%d-%m %T') as `End Time`, "
		."date_format(s.`DEF_timestamp`, '%Y-%m-%d') as `btime`,"
		."date_format(a.`DEF_timestamp`, '%Y-%m-%d') as `etime`, "
		."sec_to_time((Dayofyear(a.`DEF_timestamp`)-Dayofyear(s.`DEF_timestamp`))*86400-"
		."time_to_sec(s.`DEF_timestamp`)+time_to_sec(a.`DEF_timestamp`)) as `Total Duration`, "
		."s.`Image path`, "
		."i.name as Instrument, "
		."i.description as `Instrument description`, "
		."u.`full name` as User "
		."from `SessionData` s "
		."left join UserData u on (u.`DEF_id`=s.`REF|UserData|user`) "
		."left join InstrumentData i on (i.`DEF_id`=s.`REF|InstrumentData|instrument`) "
		."left join AcquisitionImageData a on (a.`REF|SessionData|session`=s.`DEF_id`) "
		."where s.`DEF_id`='$expId' "
		."order by a.`DEF_timestamp` DESC ";
		$Rsessioninfo = $this->mysql->SQLQuery($q) or die ("No data type found");
		$sessioninfo = mysql_fetch_array($Rsessioninfo, MYSQL_ASSOC); 
		return $sessioninfo;
	}

	function getSummary($expId) {
		$summary = array();
		$q="select p.name, count(a.`DEF_id`) as nb from AcquisitionImageData a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			." where a.`REF|SessionData|session` = '$expId' "
			." group by p.name ";
		$Rsummary = $this->mysql->SQLQuery($q) or die ("No data type found");
		$ndata=mysql_num_rows($Rsummary);
		while ($row = mysql_fetch_array($Rsummary)) 
			$summary[]= array('name'=>$row['name'], 'nb'=>$row['nb']); 
		return $summary;
	}

	function getDatatypes($expId) {
		$q="select distinct name FROM AcquisitionImageData a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			." where a.`REF|SessionData|session` = '$expId'";
		$Rdatatype = $this->mysql->SQLQuery($q) or die ("No data type found");
		$ndata=mysql_num_rows($Rdatatype);
		while ($row = mysql_fetch_row($Rdatatype)) 
			if ($row[0])
				$datatypes[$row[0]]=$row[0]; 
			else
				$datatypes[$this->manualtype]=$this->manualtype; 
		return $datatypes;
	}

	function getAllDatatypes($sessionId) {
		$defaulttypes = $this->defaulttypes;
		$types = $this->getDatatypes($sessionId);
		return array_merge($defaulttypes, $types);
	}

	function getFilenames($expId, $name="", $table="AcquisitionImageData") {
		$name = (in_array($name, $this->defaulttypes)) ? "" : $name;
		if (in_array($name, $this->ffttypes)) {
		$q = "select a.`DEF_id` as `id`, f.`MRC|Image` as `name` "
		    ." from `$table` a "
		    ." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
		    ." left join AcquisitionFFTData f on (f.`REF|AcquisitionImageData|source`=a.`DEF_id`) "
		    ." where a.`REF|SessionData|session`='$expId' "
		    ." and f.`MRC|Image`<>'NULL' "
		    ." order by a.`DEF_id` DESC ";
		} else {
		$q = "select a.`DEF_id` as `id`, a.`MRC|Image` as `name` "
		    ." from `$table` a "
		    ." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
		    ." where a.`REF|SessionData|session`='$expId' ";
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

	function getPresets($fileId, $presets=array('mag','defocus','pixelsize','dose')) {
		if (!is_array($presets) || !$fileId)
			return false;
		if (in_array('mag', $presets))
			$sqlselect[]="scope.magnification as mag";
		if (in_array('defocus', $presets))
			$sqlselect[]="scope.defocus";
		if (in_array('pixelsize', $presets))
			$sqlselect[]="pi.pixelsize";
		if (in_array('dose', $presets))
			$sqlselect[]="p.dose";
		$sqlselectstr=implode(', ',$sqlselect);
		$q='
		select '.$sqlselectstr.'
		from AcquisitionImageData a , PixelSizeCalibrationData pi 
			left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) 
			left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) 
			left join SessionData s2 on (s2.`DEF_id`=pi.`REF|SessionData|session`) 
			left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) 
		where s1.`REF|InstrumentData|instrument`=s2.`REF|InstrumentData|instrument`
				and scope.magnification = pi.magnification 
				and a.`DEF_id` = '.$fileId.'
		order by pi.`DEF_timestamp` desc limit 1
		';
		$Rpreset=$this->mysql->SQLQuery($q);
		return mysql_fetch_array($Rpreset, MYSQL_ASSOC);
	}

	function formatPath($path) {
		# temporary here
		$npath = eregi_replace('^.*colossus.amishare','/ami/amishare',$path);
		$npath = eregi_replace('^Z:','/ami/amishare',$path);
		$npath = ereg_replace('[\\]','/',$npath);
		$npath = ereg("/$", $npath) ? $npath : $npath."/";
		return $npath;
	}

	function getLastFilenameId($sessionId) {
		$q = "select `DEF_id` as `id` from AcquisitionImageData "
			." where `REF|SessionData|session`='$sessionId' "
			." order by `DEF_timestamp` desc limit 1 ";
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo[id];
	} 

	function getImagePath($sessionId) {
		$q = "select `image path` as path from `SessionData` "
		    ." where `DEF_id`='$sessionId' ";
		$Rpath=$this->mysql->SQLQuery($q);
		$path = mysql_fetch_array($Rpath);
		return $this->formatPath($path[path]);
	}

	function findField($name) {
	    $result = $this->mysql->SQLQuery("SHOW TABLES");
	    while($row = mysql_fetch_row($result))
		$tables[] = $row[0];
	}

	function getId($fields=array(), $table = "AcquisitionImageData", $id="DEF_id") {
		$acq_fields = $this->mysql->getFields($table); 
		$where = array();
		
		foreach ($fields as $k=>$f) {
			if (!in_array($k, $acq_fields))
				return false;
			$where[] = "`$k`='".addslashes($f)."'";
		}
		if (empty($where))
			return false;
		$wherestr = implode(' and ', $where);
		$q = 'select `'.$id.'` as id from `'.$table.'`'
			.' where '.$wherestr;
		$R = $this->mysql->SQLQuery($q);
		$ids = array();
		while ($r = mysql_fetch_array($R))
			$ids[] = $r[id];

		if (count($ids)==1)
			return $ids[0];
		else
			return $ids;
	}

	function getDataInfo($table, $id, $fields=array()) {
		if (!$table)
			return false;
		$data = array();
		$str_fields = '*';

		$acq_fields = $this->mysql->getFields($table); 
		if (is_array($fields) && !empty($fields)) {	
			$formated_fields = array();
			foreach ($fields as $f) {
				if (!in_array($f, $acq_fields))
					return false;
				$formated_fields[] = "`$f`";
			}
			$str_fields = implode(', ', $formated_fields);
		}
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
		return $fileInfo[filename];
	}

	function getMosaicImages($id) {
		$listId = $this->getId(
				array('REF|AcquisitionImageData|image' => $id),
				'MosaicTileData',
				'REF|ImageListData|list'
				);
		return $this->getId(
				array( 'REF|ImageListData|list'  => $listId),
				'MosaicTileData',
				'REF|AcquisitionImageData|image'
				);
	}

	function getFilename($id, $table="AcquisitionImageData") {
		$q = "select `MRC|image` as filename from `$table` where "
		    ." `DEF_Id` =\"$id\"  ";
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo[filename];
	}

	function getImageMatrixCalibration($imgId, $type='image shift') {
		$q = "select "
			."mcal.`ARRAY|matrix|1_1` as `a11`,"
			."mcal.`ARRAY|matrix|1_2` as `a12`,"
			."mcal.`ARRAY|matrix|2_1` as `a21`,"
			."mcal.`ARRAY|matrix|2_2` as `a22`,"
			."mcal.`type` as `type`,"
			."atan2(mcal.`ARRAY|matrix|1_1`, mcal.`ARRAY|matrix|2_1`) as angle "
			."from AcquisitionImageData a, MatrixCalibrationData mcal "
			."left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) "
			."left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) "
			."left join SessionData s2 on (s2.`DEF_id`=mcal.`REF|SessionData|session`) "
			."where "
			."s1.`REF|InstrumentData|instrument`=s2.`REF|InstrumentData|instrument` "
			."and "
			."scope.magnification = mcal.magnification "
			."and "
			."mcal.`type`='".$type."' "
			."and "
			."mcal.`DEF_timestamp` < a.`DEF_timestamp` "
			."and "
			."a.`DEF_id` ='".$imgId."' "; 

		$Rparent = $this->mysql->SQLQuery($q);
		$parent = mysql_fetch_array($Rparent);
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
		$types = array();
		$q="select "
		."distinct mcal.`type` "
		."from MatrixCalibrationData mcal";
		$Rparent = $this->mysql->SQLQuery($q);
		while ($t= mysql_fetch_array($Rparent)) 
			$types[] = $t[type];
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

		$Rparent = $this->mysql->SQLQuery($q);
		$parent = mysql_fetch_array($Rparent);
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
		$Rparent = $this->mysql->SQLQuery($q);
		$parent = mysql_fetch_array($Rparent, MYSQL_ASSOC);
		return $parent;
	}

	function getImageInfo($imgId) {
		// --- check if image as a parent
		$parentinfo = $this->getParent($imgId);
		$parentId = ($parentinfo['parentId']) ? $parentinfo['parentId'] : false;
		$parentselect = "";
		$parentjoin = "";
		$gridtable = $this->mysql->isTable('GridData');
		$gridselect = ($gridtable) ?
			"grid.`grid ID` as gridId, " : "";
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
			."((c.`SUBD|binning|y`* sqrt(c.`SUBD|dimension|x`*c.`SUBD|dimension|x`  "
			."+ c.`SUBD|dimension|y`*c.`SUBD|dimension|y`) * pi.pixelsize) /  "
			."(cp.`SUBD|binning|y`* ppi.pixelsize)) as targetdiam,  ";
			$parentjoin = ""
			."left join AcquisitionImageData parent "
			."on (parent.`DEF_id`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."left join ScopeEMData pscope on (pscope.`DEF_id`=parent.`REF|ScopeEMData|scope`) "
			."left join SessionData ps1 on (ps1.`DEF_id`=parent.`REF|SessionData|session`) "
			."left join SessionData ps2 on (ps2.`DEF_id`=ppi.`REF|SessionData|session`) "
			."cross join PixelSizeCalibrationData ppi on "
			."(ps1.`REF|InstrumentData|instrument`=ps2.`REF|InstrumentData|instrument` and "
			."pscope.magnification = ppi.magnification) ";
		}
		$q = "select "
			.$gridselect
			.$parentselect
			."a.`DEF_id` as imageId, "
			."date_format(a.`DEF_timestamp`, '%Y-%d-%m %T') as `timestamp`,"
			."a.`REF|SessionData|session` as `sessionId`,"
			."a.`MRC|image` as filename, "
			."p.`name` as `preset`, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy, "
			."c.`SUBD|binning|y` as binning, "
			."c.`exposure time`, "
			."pi.pixelsize as pixelsize, "
			."scope.magnification, "
			."scope.defocus, "
			."scope.`high tension`, "
			."parenttarget.`delta column`, "
			."parenttarget.`delta row`, "
			."floor(parenttarget.`delta column`+cp.`SUBD|dimension|x`/2) as targetx, "
			."floor(parenttarget.`delta row`+cp.`SUBD|dimension|y`/2) as targety "
			."from AcquisitionImageData a "
			."left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) "
			."left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) "
			."left join SessionData s2 on (s2.`DEF_id`=pi.`REF|SessionData|session`) "
			."left join CameraEMData c on (a.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			."left join AcquisitionImageTargetData parenttarget "
			."on (parenttarget.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) "
			."left join CameraEMData cp "
			."on (parenttarget.`REF|CameraEMData|camera`=cp.`DEF_id`) "
			.$gridjoin
			."cross join PixelSizeCalibrationData pi on "
			."(s1.`REF|InstrumentData|instrument`=s2.`REF|InstrumentData|instrument` and "
			."scope.magnification = pi.magnification) "
			.$parentjoin
			."where "
			."a.`DEF_id` ='".$imgId."' "; 

		$Rimageinfo = $this->mysql->SQLQuery($q);
		$imageinfo = mysql_fetch_array($Rimageinfo, MYSQL_ASSOC);
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
		return $gridinfo[gridId];
	}

	function getImageRelation($imgId, $preset='', $matchtargetnb=true) {
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

			// echo $q;

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
			if ($relation[siblingpreset]==$preset && $relation[parentId]) {
				$newimage[id] = $relation[siblingimageId];
				$newimage[preset] = $relation[siblingpreset];
				break;
			}
		}
		return $newimage;
	}

	function findImage($imgId, $preset="") {
	// --- find an image related to an image Id and a preset
		$newimage=array();
		$imageinfo = $this->getImageInfo($imgId);
		if (	empty($preset)
			|| $imageinfo[preset]==$preset 
			|| in_array($preset, $this->defaulttypes)
			|| $preset == $this->manualtype
		) { 
			$newimage[id] = $imageinfo[imageId];
			$newimage[preset] = $imageinfo[preset];
			return $newimage;
		}

		// --- search for a parent
		$parentId = $imgId;
		while ($parentId) {
			$parent = $this->getParent($parentId);
			$parentId = $parent[parentId];
			$parentpreset=$parent[parentpreset];
			if ($parentpreset==$preset) {
				$newimage[id] = $parent[parentId];
				$newimage[preset] = $parent[parentpreset];
				$newimage[childid] = $parent[imageId];
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

	function getImageTargets($imgId) {
		$q =	" select "
			."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
			."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy, "
			."child.`DEF_id` as childId, "
			."t.`DEF_id` as tId, "
			."t.`version` as tversion, "
			."t.`number` as tnumber "
			."from AcquisitionImageData as a "
			."left join AcquisitionImageTargetData as t "
			."on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
			."left join CameraEMData c on (t.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."left join AcquisitionImageData as child "
			."on (child.`REF|AcquisitionImageTargetData|target`=t.`DEF_id`) "
			."where "
			."t.`type`='acquisition' and "
			."a.`DEF_id`='".$imgId."' "
			."order by t.`tnumber` ";

		$Rtargets = $this->mysql->SQLQuery($q);
		$targets= array();
		while ($target = mysql_fetch_array($Rtargets, MYSQL_ASSOC))
			$targets[] = $target;
		return $targets;
		#return $this->matchTargets($targets);
	}

	function matchVersionTargets($targets) {
		$grouptargets = array();
		$ntargets = array();
		if (!is_array($targets)) 
			return false;

		foreach ($targets as $target)
			$grouptargets[$target[tnumber]][] = $target;

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

			if (!$target[childId]) {
				$tx = $target[x];
				$ty = $target[y];
				continue;
			}

			if ($tx)
				$target[x] = $tx;
			if ($ty)
				$target[y] = $ty;

			$ntargets[] = $target;
		}
		return true;
	}

	function asChildId($targets) {
		$ret = false;
		foreach ($targets as $target)
			if ($target[childId]) {
				$ret = true;
				break;
			}
		return $ret;
	}

	function getImageFocusTargets($imgId) {
		$q =	" select "
			."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
			."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy, "
			."t.`DEF_id` as tId, "
			."t.`version` as tversion "
			."from AcquisitionImageData as a "
			."left join AcquisitionImageTargetData as t "
			."on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
			."left join CameraEMData c on (t.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."where (t.`delta row` or t.`delta column`)<>'NULL' and "
			."t.`version`='0' and "
			."t.`type`='focus' and "
			."a.`DEF_id`='".$imgId."'";
		$Rtargets = $this->mysql->SQLQuery($q);
		$targets= array();
		while ($target = mysql_fetch_array($Rtargets, MYSQL_ASSOC))
			$targets[] = $target;
		return $targets;
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
	    $result = $this->mysql->SQLQuery("SHOW KEYS FROM $table") or mysql_die();
	    while($row = mysql_fetch_array($result))
	    {
	        $kname = ($row['Key_name'] == "PRIMARY") ? 
				$row['Key_name'] : $this->addBackquotes($row['Key_name']);
	        if(($kname != "PRIMARY") && ($row['Non_unique'] == 0))
	            $kname="UNIQUE|$kname";
	         if(!isset($index[$kname]))
	             $index[$kname] = array();
	         $index[$kname][] = $this->addBackquotes($row['Column_name']);
	    }
	
	    while(list($x, $columns) = @each($index))
	    {
	         $schema_create .= "    <key>";
	         if($x == "PRIMARY")
	             $schema_create .= "PRIMARY KEY (" . implode($columns, ", ") . ")";
	         elseif (substr($x,0,6) == "UNIQUE")
	            $schema_create .= "UNIQUE ".substr($x,7)." (" . implode($columns, ", ") . ")";
	         else
	            $schema_create .= "KEY ".$x." (" . implode($columns, ", ") . ")";
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
	    $crlf = $this->crlf;
            $local_query = 'SHOW COLUMNS FROM ' . $table ;
            $result      = $this->mysql->SQLQuery($local_query); 
	    for ($i = 0; $row = mysql_fetch_array($result, MYSQL_ASSOC); $i++) 
		$columns[$i] = $row['Field'];
	    $columns_cnt     = count($columns);
	    unset($i);
	    mysql_free_result($result);

	    $local_query = 'SELECT * FROM ' . $table . $add_query;
	    $result      = $this->mysql->SQLQuery($local_query);
	    $buffer      .= '  <!-- ' . $GLOBALS['strTable'] . ' ' . $table . ' -->' . $crlf;
	    while ($record = mysql_fetch_array($result, MYSQL_ASSOC)) {
		$buffer         .= '    <sqltable name="' . $table . '" >' . $crlf;
		for ($i = 0; $i < $columns_cnt; $i++) {
			if (!function_exists('is_null') || !is_null($record[$columns[$i]])) {
			$buffer .= '        <field name="' . $columns[$i] . '" >' . htmlspecialchars($record[$columns[$i]])
			.  '</field>' . $crlf;
			}
		}
		$buffer         .= '    </sqltable>' . $crlf;
	    }
	    mysql_free_result($result);
	    return $buffer;
	}

	function dumpDeleteSession($sessionId) {
	    $result = $this->mysql->SQLQuery("SHOW TABLES");
	    while($row = mysql_fetch_row($result))
		$tables[] = $row[0];
	    // --- Get Reference Ids
	    $where = " `DEF_Id` = $sessionId ";
	    $Rinfo = $this->mysql->SQLQuery("SELECT date_format(DEF_timestamp,'%m/%d/%Y') as date, `name` from SessionData where $where");
	    $result = mysql_fetch_array($Rinfo);
	    $name = $result['name'];
	    $date = $result['date'];

	    $ref_tables[]='SessionData';
	    foreach($tables as $table) {
	    	$result = $this->mysql->SQLQuery("SHOW FIELDS FROM $table"); 
	    	while($row = mysql_fetch_array($result))
			if (ereg("^REF\|SessionData", $row[Field]))
				if(!in_array($table,$ref_tables))
					$ref_tables[]=$table;

	    }

	    $queries = array();
	    foreach($ref_tables as $table) {
		$queries[] = "delete from `$table` where $where ";
	    }
	    $this->mysql->SQLQueries($queries);
	}

	function dumpApplicationData($applicationId) {
	    $crlf = $this->crlf;
	    $format = $this->format;
	    $saveasfile = $this->saveasfile;
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
	    	$result = $this->mysql->SQLQuery("SHOW FIELDS FROM $table"); 
	    	while($row = mysql_fetch_array($result))
			if (ereg("^REF\|$tbl_applicationdata", $row[Field]))
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

	    } else {
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

	    if($format=="xml")
	    	$this->buildXML($table_def, $buffer, &$dump);
	    else {
		$dump .= $table_def;
		$dump .= $buffer;
	    }

	    if ($saveasfile) {
		$filename = $name."_".$version;
		if ($format == 'xml') {
			$ext       = 'xml';
		} else {
			$ext       = 'sql';
		}
			$mime_type = (USR_BROWSER_AGENT == 'MSIE' || USR_BROWSER_AGENT == 'OPERA')
			? 'application/octetstream'
			: 'application/octet-stream';

		$now = gmdate('D, d M Y H:i:s') . ' GMT';

		header('Content-Type: ' . $mime_type);
		header('Expires: ' . $now);
		if (USR_BROWSER_AGENT == 'MSIE') {
			header('Content-Disposition: inline; filename="' . $filename . '.' . $ext . '"');
			header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
			header('Pragma: public');
		} else {
			header('Content-Disposition: attachment; filename="' . $filename . '.' . $ext . '"');
			header('Pragma: no-cache');
		}
		echo $dump;

	    } else {
		echo "<div><pre>";
		echo htmlspecialchars($dump);
		echo "</pre></div>";
	    }

	}

	function importApplication($filename) {
		$app = new XMLApplicationImport($filename);
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
		$applicationinfo = $fieldvalues[ApplicationData];
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
			.str_replace('"', '', $applicationinfo[name])
			."-"
			.str_replace('"', '', $applicationinfo[version])
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
	   	 . " </data>" . $crlf
	   	 . "</applicationdump>" . $crlf;
	}

	function dumpFormat($format, $file="") {
		$this->format=$format;
		$this->saveasfile = (empty($file)) ? false : true;
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

	function getGoniometerModelId($label, $axis) {
		$q="SELECT `DEF_id` from StageModelCalibrationData where label=\"$label\" and axis=\"$axis\" order by `DEF_timestamp` DESC limit 1";
		$result = $this->mysql->SQLQuery($q);
		$row = mysql_fetch_array($result);
		return $row[DEF_id];
	}

	function getGoniometerModel($Id) {
		$q="SELECT * from StageModelCalibrationData where `DEF_id` = \"$Id\"";
		$result = $this->mysql->SQLQuery($q);
		$row = mysql_fetch_array($result, MYSQL_ASSOC);
		return $row;
	}
	
	function getDriftData($Id) {
		$driftdata=array();
		$q="SELECT UNIX_TIMESTAMP(`DEF_timestamp`) as timestamp, rowmeters, colmeters, `interval` from DriftData where `REF|SessionData|session` = '".$Id."' order by `DEF_timestamp` ASC";
		$result = $this->mysql->SQLQuery($q);
		while ($row= mysql_fetch_array($result, MYSQL_ASSOC))
			$driftdata[] = $row;
		return $driftdata;
	}

	function getMeasurements($label, $axis) {
		$q = " select m.$axis, 
			 s.mean/(delta/SQRT(m.imagex*m.imagex +  m.imagey*m.imagey)) as norm 
			from StageMeasurementData m 
			left join StageModelMagCalibrationData s 
			on (s.axis=m.axis and s.label = m.label and s.magnification = m.magnification)  
			where m.label='$label' and m.axis='$axis'";
		$result = $this->mysql->SQLQuery($q);
		$measurements= array();
		while ($measurement = mysql_fetch_array($result, MYSQL_ASSOC))
			$measurements[] = $measurement;
		return $measurements;
	}

	function readDataTree(&$arr_node,$Rq,$refname="",$recursive=true) {
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
		$dose = ($dose) ? number_format(($dose/1e20), 4,'.','').' e¯/Å²' : 'none' ;
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

}

$leginondata = new leginondata();

?>
