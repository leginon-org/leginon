<?php

require "inc/ptcl.inc";

$sessions = $leginondata->getSessions();
$f_sel_name=$_POST['f_sel_name'];
$f_name =$_POST['f_name'];
$f_sessionId=$_POST['f_sessionId'];
$f_criteria=$_POST['f_criteria'];
$f_allow=$_POST['f_allow'];
$f_note=$_POST['f_note'];
$f_time=$_POST['f_time'];

$maintable = "selection";
$particledata = new particledata();
$prikey = $particledata->mysql->getPriKey($maintable);
$id = $particledata->getId( array('Name' => $f_name), $maintable, $prikey);
switch ($_POST['bt_action']) {


	case "get":
			$id = $particledata->getId( array($prikey => $f_sel_name), $maintable, $prikey);
			break;
	case "save":
			$data['Name'] = $f_name;
			$data['SessionId'] = $f_sessionId;
			$data['Criteria'] = $f_criteria;
			$data['AllowPublic'] = $f_allow;
			$data['Note'] = $f_note;
			$data['Time'] = $f_time;
			
			if ($id) {
				$where[$prikey] = $id;
				$particledata->mysql->SQLUpdate($maintable, $data, $where);
			} else {
				$id = $particledata->mysql->SQLInsert($maintable, $data);
			}
			break;
	case "remove":
			$where[$prikey]=$id;
			$f_name="";
			$particledata->mysql->SQLDelete($maintable, $where);
			break;
}

$info = $particledata->mysql->getSQLResult("select * from `$maintable` where `$prikey`='$id'");
$info = $info[0];
if ($info) {
	$f_name = $info['Name'];
	$f_sessionId = $info['SessionId'];
	$f_criteria = $info['Criteria'];
	$f_allow = $info['AllowPublic'];
	$f_note = $info['Note'];
	$f_time = $info['Time'];
} else {
	$f_sessionId = "";
	$f_criteria = "";
	$f_allow = "N";
	$f_note= "";
	$f_time= "00:00:00";
}

$allow_Y = ($f_allow=='Y') ? 'checked' : '';
$allow_N = ($f_allow=='N') ? 'checked' : '';

$selections = $particledata->getSelections();
ptcl_header('onload="init()"');
?>
<script>

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
		document.data.f_criteria.focus();
	}
<?php } else { echo "}"; } ?>
}

function enable_groupdata(state) {
}

</script>
<h3>Table: <?php echo $maintable; ?></h3>
<table  border=0 cellspacing=1>
<form method="POST" name="data" enctype="multipart/form-data" action="<?php echo $_SERVER['PHP_SELF']; ?>">
<tr valign="top">
<td>
<select name="f_sel_name"  SIZE=20 onClick="update_data();" onchange="update_data();">
<?php
foreach ($selections as $selection) {
	echo "<option value='".$selection['SelectionId']."' $s>".$selection['Name']."</option>\n"; 
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
<tr>
<td class="dt1" height="40">
Name:<font color="red">*</font>
</td>
<td class="dt1"> 
<input class="field" type="text" name="f_name" maxlength="20" size="17" value ="<?php echo $f_name; ?>" onBlur="check_name();" onchange="check_name();"  >
</td>
<?php if ($error) { ?>
<td valign="top">
<div style='position: absolute; padding: 3px; border: 1px solid #000000;background-color: #ffffc8'><?php echo $error; ?></div></td>
<?php } ?>
</tr>
</td>
</tr>
<tr>
<td class="dt2" height="40">
Session:
</td>
<td class="dt2" >
<select name="f_sessionId"  SIZE=1 >
<?php
foreach ($sessions as $session) {
	$s = ($f_sessionId == $session['id'] ) ? 'selected' : '';
	echo "<option value='".$session['id']."' $s>".$session['name']."</option>\n"; 
} 
?>
</select>
</td>
</tr>

<tr>

<td class="dt1" height="40">
Criteria:
</td>
<td class="dt1"> 
  <textarea class="textarea" name="f_criteria" cols="15" rows="2" nowrap><?php echo htmlentities(stripslashes($f_criteria)); ?></textarea>
</td>
</tr>

<tr>
<td class="dt2" height="40">
Allow public:
</td>
<td class="dt2"> 
N<input class="field" type='radio' name='f_allow' value='N' <?php echo $allow_N; ?> >
Y<input class="field" type='radio' name='f_allow' value='Y' <?php echo $allow_Y; ?> >
</td>
</tr>

<tr>
<td class="dt1" height="40">
Note:
</td>
<td class="dt1"> 
  <textarea class="textarea" name="f_note" cols="15" rows="2" nowrap><?php echo htmlentities(stripslashes($f_note)); ?></textarea>
</td>
</tr>

<tr>
<td class="dt2" height="40">
Time:
</td>
<td class="dt2"> 
<input class="field" type="text" name="f_time" maxlength="20" size="17" value ="<?php echo $f_time; ?>" >
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
<?php ptcl_footer(); ?>
