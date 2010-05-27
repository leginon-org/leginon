<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once ("inc/leginon.inc");
require_once "inc/dbemauth.php";
require('inc/admin.inc');

$login_check = $dbemauth->is_logged();
$is_admin = (privilege('users')>1);

function addToGlobalString($array) {
	global $code_string ;
	#$linebreak = "<br/>";
	$linebreak = "\n";
	foreach($array as $content) {
		$code_string .= $content.$linebreak;
	}
}

function revertToDefaults($user_id) {
	global $code_string;
	global $leginondata;
	$array = defaultsettings_fileheader($user_id,$admin_init=false);
	addToGlobalString($array);
	makeSettingsCode($user_id);
	eval($code_string);
}

admin_header('onload="init()"');
if ($_POST['userId']) {
	revertToDefaults($_POST['userId']);
}
?>
<script>


function init() {
}
</script>
<h3>Revert to administrator's Node Settings</h3>
<div align="center">
<?php
$code_string = '';
if ($_POST) {
	echo "<h4> default settings restored </h4>";
} else {
?>
<form method="POST" action="<?php $_SERVER['PHP_SELF']?>" >
<?
	$q = "select u.`DEF_id` as userId, u.* "
			.",concat(u.firstname,' ',u.lastname) as `full name` "
			."from UserData u "
			."where "
			."u.password<>'' ";
	if (privilege('users') >3) {
		$q .= "and u.username not like 'administrator' ";
	} elseif (privilege('users') <= 3) {
		$q .=	"and u.`DEF_id` = ".getLoginUserId()." ";
	}
	$q .=	"order by u.`lastname`";
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
<br/>
<br/>
	<input type="submit" name="def" value="Revert" >
<? } else {
		echo "No valid user for this operation";
	} ?>
</form>
<? } ?>
</div>
<?
admin_footer();
?>
