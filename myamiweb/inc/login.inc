<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config.php";
require_once "inc/util.inc";
require_once "inc/mysql.inc";

if (ENABLE_LOGIN) {
	require_once "inc/dbemauth.php";
}

function privilege($type='') {
	global $dbemauth;
	if (ENABLE_LOGIN) {
		$login_check = $dbemauth->is_logged();
		if (is_array($login_check)) {
			if ($type) {
				$q = "select p.`".$type."` as level "
						."from privileges as p "
						."where p.`DEF_id`=".$login_check[2];
				$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
				$r = $dbc->getSQLResult($q);
				return $r[0]['level'];
			} else {
				return 1;
			}
		} else {
			return 0;
		}
	} else {
		return 4;
	}
}

function getLoginUserId() {
	global $dbemauth;
	if (ENABLE_LOGIN) {
		$login_check = $dbemauth->is_logged();
		if (is_array($login_check)) {
			$username = $login_check[0];
			$q = "select u.`DEF_id` as userId "
						."from UserData as u "
						."where u.`username` LIKE '".$username."'";
				$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
				$r = $dbc->getSQLResult($q);
			return $r[0]['userId'];
		}
	}
	return null;
}

function login_header($title="", $javascript="", $onload="") {
	global $_SERVER;
	if (ENABLE_LOGIN) {
	global $dbemauth;
	$redirect=$_SERVER['PHP_SELF'];
	$authorized_files=array(BASE_URL.'login.php', 'lostpass.php', 'register.php', 'confirm.php');
	if (!ereg(implode("|", $authorized_files), $_SERVER['PHP_SELF'])) {
    if (!$login_check = $dbemauth->is_logged()) {
      redirect(BASE_URL.'login.php?ln='.$redirect);
      exit;     
		}
  }

	$login_check = $dbemauth->is_logged();
	$username = $login_check[0];
	$privilege = $login_check[2];
	}
	$url = "ln=".urlencode($_SERVER['REQUEST_URI']);
	$path = getPathFromString($_SERVER['SCRIPT_NAME']);
	$onload = (empty($onload)) ? '' : 'onload="'.$onload.'"';
	echo '
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"  "http://www.w3.org/TR/html4/strict.dtd">
<html>
	<head>
		<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
		<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
		<style>
		.bgimg1 {
			background-image:url('.$path.'/img/banner2.gif);
		}
		</style>
	';
	if (!empty($title))
			echo '<title>',$title,'</title>';
	if (!empty($javascript))
		echo $javascript;
	echo '
	</head>
	<body '.$onload.' >
';
if (ENABLE_LOGIN) {
	if ($username) {
		echo '<a class="header" href="'.BASE_URL.'logout.php">[Logout '.$username.']</a>';
		echo '<a class="header" href="'.BASE_URL.'prefs.php">['.$username.' Prefs]</a>';
	} else {
		if (!ereg(BASE_URL.'login.php', $_SERVER['PHP_SELF']))
			echo '<a class="header" href="'.BASE_URL.'login.php?'.$url.'">[Login]</a>';
		echo '<a class="header" href="register.php?'.$url.'">[register]</a>';
	}
}
}

function login_footer() {
echo '
	</body>
</html>
';
}

function insertlog($username, $ip, $info) {
  global $DB_HOST, $DB_USER, $DB_PASS, $DB;
  $data['username']=$username;
  $data['ip']=$ip;
  $data['info']=$info;
  $dbc=new mysql($DB_HOST, $DB_USER, $DB_PASS, $DB);
  $dbc->SQLInsert('viewer_log', $data);
  return true;
}

function lostpwd(){
	
}

?>
