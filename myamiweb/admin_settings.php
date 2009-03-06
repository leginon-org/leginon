<html><head><title>Administrator Settings</title>
<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

include ("inc/jpgraph.php");
include ("inc/jpgraph_line.php");
include ("inc/jpgraph_scatter.php");
include ("inc/jpgraph_bar.php");
require ("inc/leginon.inc");

function displayResult($result,$title) {
	if ($result) {
		?><p><? echo $title;
		?></p> <p><? print_r($result);
		?></p><p>-------------------------------------</p><?
	} else {
		?><p><? echo $title;
		?></p> <p><? echo "empty";
		?></p><p>-------------------------------------</p><?
	} 
	return;
}

function displayFirstResult($results,$title) {
		displayResult($results[0],$title);
}
		
function getSettingsById($table,$id) {
  global $leginondata;
	 $sql = 'SELECT * from `'.$table.'` '
			. 'where `DEF_id`='.$id.' ';
	$results = $leginondata->mysql->getSQLResult($sql);
	displayFirstResult($results,$table.': '.$id);
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
	displayFirstResult($results,$table.': '.$name);
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

	displayFirstResult( $leginondata->mysql->getSQLResult($sql),'FocusSettingData: '.$nodename.': '.$focusname);
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

function getAdminUserId(){
  global $leginondata;
	$sql = 'SELECT `DEF_id` from `UserData` where `name` like "Administrator"';
	$results = $leginondata->mysql->getSQLResult($sql);
	return $results[0]['DEF_id'];
}

$nodenames = array(
	'AcquisitionSettingsData'=>array('Grid','Square','Hole','Preview','Exposure','Square Q','Hole Q','Tomography Preview','Final Section','Subsquare','Centered Square','Rough Tissue','Final Raster','Grid Survey','Mid Mag Survey','Reacquisition','High Mag Acquisition'),
	'FocuserSettingsData'=>array('Focus','Z Focus','Tomo Focus','Tomo Z Focus','RCT Focus','Section Z Focus','Grid Focus','Section Focus'),
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
);

$lpfids = array();
$bfids = array();
$aliases = array('edge lpf','template lpf','lpf');

$user_id = getAdminUserId();
foreach (array_keys($nodenames) as $table) {
	foreach ($nodenames[$table] as $name) { 
		$sqldata1 = getSettingsData($user_id,$table,$name);
		if ($table == 'MosaicClickTargetFinderSettingsData' or 'HoleFinderSettingsData' or 'JAHCFinderSettingsData' or 'DTFinderSettingsData') {
			foreach ($aliases as $alias) {
				$id = $sqldata1['REF|LowPassFilterSettingsData|'.$alias]; 
				if ($id != 0 and !in_array($id,$lpfids)) {
					array_push($lpfids,$sqldata1['REF|LowPassFilterSettingsData|'.$alias]);
					getSettingsById('LowPassFilterSettingsData',$id);
				}
			}
		}
		if ($table == 'MosaicClickTargetFinderSettingsData') {
			$id = $sqldata1['REF|BlobFinderSettingsData|blobs']; 
			if ($id != 0 and !in_array($id,$bfids)) {
				array_push($bfids,$sqldata1['REF|BlobFinderSettingsData|blobs']);
				getSettingsById('BlobFinderSettingsData',$id);
			}
		}
	displayResult($sqldata1,$table.": ".$name);
	}
}

$nodenames = array(
	'FocusSequenceData'=>array('Focus','Z Focus','Tomo Focus','Tomo Z Focus'),
);
foreach (array_keys($nodenames) as $table) {
	foreach ($nodenames[$table] as $name) { 
		$sqldata1 = getFocusSequenceData($user_id,$table,$name);
	}
}
?>
</body></html>
