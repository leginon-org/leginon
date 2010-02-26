<?php

require "inc/admin.inc";

$f_sel_name=$_POST['f_sel_name'];
$f_name=$_POST['f_name'];
$f_description=$_POST['f_description'];
$f_privilegeId=$_POST['f_privilegeId'];

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
			$data['REF|projectdata|privileges|privilege'] = $f_privilegeId;
			
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
	$f_privilegeId=$info['REF|projectdata|privileges|privilege'];
} else {
	$f_description="";
}

$groups = $leginondata->getGroups('name');
admin_header('onload="init()"');
?>
<script>

var jsname = "<?php echo $f_name; ?>";

function init() {
	var index=-1;
	for (var i = 0; i < document.data.f_sel_name.length; i++) {
		if (document.data.f_sel_name.options[i].text == jsname) {
			index=i;  
		} 
	}
	if (index >=0) {
		document.data.f_sel_name.options[index].selected = true;
		document.data.f_sel_name.focus();
<?php if ($_POST['f_name'] && $_POST['bt_action']!='remove') { ?>
	} else {
		document.data.f_description.focus();
	}
<?php } else { echo "}"; } ?>
}
</script>
<h3>Table: <?php echo $maintable; ?></h3>
Choose a Name in the list or type one, then &lt;Tab&gt;
<br>
<form method="POST" name="data" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<table  border=0 cellspacing=1>
<tr valign="top">
<td>
<select name="f_sel_name"  SIZE=20 onClick="update_data();" onchange="update_data();">
<?php
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
<input class="field" type="text" name="f_name" maxlength="20" size="17" value ="<?php echo $f_name; ?>" onBlur="check_name();" onchange="check_name();"  >
</td>
<?php if ($error) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $error; ?></div></td>
<?php } ?>
</tr>
<tr>
<td class="dt2" height="40">
description:
</td>
<td class="dt2" valign="top">
  <textarea class="textarea" name="f_description" cols="15" rows="2" nowrap><?php echo htmlentities(stripslashes($f_description)); ?></textarea>
</td>
</tr>
<tr>
<td class="dt1" height="40">
privilege:<font color="red">*</font>
</td>
<td class="dt2" valign="top">
<?php
	$privilegeinfo = $leginondata->getPrivilegeInfo();
	if (!(array)$privilegeinfo) echo "Initialize Project Tables First";
	$privileges = array();
	foreach ($privilegeinfo as $p)
			$privileges[$p['description']] = $p['DEF_id'];
	if (privilege('groups')>3) {
?>
	<select name="f_privilegeId" onChange="javascript:document.dataimport.submit();">
		<?php
		foreach($privileges as $privilege_name=>$pId) {
			$selected = ($f_privilegeId==$pId) ? "selected" : "";
			echo "<option value='$pId' $selected >$privilege_name\n";
		}
		?>
	</select>
<?
	} else {
	echo array_search($f_privilegeId,$privileges);
	}
?>
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
<?php
admin_footer();
?>
