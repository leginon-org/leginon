<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once("config.php");
require_once("inc/util.inc");
require_once('inc/xmlapplicationimport.inc');
require_once('inc/mysql.inc');

class leginondata {

	var $format = "sql";
	var $saveasfile = false;
	var $crlf = "\n";

	function leginondata() {
		require("config.php");
		$this->mysql = new mysql($HOSTNAME, $DBUSER, $DBPASSWORD, $DATABASE);
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

	function getSessions() {
		$q = "select distinct(s.DEF_id), s.name from AcquisitionImageData a left join SessionData s on (s.`DEF_id` = a.`REF|SessionData|Session`) order by s.DEF_timestamp DESC ";
		$result = $this->mysql->SQLQuery($q);
		$ids = array();
		$sessions = array();
		if ($result)
			while($row = mysql_fetch_array($result))
			{
				$ids[] = $row["DEF_id"];
				$sessions[] = $row["name"];
			}
		return array('ids'=>$ids,'sessions'=>$sessions);
	}

	function getDatatypes($expId) {
		$datatypes = array();
		// select a.`MRC|Image`, concat(a.label,'->',p.name) as name FROM AcquisitionImageData a left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) where a.`REF|SessionData|session`=838 and a.label="exp";
		$q="select distinct name FROM AcquisitionImageData a "
			." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
			." where a.`REF|SessionData|session` = '$expId'";
		$Rdatatype = $this->mysql->SQLQuery($q) or die ("No data type found");
		$ndata=mysql_num_rows($Rdatatype);
		while ($row = mysql_fetch_row($Rdatatype)) 
			$datatype[]=$row[0]; 
		return $datatype;
	}

	function getFilenames($expId, $name, $table="AcquisitionImageData") {
		$q = "select a.`DEF_id`, a.`MRC|Image` as filename "
		    ." from `$table` a "
		    ." left join PresetData p on (p.DEF_id=a.`REF|PresetData|preset`) "
		    ." where a.`REF|SessionData|session`='$expId' "
		    ." and p.name = '$name' "
		    ." order by a.`DEF_id` DESC ";
		$Rfile=$this->mysql->SQLQuery($q);
		return $Rfile;
	}

	function getPresets($fileId, $presets) {
		if (!is_array($presets))
			return false;
		if (in_array('mag', $presets))
			$sqlselect[]="scope.magnification as mag";
		if (in_array('defocus', $presets))
			$sqlselect[]="scope.defocus";
		if (in_array('pixelsize', $presets))
			$sqlselect[]="pi.pixelsize";
		$sqlselectstr=implode(', ',$sqlselect);
		$q='
		select '.$sqlselectstr.'
		from AcquisitionImageData a , PixelSizeCalibrationData pi 
			left join ScopeEMData scope on (scope.`DEF_id`=a.`REF|ScopeEMData|scope`) 
			left join SessionData s1 on (s1.`DEF_id`=a.`REF|SessionData|session`) 
			left join SessionData s2 on (s2.`DEF_id`=pi.`REF|SessionData|session`) 
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

	function getImagePath($sessionId){
		$q = "select `image path` as path from `SessionData` "
		    ." where `DEF_id`='$sessionId' ";
		$Rpath=$this->mysql->SQLQuery($q);
		$path = mysql_fetch_array($Rpath);
		return $this->formatPath($path[path]);
	}

	function getFilename($id, $table="AcquisitionImageData") {
		$q = "select `MRC|image` as filename from `$table` where "
		    ." `DEF_Id` =\"$id\"  ";
		$RfileInfo = $this->mysql->SQLQuery($q);
		$fileInfo = mysql_fetch_array($RfileInfo);
		return $fileInfo[filename];
	}

	function getParentImageInfo($imgId) {
		$q = "select  parent.`DEF_id` as parentId, "
			."floor(parenttarget.`delta column`+c.`SUBD|dimension|x`/2) as targetx, "
			."floor(parenttarget.`delta row`+c.`SUBD|dimension|y`/2) as targety, "
			."parent.`MRC|image` as parentimage, "
			."pp.`name` as parentpreset, "
			."parenttarget.`type` as parenttype, "
			."p.`name` as inputpreset, "
			."a.`DEF_id` as imageId, "
			."a.`MRC|image` as image "
			."from "
			."AcquisitionImageData a "
			."left join PresetData p "
			."on (p.DEF_id=a.`REF|PresetData|preset`) "
			."left join AcquisitionImageTargetData parenttarget "
			."on (parenttarget.`DEF_id`=a.`REF|AcquisitionImageTargetData|target`) "
			."left join AcquisitionImageData parent "
			."on (parent.`DEF_id`=parenttarget.`REF|AcquisitionImageData|image`) "
			."left join PresetData pp "
			."on (pp.DEF_id=parent.`REF|PresetData|preset`) "
			."left join CameraEMData c "
			."on (parenttarget.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."where a.`DEF_id` ='".$imgId."' "; 
		$Rparent = $this->mysql->SQLQuery($q);
		$parent = mysql_fetch_array($Rparent);
		return $parent;
	}

	function getParent($imgId, $preset) {
		$newparent=array();
		$parentId = $imgId;

		// -- check if the current preset correspond to current image Id
		$parent = $this->getParentImageInfo($parentId);
		if ($parent[inputpreset]==$preset) 
			return array	(	parentId=>$imgId,
						parentpreset=>$preset,
					);
		while (!empty($parentId)) {
			$parent = $this->getParentImageInfo($parentId);
			$parentId=$parent[parentId];
			$parentpreset=$parent[parentpreset];
			if ($parentpreset==$preset) {
				$newparent = $parent;
				break;
			}
		}
		return $newparent;
	}

	function getImageTargets($imgId) {
		$q =	" select "
			."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
			."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy "
			."from AcquisitionImageData as a "
			."left join AcquisitionImageTargetData as t "
			."on (a.`DEF_id` = t.`REF|AcquisitionImageData|image`) "
			."left join CameraEMData c on (t.`REF|CameraEMData|camera`=c.`DEF_id`) "
			."where (t.`delta row` or t.`delta column`)<>'NULL' and "
			."t.`version`='0' and "
			."t.`type`='acquisition' and "
			."a.`DEF_id`='".$imgId."'";
		$Rtargets = $this->mysql->SQLQuery($q);
		$targets= array();
		while ($target = mysql_fetch_array($Rtargets, MYSQL_ASSOC))
			$targets[] = $target;
		return $targets;
	}

	function getImageFocusTargets($imgId) {
		$q =	" select "
			."floor(t.`delta column`+c.`SUBD|dimension|x`/2) as x, "
			."floor(t.`delta row`+c.`SUBD|dimension|y`/2) as y, "
			."c.`SUBD|dimension|x` as dimx, "
			."c.`SUBD|dimension|y` as dimy "
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
	        $kname=$row['Key_name'];
	        if(($kname != "PRIMARY") && ($row['Non_unique'] == 0))
	            $kname="UNIQUE|$kname";
	         if(!isset($index[$kname]))
	             $index[$kname] = array();
	         $index[$kname][] = $row['Column_name'];
	    }
	
	    while(list($x, $columns) = @each($index))
	    {
	         $schema_create .= "    <key>";
	         if($x == "PRIMARY")
	             $schema_create .= "PRIMARY KEY (" . implode($columns, ", ") . ")";
	         elseif (substr($x,0,6) == "UNIQUE")
	            $schema_create .= "UNIQUE ".substr($x,7)." (" . implode($columns, ", ") . ")";
	         else
	            $schema_create .= "KEY $x (" . implode($columns, ", ") . ")";
	         $schema_create .= "</key>$crlf";
	    }
	
	    $schema_create .= "  </sqltable>$crlf";
	    return (stripslashes($schema_create));
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

	function getXMLData2($table, &$buffer, $where="") {
	    $add_query = empty($where) ? "" : " WHERE $where";
	    $crlf = $this->crlf;
            $local_query = 'SHOW COLUMNS FROM ' . $table ;
            $result      = $this->mysql->SQLQuery($local_query); 
	    for ($i = 0; $row = mysql_fetch_array($result, MYSQL_ASSOC); $i++) {
		$field = $row['Field'];
		if  (!eregi("^REF\||^DEF_id|^SEQ",$field))
			$columns[$i] = $field;
	}
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

	function dumpApplicationData2($applicationId) {
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
		$getdata="getXMLData2";
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

	    //eval('$table_def='.'$this->'.$getdefinition.'($tbl_applicationdata);');
	    $table_def='';
	    foreach($ref_tables as $table) {
	    	//eval('$table_def.='.'$this->'.$getdefinition.'($table);');
	    }
	    


	    //eval('$this->'.$getdata.'($tbl_applicationdata, $buffer, $where);');

	    $where = " `REF|ApplicationData|application` = $applicationId";
	    foreach($ref_tables as $table) { 
		    eval('$this->'.$getdata.'($table, $buffer, $where);');
		}

	    if($format=="xml")
	    	$this->buildXML($table_def, $buffer, &$dump);
	    else {
//		$dump .= $table_def;
		$dump .= $buffer;
	    }
		echo "<div><pre>";
		echo htmlspecialchars($dump);
		echo "</pre></div>";

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

	function getDataTree($table, $id) {
	/**
	*	Build a javascript tree from a query result
	**/
		// ---  Default node is root
		$arr_node = array('/');
		// --- build a tree with '/' as separator

		$q="	select * from $table 
			where  `DEF_id` = \"$id\" ";
		$Rq = $this->mysql->SQLQuery($q);
		$this->readDataTree($arr_node,$Rq); 
		return $arr_node;
	}

}

$leginondata = new leginondata();


?>
