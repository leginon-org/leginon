<?
require('inc/leginon.inc');
require('inc/admin.inc');

// --- testing
$leginondata->mysql = new mysql('stratocaster', 'usr_object', '' ,'dbemdata');

$f_sel_name=$_POST['f_sel_name'];
$f_name=$_POST['f_name'];
$f_description=$_POST['f_description'];

$maintable = "GroupData";
$id = $leginondata->getId( array('name' => $f_name), $maintable);
$id = (is_array($id)) ? $id[0] : $id;
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
	$f_description=$info['description'];
} else {
	$f_description="";
}

$groups = $leginondata->getGroups();
admin_header('onload="init()"');
?>
<script>

var jsname = "<?=$f_name?>";

function init() {
	var index=-1;
	for (var i = 0; i < document.f_userdata.f_sel_name.length; i++) {
		if (document.f_userdata.f_sel_name.options[i].text == jsname) {
			index=i;  
		} 
	}
	if (index >=0) {
		document.f_userdata.f_sel_name.options[index].selected = true;
		document.f_userdata.f_sel_name.focus();
<? if ($_POST['f_name'] && $_POST['bt_action']!='remove') { ?>
	} else {
		document.f_userdata.f_description.focus();
	}
<? } else { echo "}"; } ?>
}
</script>
<h3>Table: <?=$maintable?></h3>
Choose a Name in the list or type one, then &lt;Tab&gt;
<br>
<form method="POST" name="f_userdata" enctype="multipart/form-data" action="<?=$_SERVER['PHP_SELF']?>">
<table  border=0 cellspacing=1>
<tr valign="top">
<td>
<select name="f_sel_name"  SIZE=20 onClick="update_userdata();" onchange="update_userdata();">
<?
foreach ($groups as $group) {
	echo "<option value='".$group['DEF_id']."' $s>".stripslashes($group['name'])."</option>\n"; 
} 

?>
</select>
</td>
<td>
<table>
<tr valign="top">
<td colspan=2>
<font color="red">*: required fields</font>
</td>
</tr>
<tr>
<td class="dt1" height="40">
name:<font color="red">*</font>
</td>
<td class="dt1"> 
<input class="field" type="text" name="f_name" maxlength="20" size="17" value ="<?=$f_name?>" onBlur="check_name();" onchange="check_name();"  >
</td>
<? if ($error) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?=$error?></div></td>
<? } ?>
</tr>
<tr>
<td class="dt2" height="40">
full name:
</td>
<td class="dt2" valign="top">
  <textarea class="textarea" name="f_description" cols="15" rows="2" nowrap><?=htmlentities(stripslashes($f_description)); ?></textarea>
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

</table>
</form>
<?
admin_footer();
?>
