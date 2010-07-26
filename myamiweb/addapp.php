<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/admin.inc";

$is_admin = (privilege('groups')>3);
if (privilege('groups') < 2)
	redirect(BASE_URL.'accessdeny.php?text=You do not have the privilege to view this');

$sqlhosts = $SQL_HOSTS;
$hostkeys = array_keys($sqlhosts);
$applicationId = $_POST[applicationId];
$exfromhostId = ($_POST[exportfromhostId]) ? $_POST[exportfromhostId] : current($hostkeys);
$extohostId = ($_POST[exporttohostId]) ? $_POST[exporttohostId] : current($hostkeys);
$im_hostId = ($_POST[import_hostId]) ? $_POST[import_hostId] : current($hostkeys);

$leginondata->mysql->setSQLHost($SQL_HOSTS[$exfromhostId]);
$applications = $leginondata->getApplications();
$check_str = 'checked="checked"';

if ($_POST[format]) {
	$xmlradiochecked = ($_POST[format]=="xml") ? $check_str : '';
	$tableradiochecked = ($_POST[format]=="table") ? $check_str : '';
	$hostradiochecked = ($_POST[format]=="host") ? $check_str : '';
	$filechecked  = ($_POST[saveasfile]) ? 'checked="checked"' : '';
} else {
	$xmlradiochecked = $check_str;
}

if ($_POST[bt_export]) {
	if ($_POST[applicationId]) {
		list($appinfo) = $leginondata->getApplicationInfo($applicationId);
		$dumpapplication = $leginondata->dumpApplicationData($applicationId,'xml');
		if ($_POST[format]=='xml' && $_POST[saveasfile]) {
			$filename = $appinfo['name'].'_'.$appinfo['version'].'.xml';
			$leginondata->download($filename, $dumpapplication);
			exit;
		}
	}
}
if ($_POST[bt_import]) {
	if ($filename = $_FILES[import_file][name])
		$xmldata = $_FILES[import_file][tmp_name];
}

admin_header();
if ($is_admin) {
	$title = "Import/Export";
} else {
	$title = "Export";
}
?>
<h3>Applications <?php echo $title?></h3>
<form name="data" method="POST" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<table border=0 class=tableborder>
<tr valign=top >
<td>
  <table border=0>
    <tr>
      <td>
  	<h3>Export</h3>
      </td>
    </tr>
<tr valign=top >
<td>
From Host:
	<select name="exportfromhostId" onChange="javascript:document.data.submit();">
		<?php
		foreach($hostkeys as $host) {
			$selected = ($host==$exfromhostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
</td>
</tr>
    <tr>
      <td>
	Application-version 
     </td>
    </tr>
    <tr>
     <td colspan="2">
	<select name="applicationId">
	<?php
	foreach ($applications as $application) {
		$selected = ($application['DEF_Id']==$applicationId) ? "selected" : "";
		echo "<option value=\"".$application['DEF_Id']."\" $selected >".$application['name'].'-'.$application['version'];
	}
	?>
	</select>
     </td>
    </tr>
    <tr valign=top>
     <td>
	<input type="radio" name="format" value="xml" id="radio_format_xml"  <?php echo $xmlradiochecked; ?> >
	<label for="radio_format_xml">Export to XML format</label>
     <br>
	<input type="radio" name="format" value="table" id="radio_format_Id" <?php echo $tableradiochecked; ?> >
	<label for="radio_format_Id">View </label>
     <br>
	<input type="radio" name="format" value="host" id="radio_format_host" <?php echo $hostradiochecked; ?> >
	<label for="radio_format_host">To Host:</label>
	<select name="exporttohostId" >
		<?php
		foreach($hostkeys as $host) {
			$selected = ($host==$extohostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
     </td>
     <td>
	<input type="checkbox" name="saveasfile" id="checkbox_file_Id" <?php echo $filechecked; ?> >
	<label for="checkbox_file_Id">Save as...</label>
     </td>
    </tr>
    <tr>
     <td>
	<input id="bt_export_id" type="submit" name="bt_export" value="Export">
     </td>
    </tr>
   </table>
  </td>
  <td class=tablebg width=1>
  </td>
<?php if ($is_admin) { ?>
  <td>
   <table border=0>
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
	<select name="import_hostId">
		<?php
		foreach($hostkeys as $host) {
			$selected = ($host==$im_hostId) ? "selected" : "";
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
<?php } ?>
 </tr>
</table>

</form>
<?php
if ($_POST[bt_export]) {
	echo "<hr>";
	if ($_POST[format]=="xml") {
		echo "<pre>";
		echo htmlspecialchars($dumpapplication);
		echo "</pre>";
	} else if ($_POST[format]=="table") {
	   foreach ($leginondata->applicationtables as $table) {
		echo "<b>".$table."</b>";
			if (!$leginondata->mysql->SQLTableExists($table)) {
				echo " not found <br>";continue;
			}
		    $where = ($table=='ApplicationData') 
			? " `DEF_id` = $applicationId"
			: " `REF|ApplicationData|application` = $applicationId";
		$q = "select * from `$table` where $where";
		$r = $leginondata->mysql->getSQLResult($q);
		display($r, True);
	}
		echo "<br>";
	} else if ($_POST[format]=="host") {
		$xmldata=$dumpapplication;
	}
} 
if ($xmldata) {
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$extohostId]);
	if ($_POST[bt_import])
		$leginondata->mysql->setSQLHost($SQL_HOSTS[$im_hostId]);
	$app = $leginondata->importApplication($xmldata);
	echo $app;
}

admin_footer();
?>
