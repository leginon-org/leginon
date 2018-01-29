<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/admin.inc";

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
$app_change_display = array();

if ($_POST[format]) {
	$xmlradiochecked = ($_POST[format]=="xml") ? $check_str : '';
	$tableradiochecked = ($_POST[format]=="table") ? $check_str : '';
	$hostradiochecked = ($_POST[format]=="host") ? $check_str : '';
	$hideradiochecked = ($_POST[format]=="hide") ? $check_str : '';
	$unhideradiochecked = ($_POST[format]=="unhide") ? $check_str : '';
	$filechecked  = ($_POST[saveasfile]) ? 'checked="checked"' : '';
	$allversionschecked  = ($_POST[all_versions]) ? 'checked="checked"' : '';
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
	if ( $hideradiochecked || $unhideradiochecked ) {
		$hide_status = ( $hideradiochecked ) ? 1:0;
		if ($_POST[applicationId]) {
			$app_ids_to_update = array($applicationId);
			if ($allversionschecked)
				$app_ids_to_update = $leginondata->getAllApplicationIdsOfSameName($applicationId);
			foreach ($app_ids_to_update as $app_id)
				$app_change_display[] = $leginondata->updateApplicationHideStatus($app_id, $hide_status);
		}
	}
}

	if ($_POST[bt_import]) {
	if ($filename = $_FILES[import_file][name])
		$xmldata = $_FILES[import_file][tmp_name];
}

admin_header();
if ($is_admin) {
	$title = "Management";
} else {
	$title = "Export";
}
?>
<h3>Application <?php echo $title?></h3>
<form name="data" method="POST" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<table border=0 class=tableborder>
<tr valign=top >
<td>
  <table border=0>
<tr valign=top >
<td>
	<h3>Select</h3>
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
    <tr>
      <td>
				<h4>Export</h4>
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
	<?php if ($is_admin) { ?>
    <tr>
     <td>
			<h4>or Change Status</h4>
	<input type="radio" name="format" value="hide" id="radio_app_status"  <?php echo $hideradiochecked; ?> >
	<label for="radio_hide_app">Hide</label>
     <br>
	<input type="radio" name="format" value="unhide" id="radio_app_status"  <?php echo $unhideradiochecked; ?> >
	<label for="radio_hide_app">Unhide</label>
     <br>
     </td>
     <td>
	<input type="checkbox" name="all_versions" id="checkbox_all_versions" <?php echo $allversionschecked; ?> >
	<label for="checkbox_all_versions">All versions</label>
     </td>
    </tr>
	<?php } ?>
    <tr>
     <td colspan=2>
     <br>
			<hr>
	<input id="bt_export_id" type="submit" name="bt_export" value="Execute">
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
	} else if ($_POST[format]=="hide" || $_POST[format]=="unhide") {
		foreach ($app_change_display as $display_str)
			echo $display_str."<br>";
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
