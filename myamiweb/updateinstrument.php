<?php

require_once "inc/admin.inc";
$login_check = $dbemauth->is_logged();
$is_admin = (privilege('groups')>3);
if (privilege('groups') < 2)
	redirect(BASE_URL.'accessdeny.php?text=You do not have the privilege to view this');

$leginondata->mysql->setSQLHost("default");

$f_sel_name=$_POST['f_sel_name'];
$f_name=$_POST['f_name'];
$f_description=$_POST['f_description'];
$f_hostname=$_POST['f_hostname'];
$f_hidden=$_POST['f_hidden'];
$f_type=$_POST['f_type'];

$maintable = "InstrumentData";
$id = $f_sel_name;

switch ($_POST['bt_action']) {


	case "get":
			/* no need to do something yet */
			break;
	case "save":
			if (!$f_name) {
				$error = "Enter a Name";
				break;
			}

			$data['name'] = $f_name;
			$data['hostname'] = $f_hostname;
			$data['description'] = $f_description;
			$data['hidden']= ($f_hidden == 'Yes') ? '1':'0';
			
			if ($id) {
				$where['DEF_id'] = $id;
				$leginondata->mysql->SQLUpdate($maintable, $data, $where);
			}
			break;
}

$info = $leginondata->getDataInfo($maintable, $id);
$info = $info[0];
if ($info) {
	$f_name=$info['name'];
	$f_hostname = $info['hostname'];
	$f_description=$info['description'];
	$f_type = ($info['cs']) ? 'Microscope' : 'Camera';
	$f_hidden = ($info['hidden']) ? 'Yes': 'No';
} else {
	$f_description="";
	$f_hostname = "";
	$f_hidden = "";
}

$instruments = $leginondata->getInstruments();
admin_header('onload="init()"');
?>
<script>

var jsid = "<?php echo $id; ?>";

function init() {
	document.data.f_sel_name.focus();
}
</script>

<?php
if (privilege('groups')) {
?>
	<h3>Table: <?php echo $maintable; ?></h3>
	<hr>
<?php
 }
?>
<table  border=0 cellspacing=1>
<form method="POST" name="data" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<tr valign="top">
<td>
<select name="f_sel_name"  SIZE=20 onClick="update_data();" onchange="update_data();">
<?php
foreach ($instruments as $instrument) {
	$selected = ($instrument['DEF_id']==$f_sel_name) ? "selected" : "";
	echo "<option value='".$instrument['DEF_id']."' $selected >".stripslashes($instrument['name'])."</option>\n"; 
} 

?>
</select>
</td>
<td>
<table>
<tr valign="top">
<td colspan=2>
Choose a Name in the list
<br>
<font color="red">*: required fields</font>
</td>
</tr>
<tr>
<td class="dt1" height="40">
class name:<font color="red">*</font>
</td>
<td class="dt1"> 
	<input type="hidden" name="f_name" value = "<?php echo $f_name; ?>" >
<?php echo $f_name; 
//  onBlur="check_name();" onchange="check_name();"  >
?>
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
hostname:
</td>
<td class="dt1"> 
<input class="field" type="text" name="f_hostname" maxlength="30" size="17" value ="<?php echo $f_hostname; ?>" >
</td>
</tr>

<tr>
<td class="dt2" height="40">
type:
</td>
<td class="dt2"> 
<?php
	echo $f_type ;
?>
</select>
</td>
</tr>
<td class="dt1" height="40">
is hidden:
</td>
<td class="dt1"> 
<select name="f_hidden">
<?php
$is_hiddens = array('Yes', 'No');
foreach ($is_hiddens as $choice) {
	$selected = ($choice==$f_hidden) ? "selected" : "";
	echo "<option value='$choice' $selected >$choice</option>\n";
}
?>
</select>
</td>
</tr>

<tr>
<td colspan="2">
	<input type="hidden" name="bt_action" value = "" >
<?php
if (privilege('groups') > 3) {
?>
	<input type="button" name="save" value = "Save" onClick="confirm_update();" >

<?php
}
?>
</td>
</tr>

</table>
</td>
</tr>

</form>
</table>
<?php
admin_footer();
?>
