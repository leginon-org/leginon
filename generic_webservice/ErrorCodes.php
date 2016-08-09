<?php

// A location for generic error codes... 400 is the only one used.  
// The others are just examples

class Error_codes {

	public static function bad_method() {
		header('HTTP/1.1 405 Method Not Allowed');
		header('Allow: GET, PUT, DELETE');
                echo '{"result":"1","message":"No Valid method specified"}';
		exit;
	}
	public static function bad_sig() {           
	        header('HTTP/1.1 401 Unauthorized');
        	echo '{"result":"1","message":"Bad Signature"}';
	        exit;
	}
	public static function bad_permissions() {           
	        header('HTTP/1.1 401 Unauthorized');
        	echo '{"result":"1","message":"Permission Denied"}';
	        exit;
	}
	public static function bad_params() {
		header('HTTP/1.1 400 Bad Request');
		echo '{"result":"1","message":"Bad Parameters"}';
		exit;
	}
	public static function bad_service() {
		header('HTTP/1.1 400 Bad Request');
		echo '{"result":"1","message":"No Such Service"}';
		exit;
	}

}
