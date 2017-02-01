<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "config.php";
require_once "inc/util.inc";
require_once "inc/mysql.inc";
require_once "inc/path.inc";

require_once "inc/dbemauth.inc";

function privilege($type='data') {
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
				return $r[0]['level'] + 0;
			} else {
				return 0;
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
		} else {
			return false;
		}
	} else {
		return true;
	}
}

function isAdvancedUser() 
{
	global $dbemauth;
	if (ENABLE_LOGIN) {
		$login_check = $dbemauth->is_logged();
		if (is_array($login_check)) {
			$username = $login_check[0];
			$q = "select u.`advanced` as advanced "
						."from UserData as u "
						."where u.`username` LIKE '".$username."'";
			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
			$r = $dbc->getSQLResult($q);
			return $r[0]['advanced'];
		} else {
			return false;
		}
	} else {
		return false;
	}
}

function checkProjectAccessPrivilege($projectId) {
	$userId = getLoginUserId();
	if (is_numeric($projectId)) {	
		if ($userId === true || privilege('projects')>=3) return true;
		if ($userId) {
			global $dbemauth;
			$q = "select o.`DEF_id` as ownerId "
				."from projectowners o "
				."where o.`REF|projects|project` = ".$projectId." "
				."and o.`REF|leginondata|UserData|user` = ".$userId." "
				;
			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
			$r = $dbc->getSQLResult($q);
			if (is_array($r) && !empty($r)) 
				return true;
		}
	}
	redirect(BASE_URL.'accessdeny.php');
	return false;
}

function checkProjectAdminPrivilege($projectId) {
	if (privilege('projects') < 2 || empty($projectId)) return false;
	$userId = getLoginUserId();
	if ($userId === true || privilege('projects')>=4) return true;
	if ($userId) {
		global $dbemauth;
		$q = "select o.`DEF_id` as ownerId "
			."from projectowners o "
			."where o.`REF|projects|project` = ".$projectId." "
			."and o.`REF|leginondata|UserData|user` = ".$userId." "
			;
		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
		$r = $dbc->getSQLResult($q);
		if (is_array($r) && !empty($r)) 
			return true;
	}
	return false;
}

function checkExptAccessPrivilege($sessionId,$privilege_type='data',$min_privilege_level=1) {
	// return true or redirect
	$userId = getLoginUserId();
	
	if(!$userId || !$sessionId){
		$redirect=$_SERVER['PHP_SELF']."?";
		
		foreach($_GET as $key => $value)
			$redirect .= $key.'='.$value.'&';	

		redirect(BASE_URL.'login.php?ln='.$redirect);
	    exit;
	}
	$r = hasExptAccessPrivilege($sessionId,$privilege_type, $min_privilege_level);
	if ( !$r ) {
		// arrives here if no view privilege
		redirect(BASE_URL.'accessdeny.php');
		exit;
	}
	return true;
}

function hasExptAccessPrivilege($sessionId,$privilege_type='data',$min_privilege_level=1) {	
	// return true or false but not redirect
	//Access privilege of data means data viewing/downloading and processing result viewing are allowed
	$userId = getLoginUserId();
	$privilege_level = privilege($privilege_type);

	// administrators
	if ($userId === true || $privilege_level >=3) return true;

	if ($userId && $privilege_level >= $min_privilege_level) {
		// check access privilege for users with owned/shared view privilege
		global $dbemauth;
		// experiment shared to the user
		$q = "select sh.`DEF_id` as shareId "
			."from shareexperiments sh "
			."where sh.`REF|leginondata|SessionData|experiment` = ".$sessionId." "
			."and sh.`REF|leginondata|UserData|user` = ".$userId;
				$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
				$r = $dbc->getSQLResult($q);
		if ($r != false && (array)$r) return true;

		// project owner
		$q = "select o.`DEF_id` as ownerId "
			."from projectexperiments pe "
			."left join ".DB_LEGINON.".`SessionData` s "
			."on s.`DEF_id` = pe.`REF|leginondata|SessionData|session` "
			."left join projectowners o "
			."on o.`REF|projects|project` = pe.`REF|projects|project` "
			."where s.`DEF_id` = ".$sessionId." "
			."and o.`REF|leginondata|UserData|user` = ".$userId;
		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
		$r = $dbc->getSQLResult($q);
		if (is_array($r) && !empty($r)) 
			return true;
	}
	// arrives here if no privilege
	return false;
}
	
