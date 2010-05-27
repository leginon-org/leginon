<?
require('inc/admin.inc');

admin_header('onload="init()"');
if ($_POST) {
	print_r($_POST);
}
?>
<script>


function init() {
}
</script>
<h3>Load Default Settings</h3>
<div align="center">
<?php
if ($_POST) {
	echo "default settings loaded";
} else {
?>
<form method="POST" action="<?php $_SERVER['PHP_SELF']?>" >
<?
	$is_admin = true;
	$q = "select u.`DEF_id` as userId, u.* "
			.",concat(u.firstname,' ',u.lastname) as `full name` "
			."from UserData u "
			."where "
			."u.password<>'' "
			."order by u.`lastname`";
	$users = $leginondata->mysql->getSQLResult($q);
	if ($is_admin) {
	$bt_add= "<input class='bt1' type='submit' name='bt' value='add'>";
	?>
	<select name="userId">
	<?
		echo "<option value='default' > -- select user -- </option>";
		foreach($users as $user) {
			$s = ($user['userId']==$_POST['userId']) ? "selected" : "";
			$firstname = $user['firstname'];
			$lastname = $user['lastname'];
			echo "<option value='".$user['userId']."' $s >"
					.$firstname
					." "
					.$lastname
					."</option>\n";
			
		}
	?>
	</select>
<? } ?>
<br/>
	<input type="submit" name="def" value="Load" >
</form>
<? } ?>
</div>
<?
admin_footer();
?>
