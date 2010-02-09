<?php

require "inc/admin.inc";

$f_sel_name=$_POST['f_sel_name'];
$f_username=$_POST['f_username'];

$f_first_name=$_POST['f_first_name'];
$f_last_name=$_POST['f_last_name'];
$f_email=$_POST['f_email'];
$f_password=$_POST['f_password'];
$f_password_confirm=$_POST['f_password_confirm'];
$f_group=$_POST['f_group'];
$maintable = "UserData";
$id = $leginondata->getId( array('username' => $f_username), 'UserData');
$id = (is_array($id)) ? $id[0] : $id;

switch ($_POST['bt_action']) {


	case "get":
			$id = $leginondata->getId( array('DEF_id' => $f_sel_name), 'UserData');
			break;
	case "save":
			if (!$f_username) {
				$nameerror = "Enter a user name";
				break;
			}
			if (!$f_first_name){
				$nameerror = "Enter a first name";
				break;
			}
			if (!$f_last_name){
				$nameerror = "Enter a last name";
				break;
			}
			if (!$f_email){
				$nameerror = "Enter a email address";
				break;
			}
			
			if (!$f_password) {
				$passworderror = "Enter password";
				break;
			}
			if ($f_password != $f_password_confirm) {
				$passworderror = "Both password are not match";
				break;
			}
			$data['username'] = $f_username;
			$data['firstname'] = $f_first_name;
			$data['lastname'] = $f_last_name;
			$data['email'] = $f_email;
			//$data['full name'] = $f_full_name;
			$data['REF|GroupData|group'] = $f_group;
			$data['password'] = $f_password;

			if ($id) {
				$where['DEF_id'] = $id;
				$leginondata->mysql->SQLUpdate($maintable, $data, $where);
			} else {
				$id = $leginondata->mysql->SQLInsert('UserData', $data);
			}
			break;
	case "remove":
			$where['DEF_id']=$id;
			$f_name="";
			$leginondata->mysql->SQLDelete('UserData', $where);
			unset($f_username, $f_first_name, $f_last_name, $f_email, $f_group, $f_password);
			break;
}


$userinfo = $leginondata->getDataInfo('UserData', $id);
$userinfo = $userinfo[0];
if ($userinfo) {
	$f_username=$userinfo['username'];
	$f_first_name=$userinfo['firstname'];
	$f_last_name=$userinfo['lastname'];
	$f_email=$userinfo['email'];
	$f_group=$userinfo['REF|GroupData|group'];
	$f_password=$userinfo['password'];
}else{
	if(empty($id)){
		$f_username="";
		$f_first_name="";
		$f_last_name="";
		$f_email="";
		$f_group="";
		$f_password="";	
	}
	
}

$groups = $leginondata->getGroups('name');
$users = $leginondata->getUsers('username');
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
Choose a user name in the list or type one, then &lt;Tab&gt;
<br>
<form method="POST" name="data" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<table  border=0 cellspacing=1>
<tr valign="top">
<td>

<!-- list out all the users -->
<select name="f_sel_name"  SIZE=20 onClick="update_data();" onchange="update_data();">
<?php
foreach ($users as $user) {
//	$s = ($f_sel_name==$user['DEF_id']) ? 'selected' : '';
	echo "<option value='".$user['DEF_id']."' $s>".stripslashes($user['username'])."</option>\n"; 
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
    User name:<font color="red">*</font>
  </td>
  <td class="dt1"> 
    <input class="field" type="text" name="f_username" maxlength="20" size="17" value ="<?php echo $f_username; ?>" >
  </td>
  <?php if ($nameerror) { ?>
  <td valign="top">
    <div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $nameerror; ?></div></td>
  <?php } ?>
</tr>
<tr>
  <td class="dt1" height="40">
    First name:<font color="red">*</font>
  </td>
  <td class="dt1">
		<input class="field" type="text" name="f_first_name" maxlength="20" size="17" value="<?php echo $f_first_name ?>">
  </td>
</tr>
<tr>
  <td class="dt1" height="40">
    Last name:<font color="red">*</font>
  </td>
  <td class="dt1">
		<input class="field" type="text" name="f_last_name" maxlength="20" size="17" value="<?php echo $f_last_name ?>">
  </td>
</tr>
<tr>
  <td class="dt1" height="40">
    Email:<font color="red">*</font>
  </td>
  <td class="dt1">
		<input class="field" type="text" name="f_email" maxlength="25" size="23" value="<?php echo $f_email ?>">
  </td>
</tr>
<tr>
  <td class="dt2" height="40">
    Password:<font color="red">*</font>
  </td>
  <td class="dt2" valign="top">
		<input class="field" type="password" name="f_password" size="15" value="<?php echo $f_password ?>">
  </td>
<?php if ($passworderror) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $passworderror; ?></div></td>
<?php } ?>
</tr>
<tr>
<td class="dt2" height="40">
Confirm password:<font color="red">*</font>
</td>
<td class="dt2" valign="top">
		<input class="field" type="password" name="f_password_confirm" size="15">
</td>
</tr>
<tr>
<td class="dt1" height="40">
Group:
</td>
<td class="dt1">
  <table border="0">
    <tr valign="top">
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
<?php if($id != NULL) { ?>
<td>
	<input type="button" name="save" value = "Remove" onClick="confirm_delete();" >
</td>
</tr>
<?php } ?>


</table>
</td>
</tr>

</table>
</form>

<?php
/* footer comment */
admin_footer();
?>
