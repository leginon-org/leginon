<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/admin.inc');


$check_str = 'checked="checked"';
$limit=1;
$hostkeys = array_keys($SQL_HOSTS);

// --- set import hosts / instruments
$importfilehostId = ($_POST[importfilehostId]) ? $_POST[importfilehostId] : current($hostkeys);
$importhostId = ($_POST[importhostId]) ? $_POST[importhostId] : current($hostkeys);
$leginondata->mysql->setSQLHost($SQL_HOSTS[$importhostId]);
$importinstruments = $leginondata->getInstrumentDescriptions();
$importinstrumentId = $_POST['importinstrument'];

// --- set export hosts / instrumenits
$hostId = ($_POST[hostId]) ? $_POST[hostId] : current($hostkeys);
$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
$instruments = $leginondata->getInstrumentDescriptions();

$calibrationtypes = $leginondata->getMatrixCalibrationTypes();
$instrumentId = $_POST['instrument'];
list($instrumentinfo) = $leginondata->getInstrumentInfo($instrumentId);
$calibrations = is_array($_POST['calibrations']) ? $_POST['calibrations'] : array($_POST['calibrations']);
$types = $_POST['types'];

// print_r($_POST);

if ($_POST[format]) {
	$xmlradiochecked = ($_POST[format]=="xml") ? $check_str : '';
	$tableradiochecked = ($_POST[format]=="table") ? $check_str : '';
	$hostradiochecked = ($_POST[format]=="host") ? $check_str : '';
	$filechecked  = ($_POST[saveasfile]) ? 'checked="checked"' : '';
} else {
	$xmlradiochecked = $check_str;
}

if ($_POST[bt_export]) {
	if(!empty($_POST['calibrations'])) {
		$xmlcalibrations = $leginondata->dumpcalibrations($calibrations, $instrumentId, $limit, $types);
		if ($_POST[format]=='xml' && $_POST[saveasfile]) {
			$filename = $instrumentinfo['name'].'-'.date('Ymd').'.xml';
			$leginondata->download($filename, $xmlcalibrations);
			exit;
		}
	}
} 
if ($_POST[bt_import]) {
	if ($filename = $_FILES[import_file][name])
		$xmldata = $_FILES[import_file][tmp_name];
}

admin_header();
?>
<h3>Calibrations Import/Export</h3>
<form name="data" method="POST" enctype="multipart/form-data" action="<?=$_SERVER['PHP_SELF'] ?>">
<table border="0" class=tableborder>
<tr valign=top >
<td>
  <table border="0">
    <tr>
      <td>
  	<h3>Export</h3>
      </td>
    </tr>
<tr valign=top >
<td colspan="2">
<table border="0">
 <tr>
  <td>
From Host:
	<select name="hostId" onChange="javascript:document.data.submit();">
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$hostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
</td>
</tr>
<tr valign="top" >
<td nowrap >
Instrument:
	<select name="instrument">
	<? foreach ($instruments as $instrument) {
		$s = ($_POST['instrument']==$instrument['id']) ? 'selected' : '';
		echo "<option value='".$instrument['id']
			."' $s >".$instrument['fullname']."</option>\n";
	}
	?>
	</select>
