<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
$sqlhosts = $SQL_HOSTS;
$hostkeys = array_keys($sqlhosts);
$applicationId = $_POST[applicationId];
$ex_hostId = ($_POST[export_hostId]) ? $_POST[export_hostId] : current($hostkeys);
$im_hostId = ($_POST[import_hostId]) ? $_POST[import_hostId] : current($hostkeys);

$leginondata->mysql->setSQLHost($SQL_HOSTS[$ex_hostId]);
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

?>
<html>
<head>
<title>Leginon2 Application Import/Export</title>
<link rel="stylesheet" type="text/css" href="css/leginon.css"> 
</head>

<body>
<h3>Leginon2 Application Import/Export</h3>
<form name="data" method="POST" enctype="multipart/form-data" action="<? $PHP_SELF ?>">
<table border=0 class=tableborder>
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
	Host
      </td>
      <td>
	Application-version 
     </td>
    </tr>
    <tr>
     <td>
	<select name="export_hostId" onChange="javascript:document.data.submit();">
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$ex_hostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
     </td>
     <td>
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
  <td>
   <table border=0>
    <tr>
      <td>
  	<h3>Import</h3>
      </td>
    </tr>
    <tr>
      <td>
	Host
      </td>
      <td>
	Application.xml file
     </td>
    </tr>
    <tr>
     <td>
	<select name="import_hostId">
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$im_hostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
     </td>
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

</table>
</form>
<?
if ($applicationId && $_POST[bt_export]) {
	$leginondata->dumpFormat($_POST[format]);
	$leginondata->dumpApplicationData($applicationId);
} else if ($filename) {
	echo "$filename <br><br>";
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$im_hostId]);
	$app = $leginondata->importApplication($tmpfile);
	echo $app;
}

?>
</body>
</html>
