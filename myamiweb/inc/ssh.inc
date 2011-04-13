<?php

/**
 *      The Leginon software is Copyright 2007 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

$showDebug = false;
$showErrors = false;
$connError = 'NOTSET';

function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22) {
	global $showDebug;
	global $showErrors;
	global $connError;
	
	if($showDebug) { echo "'$host', '$username', '$command', '$result', '$port'<br/>\n"; }

	if (!function_exists(ssh2_connect)) {
		if($showErrors) { echo "ssh2_connect function does not exist"; }
		return false;
	}

	$connection = @ssh2_connect($host, $port);
	
	if (!$connection){
		$connError='CONERROR';
		return false;
	}
	
	if (!@ssh2_auth_password($connection, $username, $password)) {
		if($showErrors) { echo "ssh2_connect: could not connect to host: $host"; }
		$connError = "AUTHERROR";
		return false;
	}

	
	if (!$stream = ssh2_exec($connection, $command)) {
		if($showErrors) { echo "ssh2_connect: could not run command"; }		
		$connError="EXECERROR";
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
	global $connError;
	
	if (!@is_file($localfile)){
		die("$file: No such file\n");
	}
	
	$connection = ssh2_connect($host, $port);
	
	if (!$connection){
		$connError = "CONERROR";
		return false;
	}
		
	if (!@ssh2_auth_password($connection, $username, $password)) {
		$connError="AUTHERROR";
		die("Authentication Failed\n");
	}

	if (ssh2_scp_send($connection, $localfile, $remotefile, $mode)){
		ssh2_exec($connection, 'exit');
		return true;
	}
	else
		$connError = "COPYERROR";
		    
	return false;
}

function check_ssh($host, $username, $password, $port=22) {
	$connection = ssh2_connect($host, $port);
	$is_connected=(!@ssh2_auth_password($connection, $username, $password)) ? false : true;
	return $is_connected;
}

/* pconnError:
* This function returns a error message string that corresponds to the error 
* set by the remote execution and copy functions.  If the function is 
* called without any paramaters it will use the global variable connError,
* which is set by the remote execution and coppy functions, to determine the 
* correct error message. 
*/
function pconnError($errorno='NOTPASSED') 
{
	global $connError;
	
	//If error code isn't supplied in fuction call, use global variable value.
	if ( 'NOTPASSED' == $errorno){
		$errorno=$connError;
	}
	
	switch ($errorno){
		
		case "CONERROR":			
			$msg = "Connection to remote host failed.";
			$msg .=" Please check the address.";		
			break;

		case "AUTHERROR":
			$msg = "Authentication Failure, verify login credentials";
			break;
			
		case "EXECERROR": 
			$msg = "Could not run command on remote host.";
			break;
	
		case "COPYERROR":
			$msg = "Could not copy file to remote host.  Check permissions on remote file/directory";
			break;
	
		case "NOTSET":
			$msg = "Unkown problem on remote host.  This is not a connection issue.";
			$msg .= " Check executable path and/or file permissions!";
			break;
		default:
			$msg = "Unkown connection error!";  // Unkown value was passed (default)
	}
	
	return $msg;
}

?>
