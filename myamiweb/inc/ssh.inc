<?php

/**
 *      The Leginon software is Copyright 2007 
 *      Apache License, Version 2.0
 *      For terms of the license agreement
 *      see  http://leginon.org
 *      
 *      This file has basically become an abstaction layer for ssh calls defined in cluster.inc.
 *      It also provides a global error message that can be accessed with pconnError() after a failed ssh command.
 *      At some point in the near future, we should be able to remove this file completely and just use the cluster class directly.
 */

require_once "../processing/inc/cluster.inc";

$errorMessage = "No error code has been set by the system.";

// Set $blocking to true to wait for the command to execute before returning.
function exec_over_ssh($host, $username, $password, $command, $result=false, $port=22, $max_time=1) 
{
	global $errorMessage;		
	$sshResult = true;
	
	try {
		$cluster = new Cluster($host);
		$sshResult = $cluster->executeOnHost($username, $password, $command, $result=$result, $port=$port, $max_time=$max_time);
	} catch(Exception $e) {
  		$errorMessage = 'Failed to execute command ('.$command.') on host ('.$host.') for user ('.$username.'). Message: ' .$e->getMessage();
  		$sshResult = false;
	}
	
	return $sshResult;
}

function scp($host, $username, $password, $localfile, $remotefile, $mode=0644, $port=22) 
{
	global $errorMessage;
	
	$sshResult = true;
	
	try {
		$cluster = new Cluster($host);
		$sshResult = $cluster->copyToHost($username, $password, $localfile, $remotefile, $mode, $port);
	} catch(Exception $e) {
  		$errorMessage = 'Error copying file over ssh on host: '.$host.' local file: '.$localfile.' remote file: '.$remotefile.' username: '.$username.' Error Message: ' .$e->getMessage();
  		$sshResult = false;
	}
	
	return $sshResult;
}

function check_ssh($host, $username, $password, $port=22) {
	$connection = ssh2_connect($host, $port);
	$is_connected=(!@ssh2_auth_password($connection, $username, $password)) ? false : true;
	return $is_connected;
}

function pconnError($errorno='NOTPASSED') 
{
	global $errorMessage;

	return $errorMessage;
}

?>
