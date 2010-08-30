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
	$error_html = makeSettingsCode($user_id);
	#echo $code_string;
	eval($code_string);
	return $error_html;
}

admin_header('onload="init()"');
$title = "Revert to administrator's Node Settings";
if ($_POST['userId'] && !$_POST['orig']) {
	$title = "";
	$error_html = revertToDefaults($_POST['userId']);
}
if ($_POST['orig']) {
	$title = "";
	if ($_POST['adminId']) {
		$leginondata->importTables('xml/leginonDBSchema.xml');
		require_once("inc/setLeginonDefaultValues.inc");
		$setLeginonDefaultValues = new setLeginonDefaultValues($leginondata->mysql);
	} else {
		$error_html = "Error: No administrator found";
	}
}
?>
<script>


function init() {
}
</script>
<h3><? echo $title ?></h3>
<div align="center">
<?php
$code_string = '';
if ($_POST) {
	if (!$error_html) {
		echo "<h4> default settings restored </h4>";
	} else {
		echo "<h4> ".$error_html." </h4>";
	}
} else {
?>
<form method="POST" action="<?php $_SERVER['PHP_SELF']?>" >
<?
	$q = "select u.`DEF_id` as userId, u.* "
			.",u.username "
			.",concat(u.firstname,' ',u.lastname) as `full name` "
			."from UserData u "
			."where "
			."u.password<>'' ";
	if (privilege('users') <= 3) {
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
				if ($user['username'] == 'administrator') {
					$admin_user = $user;
					continue;
				}
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
<?
		if (privilege('users') > 3) {
?>
			<h3>            OR
			<h3>Revert the administrator's Node Settings to the original installation values.</h3>
			<input type="hidden" name="adminId" value= "<? echo $admin_user['userId'] ?>" >
			<input type="submit" name="orig" value="Revert to Original" >
		
<?
		}
	} else {
		echo "No valid user for this operation";
	} ?>
</form>
<? } ?>
</div>
<?
admin_footer();
?>
