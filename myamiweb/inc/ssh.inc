<?php

/**
 *      The Leginon software is Copyright 2007 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

require_once "../processing/inc/cluster.inc";

$showDebug = false;
$showErrors = false;
$connError = 'NOTSET';
$errorMessage = "No error code has been set by the system.";
$testNewStuff = true;


function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22) 
{
	global $testNewStuff;
	global $errorMessage;
	
	if ( $testNewStuff ) {
		
		$sshResult = true;
		
		$cluster = new Cluster($host);
		if ( $cluster->usesLoginMethod() ) {			
			try {
				$sshResult = $cluster->executeOnHost($username, $password, $command, $result, $port);
			} catch(Exception $e) {
	  			$errorMessage = 'Error executing over ssh on host: '.$host.' sending command: '.$command.' username: '.$username.' Error Message: ' .$e->getMessage();
	  			$sshResult = false;
			}
			
			return $sshResult;
		}
	}
	
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
	
	// Not sure why this is here, but submission appears to fail without it.
	// was set to 1.1, but having trouble. increasing sleep time to 5.1. AH
	sleep(5.1);

	//stream_set_blocking($stream, true);
	// testing to see if this allows ssh to return after spawning a thread...
	stream_set_blocking($stream, false);
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

function scp($host, $username, $password, $localfile, $remotefile, $mode=0644, $port=22) 
{
	global $testNewStuff;
	global $errorMessage;
	
	if ( $testNewStuff ) {
		
		$sshResult = true;
		
		$cluster = new Cluster($host);
		if ( $cluster->usesLoginMethod() ) {			
			try {
				$sshResult = $cluster->copyToHost($username, $password, $localfile, $remotefile, $mode, $port);
			} catch(Exception $e) {
	  			$errorMessage = 'Error copying file over ssh on host: '.$host.' local file: '.$localfile.' remote file: '.$remotefile.' username: '.$username.' Error Message: ' .$e->getMessage();
	  			$sshResult = false;
			}
			
			return $sshResult;
		}
	}
	
	global $connError;
	
	if (!@is_file($localfile)){
		$msg = $localfile.": No such file\n";
		// TODO: lets use exceptions here instead of die!
		die($msg);
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
	global $testNewStuff;
	global $errorMessage;
	// Testing new ssh methods
	if ( $testNewStuff ) {	
		return $errorMessage;
	}
	
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
