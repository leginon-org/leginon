<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config.php";
require_once "Mail.php";

class authlib{

	var $error = array (
				 "passwd_not_match"=>"Passwords do not match each other",
				 "passwd_short"=>"Password is too short. Minimum is 3 valid characters.",
				 "passwd_long"=>"Password is too long. Maximum is 20 valid characters.",
				 "passwd_invalid"=>"Password contains invalid characters.",
				 "username_exists"=>"Username already exists.",
				 "username_email_exists"=>"A user with that email already exists.",
				 "username_short"=>"Username is too short. Minimum is 3 valid characters.",
				 "username_long"=>"Username is too long. Maximum is 11 valid characters.",
				 "username_invalid"=>"Username contains invalid characters.",
				 "email_invalid"=>"Email address format is invalid.",
				 "name_invalid"=>"Name contains invalid characters.",
				 "hash_invalid"=>"Hash is not valid.",
				 "fields_empty"=>"Some fields were left empty.",
				 "temp_username_incorrect"=>"Temporary ID and Username combination incorrect, or account purged.",
				 "database_error"=>"Unknown database failure, please try later.",
				 "confirm_email_error"=>"Unknown email server failure, please try again later.",
				 "flushing"=>"The flushing process was unsuccessful.",
				 "username_email"=>"No username corresponding to that email.",
				 "no_email"=>"The email address entered could not be found. ",
				 "no_username" => "The username entered could not be found.",
				 "database_err1"=>"Your registration details could not be updated.",
				 "database_err2"=>"Your password could not be updated due to a database fault.",
				 "emails_not_match"=>"Your emails do not match.",
				 "emails_match"=>"I think your current email and the email you entered for modification are same hence I can't change anything."
				 );

