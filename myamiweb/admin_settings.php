<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once ("inc/leginon.inc");

function displayResult($result,$table,$name) {
	$dlinebreak = '<br/>';
	$linebreak = "\n";
	$filearray = array();
	if ($result) {
		$id = $result['DEF_id'];
		$removekeys = array('DEF_id'=>1,'DEF_timestamp'=>2,'REF|SessionData|session'=>null);
		$result = array_diff_key($result,$removekeys);
		echo '$table = "'.$table.'";'.$dlinebreak.'';
		echo '$data=array();'.$dlinebreak.''; 
		$filearray[] = '$table = "'.$table.'";'.$linebreak.'';
		$filearray[] = '$data=array();'.$linebreak.''; 
		foreach ($result as $key=>$r) {
			if (!is_numeric($r) && !$r) continue;
			if (substr_count($r,'$') == 0) {
				echo '$data["'.$key.'"] = "'.$r.'";'.$dlinebreak.''; 
				$filearray[] = '$data["'.$key.'"] = "'.$r.'";'.$linebreak.''; 
			} else {
				echo '$data["'.$key.'"] = '.$r.';'.$dlinebreak.''; 
				$filearray[] = '$data["'.$key.'"] = '.$r.';'.$linebreak.''; 
			}
		}
		$t = strtolower(substr($table,0,1));
		if ($table !='LowPassFilterSettingsData') {
			echo '$data["REF|SessionData|session"]= $sessionId;'.$dlinebreak.'';
			$filearray[] = '$data["REF|SessionData|session"]= $sessionId;'.$linebreak.'';
		}
		echo '$'.$t.'id'.$id.'=$dbc->SQLInsert($table, $data);'.$dlinebreak.'';
		$filearray[] = '$'.$t.'id'.$id.'=$dbc->SQLInsert($table, $data);'.$linebreak.'';
		echo $dlinebreak;
		$filearray[] = $linebreak;
	}
	return writeFile($filearray);
}

function writeFile($array) {
	global $filename;
	static $state = 'w';
	$fd = fopen($filename, $state);
	foreach($array as $content) {
		fwrite($fd, $content);
	}
	fclose($fd);
	$state = 'a';
}

function fileHeader() {
	global $filename;
	$array = array();
	$linebreak = "\n";
	$array[] = '<?php'.$linebreak;
	$array[] = '$user_id = $leginondata->getAdminUserId();'.$linebreak;
	$array[] = 'if ($user_id < 1) {'.$linebreak;
	$array[] = '	echo "<h3> Error: Create administrator user first </h3>";'.$linebreak;
	$array[] = '	exit();'.$linebreak;
	$array[] = '}'.$linebreak;
	$array[] = '$dbc=$leginondata->mysql;'.$linebreak;
	$array[] = '$q = "insert into `SessionData` (`name`,`REF|UserData|user`,`comment`) "'.$linebreak;
	$array[] = '      . " VALUES "'.$linebreak;
	$array[] = '      . " ( concat(\'importsettings\', DATE_FORMAT(now(), \'%Y%m%d%H%i%s\')), "'.$linebreak;
	$array[] = '			. " ".$user_id.",\'import default\' ) ";'.$linebreak;
	$array[] = '$sessionId = $dbc->SQLQuery($q, true);'.$linebreak;
	$array[] = $linebreak;
	writeFile($array);
}

function fileFooter() {
	$linebreak = "\n";
	$array = array();
	$array[] = '?>'.$linebreak;
	writeFile($array);
}

function displayFirstResult($results,$table,$name) {
	displayResult($results[0],$table,$name);
}
		
function getSettingsById($table,$id) {
  global $leginondata;
	 $sql = 'SELECT * from `'.$table.'` '
			. 'where `DEF_id`='.$id.' ';
	$results = $leginondata->mysql->getSQLResult($sql);
	displayFirstResult($results,$table,$id);
	return $results[0];
}

function getFocusSequenceData($user_id,$table,$name) {
  global $leginondata;
	$sql = 'SELECT a.* from `'.$table.'` a'
        . ' left join `SessionData` s on a.`REF|SessionData|session`=s.`DEF_id`'
        . ' where s.`REF|UserData|user`='.$user_id.' and a.`node name`=\''.$name.'\' '
        . ' ORDER BY a.`DEF_timestamp` DESC'
        . ' LIMIT 0,1';
	$results = $leginondata->mysql->getSQLResult($sql);
	displayFirstResult($results,$table);
	$focusnamesstr = $results[0]['SEQ|sequence'];
	$focusnames = explode("'",$focusnamesstr);
	foreach ($focusnames as $focusname) {
		if (strlen($focusname)>2 && (strcmp($focusname,', u')!=0))  {
			getFocusSettingData($user_id,$name,$focusname);
		}
	}
	return $results[0];
}

function getFocusSettingData($user_id,$nodename,$focusname) {
  global $leginondata;
	$sql = 'SELECT a.* from `FocusSettingData` a'
        . ' left join `SessionData` s on a.`REF|SessionData|session`=s.`DEF_id`'
        . ' where s.`REF|UserData|user`='.$user_id.' and a.`node name`=\''.$nodename.'\' and a.`name`=\''.$focusname.'\''
        . ' ORDER BY a.`DEF_timestamp` DESC'
        . ' LIMIT 0,1';

	displayFirstResult( $leginondata->mysql->getSQLResult($sql),'FocusSettingData');
}

