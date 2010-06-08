<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once('inc/leginon.inc');

function admin_header($javascriptinit="") {
login_header();



$link = new iconlink();
$link->align = 'center';
$link->cols = 1;
$link->onimg = "_on.png";
$link->offimg = "_off.png";
$link->setImagePath('img/');
$link->addlink('addgroup.php','Groups','', 'group1', '');
$link->addlink('user.php','Users','', 'user', '');
$link->addlink('addinstrument.php','Instruments','', 'tem_tecnai_icon', '');
if (privilege('users')>1)
	$link->addlink('revertsettings.php','Revert Settings','', 'calibration', '');
#$link->addlink('addcal.php','Calibrations','', 'calibration', '');
$link->addlink('addapp.php','Applications','', 'application', '');
$link->addlink('goniometer.php','Goniometer','', 'goniometer', '');


?>

<html>
<head>
<title>Manage Groups</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
<script src="js/dataform.js"></script>
</head>
<body Background='img/background.jpg' leftmargin="0" topmargin="5" marginwidth="0" marginheight="5" alink="#00CCCC" vlink="#006699" link="#006699" <?php echo $javascriptinit; ?>>

<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
<hr/>
<table border=0>
<tr valign="top">
<td width=100>
<?php $link->Display(); ?>
</td>
<td>
<?php
}

function admin_footer() {
	echo "
 	 </td>
	</tr>
    </body>
</html>
";
}

function wizard_footer() {
}

function mysql2UnixTime($mysqltime) {
	$year = substr($mysqltime, 0,4);
	$month  = substr($mysqltime, 4,2);
	$day = substr($mysqltime, 6,2);
	$hour = substr($mysqltime, 8,2);
	$minute = substr($mysqltime, 10,2);
	$second = substr($mysqltime, 12,2);
	return mktime($hour, $minute, $second, $month, $day, $year);
}

function display($r, $display_fields=False) {
	echo "<table class='tableborder' border=1 cellspacing=0, cellpadding=5>";
	if (!is_array($r))
		return False;
	$data = $r;
	if ($display_fields) {
		if ($r[0]) {
			$fields = array_keys($r[0]);
			foreach ($fields as $field)
				$f[$field] = $field;
			$data = array_merge(array($f), $r);
		}
	}
	foreach ($data as $row) {
	echo "<tr>";
		foreach ($row as $k=>$value) {
			if (eregi('^DEF_id|^REF\|', $k)) 
				continue;
			else if (eregi('^DEF_timestamp$', $k)) {
				if (!$display_fields)
					$value = date('D, j M Y G:i:s ', mysql2UnixTime($value));
				$display_fields = False;
			}
			echo "	<td>$value</td>\n";
		}
	echo "</tr>";
	}
	echo "</table>";
}

function defaultsettings_fileheader($user_id,$admin_init=false) {
	global $filename;
	$array = array();
	$linebreak = "\n";
	if ($admin_init) {
		$array[] = '<?php'.$linebreak;
		$error_msg = 'Create administrator user first';
	} else {
		$error_msg = 'Can not revert without a known user';
	}
	$array[] = 'if ($user_id < 1) {'.$linebreak;
	$array[] = '	echo "<h3> Error: '.$error_msg.' </h3>";'.$linebreak;
	$array[] = '	exit();'.$linebreak;
	$array[] = '}'.$linebreak;
	$array[] = '$dbc=$leginondata->mysql;'.$linebreak;
	$array[] = '$q = "insert into `SessionData` (`name`,`REF|UserData|user`,`comment`) "'.$linebreak;
	$array[] = '      . " VALUES "'.$linebreak;
	$array[] = '      . " ( concat(\'importsettings\', DATE_FORMAT(now(), \'%Y%m%d%H%i%s\')), "'.$linebreak;
	$array[] = '			. " ".$user_id.",\'revert to default\' ) ";'.$linebreak;
	$array[] = '$sessionId = $dbc->SQLQuery($q, true);'.$linebreak;
	$array[] = $linebreak;
	return $array;
}

