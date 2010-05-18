<?php

/**
 *      The Leginon software is Copyright 2007 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

$showDebug = false;
$showErrors = false;

function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22) {
	global $showDebug;
	global $showErrors;

	if($showDebug) { echo "'$host', '$username', '$command', '$result', '$port'<br/>\n"; }

	if (!function_exists(ssh2_connect)) {
		if($showErrors) { echo "ssh2_connect function does not exist"; }
		return false;
	}

	$connection = ssh2_connect($host, $port);
	if (!@ssh2_auth_password($connection, $username, $password)) {
		if($showErrors) { echo "ssh2_connect: could not connect to host: $host"; }
		return false;
	}

	if (!$stream = ssh2_exec($connection, $command)) {
		if($showErrors) { echo "ssh2_connect: could not run command"; }
		return false;
	}

	if (!$result)
		return true;
	sleep(1.1);

	stream_set_blocking($stream, true);
	if (function_exists("stream_get_contents")) {
		if($showDebug) { echo "ssh2_connect: stream_get_contents"; }
		$result = stream_get_contents($stream);
	} else {
		if($showDebug) { echo "ssh2_connect: fread"; }
		$result = fread($stream,4096);
		fclose($stream);
	}
	if($showDebug) { echo "<br/><pre>\n"; print_r($result); echo "</pre><br/>\n"; }
	return $result;
}

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

function check_ssh($host, $username, $password, $port=22) {
	$connection = ssh2_connect($host, $port);
	$is_connected=(!@ssh2_auth_password($connection, $username, $password)) ? false : true;
	return $is_connected;
}

?>
