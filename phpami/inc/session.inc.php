<?php
checkos();
function setsession($name="dbem") {
	session_name($name);
	if (!session_id()) {
		session_start();
	}
}

function endsession($name="dbem") {
	global $_COOKIE, $_SESSION;
	session_destroy();
	if (isset($_COOKIE[session_name($name)])) {
	   setcookie(session_name($name), '', time()-42000, '/');
	}
	foreach($_SESSION as $k=>$v) {
		unset($_SESSION[$k]);
	}

}
function checkos() {
#	echo exec("uname -a");
}
?>
