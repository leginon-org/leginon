<?php

class config_class {

	var $server = "cronus4";  // mysql server name
	var $db_user = "dfellman"; // username
	var $db_pass = "1pacha2"; // password
	var $database = "project"; // db name

	var $secret = "jhabiteaguewenheim"; // secret key, CHANGE THIS!!

	var $wsname = "stratocaster"; // website name
	var $config_reg_subj = "website name registration"; // registration email subject
	var $webmaster = "dfellman@scripps.edu"; // webmaster email address

	var $server_url = "http://cronus3.scripps.edu/projectdb/";

	var $error = array (
				 "Passwords donot match each other",
				 "Username is too short. Minimum is 3 valid characters.",
				 "Username is too long. Maximum is 11 valid characters.",
				 "Username contains invalid characters.",
				 "Email address format is invalid.",
				 "Password is too short. Minimum is 3 valid characters.",
				 "Password is too long. Maximum is 20 valid characters.",
				 "Password contains invalid characters.",
				 "Name contains invalid characters.",
				 "School contains invalid characters.",
				 "Age contains invalid characters.",
				 "Sex can either be Male or Female.",
				 "Username already exists.",
				 "A user with that email already exists.",
				 "Some fields were left empty.",
				 "Temporary ID and Username combination incorrect, or account purged.",
				 "Unknown database failure, please try later.",
				 "Your login information was entered but due to an unknown error other details could not be filled in, so please <a href=\"login.html\">login</a> to your account and remove it immediately and then re-register.",
				 "The flushing process was unsuccessful.",
				 "No username corresponding to that email.",
				 "Your reg. details couldnot be updated due to a database fault.",
				 "Your password couldnot be updated due to a database fault.",
				 "Your emails donot match.",
				 "I think your current email and the email you entered for modification are same hence I can't change anything."
				 );

	var $logout_url = "http://cronus3.scripps.edu/projectdb/";

function namer() {
	return $this->wsname;
}

};
