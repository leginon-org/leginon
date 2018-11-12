<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once ("inc/leginon.inc");
require_once "inc/dbemauth.inc";
require_once('inc/admin.inc');

// Change $test to true to print out the code_string without executing it.
$test=false;

$login_check = $dbemauth->is_logged();
$is_admin = (privilege('users')>1);

function addToGlobalString($array,$test=false) {
	global $code_string ;
	if ($test) {
		// Use <br/> for printing on page as testing
		$linebreak = "<br/>";
	} else {
		// Use \n for executing
		$linebreak = "\n";
	}
	foreach($array as $content) {
		$code_string .= $content.$linebreak;
	}
}

function revertToDefaults($user_id,$test=false) {
	global $code_string;
	global $leginondata;
	$array = defaultsettings_fileheader($user_id,$admin_init=false);
	addToGlobalString($array,$test);
	$error_html = makeSettingsCode($user_id,false,false,$test);
	if ($test) {
		echo $code_string;
	} else {
		eval($code_string);
	}
	return $error_html;
}

function revertToSession($user_id,$sessionid,$test=false) {
	global $code_string;
	global $leginondata;
	global $is_admin;
	$sessioninfo = $leginondata->getSessionInfo($sessionid,true);
	if ($sessioninfo['userId']!=$user_id && !$is_admin) return 'Error: Session does not belong to the user';
	$array = defaultsettings_fileheader($user_id,$admin_init=false,$sessionname=$sessioninfo['Name']);
	addToGlobalString($array,$test);
	$error_html = makeSettingsCode($user_id,$sessioninfo['End sqlTimestamp'],$sessioninfo['userId'],$test);
	if ($test) {
		echo $code_string;
	} else {
		eval($code_string);
	}
	return $error_html;
}

admin_header('onload="init()"');


$title = "Revert Node Settings";
if ($_POST['userId'] && !$_POST['orig']) {
	$title = "";
	if ($_POST['sessionId'] && is_numeric($_POST['sessionId']))
		$error_html = revertToSession($_POST['userId'],$_POST['sessionId'],$test);
	else
		$error_html = revertToDefaults($_POST['userId'],$test);
}
if ($_POST['orig']) {
	$title = "";
	if ($_POST['adminId']) {
		$leginondata->importTables('xml/leginonDBSchema.xml');
		require_once("inc/setLeginonDefaultValues.inc");
		new setLeginonDefaultValues($leginondata->mysql);
	} else {
		$error_html = "Error: No administrator found";
	}
}
?>
<script>


function init() {
}
</script>
<h3><?php echo $title ?></h3>
<div align="center">
<?php
$code_string = '';
if ($_POST) {
	if (!$error_html) {
		echo "<h4> Settings Restored </h4>";
	} else {
		echo "<h3> ".$error_html." </h3>";
	}
} else {
?>
<form method="POST" action="<?php $_SERVER['PHP_SELF']?>" >
<?php
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
	$sessions = $leginondata->getSessions();
	if ($is_admin) {
?>
		<select name="userId">
<?php
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
		<select name="sessionId">
<?php
			echo "<option value='default' > -- select a session if you want to revert to it -- </option>";
			foreach($sessions as $session) {
				if (!is_numeric($session['id'])) continue;
				$s = ($session['id']==$_POST['sessionId']) ? "selected" : "";
				$sessionname = $session['name'];
				echo "<option value='".$session['id']."' $s >"
					.$sessionname
					."</option>\n";
			}
?>
		</select>
		<p>* If a session is not selected, default is to revert to the latest administrator settings</p>
		<br/>
		<br/>
		<input type="submit" name="def" value="Revert Node Settings" >
<?php

// Administrator revert to the original
		if (privilege('users') > 3) {
?>
			<h3>            OR
			<h3>Revert the administrator's Node Settings to the original installation values.</h3>
			<input type="hidden" name="adminId" value= "<?php echo $admin_user['userId'] ?>" >
			<input type="submit" name="orig" value="Revert to Original" >
		
<?php
		}
	} else {
		echo "No valid user for this operation";
	} ?>
</form>
<?php } ?>
</div>
<?php
admin_footer();
?>
