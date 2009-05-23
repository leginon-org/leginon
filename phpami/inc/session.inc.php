<?php


/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

/**
 * PHP Session Extension needs to be installed
 */

/**
 * setsession, starts a PHP session (default dbem)
 */
function setsession($name="dbem") {
	session_name($name);
	if (!session_id()) {
		session_start();
	}
}

/**
 * endsession, ends a PHP session (default dbem)
 */
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

?>