function makeSettingsCode($user_id) {
	global $leginondata;
	global $code_string;
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
	$lpfids = array();
	$bfids = array();
	$html = '';
	defaultsettings_fileheader($user_id);
	$aliases = array('edge lpf','template lpf','lpf');
	$admin_id = $leginondata->getAdminUserId();
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
			$sqldata1 = $leginondata->getSettingsData($admin_id,$table,$name);
			if ($table == 'MosaicClickTargetFinderSettingsData' or 'HoleFinderSettingsData' or 'JAHCFinderSettingsData' or 'DTFinderSettingsData') {
				foreach ($aliases as $alias) {
					$lid = $sqldata1['REF|LowPassFilterSettingsData|'.$alias]; 
					if ($lid != 0 ) {
						if (!in_array($lid,$lpfids)) {
							array_push($lpfids,$sqldata1['REF|LowPassFilterSettingsData|'.$alias]);
							$result = $leginondata->getSettingsById('LowPassFilterSettingsData',$lid);
							$lpfids[$table.'.'.$name.'.'.$alias] = $result;
							assembleResult($result,'LowPassFilterSettingsData',$lid);
						}
						$sqldata1['REF|LowPassFilterSettingsData|'.$alias] = '$lid'.$lid; 
					} else {
						if (is_array($sqldata1)) {
							$sqldata1 = array_diff_key($sqldata1,array('REF|LowPassFilterSettingsData|'.$alias=>$lid)); 
						} else {
							$html .= 'Node '.$name. ' has no administrator settings in the table called '.$table.'<br/>';
						} 
					}
				}
			}

			if ($table == 'MosaicClickTargetFinderSettingsData') {
				$id = $sqldata1['REF|BlobFinderSettingsData|blobs']; 
				if ($id != 0) {
					if (!in_array($id,$bfids)) {
						array_push($bfids,$sqldata1['REF|BlobFinderSettingsData|blobs']);
						$result = $leginondata->getSettingsById('BlobFinderSettingsData',$id);
						assembleResult($result,'BlobFinderSettingsData',$id);
						$blobids[$table.'.'.$name.'.'.'blobs'] = $id;
					}
					$sqldata1['REF|BlobFinderSettingsData|blobs'] = '$bid'.$id;
				} else {
						$sqldata1 = array_diff_key($sqldata1,array('REF|BlobFinderSettingsData|blobs'=>$id));
				} 
			}
		assembleResult($sqldata1,$table,$name);
		}
	}
	$focusernodenames = $nodenames['FocuserSettingsData'];
	$table = 'FocusSequenceData';
	foreach ($focusernodenames as $name) { 
		$sequence_results = $leginondata->getUserFocusSequenceDataByName($admin_id,$table,$name);
		assembleResult($sequence_results[0],$table);
		$focusnamesstr = $sequence_results[0]['SEQ|sequence'];
		$focusnames = explode("'",$focusnamesstr);
		foreach ($focusnames as $focusname) {
			if (strlen($focusname)>2 && (strcmp($focusname,', u')!=0))  {
				$focus_results = $leginondata->getUserFocusSettingDataByName($admin_id,$name,$focusname);
				assembleResult($focus_results[0],'FocusSettingData');
			}
		}
	}
	return $html;
}

function assembleResult($result,$table,$name='') {
	$filearray = array();
	if ($result) {
		$id = $result['DEF_id'];
		$removekeys = array('DEF_id'=>1,'DEF_timestamp'=>2,'REF|SessionData|session'=>null);
		$result = array_diff_key($result,$removekeys);
		$filearray[] = '$table = "'.$table.'";'.$linebreak.'';
		$filearray[] = '$data=array();'.$linebreak.''; 
		foreach ($result as $key=>$r) {
			if (!is_numeric($r) && !$r) continue;
			if (substr_count($r,'$') == 0) {
				$filearray[] = '$data["'.$key.'"] = "'.$r.'";'.$linebreak.''; 
			} else {
				$filearray[] = '$data["'.$key.'"] = '.$r.';'.$linebreak.''; 
			}
		}
		$t = strtolower(substr($table,0,1));
		if ($table !='LowPassFilterSettingsData') {
			$filearray[] = '$data["REF|SessionData|session"]= $sessionId;'.$linebreak.'';
		}
		$filearray[] = '$'.$t.'id'.$id.'=$dbc->SQLInsert($table, $data);'.$linebreak.'';
		$filearray[] = $linebreak;
	}
	# addToGlobalString() is defined at the script calling this
	return addToGlobalString($filearray);
}

?>
