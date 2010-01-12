<?php

require "inc/admin.inc";

$f_sel_name=$_POST['f_sel_name'];
$f_name=$_POST['f_name'];
$f_full_name=$_POST['f_full_name'];
$r_groupdata=$_POST['r_groupdata'];
$f_group=$_POST['f_group'];

$maintable = "UserData";
$id = $leginondata->getId( array('name' => $f_name), 'UserData');
$id = (is_array($id)) ? $id[0] : $id;
switch ($_POST['bt_action']) {


	case "get":
			$id = $leginondata->getId( array('DEF_id' => $f_sel_name), 'UserData');
			break;
	case "save":
			if ($r_groupdata=="Y") {
				if (!$_POST['f_groupdata_name']) {
					$grouperror = "Enter a Group Name";
				} else {
					$ginfo['name'] = $_POST['f_groupdata_name'];
					$ginfo['description'] = $_POST['f_groupdata_description'];
					$f_group = $leginondata->mysql->SQLInsert('GroupData', $ginfo);
				}
			}
			if (!$f_name) {
				$nameerror = "Enter a Name";
				break;
			}
			$data['name'] = $f_name;
			$data['full name'] = $f_full_name;
			$data['REF|GroupData|group'] = $f_group;
			
			if ($id) {
				$where['DEF_id'] = $id;
				$leginondata->mysql->SQLUpdate('UserData', $data, $where);
			} else {
				$id = $leginondata->mysql->SQLInsert('UserData', $data);
			}
			break;
	case "remove":
			$where['DEF_id']=$id;
			$f_name="";
			$leginondata->mysql->SQLDelete('UserData', $where);
			break;
}


$userinfo = $leginondata->getDataInfo('UserData', $id);
$userinfo = $userinfo[0];
if ($userinfo) {
	$f_name=$userinfo['name'];
	$f_full_name=$userinfo['full name'];
	$f_group=$userinfo['REF|GroupData|group'];
} else {
	$f_full_name="";
	$f_group="1";
}

$groups = $leginondata->getGroups('name');
$users = $leginondata->getUsers('name');

admin_header('onload="init()"');
?>
<script>
function enable_groupdata(state) {
	enable_input(state);
}

function enable_input(state) {
	var color = "#FFFFFF";
	var value = "";
	if (state) {
		 color="#DCDAD5";
		 value="add new";
	}
	document.data.f_groupdata_name.value=value;
	document.data.f_groupdata_name.disabled=state;
	document.data.f_groupdata_description.disabled=state;
	if (	(style_groupdata_name = getStyleObject("id_groupdata_name")) &&
		(style_groupdata_description = getStyleObject("id_groupdata_description"))) {
		style_groupdata_name.background = color;
		style_groupdata_description.background = color;
	}
}

var jsid = "<?php echo $id; ?>";

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
<?php if ($_POST['f_name']) { ?>
	} else {
		document.data.f_full_name.focus();
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
foreach ($users as $user) {
//	$s = ($f_sel_name==$user['DEF_id']) ? 'selected' : '';
	echo "<option value='".$user['DEF_id']."' $s>".stripslashes($user['name'])."</option>\n"; 
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
<?php if ($nameerror) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $nameerror; ?></div></td>
<?php } ?>
</tr>
<tr>
<td class="dt2" height="40">
full name:
</td>
<td class="dt2" valign="top">
  <textarea class="textarea" name="f_full_name" cols="15" rows="2" nowrap><?php echo htmlentities(stripslashes($f_full_name)); ?></textarea>
</td>
</tr>
<tr>
<td class="dt1" height="40">
group:
</td>
<td class="dt1">
  <table border="0">
    <tr valign="top">
     <td>
	<input class="field" type='radio' name='r_groupdata' value='N' checked onChange="enable_groupdata(true)">
     </td>
     <td>
	<select size="1" name="f_group" > 
	<?php foreach ($groups as $group) {
		$s = ($f_group == $group['DEF_id'] ) ? 'selected' : '';
		echo "<option value='".$group['DEF_id']."' $s >".$group['name']."</option>\n";
		}
	?>
	</select>
     </td>
    </tr>
    <tr valign="top">
     <td>
	<input type='radio' name='r_groupdata' value='Y' onChange="enable_groupdata(false)">
     </td>
     <td>
	<table  bgcolor="#FFFFFF" border=0 cellspacing=1>
	<tr>
	<td class="dt1" height="40">
	name:<font color="red">*</font>
	</td>
	<td class="dt1" height="40">
	<input class="field" disabled name="f_groupdata_name" size="17" value="add new" id="id_groupdata_name" style="background-color: #DCDAD5;">
	</td>
<?php if ($grouperror) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $grouperror; ?></div></td>
<?php } ?>
	</tr>
	<tr>
	<td class="dt2" height="40">
	description:
	</td>
	<td class="dt2" height="40">
	<textarea class="textarea" disabled name="f_groupdata_description" cols="15" rows="2" id="id_groupdata_description" style="background-color: #DCDAD5;"></textarea>
	</td>
	</tr>
	</table>
     </td>
    </tr>
  </table>

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
/* footer comment */
admin_footer();
?>