</td>
</tr>
</table>
 </td>
  </tr>
 <tr valign="bottom">
  <td>
	<select multiple name="calibrations[]" size="6" >
	<? foreach ($leginondata->calibrationtables as $table) {
		$s = (is_array($_POST['calibrations'])) ? ((in_array($table, $_POST['calibrations'])) ? 'selected' : '') : 'selected';
		echo "<option value='$table' $s >$table</option>\n";
	}
	?>
	</select> 
  </td>
  <td>
	<font color="red">*</font><small>Only for MatrixCalibrationData</small><br>
	<select multiple name="types[]" size="6" >
	<? foreach ($calibrationtypes as $type) {
		$s = (is_array($_POST['types'])) ? ((in_array($type['type'], $_POST['types'])) ? 'selected' : '') : 'selected';
		echo "<option value='".$type['type']."' $s >".$type['type']."</option>\n";
	}

	?>
	</select>
  </td>
    </tr>
    <tr valign="top">
     <td colspan="2">
   <table border="0">
	<tr>
		<td>
	<input type="radio" name="format" value="xml" id="radio_format_xml"  <? echo $xmlradiochecked ?> >
		</td>
		<td>
	<label for="radio_format_xml">Export to XML format</label>
	<input type="checkbox" name="saveasfile" id="checkbox_file_Id" <? echo $filechecked ?> >
	<label for="checkbox_file_Id">Save as...</label>
		</td>
	</tr>
	<tr>
		<td>
	<input type="radio" name="format" value="host" <? echo $hostradiochecked ?> >
		</td>
		<td>
To Host:

	<select name="importhostId" onChange="javascript:document.data.submit();">
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$importhostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
Instrument:
	<br>
	<select name="importinstrument">
	<? foreach ($importinstruments as $instrument) {
		$s = ($_POST['importinstrument']==$instrument['id']) ? 'selected' : '';
		echo "<option value='".$instrument['id']
			."' $s >".$instrument['fullname']."</option>\n";
	}
	?>
	</select>
		</td>
		</tr>
	<tr>
		<td>
	<input type="radio" name="format" value="table" id="radio_format_Id" <? echo $tableradiochecked ?> >
		</td>
		<td>
	<label for="radio_format_Id">View </label>
		</td>
	</tr>
	</table>

     </td>
    </tr>
    <tr>
     <td>
	<input id="bt_export_id" type="submit" name="bt_export" value=" Go ">
     </td>
    </tr>
   </table>
  </td>
  <td class=tablebg width=1>
  </td>
  <td>
   <table border="0">
    <tr>
      <td>
  	<h3>Import</h3>
      </td>
    </tr>
    <tr>
     <td nowrap>
	From xml file
     </td>
     <td>
	<input type="file" name="import_file" >
     </td>
    </tr>
    <tr>
     <td>
To Host:
     </td>
     <td>

	<select name="importfilehostId" >
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$importfilehostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
     </td>
    </tr>
    <tr>
     <td>
	<input id="bt_import_id" type="submit" name="bt_import" value="Import">
     </td>
    </tr>
   </table>
  </td>
 </tr>
</table>

</form>
<?
if ($_POST[bt_export]) {
	echo "<hr>";
	if ($_POST[format]=="xml") {
		echo "<pre>";
		echo htmlspecialchars($xmlcalibrations);
		echo "</pre>";
	} else if ($_POST[format]=="table") {
	   foreach ($calibrations as $calibration) {
		echo "<b>".$calibration."</b>";
			if (!$leginondata->mysql->SQLTableExists($calibration)) {
				echo " not found <br>";continue;
			}
		$calibration_fields = $leginondata->mysql->getFields($calibration); 
		if (in_array('type', $calibration_fields) && $types) {
			foreach ($types as $type) {
				echo "<div style='margin-left: 2em; margin-top: 1em;'>- ".$type;
				$r = $leginondata->getCalibrations($calibration, $instrumentId, $limit, $type);
				display($r, True);
				echo "</div>";
			}
		} else {
			$r = $leginondata->getCalibrations($calibration, $instrumentId, $limit);
			display($r, True);
		}
		echo "<br>";
	    }
	} else if ($_POST[format]=="host") {
		$xmldata = $xmlcalibrations;
	}
} 
if ($xmldata) {
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$importhostId]);
	if ($_POST[bt_import])
		$leginondata->mysql->setSQLHost($SQL_HOSTS[$importfilehostId]);
	if(!$leginondata->importCalibrations($xmldata, $importinstrumentId))
		echo "data not imported";
	else
		echo "data imported";
}



admin_footer();
?>
