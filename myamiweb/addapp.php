<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/admin.inc');
$sqlhosts = $SQL_HOSTS;
$applicationId = $_POST[applicationId];
$hostId = $_POST[hostId];

$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
$applications = $leginondata->getApplications();
$check_str = 'checked="checked"';

if ($_POST[format]) {
	$xmlradiochecked = ($_POST[format]=="xml") ? $check_str : '';
	$sqlradiochecked = ($_POST[format]=="sql") ? $check_str : '';
	$filechecked  = ($_POST[saveasfile]) ? 'checked="checked"' : '';
} else {
	$xmlradiochecked = $check_str;
}

if ($_POST[bt_export]) {
	if ($_POST[applicationId] && $_POST[saveasfile]) {
		$leginondata->dumpFormat($_POST[format],$_POST[saveasfile]);
		$leginondata->dumpApplicationData($applicationId);
		exit;
	}
} else if ($_POST[bt_import]) {
	if ($filename = $_FILES[import_file][name])
		$tmpfile = $_FILES[import_file][tmp_name];
}

admin_header();
?>
<h3>Applications Import/Export</h3>
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
  <table border=0>
    <tr>
      <td>
  	<h3>Export</h3>
      </td>
    </tr>
    <tr>
      <td>
	Application-version 
     </td>
    </tr>
    <tr>
     <td colspan=2>
	<select name="applicationId">
	<?
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
	<input type="radio" name="format" value="xml" id="radio_format_xml"  <? echo $xmlradiochecked ?> >
	<label for="radio_format_xml">Export to XML format</label>
     <br>
	<input type="radio" name="format" value="sql" id="radio_format_Id" <? echo $sqlradiochecked ?> >
	<label for="radio_format_Id">Export to SQL</label>
     </td>
     <td>
	<input type="checkbox" name="saveasfile" id="checkbox_file_Id" <? echo $filechecked ?> >
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
	Application.xml file
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
if ($applicationId && $_POST[bt_export]) {
	$leginondata->dumpFormat($_POST[format]);
	$leginondata->dumpApplicationData($applicationId);
} else if ($filename) {
	echo "$filename <br><br>".$SQL_HOSTS[$hostId];
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
	$app = $leginondata->importApplication($tmpfile);
	echo $app;
}
admin_footer();
?>
