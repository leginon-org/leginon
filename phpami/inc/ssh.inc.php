<?php

/**
 *      The Leginon software is Copyright 2007 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

/**
 *
 *  To use these functions, ssh2 PHP module needs to be installed
 *	http://www.php.net/manual/en/ssh2.installation.php
 *
 */

/**
 *
 * exec_over_ssh: connects and runs a command vi SSH.
 *
 */
function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22) {
	$connection = ssh2_connect($host, $port);
	if (!@ssh2_auth_password($connection, $username, $password)) {
		die('Authentication Failed...');
	}

	if (!$stream = ssh2_exec($connection, $command))
		return false;

	if (!$result)
		return true;

	stream_set_blocking($stream, true);
	if (function_exists("stream_get_contents")) {
		$result = stream_get_contents($stream);
	} else {
		$result = fread($stream,4096);
		fclose($stream);
	}
	return $result;
}

/**
 *
 * scp: copy over SSH.
 *
 */
function scp($host, $username, $password, $localfile, $remotefile, $mode=0644, $port=22) {
	$connection = ssh2_connect($host, $port);
	if (!@ssh2_auth_password($connection, $username, $password)) {
		die("Authentication Failed\n");
	}

	foreach (array($localfile, $remotefile) as $file) {
		if (!@is_file($file)) {
			die("$file: No such file\n");
		}
	}

	if (ssh2_scp_send($connection, $localfile, $remotefile, $mode))
		return true;

	return false;
}

/**
 *
 * check_ssh: authenticate via SSH
 *
 */
function check_ssh($host, $username, $password, $port=22) {
	$connection = ssh2_connect($host, $port);
	$is_connected=(!@ssh2_auth_password($connection, $username, $password)) ? false : true;
	return $is_connected;
}

?>