function checkExptAdminPrivilege($sessionId,$privilege_type='data') {
	// Admin privilege of data means data processing and session.comment editing is allowed
	// return true or redirect
	if ( hasExptAdminPrivilege($sessionId,$privilege_type) ) return true;
	redirect(BASE_URL.'accessdeny.php');
	exit;
}

function hasExptAdminPrivilege($sessionId,$privilege_type='data') {
	// Admin privilege of data means data processing and session.comment editing is allowed
	// return true or false but not redirect
	if (privilege($privilege_type) < 2 || !$sessionId) return false;
	$userId = getLoginUserId();
	if ($userId === true || privilege($privilege_type)>=4) return true;
	if ($userId) {
		// for other users,data processing is allowed if access is allowed and allow to administrate privilege_type.
		return hasExptAccessPrivilege($sessionId,$privilege_type='data', $min_privilege_level=2);
	}
	return false;
}

function checkProjectExptAdminPrivilege($projectId,$privilege_type='data') {
	if (privilege($privilege_type) < 2 || !$projectId) return false;
	$userId = getLoginUserId();
	if ($userId === true || privilege($privilege_type)>=4) return true;
	if ($userId) {
		global $dbemauth;
		$q = "select o.`DEF_id` as ownerId "
			."from projectowners o "
			."where o.`REF|projects|project` = ".$projectId." "
			."and o.`REF|leginondata|UserData|user` = ".$userId;
				$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
				$r = $dbc->getSQLResult($q);
		if (is_array($r) && !empty($r)) 
			return true;
	}
	return false;
}

function login_header($title="", $javascript="", $onload="",$athome=false) {
	global $_SERVER;
	if (ENABLE_LOGIN) {
		global $dbemauth;
		
		
		$redirect=$_SERVER['PHP_SELF']."?";
		
		foreach($_GET as $key => $value)
			$redirect .= $key.'='.$value.'&';
		
		$authorized_files=array(BASE_URL.'login.php', 'lostpass.php', 'register.php', 'confirm.php');
	
		$login_check = $dbemauth->is_logged();
		if (!preg_match('%'.implode("|", $authorized_files).'%', $_SERVER['PHP_SELF'])) {
	   	if (!$login_check)  {
				//  unautorized files can only be loaded if logged in
				redirect(BASE_URL.'login.php?ln='.$redirect);
				exit;
			} else {
				// not allow user with zero privilege to login
				if (privilege('data') < 1) {
					redirect(BASE_URL.'logout.php');
					exit;
				}
			}
		} else {
			// authorized files
  		if($login_check) {
				if (privilege('data') > 0) {
					redirect(BASE_URL);
					exit;
				} else {
					// not allow user with zero privilege to login
					redirect('logout.php');
					exit;
				}
			}
		}

		$username = $login_check[0];
	}
	$url = "ln=".urlencode($_SERVER['REQUEST_URI']);
	$path = Path::getPathFromString($_SERVER['SCRIPT_NAME']);
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
	// To display a notice to users on the processing header, add the following line to the myami/config.php file:
	// define('STARTUP_MESSAGE', "Your Message here");
	if (defined('STARTUP_MESSAGE') && STARTUP_MESSAGE != '') {
		echo "<font size=-1><b>Important Notice:</b> ".STARTUP_MESSAGE."</font><br><br>\n";
	}	
	
	if (!$athome)
		echo '<a class="header" href="'.BASE_URL.'index.php">[Home]</a>';	
	if (ENABLE_LOGIN) {
		if ($username) {
			echo '<a class="header" href="'.BASE_URL.'logout.php">[Logout '.$username.']</a>';
			if($username != 'Anonymous')
				echo '<a class="header" href="'.BASE_URL.'prefs.php">['.$username.' Profile]</a>';
		} else {
			if (!preg_match('%'.BASE_URL.'login.php%', $_SERVER['PHP_SELF']))
				echo '<a class="header" href="'.BASE_URL.'login.php?'.$url.'">[Login]</a>';
			# register is no longer used
			//echo '<a class="header" href="register.php?'.$url.'">[register]</a>';
		}
	}

	
}

function login_footer() {
echo '
	</body>
</html>
';
}

?>
