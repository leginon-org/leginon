<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/admin.inc');

function mysql2UnixTime($mysqltime) {
	$year = substr($mysqltime, 0,4);
	$month  = substr($mysqltime, 4,2);
	$day = substr($mysqltime, 6,2);
	$hour = substr($mysqltime, 8,2);
	$minute = substr($mysqltime, 10,2);
	$second = substr($mysqltime, 12,2);
	return mktime($hour, $minute, $second, $month, $day, $year);
}

$sqlhosts = $SQL_HOSTS;
$applicationId = $_POST[applicationId];
$hostId = $_POST[hostId];

$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
$instruments = $leginondata->getInstruments2();
$calibrationtypes = $leginondata->getMatrixCalibrationTypes();
$applications = $leginondata->getApplications();
$check_str = 'checked="checked"';
$limit=1;
$instrumentid = $_POST['instrument'];
list($instrumentinfo) = $leginondata->getInstrumentInfo($instrumentid);
$calibrations = is_array($_POST['calibrations']) ? $_POST['calibrations'] : array($_POST['calibrations']);
$types = $_POST['types'];

if ($_POST[format]) {
	$xmlradiochecked = ($_POST[format]=="xml") ? $check_str : '';
	$tableradiochecked = ($_POST[format]=="table") ? $check_str : '';
	$filechecked  = ($_POST[saveasfile]) ? 'checked="checked"' : '';
} else {
	$xmlradiochecked = $check_str;
}

if ($_POST[bt_export]) {
	if(!empty($_POST['calibrations'])) {
		$xmlcalibrations = $leginondata->dumpcalibrations($calibrations, $instrumentid, $limit, $types);
		if ($_POST[format]=='xml' && $_POST[saveasfile]) {
			$filename = $instrumentinfo['name'].'-'.date('Ymd').'.xml';
			$leginondata->download($filename, $xmlcalibrations);
			exit;
		}
	}
} else if ($_POST[bt_import]) {
	if ($filename = $_FILES[import_file][name])
		$tmpfile = $_FILES[import_file][tmp_name];
}

admin_header();
?>
<h3>Calibrations Import/Export</h3>
<form name="data" method="POST" enctype="multipart/form-data" action="<? $PHP_SELF ?>">
<table border=0 class=tableborder>
<tr valign=top >
<td>
From Host:
	<select name="hostId" onChange="javascript:document.data.submit();">
		<?
		foreach($sqlhosts as $id=>$host) {
			$selected = ($id==$hostId) ? "selected" : "";
			echo "<option value=$id $selected >$host\n";
		}
		?>
	</select>
</td>
</tr>
<tr valign=top >
<td>
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
<tr valign=top >
<td>
  <table border=0>
    <tr>
      <td>
  	<h3>Export</h3>
      </td>
    </tr>
 <tr valign="bottom">
  <td>
	<select multiple name="calibrations[]" size="6" >
	<? foreach ($leginondata->calibrationtables as $table) {
		$s = (is_array($_POST['calibrations']) && in_array($table, $_POST['calibrations'])) ? 'selected' : '';
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
    <tr valign=top>
     <td colspan=2>
	<input type="radio" name="format" value="xml" id="radio_format_xml"  <? echo $xmlradiochecked ?> >
	<label for="radio_format_xml">Export to XML format</label>
	<input type="checkbox" name="saveasfile" id="checkbox_file_Id" <? echo $filechecked ?> >
	<label for="checkbox_file_Id">Save as...</label>
	<br>
	<input type="radio" name="format" value="table" id="radio_format_Id" <? echo $tableradiochecked ?> >
	<label for="radio_format_Id">View </label>
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
</tr>
<tr>
  <td>
   <table border=0>
    <tr>
      <td>
  	<h3>Import</h3>
      </td>
    </tr>
    <tr>
      <td>
	calibration.xml file
     </td>
    </tr>
    <tr>
     <td>
	<input type="file" name="import_file" >
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
			if (!$leginondata->mysql->SQLTableExists($table)) {
				echo " not found <br>";continue;
			}
		$calibration_fields = $leginondata->mysql->getFields($calibration); 
		if (in_array('type', $calibration_fields) && $types) {
			foreach ($types as $type) {
				echo "<div style='margin-left: 2em; margin-top: 1em;'>- ".$type;
				$r = $leginondata->getCalibrations($calibration, $instrumentid, $limit, $type);
				display($r, True);
				echo "</div>";
			}
		} else {
			$r = $leginondata->getCalibrations($calibration, $instrumentid, $limit, $type);
			display($r, True);
		}
		echo "<br>";
	    }
	}
} else if ($filename) {
	echo "$filename <br><br>".$SQL_HOSTS[$hostId];
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
	$app = $leginondata->importApplication($tmpfile);
	echo $app;
}


function display($r, $display_fields=False) {
	echo "<table border=1 cellspacing=0, cellpadding=5>";
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

admin_footer();
exit;
?>