	function register ($username, $password, $password2, $email, $lastname, $firstname) {

		if (!$username || !$password || !$password2 || !$email || !$lastname || !$firstname) {

			return $this->error['fields_empty'];

		}

		else {

			if (!eregi("^[a-z ]+$", $lastname)) {

				return $this->error['name_invalid'];

			}
			
			if(!eregi("^[0-9a-z ]+$", $firstname)) {

				return $this->error['name_invalid'];

			}
			
			$filterError = $this->filter_email($email);
			
			if(!empty($filterError))
				return $filterError;
				
			$filterError = $this->filter_username($username);
			
			if(!empty($filterError))
				return $filterError;
				
			if ($password != $password2) {

				return $this->error['passwd_not_match'];

			}

			$filterError = $this->filter_password($password);
			if(!empty($filterError))
				return $filterError;
			
			
			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

			if (!get_magic_quotes_gpc()) {
				$username=addslashes($username);
			}

			$q="select DEF_id from UserData where username = '$username'";
			$query = $dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);

			if ($result > 0) {

				return $this->error['username_exists'];

			}
			
			$now=date('Y-m-d H:i:s', time());
			$hash = md5($username.$now);
			$password = md5($password);
			
			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
			
			$q = "Insert into confirmauth (mdhash, username, password, firstname, lastname, email, date)
					values ('$hash', '$username', '$password', '$firstname', '$lastname', '$email', now())";

			if(!$dbc->SQLQuery($q)){
				return $this->error['database_error'];		
			}	
			$from = EMAIL_TITLE." <".ADMIN_EMAIL.">";
			$to = $firstname . " " . $lastname . " <" . $email . ">";
			$subject = "Registration: Appion / Legnion Tools";
			$body = "Thank you, $firstname for registering. Here is the information we received: \n\n "
						."First name:	$firstname \n "
						."Last name:	$lastname \n "
						."Email:		$email \n "
						."Username		$username \n "
						."You need to confirm the account by pointing your browser at \n "
						.'http://'.$_SERVER['HTTP_HOST'].BASE_URL.'confirm.php?hash='.$hash. "\n\n "
						."If you did not apply for the account, please ignore this message.";	
						
			$sendEmailResult = $this->outgoingMail($from, $to, $subject, $body);			
			
			if(!$sendEmailResult)
				return $this->error['confirm_email_error'];
			return 2;
				

		}

	}
	
	
	/*
	 * This registation is for adminstrator manually create user
	 * No email will be send out and no confirmation needed.
	 */
	function adminRegister($username, $firstname, $lastname, $title, $institution, $dept, 
						$address, $city, $statecountry, $zip, $phone, $fax, $email, $url, 
						$password, $password2, $groupId){

		if (empty($username) || empty($password) || empty($password2) || empty($email) || empty($lastname) || empty($firstname)) {
			return $this->error['fields_empty'];

		}

		if (!eregi("^[a-z ]+$", $lastname)) {

		return $this->error['name_invalid'];

		}
		
		if(!eregi("^[0-9a-z ]+$", $firstname)) {

			return $this->error['name_invalid'];

		}
		
		$filterError = $this->filter_email($email);
		
		if(!empty($filterError))
			return $filterError;
			
		$filterError = $this->filter_username($username);
		
		if(!empty($filterError))
			return $filterError;
			
		if ($password != $password2) {

			return $this->error['passwd_not_match'];

		}

		$filterError = $this->filter_password($password);
		if(!empty($filterError))
			return $filterError;

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

		if (!get_magic_quotes_gpc()) {
			$username=addslashes($username);
		}

		$q="select DEF_id from UserData where username = '$username'";
		$query = $dbc->SQLQuery($q);
		$result = @mysql_num_rows($query);

		if ($result > 0) {
			return $this->error['username_exists'];
		}

		$fullname = $firstname . ' '. $lastname;
		$password = md5($password);
		
		$q = "insert into UserData (username, firstname, lastname, 
							`REF|GroupData|group`, password, email) 
				  values ('$username', '$firstname', '$lastname'," . $groupId 
							.", '$password', '$email')";
		if(!$dbc->SQLQuery($q)){

			return $this->error['database_error'];		
		}

		$user = $this->getUserInfo($username);
		
		if(!empty($user)){
			
			$dbp=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
			
			$userId = $user['DEF_id'];
			$addUserDetails = "insert into userdetails (
					  `REF|leginondata|UserData|user`, title, institution,
					  dept, address, city, statecountry, zip, phone, fax, url) 
					  values ($userId, '$title', '$institution', '$dept', 
					  '$address', '$city', '$statecountry', '$zip', '$phone',
					  '$fax', '$url')";	

			if(!$dbp->SQLQuery($addUserDetails)){
				return $this->error['database_error'];
			}
		}
				
		return 2;
		
	}
	function updateUser($userId, $username, $firstname, $lastname, $title, $institution, $dept, 
						$address, $city, $statecountry, $zip, $phone, $fax, $email, $url, $chpass, 
						$password, $password2, $groupId=null) {

		if (empty($firstname) || empty($lastname) || empty($email)) {

			return $this->error['fields_empty'];

		}

		if (!eregi("^[a-z ]+$", $lastname)) {

			return $this->error['name_invalid'];

		}

		$filterError = $this->filter_email($email);
		
		if(!empty($filterError))
			return $filterError;

		// check password
		if ($chpass == "on") {

			if ($password != $password2) {
				return $this->error['passwd_not_match'];
			}
			$filterPassword = $this->filter_password($password);
			
			if(!empty($filterPassword))
				return $filterPassword;
		}


		$data=array();

		$data['firstname']=$firstname;
		$data['lastname']=$lastname;
		$data['title']=$title;
		$data['institution']=$institution;
		$data['dept']=$dept;
		$data['address']=$address;
		$data['city']=$city;
		$data['statecountry']=$statecountry;
		$data['zip']=$zip;
		$data['phone']=$phone;
		$data['fax']=$fax;
		$data['email']=$email;
		$data['url']=$url;

		$where['userId']=$userId;

		if (!is_numeric($userId) && $userId) {
			return "userId not valid";
		}


		$hasUserDetail = $this->hasUserDetail($userId);

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

		$fullname = $firstname . ' '. $lastname;
		
		$q = "update UserData set 
				firstname = '$firstname', 
				lastname = '$lastname', email = '$email'
			  where DEF_id = $userId";

		if(!$dbc->SQLQuery($q)){

			return $this->error['database_error'];		
		}
		
		$dbp=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);

		if($hasUserDetail){
			$userDetailsQuery = 
					"update userdetails set 
					  title = '$title',
					  institution = '$institution',
					  dept = '$dept',
					  address = '$address',
					  city = '$city',
					  statecountry = '$statecountry',
					  zip = '$zip',
					  phone = '$phone',
					  fax = '$fax',
					  url = '$url'
					  where `REF|leginondata|UserData|user` = $userId";
		}else{
			$userDetailsQuery = 
					"insert into userdetails (
					  `REF|leginondata|UserData|user`, title, institution,
					  dept, address, city, statecountry, zip, phone, fax, url) 
					  values ($userId, '$title', '$institution', '$dept', 
					  '$address', '$city', '$statecountry', '$zip', '$phone',
					  '$fax', '$url')";
		}

		if(!$dbp->SQLQuery($userDetailsQuery)){

			return $this->error['database_error'];		
		}	


		if ($chpass){

			$this->updatePassword($userId, $password);
		}
		
		if (!empty($groupId)){
			$this->updateGroupId($userId, $groupId);
		}
		
		return 2;
	}

	function updatePassword($userId, $password) {

		$dbc = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
		$password = md5($password);
		
		$q = "update UserData set password = '$password' where DEF_id = $userId";

		if(!$dbc->SQLQuery($q))
			return false;
		return true;
	}
	
	function updateGroupId($userId, $groupId){
		$dbc = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

		$q = "update UserData set `REF|GroupData|group` = '$groupId' where DEF_id = $userId";

		if(!$dbc->SQLQuery($q))
			return false;
		return true;
		
	}

	function getUserInfo($username) {
			
			$projectDB = DB_PROJECT;
			$this->filter_username($username);

			if (!get_magic_quotes_gpc()) {
					$username = addslashes($username);
			}

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
			
			$q="select du.DEF_id, du.username, du.firstname, du.lastname, du.email, du.password, 
					up.title, up.institution, up.dept, up.address, up.city, up.statecountry, 
					up.zip, up.phone, up.fax, up.url, dg.name
				from ".DB_LEGINON.".UserData du 
				left join ".DB_PROJECT.".userdetails up 
					on du.DEF_id = up.`REF|leginondata|UserData|user` 
				join ".DB_LEGINON.".GroupData dg 
					on du.`REF|GroupData|group` = dg.DEF_id
				where du.username = '".$username."' ";
			
			list($r)=$dbc->getSQLResult($q);

			return $r;
	}

	function hasPassword($userId) {

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
    	$sqlwhere = (is_numeric($userId)) ? "userId=$userId" : "username='$userId'";
    	$q='select *  '
      		.'from UserData '
      		.'where '.$sqlwhere;

		list($r)=$dbc->getSQLResult($q);
		return ($r['password']) ? true : false;
	}
  
	function hasUserDetail($userId){
  		
		if(empty($userId) || !is_numeric($userId)) return false;
		
  		$dbc = new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
  		
  		$q = "select * from userdetails where `REF|leginondata|UserData|user` = $userId";

  		$result = $dbc->getSQLResult($q);
 
  		if(empty($result)) return false;
  		
  		return true;
  	
  	}
  	
  	function getGroupId($name){
  		
  		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
  		
		$q="select DEF_id from GroupData where name = '$name'";
			
		$query=$dbc->SQLQuery($q);
		$result = @mysql_fetch_array($query);

		if(!empty($result))
			return $result['DEF_id'];
		return false;
  	}

	function login ($username, $password) {

		if (empty($username))	
			return $this->error['fields_empty'];
		
		if (empty($password) && $username!='Anonmynous')
			return $this->error['fields_empty'];
		
		if($username != 'Anonmynous'){
			$this->filter_username($username);

			$this->filter_password($password);

			$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

			if (!get_magic_quotes_gpc()) {
				$password=addslashes($password);
				$username=addslashes($username);
			}
			$password = md5($password);
			$q="select DEF_id from UserData where username = '$username' and password = '$password'";
		
			$query=$dbc->SQLQuery($q);
			$result = @mysql_num_rows($query);
		
			if ($result != 1) {
				return false;
			}
		}
		
		$hash = md5($username);
		$expire = (COOKIE_TIME) ? time()+COOKIE_TIME : 0;

		setcookie(PROJECT_NAME, "$username:$hash", COOKIE_TIME);
		return 2;		
		
	}

	function is_logged () {

		global $_COOKIE;
		$cookie = $_COOKIE[PROJECT_NAME];

		$session_vars = explode(":", $cookie);
		$username = $session_vars[0];

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

		$q="select u.DEF_id, g.`REF|projectdata|privileges|privilege` as privilege from UserData as u "
			."left join GroupData as g "
			."on u.`REF|GroupData|group` = g.`DEF_id` "
			."where u.username = '$username'";
		$query=$dbc->SQLQuery($q);
		
		$result = @mysql_num_rows($query);

		if ($result < 1) {

			return false;

		}

		list ($id, $privilege) = mysql_fetch_row($query);

		$hash = md5($session_vars[0]);

		if ($hash != $session_vars[1]) {

			return false;

		} else {

			return array($session_vars[0], $id, $privilege);

		}

	}

	function logout () {

		setcookie(PROJECT_NAME, "", time()-3600);
		
		header("Location: ".BASE_URL);

	}

	function confirm ($hash) {

		if (!$hash || strlen($hash)!=32) {

			return $this->error['hash_invalid'];

		} 
		
		// if already login, redirect to homepage.
		if ($this->is_logged() !==false){
			redirect(BASE_URL);
			exit();
		}
		else {

			$dbP=new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);

			$q="select username, password, firstname, lastname, email "
				."from confirmauth "
				."where mdhash = '$hash'";
			$query = $dbP->SQLQuery($q);
			$result = @mysql_num_rows($query);


			if ($result < 1) {
				return $this->error['database_err1'];
			}

			list($username,$password,$firstname,$lastname,$email) = mysql_fetch_row($query);

			
			$dbL = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
			
			$fullname = $firstname. ' '. $lastname;
			$grUserId = $this->getGroupId(GP_USER);
			$q = "insert into UserData (username, firstname, lastname, 
							`REF|GroupData|group`, password, email) 
				  values ('$username', '$firstname', '$lastname'," . $grUserId .", '$password', '$email')";
				
				// insert user to UserData table
			if(!$dbL->SQLQuery($q)){	
				return $this->error['database_err1'];
			}
		
				// remove registration 
			$dbP->SQLDelete("confirmauth", array('username'=>$username));

			$from = EMAIL_TITLE . " <".ADMIN_EMAIL.">";
			$to = $firstname . " " . $lastname . " <" . $email . ">";
			$subject = "Create Account Confirmation: Appion / Legnion Tools";
			
			$body = "Thank You, $firstname for registering. Here is the information we received :\n
					\nFirst Name	: $firstname
					\nLast Name		: $lastname
					\nEmail    		: $email
					\nUsername 		: $username
					\nYou can login to the system by using your username and password at the following link
					\nURL			: http://". $_SERVER['HTTP_HOST'] . BASE_URL."\n\n";

			
			$sendEmailResult = $this->outgoingMail($from, $to, $subject, $body);			
			
			if(!$sendEmailResult)
				return $this->error['confirm_email_error'];
			return 2;

		}

	}

	function conf_flush () {


		$q="delete from confirmauth where date_add(date, interval 2 day) < now()";

		if (!$query) {

			return $this->error['flushing'];

		}

		return 2;

	}

	function lostpwd ($username) {

		// check input variable has value
		if (empty($username)) {
			return $this->error['fields_empty'];
		}

		$dbc=new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);

		$q="select DEF_id, username, firstname, lastname, email from UserData where username = '$username'";

		$query = $dbc->SQLQuery($q);
		$result = @mysql_num_rows($query);

		// setup query result value and assign to those variables
		list($userID, $username, $firstname, $lastname, $email) = @mysql_fetch_row($query);

		if (!$username) {
			return $this->error['no_username'];
		}
		
		// generate new password for user
		$password=$this->generatePassword();
		
		// assign new password to this user
		$result = $this->updatePassword($userID, $password);

		// sent out email with necessary information.
		$from = EMAIL_TITLE . " <".ADMIN_EMAIL.">";

		$to = $firstname . " " . $lastname . " <" . $email . ">";

		$subject = "Forget password: Account Infomation: Appion / Legnion Tools";
		$body = "Dear User,\n\nAs per your request here is your account information:\n
				Username: $username
 				Password: $password
 				\nYou can use this password to login and change your password in your profile page.
 				\nPlease use the following link to login : http://". $_SERVER['HTTP_HOST'] . BASE_URL .
				"\nWe hope you remember your password next time ;-)"; 

		$sendEmailResult = $this->outgoingMail($from, $to, $subject, $body);			
	
		if(!$sendEmailResult)
			return $this->error['confirm_email_error'];
		return 2;

	}


	function confirm_email($id, $email, $mdhash) {

		if (!$id || !$email || !$mdhash) {

			return '$this->error[14]';

		}

		else {

			mysql_connect(DB_HOST, DB_USER, DB_PASS);
			mysql_select_db(DB_LEGINON);

			$query = mysql_query("select * from confirmauth where id = '$id' AND email = '$email' AND mdhash = '$mdhash'");
			$result = @mysql_num_rows($query);

			if ($result < 1) {

				mysql_close();

				return $this->error[15];

			}

			$update = mysql_query("update UserData set email = '$email' where id = '$id'");
			$delete = mysql_query("delete from confirmauth where email = '$email'");

			mysql_close();

			return 2;

		}

	}

	function email_flush () {

		mysql_connect(DB_HOST, DB_USER, DB_PASS);
		mysql_select_db(DB_LEGINON);

		$query = mysql_query("delete from confirmauth where date_add(date, interval 2 day) < now()");

		mysql_close();

		if (!$query) {

			return $this->error[18];

		}

		return 2;

	}

	function chpass ($id, $password, $password2) {

		if ($password != $password2) {

			return $this->error[0];

		}

		else {

			if (strlen($password) < 5) {

				return $this->error[5];

			}

			if (strlen($password) > 20) {

				return $this->error[6];

			}

			if (!ereg("^[[:alnum:]_-]+$", $password)) {

				return $this->error[7];

			}

			mysql_connect(DB_HOST, DB_USER, DB_PASS);
			mysql_select_db(DB_LEGINON);
			$password = md5($password);
			
			$query = mysql_query("update UserData set password = '$password' where id = '$id'");

			mysql_close();

			if (!$query) {

				return $this->error[21];

			}

			return 2;

		}

	}

	function delete($id) {

		mysql_connect(DB_HOST, DB_USER, DB_PASS);
		mysql_select_db(DB_LEGINON);

		$query = mysql_query("delete from UserData where id = '$id'");

		mysql_close();

		return 2;

	}

	function filter_password($val) {

			if (strlen($val) < 3) {
				return $this->error['passwd_short'];

			}

			if (strlen($val) > 20) {

				return $this->error['passwd_long'];

			}

			if (!ereg("^[\*@[:alnum:]._-]+$", $val)) {

				return $this->error['passwd_invalid'];

			}
			
	}

	function filter_username($val) {
			if (strlen($val) < 3) {

				return $this->error['username_short'];

			}
			if (strlen($val) > 20) {

				return $this->error['username_long'];

			}
			if (!ereg("^[[:alnum:]_]+$", $val)) {

				return $this->error['username_invalid'];

			}

	}
	
	function filter_email($val) {

			if (!eregi("^([a-z0-9]+)([._-]([a-z0-9]+))*[@]([a-z0-9]+)([._-]([a-z0-9]+))*[.]([a-z0-9]){2}([a-z0-9])?$", $val)) {

				return $this->error['email_invalid'];

			}
	}

	function generatePassword($length=6) {

		$vowels = 'aeuy';
		$chars = 'bdghjmnpqrstvz'.'0123456789';
		$lvowels=strlen($vowels);
		$lchars=strlen($chars);
		$password = '';

		foreach(range(1,$length) as $k) {
			$strfunc=(rand()%2) ? 'strtolower' : 'strtoupper';
			$alt=(rand()%2) ? true: false;
			$c=($alt) ? $chars[(rand() % $lchars)] : $vowels[(rand() % $lvowels)];
			$password .= $strfunc($c);
		}

		return $password;

	}
	
	/*
	 * This method is going to send out email, if will find out
	 * the mail should use smtp or regular mail function by
	 * looking at the config file
	 * return false if email did not get send out
	 * otherwise return true
	 */
	function outgoingMail($from, $to, $subject, $body){

		// build the email headers
		$headers = array('From' => $from,
						 'To' => $to,
						 'Subject' =>$subject);
		
		// find out what type of email sending method and build
		// out the email factory
		$mailFactoryType = (ENABLE_SMTP ? "smtp" : "mail");
		
		if($mailFactoryType == 'smtp'){			
			$authParams = array('host' => SMTP_HOST,
								'auth' => SMTP_AUTH,
                        	  	'username' => SMTP_USERNAME,
                        	  	'password' => SMTP_PASSWORD);
		}
		
		$mailing = Mail::factory($mailFactoryType, $authParams);
		$mail = $mailing->send($to, $headers, $body);
		
		if(PEAR::isError($mail)){
			return false;
		}
		return true;
	}

}

function redirect($location = "index.php") {
        header("Location: $location");
        exit;
}

?>
