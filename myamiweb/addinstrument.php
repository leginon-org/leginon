<?
require('inc/admin.inc');

$hostkeys = array_keys($SQL_HOSTS);
$hostId = ($_POST[hostId]) ? $_POST[hostId] : current($hostkeys);
$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);

$importinstrumenthosts = $leginondata->getInstrumentHosts();
$importinstrumenthost = ($_POST[importinstrumenthost]) ? $_POST[importinstrumenthost] : $importinstrumenthosts[0];
$importscopeId = $_POST['importscopeId'];
$importcameraId = $_POST['importcameraId'];
$importscopes  = $leginondata->getScopes($importinstrumenthost);
$importcameras = $leginondata->getCameras($importinstrumenthost);

$leginondata->mysql->setSQLHost("default");
if ($_POST['import']) {
	$leginondata->mysql->setSQLHost($SQL_HOSTS[$hostId]);
	list($importinfo) = $leginondata->getInstrumentInfo($_POST['importinstrument']);
	unset($importinfo['DEF_id']);
	unset($importinfo['date']);
	$leginondata->mysql->setSQLHost("default");
	$leginondata->mysql->SQLInsert('InstrumentData', $importinfo);
} 


$f_sel_name=$_POST['f_sel_name'];
$f_name=$_POST['f_name'];
$f_description=$_POST['f_description'];
$f_hostname=$_POST['f_hostname'];
$f_type=$_POST['f_type'];

$maintable = "InstrumentData";
$id = $leginondata->getId( array('name' => $f_name), $maintable);
if ($id) {
	$id = (is_array($id)) ? $id[0] : $id;
	$id = $leginondata->getId( array('DEF_id' => $id), $maintable);
}
switch ($_POST['bt_action']) {


	case "get":
			$id = $leginondata->getId( array('DEF_id' => $f_sel_name), $maintable);
			break;
	case "save":
			if (!$f_name) {
				$error = "Enter a Name";
				break;
			}
			$data['name'] = $f_name;
			$data['hostname'] = $f_hostname;
			$data['type'] = $f_type;
			$data['description'] = $f_description;
			
			if ($id) {
				$where['DEF_id'] = $id;
				$leginondata->mysql->SQLUpdate($maintable, $data, $where);
			} else {
				$id = $leginondata->mysql->SQLInsert($maintable, $data);
			}
			break;
	case "remove":
			$where['DEF_id']=$id;
			$f_name="";
			$leginondata->mysql->SQLDelete($maintable, $where);
			break;
}

$info = $leginondata->getDataInfo($maintable, $id);
$info = $info[0];
if ($info) {
	$f_name=$info['name'];
	$f_hostname = $info['hostname'];
	$f_type= $info['type'];
	$f_description=$info['description'];
} else {
	$f_description="";
	$f_hostname = "";
	$f_type= "";
}

$instruments = $leginondata->getInstruments();
admin_header('onload="init()"');
?>
<script>

var jsid = "<?=$id?>";

function init() {
	var index=-1;
	for (var i = 0; i < document.data.f_sel_name.length; i++) {
		if (document.data.f_sel_name.options[i].value == jsid) {
			index=i;  
		} 
	}
	if (index >=0) {
		document.data.f_sel_name.options[index].selected = true;
		document.data.f_sel_name.focus();
<? if ($_POST['f_name']) { ?>
	} else {
		if (f_d=document.data.f_hostname)
			f_d.focus();
		document.data.f_sel_name.focus();
	}
<? } else { echo "}"; } ?>
}
</script>
<h3>Table: <?=$maintable?></h3>
<table  border=0>
<form method="POST" name="dataimport" enctype="multipart/form-data" action="<?=$_SERVER['PHP_SELF']?>">
<tr valign=top >
<td>
From Host:
	<select name="hostId" onChange="javascript:document.dataimport.submit();">
		<?
		foreach($hostkeys as $host) {
			$selected = ($host==$hostId) ? "selected" : "";
			echo "<option value='$host' $selected >$host\n";
		}
		?>
	</select>
</td>
<td>
Instrument host:
	<select name="importinstrumenthost" onChange="javascript:document.dataimport.submit();">
<?
foreach($importinstrumenthosts as $h) {
	$selected = ($h==$importinstrumenthost) ? "selected" : "";
	echo "<option $selected >".$h."</option>";
}
?>
</select>
Scope
<select name='importscopeId' >
<?
foreach($importscopes as $s) {
	echo "<option value='".$s['id']."' >".$s['name']."</option>";
}
?>
</select>
Camera
<select name='importcameraId' >
<?
foreach($importcameras as $c) {
	echo "<option value='".$c['id']."' >".$c['name']."</option>";
}
?>
</select>
</td>
</tr>
<tr>
<td>
<input type="submit" name="import" value = "Import" >
</td>
</tr>
</form>
</table>
<hr>
<table  border=0 cellspacing=1>
<form method="POST" name="data" enctype="multipart/form-data" action="<?=$_SERVER['PHP_SELF']?>">
<tr valign="top">
<td>
<select name="f_sel_name"  SIZE=20 onClick="update_data();" onchange="update_data();">
<?
foreach ($instruments as $instrument) {
//	$selected = ($instrument['DEF_id']==$f_sel_name) ? "selected" : "";
	echo "<option value='".$instrument['DEF_id']."' $selected >".stripslashes($instrument['name'])."</option>\n"; 
} 

?>
</select>
</td>
<td>
<table>
<tr valign="top">
<td colspan=2>
Choose a Name in the list or type one, then &lt;Tab&gt;
<br>
<font color="red">*: required fields</font>
</td>
</tr>
<tr>
<td class="dt1" height="40">
name:<font color="red">*</font>
</td>
<td class="dt1"> 
<input class="field" type="text" name="f_name" maxlength="30" size="17" value ="<?=$f_name?>" onBlur="check_name();" onchange="check_name();"  >
</td>
<? if ($error) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?=$error?></div></td>
<? } ?>
</tr>
<? /*
<tr>
<td class="dt2" height="40">
description:
</td>
<td class="dt2" valign="top">
  <textarea class="textarea" name="f_description" cols="15" rows="2" nowrap><?=htmlentities(stripslashes($f_description)); ?></textarea>
</td>
</tr>
*/ ?>

<tr>

<td class="dt1" height="40">
hostname:
</td>
<td class="dt1"> 
<input class="field" type="text" name="f_hostname" maxlength="30" size="17" value ="<?=$f_hostname?>" >
</td>
</tr>

<tr>
<td class="dt2" height="40">
type:
</td>
<td class="dt2"> 
<select name="f_type">
<?
$intrument_types = array('', 'CCDCamera', 'TEM');
foreach ($intrument_types as $intrument_type) {
	$selected = ($intrument_type==$f_type) ? "selected" : "";
	echo "<option value='$intrument_type' $selected >$intrument_type</option>\n";
}
?>
</select>
</td>
</tr>

<tr>
<td>
	<input type="hidden" name="bt_action" value = "" >
	<input type="button" name="save" value = "Save" onClick="confirm_update();" >
</td>
<td>
	<input type="button" name="save" value = "Remove" onClick="confirm_delete();" >
</td>
</tr>


</table>
</td>
</tr>

</form>
</table>
<?
admin_footer();
?>
