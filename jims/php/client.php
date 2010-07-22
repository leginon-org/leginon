<?php

$address = "localhost";
$port = 55123;

function jims_request_array($request_array) {
	$msg = "";
	foreach($request_array as $key => $value){
		$msg .= $key . '=' . $value . '&'; 
	}
	$msg = substr($msg, 0, -1);
	return jims_request_string($msg);
}

function jims_request_string($request_string) {
	global $address;
	global $port;
	$msg = $request_string."\n";   // new line indicates end of request
	$jimsock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	socket_connect($jimsock, $address, $port);
	socket_write($jimsock, $msg, strlen($msg));

	$reply = "";
	do {
			 $recv = "";
			 $recv = socket_read($jimsock, 8192);
			 #$recv = socket_read($jimsock, '100000000');
			 if($recv != "") {
					 $reply .= $recv;
			 }
	} while($recv != ""); 

	return $reply;
}

$reply = jims_request_string($_SERVER["QUERY_STRING"]);
#$reply = jims_request_array($_GET);

header('Content-Type: image/jpeg');
echo($reply);

?>