function getSettingsData($user_id,$table,$name) {
  global $leginondata;
	$sql = 'SELECT a.* from `'.$table.'` a'
        . ' left join `SessionData` s on a.`REF|SessionData|session`=s.`DEF_id`'
        . ' where s.`REF|UserData|user`='.$user_id.' and a.`name`=\''.$name.'\' '
        . ' ORDER BY a.`DEF_timestamp` DESC'
        . ' LIMIT 0,1';
	$results = $leginondata->mysql->getSQLResult($sql);
	return $results[0];
}

$nodenames = array(
	'AcquisitionSettingsData'=>array('Grid','Square','Hole','Preview','Exposure','Square Q','Hole Q','Tomography Preview','Final Section','Subsquare','Centered Square','Rough Tissue','Final Raster','Grid Survey','Mid Mag Survey','Reacquisition','High Mag Acquisition'),
	'FocuserSettingsData'=>array('Focus','Z Focus','Tomo Focus','Tomo Z Focus','RCT Focus','Section Z Focus','Grid Focus','Section Focus','Screen Z Focus'),
	'MosaicTargetMakerSettingsData'=>array('Grid Targeting','Grid Targeting Robot','Grid Survey Targeting'),
	'MosaicClickTargetFinderSettingsData'=>array('Square Targeting','Raster Center Targeting','Rough Tissue Targeting','Atlas View'),
	'ClickTargetFinderSettingsData'=>array('Hole Targeting','Tomography Targeting'),
	'HoleFinderSettingsData'=>array('Hole Targeting','Exposure Targeting'),
	'JAHCFinderSettingsData'=>array('Hole Targeting','Exposure Targeting','RCT Targeting','Square Targeting'),
	'RasterFinderSettingsData'=>array('Subsquare Targeting','Exposure Targeting','Square Centering','RCT Targeting','Mid Mag Survey Targeting','High Mag Raster Targeting'),
	'RasterTargetFilterSettingsData'=>array('Raster Generation','Final Raster Targeting'),
	'CenterTargetFilterSettingsData'=>array('Square Target Filtering'),
	'TomographySettingsData'=>array('Tomography'),
	'RCTAcquisitionSettingsData'=>array('RCT'),
	'DTFinderSettingsData'=>array('Tissue Centering'),
	'CorrectorSettingsData'=>array('Correction'),
	'BeamFixerSettingsData'=>array('Fix Beam'),
	'GonModelerSettingsData'=>array('GonioModeling'),
	'BeamTiltImagerSettingsData'=>array('Beam Tilt Image'),
);
$show_tables = false;
$filename = 'test.php';
$lpfids = array();
$bfids = array();
fileHeader();
$aliases = array('edge lpf','template lpf','lpf');
$user_id = $leginondata->getAdminUserId();
$extratables = array('LowPassFilterSettingsData','BlobFinderSettingsData','FocusSequenceData');
//Tables
if ($show_tables) {
	foreach ($extratables as $table) {
		echo $table?></br><?;
	}
	foreach (array_keys($nodenames) as $table) {
		echo $table?></br><?;
	}
}
//Default values
$lpfids = array();
$blobids = array();
foreach (array_keys($nodenames) as $table) {
	foreach ($nodenames[$table] as $name) { 
		$sqldata1 = getSettingsData($user_id,$table,$name);
		if ($table == 'MosaicClickTargetFinderSettingsData' or 'HoleFinderSettingsData' or 'JAHCFinderSettingsData' or 'DTFinderSettingsData') {
			foreach ($aliases as $alias) {
				$lid = $sqldata1['REF|LowPassFilterSettingsData|'.$alias]; 
				if ($lid != 0 ) {
					if (!in_array($lid,$lpfids)) {
						array_push($lpfids,$sqldata1['REF|LowPassFilterSettingsData|'.$alias]);
						$lpfids[$table.'.'.$name.'.'.$alias] = getSettingsById('LowPassFilterSettingsData',$lid);
					}
					$sqldata1['REF|LowPassFilterSettingsData|'.$alias] = '$lid'.$lid; 
				} else {
					$sqldata1 = array_diff_key($sqldata1,array('REF|LowPassFilterSettingsData|'.$alias=>$lid)); 
				}
			}
		}

		if ($table == 'MosaicClickTargetFinderSettingsData') {
			$id = $sqldata1['REF|BlobFinderSettingsData|blobs']; 
			if ($id != 0) {
				if (!in_array($id,$bfids)) {
					array_push($bfids,$sqldata1['REF|BlobFinderSettingsData|blobs']);
					getSettingsById('BlobFinderSettingsData',$id);
					$blobids[$table.'.'.$name.'.'.'blobs'] = $id;
				}
				$sqldata1['REF|BlobFinderSettingsData|blobs'] = '$bid'.$id;
			} else {
					$sqldata1 = array_diff_key($sqldata1,array('REF|BlobFinderSettingsData|blobs'=>$id));
			} 
		}
	displayResult($sqldata1,$table,$name);
	}
}
$focusernodenames = $nodenames['FocuserSettingsData'];
$table = 'FocusSequenceData';
foreach ($focusernodenames as $name) { 
	$sqldata1 = getFocusSequenceData($user_id,$table,$name);
}
fileFooter();
?>
