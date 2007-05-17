<?php

/**
 *      The Leginon software is Copyright 2007 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22) {
	$connection = ssh2_connect($host, $port);
	if (!@ssh2_auth_password($connection, $username, $password)) 
		die('Authentication Failed...');
	}

	if (!$stream = ssh2_exec($connection, $command))
		return false;

	if (!$result)
		return true;

	stream_set_blocking($stream, true);
	if (function_exists(stream_get_contents)) {
		$result = stream_get_contents($stream);
	} else {
		$result = fread($stream,4096);
		fclose($stream);
	}
	return $result;
}

?>
